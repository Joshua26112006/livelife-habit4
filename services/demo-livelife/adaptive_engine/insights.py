"""The class picture, question by question: how many students answered each way, and what each way shows.

A mark of right or wrong hides most of what a sheet says, so answers are grouped by the thinking they show, with a real example of each.
"""
from .pack import NO_EVIDENCE_RESULTS, UNMAPPED

LEVEL_LABELS = {"secure": "Correct, method shown", "shown": "Correct, no working", "slip": "Slip or missing fact", "wrong": "Thinking error",
                "teacher": "For the teacher", "blank": "Left blank"}
LEVEL_ORDER = list(LEVEL_LABELS)
SOUND = ("secure", "shown")
MAX_STUDENTS_SHOWN = 40


def answer_level(pack, trace):
    """One answer -> (level, the error it shows or None)."""
    result = trace["result"]
    if result == "blank":
        return "blank", None
    if result in NO_EVIDENCE_RESULTS or any(f["belief"] == UNMAPPED for f in trace["findings"]):
        return "teacher", None
    codes = [f["belief"] for f in trace["findings"]]
    beliefs = [c for c in codes if pack.misconceptions[c]["kind"] == "belief"]
    if result.startswith("correct"):
        if beliefs:
            return "wrong", beliefs[0]
        return ("secure" if result == "correct" and trace.get("shows_working") else "shown"), None
    if beliefs:
        return "wrong", beliefs[0]
    return "slip", codes[0] if codes else None


def _default_thought(pack, level, code, trace):
    if code:
        lead = "Right answer, wrong reason. " if trace["result"] == "correct_wrong_reason" else ""
        return lead + pack.misconceptions[code]["belief"]
    return {"secure": "Solved it, with the method on the page.", "shown": "Right answer, but no working to check.", "blank": "Left blank.",
            "teacher": "The system could not place this answer, so the teacher reads it."}.get(level, "")


def question_view(pack, diagnoses, items=None):
    """Per question: how it was answered, grouped into ways of thinking, with counts and a real example."""
    students = list(diagnoses)
    out = []
    for index, item in enumerate(pack.items if items is None else items):
        ways = {}
        for student in students:
            trace = diagnoses[student]["traces"][index]
            level, code = answer_level(pack, trace)
            way_id = f"{level}:{code or trace.get('method') or ''}:{trace.get('final', '') if level in ('wrong', 'slip') else ''}:{trace['result']}"
            way = ways.setdefault(way_id, {"id": way_id, "level": level, "label": LEVEL_LABELS[level], "error": code,
                                           "error_name": pack.misconceptions[code]["name"] if code else None,
                                           "sample": trace["working"], "think": _default_thought(pack, level, code, trace), "count": 0, "students": []})
            way["count"] += 1
            if len(way["students"]) < MAX_STUDENTS_SHOWN:
                way["students"].append(student)
        ordered = sorted(ways.values(), key=lambda w: (LEVEL_ORDER.index(w["level"]), -w["count"]))
        out.append({"id": item["id"], "text": item["text"], "level": item.get("level"), "icon": item.get("icon"),
                    "answer": str(item.get("correct") or item.get("answer") or item.get("key") or "Reasoned answer"), "ways": ordered,
                    "sound": sum(w["count"] for w in ordered if w["level"] in SOUND), "students": len(students)})
    return out


def overview(pack, diagnoses, questions):
    errors = {w["error"] for q in questions for w in q["ways"] if w["error"] and pack.misconceptions[w["error"]]["kind"] == "belief"}
    wrong_reason = sum(t["result"] == "correct_wrong_reason" for d in diagnoses.values() for t in d["traces"])
    return {"students": len(diagnoses), "answers_read": sum(q["students"] for q in questions), "thinking_errors": len(errors), "right_answer_wrong_reason": wrong_reason}


def examples(questions, code, limit=2):
    """Real lines of working that show one error."""
    found = [{"q": q["id"], "sample": w["sample"]} for q in questions for w in q["ways"] if w["error"] == code and w["sample"]]
    return found[:limit]
