"""Module 5: student clustering, and the class view of who owns each fix.

Groups are temporary and describe a learning need, never ability or identity. Each student has one primary group for the
session and keeps other needs for later ones. A group is a proposal until the teacher approves it.

Owners, by share of the class showing the misconception (on any question, at any status, as in the class report):
  25% or more        content + teacher + student
  10% up to 25%      teacher + student
  under 10%, or slip student only
"""
from fractions import Fraction as F

from .pack import UNMAPPED

CONTENT_SHARE = F(25, 100)
TEACHER_SHARE = F(10, 100)
DEFAULT_MAX_GROUP_SIZE = 12


def owners_for(pack, code, share):
    if code in pack.slips or share < TEACHER_SHARE:
        return ["student"]
    return ["content", "teacher", "student"] if share >= CONTENT_SHARE else ["teacher", "student"]


def build_groups(pack, mappings, max_group_size=DEFAULT_MAX_GROUP_SIZE):
    """Students sharing a primary intervention form a group, largest split to fit. Earliest need in teaching order first."""
    by_intervention = {}
    for mapping in mappings:
        primary = mapping["primary"]
        if primary and primary["recommended"]:
            need = by_intervention.setdefault(primary["recommended"], {"code": primary["misconception_id"], "students": []})
            need["students"].append(mapping["student"])
    rank = {code: i for i, code in enumerate(pack.teaching_order)}
    ordered = sorted(by_intervention.items(), key=lambda kv: (rank.get(kv[1]["code"], len(rank)), -len(kv[1]["students"])))
    groups = []
    for intervention_id, need in ordered:
        members = need["students"]
        for part, start in enumerate(range(0, len(members), max_group_size), 1):
            entry = pack.misconceptions[need["code"]]
            groups.append({
                "group_id": f"G-{intervention_id}-{part}",
                "need": entry["name"],
                "misconception_id": need["code"],
                "competency_need_ids": entry["competency_ids"],
                "intervention_id": intervention_id,
                "student_ids": members[start:start + max_group_size],
                "status": "proposed",
                "teacher_edits": [],
            })
    return groups


def _misconception_rows(pack, students):
    size = len(students)
    rows = []
    for code, entry in pack.misconceptions.items():
        showing = [s for s in students if code in s["summary"]]
        if not showing:
            continue
        share = F(len(showing), size)
        owners = owners_for(pack, code, share)
        questions = {}
        for s in showing:
            for q in s["summary"][code]["questions"]:
                questions[q] = questions.get(q, 0) + 1
        rows.append({
            "code": code,
            "name": entry["name"],
            "kind": entry["kind"],
            "students": [s["student"] for s in showing],
            "confirmed": [s["student"] for s in showing if s["summary"][code]["status"] == "confirmed"],
            "share_percent": round(float(share) * 100, 1),
            "questions": questions,
            "owners": owners,
            "remedies": {owner: entry[owner] for owner in owners},
            "awaiting_expert_draft": [owner for owner in owners if not entry[owner]],
            "exit_check": entry["exit_check"],
        })
    return sorted(rows, key=lambda row: -len(row["students"]))


def _question_rows(test, students):
    rows = []
    for index, q in enumerate(test):
        counts = {}
        for s in students:
            result = s["traces"][index]["result"]
            counts[result] = counts.get(result, 0) + 1
        rows.append({"q": q["id"], "text": q["text"], "correct_answer": str(q.get("correct", "")), "results": counts})
    return rows


def diagnose_class(pack, students):
    """All diagnosed students -> ownership table, proposed groups, probes, practice and the teacher's queue."""
    groups, probes, practice, extension, teacher_review = {}, [], [], [], []
    for s in students:
        step = s["next"]
        if step["action"] == "group":
            groups.setdefault(step["target"], []).append(s["student"])
        elif step["action"] == "probe":
            probes.append({"student": s["student"], "target": step["target"], "probe": step["probe"]})
        elif step["action"] == "practice":
            practice.append({"student": s["student"], "slips": step["target"]})
        elif step["action"] == "extension":
            extension.append(s["student"])
        else:
            teacher_review.append(s["student"])
    return {
        "class_size": len(students),
        "misconceptions": _misconception_rows(pack, students),
        "questions": _question_rows(pack.items, students),
        "proposed_groups": groups,
        "probes": probes,
        "practice": practice,
        "extension": extension,
        "teacher_review": teacher_review,
        "teacher_queue": [{"student": s["student"], "questions": s["teacher"]} for s in students if s["teacher"]],
        "unmapped_answers": sum(UNMAPPED in s["summary"] and len(s["summary"][UNMAPPED]["questions"]) for s in students),
    }
