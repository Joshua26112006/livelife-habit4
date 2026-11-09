"""Module 7: reassessment: a parallel item on the same competency, then an explicit reading of the result.

  demonstrated   correct with working
  insufficient   correct, but no working: may be guessed
  partial        set-up understood, a slip remains
  persistent     a belief still shows on the new item
  needs_review   blank, unreadable or matches nothing known
"""
from .pack import NO_EVIDENCE_RESULTS, UNMAPPED

NEXT_STEP = {
    "demonstrated": "leave_group",
    "insufficient": "reasoning_probe",
    "partial": "guided_practice_then_parallel_item",
    "persistent": "return_to_intervention_with_teacher_review",
    "needs_review": "teacher_review",
}


def build_item(pack, diagnosis, target, attempt=1):
    """A new item parallel to a question that showed this need, preferring one that samples the target competency."""
    wanted = set(pack.misconceptions[target]["competency_ids"])
    shown = [pack.item(q) for q in diagnosis["summary"][target]["questions"]]
    original = next((item for item in shown if wanted & set(item["competency_ids"])), shown[0])
    item = pack.parallel_item(original, attempt)
    return {**item, "target": target, "student": diagnosis["student"]}


def read_outcome(pack, item, raw):
    """One reassessment response -> its trace, outcome and next step."""
    trace = pack.read_answer(item, raw)
    beliefs = [f["belief"] for f in trace["findings"]]
    if trace["result"] in NO_EVIDENCE_RESULTS or UNMAPPED in beliefs:
        outcome = "needs_review"
    elif trace["result"].startswith("correct"):
        outcome = "demonstrated" if trace["result"] == "correct" and trace.get("shows_working") else "insufficient"
    elif any(code not in pack.slips for code in beliefs):
        outcome = "persistent"
    else:
        outcome = "partial"
    return {"student": item["student"], "item_id": item["id"], "target": item["target"], "parallel_of": item["parallel_of"],
            "trace": trace, "outcome": outcome, "next_step": NEXT_STEP[outcome]}
