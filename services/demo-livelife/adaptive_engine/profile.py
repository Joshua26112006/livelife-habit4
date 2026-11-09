"""Module 8: learner competency profile and next action.

New evidence is added, never overwritten: the status is computed from the evidence log and each change joins a timeline. These
are explicit rules, and no model sets mastery. The criteria are proposals to calibrate per competency.

  demonstrated          the latest session is all correct, with working on at least one item (high only with two or more such points)
  developing            mixed, slips only, or correct without working
  not_yet_demonstrated  the latest session shows the belief
  needs_review          nothing known fits, or a demonstrated competency is contradicted later
"""
from .pack import NO_EVIDENCE_RESULTS, UNMAPPED


def classify(pack, trace):
    """One trace -> the kind of evidence it is."""
    beliefs = [f["belief"] for f in trace["findings"]]
    if trace["result"] in NO_EVIDENCE_RESULTS:
        return "no_evidence"
    if trace["result"] == "correct":
        return "correct_with_working" if trace.get("shows_working") else "correct_no_working"
    if trace["result"].startswith("correct"):
        return "correct_no_working"
    if UNMAPPED in beliefs:
        return "unclassified"
    return "partial" if all(code in pack.slips for code in beliefs) else "incorrect"


class LearnerProfile:
    def __init__(self, pack, student_id):
        self.pack = pack
        self.student_id = student_id
        self.evidence = []
        self.interventions = []
        self.timeline = []

    def add_traces(self, session, traces, items):
        """Add one session's evidence. Competencies are read from each item, so parallel items count toward the same one."""
        before = self._statuses()
        for trace, item in zip(traces, items):
            kind = classify(self.pack, trace)
            for competency in item["competency_ids"]:
                self.evidence.append({
                    "evidence_id": f"{self.student_id}:{session}:{trace['q']}:{competency}",
                    "competency_id": competency, "session": session, "item_id": trace["q"], "kind": kind,
                    "response": trace["working"], "pack_version": self.pack.version,
                })
        self._record_changes(session, before)

    def record_intervention(self, session, intervention_id, competency_ids, approved_by):
        self.interventions.append({"session": session, "intervention_id": intervention_id, "competency_ids": list(competency_ids),
                                   "approved_by": approved_by})

    def _usable(self, competency):
        return [e for e in self.evidence if e["competency_id"] == competency and e["kind"] != "no_evidence"]

    def _state(self, competency):
        records = self._usable(competency)
        if not records:
            return {"status": "not_assessed", "confidence": None, "next_action": "assess"}
        latest_session = records[-1]["session"]
        latest = {e["kind"] for e in records if e["session"] == latest_session}
        earlier = [e for e in records if e["session"] != latest_session]
        points = sum(e["kind"] == "correct_with_working" for e in records)
        was_demonstrated = earlier and all(e["kind"] == "correct_with_working" for e in earlier)

        if "unclassified" in latest or ("incorrect" in latest and was_demonstrated):
            return {"status": "needs_review", "confidence": "low", "next_action": "review_with_teacher"}
        if "correct_with_working" in latest and latest <= {"correct_with_working", "correct_no_working"}:
            helped = any(competency in i["competency_ids"] for i in self.interventions)
            return {"status": "demonstrated", "confidence": "high" if points >= 2 else "medium",
                    "next_action": "spaced_review" if helped else "advance"}
        if latest == {"incorrect"}:
            return {"status": "not_yet_demonstrated", "confidence": "medium", "next_action": "reteach"}
        if latest == {"correct_no_working"}:
            return {"status": "developing", "confidence": "low", "next_action": "probe_further"}
        return {"status": "developing", "confidence": "medium", "next_action": "practice"}

    def _statuses(self):
        return {c: self._state(c)["status"] for c in self.pack.competencies}

    def _record_changes(self, session, before):
        for competency, status in self._statuses().items():
            if status != before[competency]:
                self.timeline.append({"session": session, "competency_id": competency, "from": before[competency], "to": status})

    def view(self):
        """Current state with the evidence behind it, for the teacher."""
        competencies = {}
        for competency, definition in self.pack.competencies.items():
            competencies[competency] = {
                "name": definition["name"],
                **self._state(competency),
                "evidence": [e["evidence_id"] for e in self.evidence if e["competency_id"] == competency],
            }
        return {"student_id": self.student_id, "competencies": competencies, "timeline": self.timeline,
                "interventions": self.interventions, "evidence_log": self.evidence}
