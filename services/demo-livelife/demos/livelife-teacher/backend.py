"""LiveLife Habit 4 "Think Win-Win" — TEACHER assessment (demo). Mounted at /demo-livelife/livelife-teacher/api/.

Built to the LiveLife document the LiveLife source document:
  - 8 competencies C1-C8, ONE primary situational question each (the optional probes are not used, so the total is /32),
    each scored 0-4 against that competency's rubric (9.1 anchors).
  - After submitting the teacher sees ONLY the thank-you message. The Teacher Assessment Outcome is a separate page
    (outcome.html), reachable by the link on the thank-you page and from the front page's third button (the latest result).

SINGLE-USER by design: only the LATEST result is kept, in memory; a new submission replaces the last; all
lost on restart. No database, no file, no login. Use made-up names. The stored record also keeps the teacher's answers and any
critical-concern flags for a reviewer later.

WHAT IS WHERE: the AI scoring is NOT here (this service holds no secret). The page sends the eight answers to the website's
/api/demo-livelife-score with kind "teacher" (off unless a person switches it on) and hands the scores back to /submit below.
This demo trusts those scores (it only checks ranges and lengths); a real build must score and store on the server.

THE RECOMMENDATION RULES (the outcome form's proposed thresholds, subject to LiveLife approval) are in ONE place, `recommend`:
  Highly recommend  overall >= 87.5%, C1 and C3 each >= 75%
  Recommend         overall 75-87.49%, C1 and C3 each >= 75%
  Recommend with coaching  overall 50-74.99%, OR C1/C3 below 75%
  Not recommend at this time  overall < 50%, OR a 0 or 1 in C1 or C3, OR a critical safety/inclusion concern
When rules overlap (for example C1 = 1 matches both coaching and not-recommend) the STRICTER one wins. A critical concern
(endorsing shaming, coercion, forced disclosure, discrimination or a harmful consequence) is a separate flag, always a 0 for that
item, and forces "Not recommend" and a reviewer flag whatever the total. A blank answer is a 0 but is NOT a critical concern.
No evaluator, signature or acknowledgement section (by design).

The C1-C8 question wording is also in the website's lib/livelifeDemo/teacher.ts (to score them): change both together.

NB: no `from __future__ import annotations` here. server.py loads this file without putting it in sys.modules, and pydantic then
cannot resolve string annotations on the request models.
"""
import secrets
import threading
from datetime import date, datetime, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

router = APIRouter()

# ---------------------------------------------------------------------------------------------------------------
# The eight primary questions, as the document words them.
# ---------------------------------------------------------------------------------------------------------------
COMPETENCIES = [
    {"id": "C1", "name": "Concept accuracy",
     "question": "Student says: “Think Win-Win means I should let my friend choose so we don’t argue.” What would you say to clarify?"},
    {"id": "C2", "name": "Scenario facilitation",
     "question": "Two students both want to lead poster design. One says, “I’m better, so I should do it.” What do you do next?"},
    {"id": "C3", "name": "Safety and inclusion",
     "question": "A learner says their family cannot afford the clothing discussed. Others begin commenting. How do you respond?"},
    {"id": "C4", "name": "Questioning and active listening",
     "question": "In pair work, one student speaks repeatedly and the other is quiet. What facilitation moves/questions would you use?"},
    {"id": "C5", "name": "Win-Win Agreement teaching",
     "question": "A pair says their agreement is “We will share the game fairly.” What would you ask them to make the agreement complete and specific?"},
    {"id": "C6", "name": "Activity management",
     "question": "You have 12 minutes for pair work. Some students do not understand the task; others finish early. What would you do?"},
    {"id": "C7", "name": "Assessment and formative feedback",
     "question": "Student response: “I will let my friend decide.” How would you assess and respond to this answer?"},
    {"id": "C8", "name": "Reflection and transfer",
     "question": "Learner’s end-of-class goal is “I will be nicer.” How would you help make it actionable?"},
]
C_IDS = [c["id"] for c in COMPETENCIES]
_NAME = {c["id"]: c["name"] for c in COMPETENCIES}
TOTAL_MAX = 4 * len(COMPETENCIES)   # 32
MAX_ANSWER = 800

THANK_YOU = ("Thank you for completing the Habit 4: Think Win-Win teacher assessment. We appreciate your time and responses. "
             "Your assessment has been submitted. You may now continue.")

# 9.1 scoring anchors, used as the rating of one competency.
ANCHORS = {4: "Highly demonstrated", 3: "Demonstrated", 2: "Partially demonstrated", 1: "Limited", 0: "No evidence / critical concern"}

HIGHLY, REC, COACH, NOT = "Highly recommend", "Recommend", "Recommend with coaching", "Not recommend at this time"
GUIDE = [
    (HIGHLY, "overall ≥87.5%, with C1 and C3 each ≥75%."),
    (REC, "overall 75–87.49%, with C1 and C3 each ≥75%."),
    (COACH, "overall 50–74.99%, or C1/C3 below 75%; specify targeted coaching and reassessment."),
    (NOT, "overall <50%, a score of 0 or 1 in C1 or C3, or a critical safety/inclusion concern."),
]
GUIDE_NOTE = "Recommendation guide (proposed thresholds; subject to LiveLife approval)."
CONVERSION = ("Percentage conversion: competency mark = (score ÷ 4) × 100. Overall performance % = (total score ÷ 32) × 100, "
              "when all eight primary questions are scored.")


def whole(x: float) -> int:
    """Round half up for display (Python's round() would turn 62.5 into 62)."""
    return int(x + 0.5)


def competency_percent(score: int) -> float:
    return score * 100 / 4


def overall_percent(scores: List[int]) -> float:
    """Overall performance % = total / 32 x 100 (all eight primary questions scored)."""
    return sum(scores) * 100 / TOTAL_MAX


def overall_rating(scores: List[int]) -> str:
    """The 9.1 anchor of the average score, rounded half up (3.5 reads as Highly demonstrated)."""
    return ANCHORS[min(4, int(sum(scores) / len(scores) + 0.5))]


def recommend(pct: float, c1: int, c3: int, critical: bool) -> str:
    """THE RECOMMENDATION RULES (see the module note). The stricter rule wins when two overlap."""
    if critical or c1 <= 1 or c3 <= 1 or pct < 50:
        return NOT
    if pct >= 87.5 and c1 >= 3 and c3 >= 3:      # C1 and C3 each >= 75% = a score of 3 or 4
        return HIGHLY
    if pct >= 75 and c1 >= 3 and c3 >= 3:
        return REC
    return COACH


def _why(rec: str, pct: float, c1: int, c3: int, critical: bool) -> str:
    p = f"{whole(pct)}%"
    if critical:
        return "A critical safety or inclusion concern was found in at least one response, which means 'Not recommend at this time' whatever the total, plus coaching and reassessment."
    if c1 <= 1 or c3 <= 1:
        return f"C1 (Concept accuracy) or C3 (Safety and inclusion) scored 0 or 1, which means 'Not recommend at this time' whatever the total ({p} overall)."
    if pct < 50:
        return f"Overall performance is {p}, below 50%."
    if rec in (HIGHLY, REC):
        return f"Overall performance is {p}, with C1 and C3 each at 75% or above."
    reasons = []
    if pct < 75:
        reasons.append(f"overall performance is {p}, within the 50–74.99% coaching range")
    if c1 < 3 or c3 < 3:
        reasons.append("C1 or C3 is below 75%")
    text = "; ".join(reasons)
    return text[:1].upper() + text[1:] + "."


# ---------------------------------------------------------------------------------------------------------------
# What the AI scorer sent back for this teacher (validated; never trusted beyond ranges and lengths)
# ---------------------------------------------------------------------------------------------------------------
class Scored(BaseModel):
    score: Optional[int] = Field(default=None, ge=0, le=4)
    evidence: str = Field(default="", max_length=300)
    coaching: str = Field(default="", max_length=300)
    critical: bool = False


class SummaryIn(BaseModel):
    strengths: List[str] = Field(default_factory=list, max_length=5)
    growth: List[str] = Field(default_factory=list, max_length=5)
    coaching_plan: List[str] = Field(default_factory=list, max_length=5)


class ScoredIn(BaseModel):
    results: Dict[str, Scored] = Field(default_factory=dict, max_length=20)
    summary: Optional[SummaryIn] = None


class SubmitIn(BaseModel):
    name: str = Field(default="", max_length=60)
    school: str = Field(default="", max_length=80)
    answers: Dict[str, str] = Field(default_factory=dict, max_length=20)
    scored: Optional[ScoredIn] = None


def _line(s: str, n: int) -> str:
    return " ".join((s or "").split())[:n]


def _fallback_summary(comps: List[dict]) -> dict:
    """Used when the AI gave no usable summary, so the outcome is never empty. Built only from the scores and coaching lines."""
    scored = [c for c in comps if c["score"] is not None]
    good = sorted([c for c in scored if c["score"] >= 3], key=lambda c: -c["score"])[:3]
    low = sorted([c for c in scored if c["score"] <= 2], key=lambda c: c["score"])
    strengths = [f"{c['id']} {c['name']}: {c['rationale']}" if c["rationale"] else f"{c['id']} {c['name']} was demonstrated." for c in good]
    if not strengths:
        strengths = ["No competency reached the Demonstrated level yet, so no strength can be named from these responses."]
    growth = [f"{c['id']} {c['name']} ({c['score']}/4): {c['rationale']}" if c["rationale"] else f"{c['id']} {c['name']} ({c['score']}/4)." for c in low[:3]]
    if not growth:
        growth = ["No competency scored below Demonstrated in the answers given."] if scored else ["The written answers could not be scored this time."]
    plan = [f"{c['id']}: {c['coaching']}" for c in low if c["coaching"]][:3]
    if low:
        plan.append("Reassess " + ", ".join(c["id"] for c in low[:3]) + " with a short follow-up question after coaching.")
    if not plan:
        plan = ["Continue with the usual support; reassess if the programme changes."]
    return {"strengths": strengths[:3], "growth": growth[:3], "coaching_plan": plan[:4]}


def build_outcome(name: str, school: str, scored: Optional[ScoredIn], today: Optional[date] = None) -> dict:
    """The Teacher Assessment Outcome exactly as the form lays it out (minus the evaluator section)."""
    results = scored.results if scored else {}
    comps: List[dict] = []
    for c in COMPETENCIES:
        r = results.get(c["id"])
        score = r.score if r is not None else None
        ok = r is not None and score is not None
        comps.append({
            "id": c["id"], "name": c["name"], "score": score,
            "mark_percent": whole(competency_percent(score)) if ok else None,
            "rating": ANCHORS[score] if ok else None,
            "rationale": _line(r.evidence, 200) if ok else "",       # no text for an answer that was not scored
            "coaching": _line(r.coaching, 200) if ok and score <= 2 else "",
            "critical": bool(ok and r.critical and score == 0),
        })
    for c in comps:
        if c["score"] is None:
            c["rationale"] = "This response could not be scored."
    got = [c["score"] for c in comps if c["score"] is not None]
    complete = len(got) == len(COMPETENCIES)
    critical_items = [c["id"] for c in comps if c["critical"]]
    critical = bool(critical_items)
    by = {c["id"]: c["score"] for c in comps}

    pct = overall_percent(got) if complete else None
    rec = recommend(pct, by["C1"], by["C3"], critical) if complete else None
    # A critical concern forces 'Not recommend' even when some answers could not be scored.
    if not complete and critical:
        rec = NOT

    # The AI's lists where it gave some; the built-in line for any list it left empty (a strong teacher may have no
    # growth areas, and a missing summary falls back entirely), so no block of the outcome is ever blank.
    summ = _fallback_summary(comps)
    if scored and scored.summary:
        sm = scored.summary
        for key, lst in (("strengths", sm.strengths), ("growth", sm.growth), ("coaching_plan", sm.coaching_plan)):
            cleaned = [_line(x, 180) for x in lst if _line(x, 180)][:3]
            if cleaned:
                summ[key] = cleaned

    why = None
    if complete:
        why = _why(rec, pct, by["C1"], by["C3"], critical)
    elif critical:
        why = _why(NOT, 0.0, 0, 0, True)

    d = today or date.today()
    return {
        "teacher": {"name": _line(name, 60), "school": _line(school, 80), "date": d.isoformat(), "version": "demo-1"},
        "score": {"total": sum(got), "max": TOTAL_MAX, "scored": len(got), "of": len(COMPETENCIES),
                  "percent": whole(pct) if pct is not None else None,
                  "overall_rating": overall_rating(got) if complete else None, "complete": complete},
        "recommendation": rec,
        "recommendation_why": why,
        "critical": {"flagged": critical, "items": critical_items},
        "competencies": comps,
        **summ,
        "guide_note": GUIDE_NOTE,
        "guide": [{"label": lbl, "rule": rule} for lbl, rule in GUIDE],
        "conversion": CONVERSION,
    }


# ---------------------------------------------------------------------------------------------------------------
# SINGLE-USER store: the latest result only (no database, no file). A new submission replaces the last one.
# ---------------------------------------------------------------------------------------------------------------
_LOCK = threading.Lock()
_LATEST: Dict[str, object] = {"id": None, "record": None}


def _remember(record: dict) -> str:
    oid = secrets.token_urlsafe(16)
    with _LOCK:
        _LATEST["id"], _LATEST["record"] = oid, record
    return oid


def private_record(oid: Optional[str] = None) -> Optional[dict]:
    """The stored record INCLUDING answers and critical flags, for a reviewer later. Not routed. `oid` None = the latest."""
    with _LOCK:
        if oid is not None and oid != _LATEST["id"]:
            return None
        return _LATEST["record"]  # type: ignore[return-value]


NO_STORE = {"Cache-Control": "no-store"}


@router.get("/items")
def items():
    """Everything the page shows: the eight questions only. No rubric, no indicators."""
    return {"level": "Level 5", "habit": "Habit 4: Think Win-Win",
            "questions": [{"id": c["id"], "question": c["question"]} for c in COMPETENCIES], "thank_you": THANK_YOU}


@router.post("/submit")
def submit(body: SubmitIn):
    """Stores the submission (replacing the last) and returns ONLY an id: the thank-you page must not show scores or a recommendation."""
    name, school = _line(body.name, 60), _line(body.school, 80)
    if not name or not school:
        return JSONResponse({"detail": "Please enter your name or ID and your school."}, status_code=422)
    outcome = build_outcome(name, school, body.scored)
    record = {
        "outcome": outcome,
        "critical_for_reviewer": outcome["critical"]["items"],     # stored for a reviewer; also shown on the outcome page
        "answers": {k: (body.answers.get(k) or "")[:MAX_ANSWER] for k in C_IDS},
        "created": datetime.now(timezone.utc).isoformat(),
    }
    return JSONResponse({"id": _remember(record)}, headers=NO_STORE)


@router.get("/outcome/latest")
def outcome_latest():
    """The most recent teacher's outcome (what the front page's third button opens)."""
    rec = private_record()
    if rec is None:
        return JSONResponse({"detail": "Not found"}, status_code=404, headers=NO_STORE)
    return JSONResponse(rec["outcome"], headers=NO_STORE)


@router.get("/outcome/{oid}")
def outcome(oid: str):
    """The teacher's outcome by its long random id (only the latest result exists)."""
    rec = private_record(oid) if (16 <= len(oid) <= 40 and oid.replace("-", "").replace("_", "").isalnum()) else None
    if rec is None:
        return JSONResponse({"detail": "Not found"}, status_code=404, headers=NO_STORE)
    return JSONResponse(rec["outcome"], headers=NO_STORE)
