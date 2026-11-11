"""Module 5: student clustering, and the class view of who owns each fix.

Groups are temporary and describe a learning need, never ability or identity. Each student has one primary group for the
session and keeps other needs for later ones. A group is a proposal until the teacher approves it.

Who fixes each error comes from the class policy (policy.py). An error with owners set in the policy goes to them, whatever
its share. Otherwise, by share of the class showing it (on any question, at any status, as in the class report), with the
default thresholds:
  content_share (25%) or more        content + teacher + student
  teacher_share (10%) up to that     teacher + student
  under teacher_share, or a slip     student only
"""
from fractions import Fraction as F

from .pack import UNMAPPED
from .policy import DEFAULTS, share as threshold

DEFAULT_MAX_GROUP_SIZE = DEFAULTS["max_group_size"]


def owners_for(pack, code, share, policy=None):
    return owners_with_source(pack, code, share, policy)[0]


def owners_with_source(pack, code, share, policy=None):
    """(owners, "set" when the policy names them for this error, or "share" when the class share decided)."""
    policy = policy or pack.settings()
    if policy["owners"].get(code):
        return list(policy["owners"][code]), "set"
    if code in pack.slips or share < threshold(policy, "teacher_share"):
        return ["student"], "share"
    return (["content", "teacher", "student"] if share >= threshold(policy, "content_share") else ["teacher", "student"]), "share"


def build_groups(pack, mappings, max_group_size=DEFAULT_MAX_GROUP_SIZE):
    """Students sharing a primary intervention form a group, largest split to fit. Earliest need in teaching order first."""
    by_intervention = {}
    for mapping in mappings:
        primary = mapping["primary"]
        if primary and primary["recommended"]:
            need = by_intervention.setdefault(primary["recommended"], {"code": primary["misconception_id"], "students": [], "evidence": {}})
            need["students"].append(mapping["student"])
            need["evidence"][mapping["student"]] = primary.get("status")
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
                "evidence": {s: need["evidence"][s] for s in members[start:start + max_group_size]},
                "status": "proposed",
                "teacher_edits": [],
            })
    return groups


def build_cohorts(pack, diagnoses, grouped_students):
    """Students with no teaching group this session still have something to do."""
    cohorts = {
        "extension": {"cohort_id": "extension", "need": "Ready for extension", "task": pack.extension_task, "student_ids": []},
        "probe": {"cohort_id": "probe", "need": "One follow-up question first", "task": "Answer the follow-up question in writing.", "student_ids": []},
        "teacher_review": {"cohort_id": "teacher_review", "need": "Teacher to read the answers first", "task": "Teacher checks in during independent work.", "student_ids": []},
    }
    for diagnosis in diagnoses:
        action = diagnosis["next"]["action"]
        if diagnosis["student"] not in grouped_students and action in cohorts:
            cohorts[action]["student_ids"].append(diagnosis["student"])
    return [c for c in cohorts.values() if c["student_ids"]]


def _misconception_rows(pack, students, policy):
    size = len(students)
    rows = []
    for code, entry in pack.misconceptions.items():
        showing = [s for s in students if code in s["summary"]]
        if not showing:
            continue
        share = F(len(showing), size)
        owners, source = owners_with_source(pack, code, share, policy)
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
            "evidence": {s["student"]: s["summary"][code]["status"] for s in showing},
            "grouped_here": [s["student"] for s in showing if s["next"]["action"] == "group" and s["next"]["target"] == code],
            "share_percent": round(float(share) * 100, 1),
            "questions": questions,
            "owners": owners,
            "owner_source": source,
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


def diagnose_class(pack, students, policy=None):
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
        "misconceptions": _misconception_rows(pack, students, policy or pack.settings()),
        "questions": _question_rows(pack.items, students),
        "proposed_groups": groups,
        "probes": probes,
        "practice": practice,
        "extension": extension,
        "teacher_review": teacher_review,
        "teacher_queue": [{"student": s["student"], "questions": s["teacher"]} for s in students if s["teacher"]],
        "unmapped_answers": sum(UNMAPPED in s["summary"] and len(s["summary"][UNMAPPED]["questions"]) for s in students),
    }
