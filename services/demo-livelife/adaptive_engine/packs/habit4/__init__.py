"""Habit 4 "Think Win-Win": connects the existing student assessment (Modules 1 and 2) to Modules 3 to 8.

Competencies and items are read from the assessment itself, so there is one source of questions. A knowledge-check answer is an
option letter. A written answer arrives already marked against its 0-4 rubric:
  3 or 4   shown
  2        partly shown: practice, not reteaching
  1        points to the patterns in that rubric level
  0        blank, irrelevant or flagged for an educator: goes to the teacher and is never counted as a misconception
"""
import importlib.util
from pathlib import Path

from ...pack import UNMAPPED, ChapterPack
from .samples import sample
from .knowledge_base import (DISTRACTORS, INTERVENTION_MAP, INTERVENTIONS, LEVEL_ONE_PATTERNS, MISCONCEPTIONS, PARALLEL_SCENARIOS,
                             PROBES, SEPARATING_PROBES, TEACHING_ORDER, VERSION)

PARTIAL = "H4-PARTIAL"
PRACTICE_ATTEMPT_BASE = 100
_BACKEND = Path(__file__).resolve().parents[3] / "demos" / "livelife-student" / "backend.py"


def _load_assessment():
    spec = importlib.util.spec_from_file_location("habit4_assessment_source", _BACKEND)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_assessment = _load_assessment()
COMPETENCIES = {s["id"]: {"name": s["name"], "prerequisites": []} for s in _assessment.SCENARIOS}
ITEMS = [{"id": q["id"], "text": q["stem"], "type": "mcq", "template": "mcq", "competency_ids": [q["competency"]],
          "key": q["key"], "options": q["options"], "level": "easy"} for q in _assessment.MCQS] + \
        [{"id": s["id"], "text": s["question"], "type": "scenario", "template": "scenario", "competency_ids": [s["id"]], "level": "medium"}
         for s in _assessment.SCENARIOS]


def _read_choice(item, raw, trace):
    choice = (raw or "").strip().upper()[:1]
    trace["working"] = choice
    trace["shows_working"] = False
    if not choice:
        trace["result"] = "blank"
    elif choice not in item["options"]:
        trace["result"] = "unreadable"
    elif choice == item["key"]:
        trace["result"] = "correct"
    else:
        trace["result"] = "wrong"
        code = DISTRACTORS.get(item["id"], {}).get(choice)
        trace["findings"].append(dict(belief=code, step="Choice", confidence="medium", evidence=f"chose {choice}: {item['options'][choice]}")
                                 if code else dict(belief=UNMAPPED, step="-", confidence="none", evidence=f"chose {choice}"))
    return trace


def _read_rubric(item, raw, trace):
    answer = raw if isinstance(raw, dict) else {"text": raw or ""}
    text, score = (answer.get("text") or "").strip(), answer.get("score")
    trace["working"] = text
    trace["shows_working"] = bool(text)
    competency = item["competency_ids"][0]
    if answer.get("flag"):
        trace["result"] = "flagged_for_review"
    elif not text:
        trace["result"] = "blank"
    elif score is None:
        trace["result"] = "unreadable"
    elif score == 0:
        trace["result"] = "irrelevant"
    elif score >= 3:
        trace["result"] = "correct"
    else:
        trace["result"] = "wrong"
        evidence = answer.get("evidence") or f"rubric level {score}"
        patterns = [PARTIAL] if score == 2 else LEVEL_ONE_PATTERNS[competency]
        trace["findings"] = [dict(belief=code, step="Rubric", confidence="high", evidence=evidence) for code in patterns]
        if len(patterns) > 1:
            trace["ambiguous"] = list(patterns)
    if score is not None:
        trace["steps"]["Rubric"] = f"level {score}"
    return trace


def read_answer(item, raw):
    trace = {"q": item["id"], "working": "", "steps": {}, "findings": []}
    return _read_choice(item, raw, trace) if item["type"] == "mcq" else _read_rubric(item, raw, trace)


def parallel_item(original, attempt):
    """A new situation for the same competency. Written answers are marked with that competency's existing rubric."""
    competency = original["competency_ids"][0]
    index = 2 + (attempt - PRACTICE_ATTEMPT_BASE) % 2 if attempt >= PRACTICE_ATTEMPT_BASE else (attempt - 1) % 2
    return {"id": f"{competency}-P{attempt}", "text": PARALLEL_SCENARIOS[competency][index], "type": "scenario", "template": "scenario",
            "competency_ids": [competency], "parallel_of": original["id"], "correct": f"Mark with the {competency} rubric"}


def to_sheet(student_id, submission):
    """A stored submission -> the sheet Module 3 reads."""
    results = submission.get("results", {})
    answers = dict(submission.get("mcq", {}))
    for scenario_id, text in submission.get("answers", {}).items():
        result = results.get(scenario_id, {})
        answers[scenario_id] = {"text": text, "score": result.get("score"), "evidence": result.get("evidence", ""),
                                "flag": result.get("flag", False)}
    return {"id": student_id, "answers": answers}


PACK = ChapterPack(
    chapter_id="livelife-habit-4",
    version=VERSION,
    competencies=COMPETENCIES,
    items=ITEMS,
    misconceptions=MISCONCEPTIONS,
    teaching_order=TEACHING_ORDER,
    probes=PROBES,
    separating_probes=SEPARATING_PROBES,
    interventions=INTERVENTIONS,
    intervention_map=INTERVENTION_MAP,
    read_answer=read_answer,
    parallel_item=parallel_item,
    retest_types=("scenario",),
    written_type="scenario",
    rubric_key=lambda item: item["competency_ids"][0],
    sample=sample,
    subject={"subject": "Life Skills", "board": "LiveLife Education", "grade": "Level 5", "chapter": "Habit 4: Think Win-Win", "source": "Discovering the Leader in Me"},
    brief=("LiveLife Education, Discovering the Leader in Me, Level 5, Habit 4: Think Win-Win, students aged 11 to 16. Keep to its three mindsets, courage and "
           "consideration, the Emotional Bank Account as a metaphor, promises, and the five-part Win-Win Agreement. Win-Win does not mean both people get their first choice."),
    upload_hint="K1 to K9: the option letter. S1 to S8: the student's own written answer.",
    extension_task="Draft a Win-Win Agreement for a real situation in your class, then check it for all five parts.",
)

__all__ = ["PACK", "to_sheet"]
