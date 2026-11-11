"""Module 3: misconception identification.

Output per student: observed evidence, hypotheses with confidence, and the next diagnostic action. A misconception is a
hypothesis, never a fact from one wrong answer:
  confirmed   two or more questions, at least one high
  likely      two or more questions, all medium
  candidate   one question
  ruled_out   a follow-up probe went against it
  A blank or unreadable answer goes to the teacher and is never counted as wrong.

The class policy's group_from (policy.py) says which of these is enough to club a student with others showing the same thinking
error. By default every status is: students are grouped by error at once, and each group records how strong each member's
evidence is. Weaker evidence than group_from gets a follow-up question first. A student's group is their strongest-evidence error,
earliest in teaching order; the others stay on the profile for later sessions.
Slips get practice only. Nobody is sent to extension while any answer is waiting for a teacher.
"""
from .pack import NO_EVIDENCE_RESULTS, UNMAPPED
from .policy import STRENGTH, groupable

PROBE_OUTCOMES = ("supports", "rules_out")


def weigh(pack, traces):
    """Each belief -> the questions that show it and its status."""
    evidence = {}
    for trace in traces:
        for finding in trace["findings"]:
            evidence.setdefault(finding["belief"], []).append((trace["q"], finding["confidence"]))
    summary = {}
    for code, items in evidence.items():
        highs = sum(confidence == "high" for _, confidence in items)
        if code in pack.slips:
            status = "slip"
        elif pack.misconceptions.get(code, {}).get("kind") == "fact":
            status = "gap"
        elif code == UNMAPPED:
            status = "unmapped"
        elif len(items) >= 2 and highs:
            status = "confirmed"
        elif len(items) >= 2:
            status = "likely"
        else:
            status = "candidate"
        summary[code] = {"questions": [q for q, _ in items], "highs": highs, "status": status}
    return summary


def _with_status(pack, summary, *statuses):
    return [code for code in pack.teaching_order if summary.get(code, {}).get("status") in statuses]


def _two_explanations(pack, traces, summary):
    """Answers two beliefs fit. Settled when the sheet confirms exactly one of them; otherwise a probe decides."""
    confirmed = _with_status(pack, summary, "confirmed")
    out = {}
    for trace in traces:
        beliefs = trace.get("ambiguous")
        if not beliefs:
            continue
        held = [code for code in beliefs if code in confirmed]
        settled = held[0] if len(held) == 1 else None
        probe = None
        if not settled:
            probe = pack.separating_probes.get(frozenset(beliefs)) or next((pack.probes[b] for b in beliefs if b in pack.probes), None)
        out[trace["q"]] = {"beliefs": beliefs, "settled_by": settled, "probe": probe}
    return out


def _route(pack, summary, teacher, policy):
    enough = groupable(policy)
    ready = [code for status in enough for code in _with_status(pack, summary, status)]
    if ready:
        return {"action": "group", "target": ready[0], "held_for_later": ready[1:], "evidence": summary[ready[0]]["status"]}
    unsure = _with_status(pack, summary, *[s for s in STRENGTH if s not in enough])
    if unsure:
        return {"action": "probe", "target": unsure[0], "probe": pack.probes.get(unsure[0])}
    practice = [code for code, entry in pack.misconceptions.items() if entry["kind"] in ("slip", "fact") and code in summary]
    if practice:
        return {"action": "practice", "target": practice}
    return {"action": "teacher_review"} if teacher else {"action": "extension"}


def _hypotheses(pack, student_id, summary, traces, policy):
    """MisconceptionHypothesis records: evidence-linked, with confidence and the follow-up action."""
    follow_up = {**{s: "intervene" if s in groupable(policy) else "probe" for s in STRENGTH}, "slip": "practice", "gap": "practice"}
    records = []
    for code, entry in summary.items():
        if code == UNMAPPED or entry["status"] == "ruled_out":
            continue
        lines = [f["evidence"] for t in traces for f in t["findings"] if f["belief"] == code]
        records.append({
            "student_id": student_id,
            "misconception_id": code,
            "competency_ids": pack.misconceptions[code]["competency_ids"],
            "evidence_response_ids": entry["questions"],
            "evidence": lines,
            "confidence": "high" if entry["highs"] else "medium",
            "status": entry["status"],
            "follow_up_action": follow_up[entry["status"]],
        })
    return records


def finish(pack, diagnosis, policy=None):
    """Recompute everything that follows from the traces and the (possibly probe-updated) summary, under the class policy."""
    policy = policy or pack.settings()
    traces, summary = diagnosis["traces"], diagnosis["summary"]
    diagnosis["next"] = _route(pack, summary, diagnosis["teacher"], policy)
    diagnosis["two_explanations"] = _two_explanations(pack, traces, summary)
    diagnosis["hypotheses"] = _hypotheses(pack, diagnosis["student"], summary, traces, policy)
    return diagnosis


def _apply_ai_reading(pack, trace, hint):
    """A catalogue-limited AI reading of an answer the rules could not place. Medium confidence: it counts as one question's evidence."""
    if not hint or pack.misconceptions.get(hint.get("code"), {}).get("kind") != "belief":
        return trace
    unplaced = trace["result"] == "argument_unclear" or any(f["belief"] == UNMAPPED for f in trace["findings"])
    if unplaced:
        trace["result"] = "wrong"
        trace["findings"] = [dict(belief=hint["code"], step="AI reading", confidence="medium", evidence=hint.get("why", ""), source="ai")]
    return trace


def diagnose_student(pack, sheet, items=None, policy=None):
    """One response sheet -> traces, evidence summary, hypotheses, next step and the teacher's queue."""
    answers, hints = sheet.get("answers", {}), sheet.get("ai_hints", {})
    traces = [_apply_ai_reading(pack, pack.read(item, answers.get(item["id"], "")), hints.get(item["id"]))
              for item in (pack.items if items is None else items)]
    teacher = [t["q"] for t in traces
               if t["result"] in NO_EVIDENCE_RESULTS or any(f["belief"] == UNMAPPED for f in t["findings"])]
    return finish(pack, {"student": sheet["id"], "traces": traces, "summary": weigh(pack, traces), "teacher": teacher}, policy)


def apply_probe(pack, diagnosis, code, outcome, policy=None):
    """Record a follow-up probe's result. Supporting evidence confirms the belief; otherwise it is ruled out."""
    if outcome not in PROBE_OUTCOMES:
        raise ValueError(f"unknown probe outcome: {outcome}")
    if code not in diagnosis["summary"]:
        raise ValueError(f"{code} is not a hypothesis for {diagnosis['student']}")
    diagnosis["summary"][code]["status"] = "confirmed" if outcome == "supports" else "ruled_out"
    diagnosis["summary"][code]["probe_outcome"] = outcome
    return finish(pack, diagnosis, policy)
