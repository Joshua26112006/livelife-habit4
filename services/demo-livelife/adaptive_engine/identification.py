"""Module 3: misconception identification.

Output per student: observed evidence, hypotheses with confidence, and the next diagnostic action. A misconception is a
hypothesis, never a fact from one wrong answer:
  confirmed   two or more questions, at least one high
  likely      two or more questions, all medium; probe first
  candidate   one question; probe
  ruled_out   a follow-up probe went against it
  A blank or unreadable answer goes to the teacher and is never counted as wrong.

Routing starts with the earliest confirmed belief in teaching order; the others stay on the profile for later sessions.
Slips get practice only. Nobody is sent to extension while any answer is waiting for a teacher.
"""
from .pack import NO_EVIDENCE_RESULTS, UNMAPPED

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


def _route(pack, summary, teacher):
    confirmed = _with_status(pack, summary, "confirmed")
    if confirmed:
        return {"action": "group", "target": confirmed[0], "held_for_later": confirmed[1:]}
    unsure = _with_status(pack, summary, "likely", "candidate")
    if unsure:
        return {"action": "probe", "target": unsure[0], "probe": pack.probes.get(unsure[0])}
    slips = [code for code in pack.slips if code in summary]
    if slips:
        return {"action": "practice", "target": slips}
    return {"action": "teacher_review"} if teacher else {"action": "extension"}


def _hypotheses(pack, student_id, summary, traces):
    """MisconceptionHypothesis records: evidence-linked, with confidence and the follow-up action."""
    follow_up = {"confirmed": "intervene", "likely": "probe", "candidate": "probe", "slip": "practice"}
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


def _finish(pack, diagnosis):
    """Recompute everything that follows from the traces and the (possibly probe-updated) summary."""
    traces, summary = diagnosis["traces"], diagnosis["summary"]
    diagnosis["next"] = _route(pack, summary, diagnosis["teacher"])
    diagnosis["two_explanations"] = _two_explanations(pack, traces, summary)
    diagnosis["hypotheses"] = _hypotheses(pack, diagnosis["student"], summary, traces)
    return diagnosis


def diagnose_student(pack, sheet):
    """One response sheet -> traces, evidence summary, hypotheses, next step and the teacher's queue."""
    answers = sheet.get("answers", {})
    traces = [pack.read_answer(item, answers.get(item["id"], "")) for item in pack.items]
    teacher = [t["q"] for t in traces
               if t["result"] in NO_EVIDENCE_RESULTS or any(f["belief"] == UNMAPPED for f in t["findings"])]
    return _finish(pack, {"student": sheet["id"], "traces": traces, "summary": weigh(pack, traces), "teacher": teacher})


def apply_probe(pack, diagnosis, code, outcome):
    """Record a follow-up probe's result. Supporting evidence confirms the belief; otherwise it is ruled out."""
    if outcome not in PROBE_OUTCOMES:
        raise ValueError(f"unknown probe outcome: {outcome}")
    if code not in diagnosis["summary"]:
        raise ValueError(f"{code} is not a hypothesis for {diagnosis['student']}")
    diagnosis["summary"][code]["status"] = "confirmed" if outcome == "supports" else "ruled_out"
    diagnosis["summary"][code]["probe_outcome"] = outcome
    return _finish(pack, diagnosis)
