"""LiveLife Habit 4 "Think Win-Win" — STUDENT assessment (demo). Mounted at /demo-livelife/livelife-student/api/.

Built to the LiveLife document the LiveLife source document:
  A. Knowledge Check: 9 MCQs (K1-K8 from the document, K9 added for this demo), 2 marks each, /18, marked HERE by
     plain code with the document's keys.
  B. Situational Check: 8 scenario answers (S1-S8), 0-4 each, /32, scored by the AI on each item's rubric.
  Outcome: a scorecard on a SEPARATE page (outcome.html?id=...) after a thank-you page that shows no marks.

WHAT IS WHERE
  - The answer keys live ONLY in this file (a .py file is never sent to a browser).
  - The AI scoring is NOT here: this service holds no secret. The page sends the eight scenario answers to the main
    site's /api/demo-livelife-score (off unless a person switches it on; its own caps) and hands the scores it gets
    back to /submit below. Nothing here depends on those scores beyond this demo, so /submit trusts them (it only
    checks ranges and lengths). A real build must score and store on the server.
  - Each submission is kept IN MEMORY only (no database, no file): name, grade, answers and marks, under a long random
    id. SINGLE-USER: only the LATEST submission is kept, a new one replaces it, all lost on a restart.
    Use made-up names. The stored record also keeps "flagged for educator
    review" marks (a 0 for disrespect or harm) for a teacher view later; they are NEVER sent to the child.

THE FINAL-RATING CALCULATION is in ONE place: `rating_for` and `final_score` below; change it here only. Now: knowledge /18 (9 MCQs x 2) + situations /32 (8 x 4) = /50, converted to /100 (every raw mark counts double), and
the Final Rating (Emerging / Building / Secure / Strong) comes from that total out of 100 by lower bound 50 / 70 / 85. This
REPLACES the document's "overall application = the eight scenarios only" rule, so the Knowledge Check now counts (36 of 100).
The eight-competency card on the scorecard still comes from the situations alone.

The S1-S8 question wording is also in the website's lib/livelifeDemo/rubrics.ts (to score them); both come from the
document - change both together.

NB: no `from __future__ import annotations` here. server.py loads this file without putting it in sys.modules, and
pydantic then cannot resolve string annotations on the request models.
"""
import re
import secrets
import threading
from collections import OrderedDict
from datetime import date, datetime, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from adaptive_engine.submissions import STORE as CLASS_SUBMISSIONS, valid_ids

router = APIRouter()

# ---------------------------------------------------------------------------------------------------------------
# A. Knowledge Check — exactly as the document gives it (ID / competency, question, options, key, rationale).
# ---------------------------------------------------------------------------------------------------------------
MCQS = [
    {"id": "K1", "competency": "S1", "stem": "What does Think Win-Win mean?",
     "options": {"A": "I get what I want even if you do not.", "B": "I give up what I want every time.",
                 "C": "We look for a solution that considers what matters to both of us.", "D": "We avoid discussing the problem."},
     "key": "C", "why": "A Win-Win solution considers both people’s needs; it is not simply winning, giving in or avoiding conflict."},
    {"id": "K2", "competency": "S2", "stem": "I insist on choosing the game and my friend cannot choose. Which mindset does this most closely show?",
     "options": {"A": "Win-Win", "B": "Win-Lose", "C": "Lose-Win", "D": "Interdependent Living"},
     "key": "B", "why": "One person gets their way at the other person’s expense: Win-Lose."},
    {"id": "K3", "competency": "S3", "stem": "Your partner wants quiet to work, while you want to discuss ideas aloud. What is the best first step?",
     "options": {"A": "Tell them to adjust.", "B": "Stop working.", "C": "Ask what they need and share what you need.", "D": "Decide without asking."},
     "key": "C", "why": "Consideration includes understanding each person’s perspective and needs."},
    {"id": "K4", "competency": "S4", "stem": "Both classmates want to use the same materials at the same time. Which is a possible Win-Win option?",
     "options": {"A": "One takes everything.", "B": "Hide the materials.", "C": "Plan turns or divide materials based on the task.", "D": "Let the louder student decide."},
     "key": "C", "why": "A workable solution can share access or plan turns; the option should be checked with both."},
    {"id": "K5", "competency": "S5", "stem": "What is a helpful way to respond when a classmate explains their point of view?",
     "options": {"A": "Interrupt to correct them.", "B": "Listen and ask a respectful question.", "C": "Laugh.", "D": "Ignore their idea."},
     "key": "B", "why": "Listening and respectful questions help understand the other person."},
    {"id": "K6", "competency": "S6", "stem": "You promised to bring a game but realize you cannot. What is the responsible action?",
     "options": {"A": "Say nothing.", "B": "Blame a friend.", "C": "Tell the person early, explain briefly and agree on a next step.", "D": "Pretend you brought it."},
     "key": "C", "why": "Trust is supported by honest communication and responsible follow-through."},
    {"id": "K7", "competency": "S7", "stem": "Which list contains the five parts of a Win-Win Agreement?",
     "options": {"A": "Desired Results, Guidelines, Resources, Accountability, Consequences.", "B": "Rules, prizes, winner, loser, score.",
                 "C": "Feelings, opinions, grades, rewards, punishment.", "D": "Goals, blame, silence, penalty, winner."},
     "key": "A", "why": "These are the five chapter components."},
    {"id": "K8", "competency": "S8", "stem": "Which is the most useful promise?",
     "options": {"A": "I will always be perfect.", "B": "I will be nice.",
                 "C": "During tomorrow’s group task, I will listen to each partner before suggesting an idea.", "D": "I will never disagree."},
     "key": "C", "why": "The commitment is observable, specific and linked to a context."},
    # K9 is NOT in the LiveLife document: drafted and approved for this demo (a Lose-Win question, since K2
    # only tests Win-Lose). Tagged to S2 (mindset classification) like K2.
    {"id": "K9", "competency": "S2", "stem": "Every break, you let your friend choose the game because you do not want an argument, even when you would like a turn. Which mindset does this most closely show?",
     "options": {"A": "Lose-Win", "B": "Win-Lose", "C": "Win-Win", "D": "Interdependent Living"},
     "key": "A", "why": "Giving up what matters to you so the other person always gets their way is Lose-Win."},
]

# ---------------------------------------------------------------------------------------------------------------
# B. Situational Check — S1-S8, exactly as the document words the questions; "name" is the scorecard's competency name.
# ---------------------------------------------------------------------------------------------------------------
SCENARIOS = [
    {"id": "S1", "name": "Think Win-Win understanding",
     "question": "Two friends disagree about whether to play football or a board game. One student says, “Win-Win means I should just agree with my friend.” What would you suggest they do?"},
    {"id": "S2", "name": "Mindset classification",
     "question": "During a class vote, a student says, “My idea must be chosen; other ideas do not matter.” Which mindset is shown? Explain briefly and suggest a better approach."},
    {"id": "S3", "name": "Perspective and consideration",
     "question": "Your teammate wants more time to practice; you want to finish the project today. What would you ask or say before deciding?"},
    {"id": "S4", "name": "Workable Win-Win option",
     "question": "Two students need the same computer for different parts of a project. Suggest one solution that could work for both and say how you would check it is fair."},
    {"id": "S5", "name": "Respectful communication",
     "question": "In a discussion, your classmate says something you disagree with. Write one sentence you could say that shows listening and respect."},
    {"id": "S6", "name": "Promises and trust",
     "question": "You promised your sibling/friend you would help, but you cannot do it at the agreed time. What would you do to protect trust?"},
    {"id": "S7", "name": "Win-Win Agreement components",
     "question": "You and a classmate want to share a game console. What would you include in your agreement so it is clear and fair?"},
    {"id": "S8", "name": "Reflection and accountable action",
     "question": "Choose one situation in which you could practice Think Win-Win this week. What specific action will you take, and how will you check whether you kept your promise?"},
]
SCENARIO_IDS = [s["id"] for s in SCENARIOS]
_MCQ_BY_ID = {q["id"]: q for q in MCQS}

MARKS_PER_MCQ = 2
KNOWLEDGE_MAX = MARKS_PER_MCQ * len(MCQS)     # 18 marks (9 questions x 2)
SITUATIONAL_MAX = 4 * len(SCENARIOS)           # 32 marks (8 situations x 4)
RAW_MAX = KNOWLEDGE_MAX + SITUATIONAL_MAX      # 50 marks, converted to 100 (x2)
FINAL_MAX = 100
MAX_ANSWER = 600

THANK_YOU = "Thank you for completing the Habit 4: Think Win-Win assessment. Your answers have been submitted."

# Document: "Rating guide: Emerging = below 50%; Building = 50-69%; Secure = 70-84%; Strong = 85-100%. These demo
# thresholds are provisional and should be confirmed by LiveLife."  Applied by LOWER BOUND, so 84.4% is Secure.
RATING_BANDS = [(85, "Strong"), (70, "Secure"), (50, "Building"), (0, "Emerging")]
RATING_GUIDE = ("Rating guide: Emerging = below 50%; Building = 50–69%; Secure = 70–84%; Strong = 85–100%. "
                "These demo thresholds are provisional and should be confirmed by LiveLife.")


def rating_for(percent: float) -> str:
    """Emerging / Building / Secure / Strong from an UNROUNDED percentage (rounding for display never changes a band)."""
    for low, label in RATING_BANDS:
        if percent >= low:
            return label
    return RATING_BANDS[-1][1]


def whole(x: float) -> int:
    """Round half up for display (Python's round() would turn 62.5 into 62)."""
    return int(x + 0.5)


def competency_percent(score: int) -> float:
    return score * 100 / 4


def final_score(knowledge_marks: int, scenario_scores: List[int]) -> float:
    """THE FINAL SCORE OUT OF 100, which the Final Rating comes from: (knowledge marks /18 + the eight situation scores /32)
    = /50, times 100 / 50. Change only here."""
    return (knowledge_marks + sum(scenario_scores)) * FINAL_MAX / RAW_MAX


# ---------------------------------------------------------------------------------------------------------------
# What the AI scorer sent back for this student (validated, never trusted beyond ranges and lengths)
# ---------------------------------------------------------------------------------------------------------------
class Scored(BaseModel):
    score: Optional[int] = Field(default=None, ge=0, le=4)
    evidence: str = Field(default="", max_length=300)
    tip: str = Field(default="", max_length=300)
    flag: bool = False


class SummaryIn(BaseModel):
    strengths: List[str] = Field(default_factory=list, max_length=4)
    skills: List[str] = Field(default_factory=list, max_length=4)
    try_next: str = Field(default="", max_length=300)
    teacher_support: str = Field(default="", max_length=300)


class ScoredIn(BaseModel):
    results: Dict[str, Scored] = Field(default_factory=dict, max_length=20)
    summary: Optional[SummaryIn] = None


class SubmitIn(BaseModel):
    class_id: str = Field(default="", max_length=40)     # optional: both ids also add this sheet to a class for the adaptive engine
    student_id: str = Field(default="", max_length=40)
    name: str = Field(default="", max_length=40)
    grade: str = Field(default="", max_length=12)
    mcq: Dict[str, str] = Field(default_factory=dict, max_length=20)
    answers: Dict[str, str] = Field(default_factory=dict, max_length=20)
    scored: Optional[ScoredIn] = None


def _line(s: str, n: int) -> str:
    return " ".join((s or "").split())[:n]


def mark_knowledge(choices: Dict[str, str]) -> dict:
    """The 9 MCQs by the keys. Unanswered or unknown = wrong. 2 marks each, so the Knowledge Check is out of 18."""
    marks = {}
    for q in MCQS:
        chosen = (choices.get(q["id"]) or "").strip().upper()[:1]
        marks[q["id"]] = {"chosen": chosen, "correct": chosen == q["key"]}
    correct = sum(1 for m in marks.values() if m["correct"])
    return {"score": correct * MARKS_PER_MCQ, "max": KNOWLEDGE_MAX, "correct": correct, "of": len(MCQS),
            "percent": whole(correct * 100 / len(MCQS)), "marks": marks}


def _fallback_summary(comps: List[dict]) -> dict:
    """Used when the AI gave no usable summary, so the scorecard is never empty. Built only from the scores."""
    scored = [c for c in comps if c["score"] is not None]
    good = sorted([c for c in scored if c["score"] >= 3], key=lambda c: -c["score"])[:2]
    low = sorted([c for c in scored if c["score"] <= 2], key=lambda c: c["score"])
    strengths = [(f"{c['name']}: {c['evidence']}" if c["evidence"] else f"You showed secure understanding in {c['name']}.") for c in good]
    if not strengths:
        strengths = ["No clear strength showed up in these answers yet, and that is okay: this is a starting point."]
    if low:
        skills = [(f"{c['name']}: {c['tip']}" if c["tip"] else f"{c['name']}: keep practising this one.") for c in low[:2]]
    elif scored:
        skills = ["Keep practising Think Win-Win in real situations."]
    else:
        skills = ["The written answers could not be scored this time."]
    first = low[0] if low else None
    return {
        "strengths": strengths[:2],
        "skills": skills[:2],
        "try_next": (first["tip"] if first and first["tip"] else
                     "Pick one real disagreement this week and ask what the other person needs before you decide."),
        "teacher_support": (f"Revisit “{first['name']}” with a short pair activity and one more example."
                            if first else "No extra support needed; offer a stretch activity."),
    }


def build_outcome(name: str, grade: str, mcq: Dict[str, str], scored: Optional[ScoredIn], today: Optional[date] = None) -> dict:
    """The scorecard exactly as the document lays it out. What a CHILD may see: no flags, no raw answers."""
    know = mark_knowledge(mcq)
    results = scored.results if scored else {}
    comps: List[dict] = []
    for s in SCENARIOS:
        r = results.get(s["id"])
        score = r.score if r is not None else None
        ev = _line(r.evidence, 200) if (r is not None and score is not None) else ""   # no text for an answer that was not scored
        tip = _line(r.tip, 200) if (r is not None and score is not None) else ""
        note = " ".join(x for x in [ev, tip] if x)
        comps.append({
            "id": s["id"], "name": s["name"], "score": score,
            "mark_percent": whole(competency_percent(score)) if score is not None else None,
            "rating": rating_for(competency_percent(score)) if score is not None else None,
            "evidence": ev, "tip": tip,
            "note": note or "We could not score this answer. Ask your teacher to look at it with you.",
        })
    got = [c["score"] for c in comps if c["score"] is not None]
    all_scored = len(got) == len(SCENARIOS)
    total = sum(got)
    final = final_score(know["score"], got) if all_scored else None   # out of 100; None until every situation is scored

    summ = None
    if scored and scored.summary:
        sm = scored.summary
        strengths = [_line(x, 160) for x in sm.strengths if _line(x, 160)][:2]
        skills = [_line(x, 160) for x in sm.skills if _line(x, 160)][:2]
        if strengths and skills and _line(sm.try_next, 200) and _line(sm.teacher_support, 200):
            summ = {"strengths": strengths, "skills": skills,
                    "try_next": _line(sm.try_next, 200), "teacher_support": _line(sm.teacher_support, 200)}
    if summ is None:
        summ = _fallback_summary(comps)

    d = today or date.today()
    return {
        "student": {"name": _line(name, 40), "grade": _line(grade, 12), "date": d.isoformat()},
        "overall": {"score": whole(final) if final is not None else None, "max": FINAL_MAX,
                    "raw": (know["score"] + total) if all_scored else None, "raw_max": RAW_MAX,
                    "rating": rating_for(final) if final is not None else None, "complete": all_scored},
        "knowledge": {"score": know["score"], "max": know["max"], "correct": know["correct"], "of": know["of"],
                      "percent": know["percent"]},
        "situational": {"score": total, "max": SITUATIONAL_MAX, "scored": len(got), "of": len(SCENARIOS),
                        "percent": whole(total * 100 / SITUATIONAL_MAX) if got else None},
        "competencies": [{k: c[k] for k in ("id", "name", "mark_percent", "rating", "note")} for c in comps],
        **summ,
        "rating_guide": RATING_GUIDE,
    }


# ---------------------------------------------------------------------------------------------------------------
# In-memory results (no database, no file). SINGLE-USER: only the latest is kept (a new submission replaces the
# last one, so an older scorecard link stops working); lost on restart.
# ---------------------------------------------------------------------------------------------------------------
MAX_STORED = 1
_STORE: "OrderedDict[str, dict]" = OrderedDict()
_LOCK = threading.Lock()
_ID_RE = re.compile(r"^[A-Za-z0-9_-]{16,40}$")


def _remember(record: dict) -> str:
    oid = secrets.token_urlsafe(16)
    with _LOCK:
        _STORE[oid] = record
        while len(_STORE) > MAX_STORED:
            _STORE.popitem(last=False)
    return oid


def private_record(oid: str) -> Optional[dict]:
    """The stored record INCLUDING flags and raw answers, for a teacher view later. Not routed: never sent to a child."""
    with _LOCK:
        return _STORE.get(oid)


@router.get("/items")
def items():
    """Everything the page shows. No answer key and no rationale."""
    return {
        "level": "Level 5", "habit": "Habit 4: Think Win-Win",
        "mcqs": [{"id": q["id"], "stem": q["stem"], "options": q["options"]} for q in MCQS],
        "scenarios": [{"id": s["id"], "question": s["question"]} for s in SCENARIOS],
        "thank_you": THANK_YOU,
    }


@router.post("/submit")
def submit(body: SubmitIn):
    """Stores the submission and returns ONLY an id: the thank-you page must not show marks or a rating."""
    name, grade = _line(body.name, 40), _line(body.grade, 12)
    if not name or not grade:
        return JSONResponse({"detail": "Please enter your name and grade."}, status_code=422)
    scored = body.scored
    outcome = build_outcome(name, grade, body.mcq, scored)
    flags = sorted(k for k, r in (scored.results.items() if scored else []) if k in SCENARIO_IDS and r.flag and r.score == 0)
    record = {
        "outcome": outcome,
        "flagged_for_educator_review": flags,          # a 0 for disrespect/harm: stored, never shown to the child
        "answers": {k: (body.answers.get(k) or "")[:MAX_ANSWER] for k in SCENARIO_IDS},
        "mcq": {q["id"]: (body.mcq.get(q["id"]) or "").strip().upper()[:1] for q in MCQS},
        "created": datetime.now(timezone.utc).isoformat(),
    }
    if valid_ids(body.class_id, body.student_id):
        CLASS_SUBMISSIONS.add(body.class_id, body.student_id, {
            "mcq": record["mcq"],
            "answers": record["answers"],
            "results": {k: r.model_dump() for k, r in (scored.results.items() if scored else []) if k in SCENARIO_IDS},
        })
    return JSONResponse({"id": _remember(record)}, headers={"Cache-Control": "no-store"})


@router.get("/outcome/{oid}")
def outcome(oid: str):
    """The student's scorecard, by its long random id. Nothing here lists other students."""
    rec = private_record(oid) if _ID_RE.match(oid) else None
    if rec is None:
        return JSONResponse({"detail": "Not found"}, status_code=404, headers={"Cache-Control": "no-store"})
    return JSONResponse(rec["outcome"], headers={"Cache-Control": "no-store"})
