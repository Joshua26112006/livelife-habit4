"""Module 7: reassessment: a parallel V2 paper for the whole class, then V1 against V2.

The paper keeps the same competencies with new questions, so one paper can be printed for everyone. The comparison is
descriptive: a change in score is evidence to look at, not proof that an intervention worked.
"""
from .pack import NO_EVIDENCE_RESULTS

OPEN_STATUSES = ("confirmed", "likely", "candidate")
SOUND_RESULTS = ("correct", "correct_reason_unclear")


def build_paper(pack, attempt=1):
    return [pack.parallel_item(item, attempt) for item in pack.retest_items]


def _score(traces, question_ids):
    judged = [t for t in traces if t["q"] in question_ids and t["result"] not in NO_EVIDENCE_RESULTS]
    if not judged:
        return None
    return round(100 * sum(t["result"] in SOUND_RESULTS for t in judged) / len(judged))


def _open_beliefs(diagnosis):
    return {code for code, entry in diagnosis["summary"].items() if entry["status"] in OPEN_STATUSES}


def compare_student(before, after, paper):
    """One student's V1 and V2 on the same set of competencies."""
    source_ids = {item["parallel_of"] for item in paper}
    paper_ids = {item["id"] for item in paper}
    v1, v2 = _open_beliefs(before), _open_beliefs(after)
    return {
        "student": before["student"],
        "v1_percent": _score(before["traces"], source_ids),
        "v2_percent": _score(after["traces"], paper_ids),
        "no_longer_seen": sorted(v1 - v2),
        "still_seen": sorted(v1 & v2),
        "newly_seen": sorted(v2 - v1),
        "next": after["next"],
        "teacher": after["teacher"],
    }


def compare_class(pack, diagnoses, retests, paper):
    """Per student and per misconception. A student who did not sit V2 is listed, not guessed at."""
    students = [compare_student(diagnoses[s], retests[s], paper) for s in diagnoses if s in retests]
    by_code = []
    for code in pack.teaching_order:
        v1 = sum(code in _open_beliefs(d) for s, d in diagnoses.items() if s in retests)
        v2 = sum(code in _open_beliefs(d) for d in retests.values())
        if v1 or v2:
            by_code.append({"code": code, "name": pack.misconceptions[code]["name"], "v1_students": v1, "v2_students": v2})
    return {"students": students, "misconceptions": by_code, "did_not_sit": [s for s in diagnoses if s not in retests]}
