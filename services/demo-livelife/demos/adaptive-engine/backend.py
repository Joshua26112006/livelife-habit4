"""Adaptive Teaching Engine API (demo). Mounted at /demo-livelife/adaptive-engine/api/.

/demo-loop runs Modules 3 to 8 on synthetic sheets with a scripted synthetic re-test. /classes/<id> runs the planning modules on
the Habit 4 sheets submitted with that class id, and returns statuses only, never answer text. The service is public with no
sign-in, so use synthetic sheets until a real deployment adds accounts and storage. The rules are in ../../adaptive_engine.

NB: no `from __future__ import annotations` here (server.py loads this file without putting it in sys.modules, and pydantic
then cannot resolve string annotations on the request models).
"""
import json
import re
from pathlib import Path
from typing import Dict, List

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from adaptive_engine import ClassCycle, analyse_sheets
from adaptive_engine.packs.habit4 import PACK as HABIT4, to_sheet
from adaptive_engine.packs.probability import PACK as PROBABILITY, needs_expert_draft
from adaptive_engine.submissions import CLASS_ID, STORE

router = APIRouter()

NO_STORE = {"Cache-Control": "no-store"}
MAX_STUDENTS = 200
MAX_ANSWER_CHARS = 2000
QUESTION_IDS = {q["id"] for q in PROBABILITY.items}
HERE = Path(__file__).parent
DEMO_TEACHER = "demo-teacher"


class Sheet(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    answers: Dict[str, str]


class AnalyseRequest(BaseModel):
    students: List[Sheet] = Field(min_length=1, max_length=MAX_STUDENTS)


@router.get("/test")
def test_paper():
    """The Probability question paper and the remedies still waiting for an expert draft."""
    return {
        "questions": [{"id": q["id"], "text": q["text"], "type": q["type"], "competency_ids": q["competency_ids"]} for q in PROBABILITY.items],
        "awaiting_expert_draft": needs_expert_draft(),
    }


@router.post("/analyse")
def analyse(request: AnalyseRequest):
    for sheet in request.students:
        for qid, text in sheet.answers.items():
            if qid not in QUESTION_IDS:
                return JSONResponse({"error": "unknown_question", "question": qid[:16]}, status_code=400, headers=NO_STORE)
            if len(text) > MAX_ANSWER_CHARS:
                return JSONResponse({"error": "answer_too_long", "question": qid}, status_code=400, headers=NO_STORE)
    return JSONResponse(analyse_sheets(PROBABILITY, [s.model_dump() for s in request.students]), headers=NO_STORE)


def _scripted_probability_answer(item, outcome):
    """A synthetic re-test answer that produces the named outcome."""
    if item["type"] == "argue":
        parts = re.search(r"has (\d+) equal", item["text"])[1]
        return f"No. {parts} equal parts, so count the parts, not the colours"
    correct = item["correct"]
    if outcome == "demonstrated":
        return f"favourable outcomes over all outcomes: {correct.numerator * 2}/{correct.denominator * 2} = {correct}"
    if outcome == "insufficient":
        return str(correct)
    if outcome == "partial":
        return f"{correct.numerator}/{correct.denominator} = 1/{correct.denominator + 97}"
    predicted = next(s for s in item["signatures"] if s["belief"] == item["target"] and "value" in s)["value"]
    return f"I think it is {predicted}"


# The one thing scripted: how each sample student does on the re-test. All other results are computed.
PROBABILITY_RETEST = {"P02": "demonstrated", "P03": "partial", "P04": "persistent", "P05": "insufficient", "P06": "demonstrated"}
HABIT4_RETEST = {"H02": 4, "H03": 2, "H04": 1, "H05": 3, "H06": 4}


def _habit4_sheets():
    """Fill the sample's differences out into full synthetic sheets."""
    sheets = []
    for student in json.loads((HERE / "sample_habit4.json").read_text())["students"]:
        mcq = {i["id"]: i["key"] for i in HABIT4.items if i["type"] == "mcq"}
        mcq.update(student.get("mcq", {}))
        ids = [i["id"] for i in HABIT4.items if i["type"] == "scenario"]
        scores = {s: student.get("scores", {}).get(s, 4) for s in ids}
        flagged = student.get("flagged", [])
        sheets.append(to_sheet(student["id"], {
            "mcq": mcq,
            "answers": {s: "Synthetic written answer." for s in ids},
            "results": {s: {"score": scores[s], "evidence": f"Synthetic evidence at rubric level {scores[s]}.", "flag": s in flagged} for s in ids},
        }))
    return sheets


def _run_loop(pack, sheets, probes, answer_for):
    cycle = ClassCycle(pack, "demo-class", allow_draft=True)
    cycle.run_diagnostic(sheets)
    for student, code in probes:
        cycle.record_probe(student, code, "supports", DEMO_TEACHER)
    plan = cycle.build_plan()
    cycle.approve_plan(DEMO_TEACHER)
    items = cycle.create_reassessment()
    cycle.submit_reassessment({s: answer_for(s, i) for s, i in items.items()})
    return JSONResponse({
        "note": "Synthetic sheets and a scripted synthetic re-test. Every intervention is an unreviewed draft.",
        "pack": pack.chapter_id,
        "class": cycle.class_view(),
        "students": list(cycle.diagnoses.values()),
        "groups": cycle.groups,
        "plan": plan,
        "reassessment": [{"student": s, "item": {"id": i["id"], "text": i["text"], "answer": str(i.get("correct", "")),
                                                  "parallel_of": i["parallel_of"]}} for s, i in items.items()],
        "outcomes": [{k: r[k] for k in ("student", "target", "outcome", "next_step")} for r in cycle.outcomes],
        "next_cycle": cycle.next_cycle(),
        "profiles": {s: p.view() for s, p in cycle.profiles.items()},
        "audit": cycle.audit,
    }, headers=NO_STORE)


@router.get("/demo-loop")
def demo_loop(pack: str = "probability"):
    """Modules 3 to 8 on synthetic sheets. Drafts are allowed here because no expert has signed them off yet."""
    if pack == "habit4":
        retest = lambda s, _: {"text": "Synthetic re-test answer.", "score": HABIT4_RETEST[s], "evidence": "", "flag": False}
        return _run_loop(HABIT4, _habit4_sheets(), [("H06", "WW-VAGUE")], retest)
    if pack == "probability":
        sheets = json.loads((HERE / "sample_sheets.json").read_text())["students"]
        return _run_loop(PROBABILITY, sheets, [("P06", "MC-L")], lambda s, i: _scripted_probability_answer(i, PROBABILITY_RETEST[s]))
    return JSONResponse({"error": "unknown_pack"}, status_code=404, headers=NO_STORE)


@router.get("/classes/{class_id}")
def class_plan(class_id: str):
    """Modules 3 to 6 for the Habit 4 sheets submitted with this class id. Statuses only: no answer text or evidence lines."""
    submissions = STORE.latest(class_id) if CLASS_ID.match(class_id) else []
    if not submissions:
        return JSONResponse({"detail": "Not found"}, status_code=404, headers=NO_STORE)
    cycle = ClassCycle(HABIT4, class_id, allow_draft=True)
    cycle.run_diagnostic([to_sheet(student, submission) for student, submission in submissions])
    return JSONResponse({
        "class": cycle.class_view(),
        "students": [{"student": d["student"], "next": d["next"], "teacher": d["teacher"], "summary": d["summary"]} for d in cycle.diagnoses.values()],
        "groups": cycle.groups,
        "plan": cycle.build_plan(),
    }, headers=NO_STORE)
