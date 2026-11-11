"""One class through Modules 3 to 8, with the teacher's controls and an audit trail.

Stages keep explicit contracts; this class only sequences them and records every recommendation and human decision.
"""
from datetime import datetime, timezone
from fractions import Fraction

from . import clustering, identification, interventions, orchestration, reassessment
from .profile import LearnerProfile

TEACHER_ACTIONS = ("accept", "edit", "override", "dismiss")
DIAGNOSTIC = "diagnostic"
RETEST = "v2"


class ClassCycle:
    def __init__(self, pack, class_id, allow_draft=False, max_group_size=None, policy=None):
        self.pack = pack
        self.class_id = class_id
        self.allow_draft = allow_draft
        self.overrides = dict(policy or {})
        if max_group_size is not None:
            self.overrides["max_group_size"] = max_group_size
        self.policy = pack.settings(self.overrides)
        self.diagnoses, self.profiles = {}, {}
        self.mappings, self.groups, self.cohorts, self.plan = [], [], [], None
        self.preferred = {}
        self.paper, self.retests, self.comparison = [], {}, None
        self.audit = []
        self.clock = lambda: datetime.now(timezone.utc).isoformat()

    def _log(self, event, actor="system", **details):
        self.audit.append({"at": self.clock(), "event": event, "actor": actor, "class_id": self.class_id,
                           "pack_version": self.pack.version, **details})

    def _refresh(self):
        diagnoses = list(self.diagnoses.values())
        self.mappings = [interventions.map_student(self.pack, d, self.allow_draft, self.preferred) for d in diagnoses]
        self.groups = clustering.build_groups(self.pack, self.mappings, self.policy["max_group_size"])
        self._set_delivery()
        self._set_cohorts()
        self.plan = None
        self._log("groups_proposed", groups=[g["group_id"] for g in self.groups])

    def _set_delivery(self):
        """Who owns the fix decides who delivers it: the teacher only teaches what the teacher owns."""
        size = len(self.diagnoses)
        for group in self.groups:
            code = group["misconception_id"]
            showing = sum(code in d["summary"] for d in self.diagnoses.values())
            group["owners"] = clustering.owners_for(self.pack, code, Fraction(showing, size), self.policy)
            group["delivery"] = "teacher" if "teacher" in group["owners"] else "practice_card"

    def _set_cohorts(self):
        grouped = {s for g in self.groups for s in g["student_ids"]}
        self.cohorts = clustering.build_cohorts(self.pack, self.diagnoses.values(), grouped)

    # Module 3
    def run_diagnostic(self, sheets):
        for sheet in sheets:
            diagnosis = identification.diagnose_student(self.pack, sheet, policy=self.policy)
            self.diagnoses[sheet["id"]] = diagnosis
            profile = self.profiles.setdefault(sheet["id"], LearnerProfile(self.pack, sheet["id"]))
            profile.add_traces(DIAGNOSTIC, diagnosis["traces"], self.pack.items)
        self._log("diagnostic_analysed", students=len(sheets))
        self._refresh()

    def record_probe(self, student, code, outcome, teacher):
        identification.apply_probe(self.pack, self.diagnoses[student], code, outcome, self.policy)
        self._log("probe_recorded", teacher, student=student, misconception=code, outcome=outcome)
        self._refresh()

    def class_view(self):
        return clustering.diagnose_class(self.pack, list(self.diagnoses.values()), self.policy)

    def set_policy(self, overrides, teacher="teacher"):
        """New class rules: every student is routed again and groups are proposed again. Probe results already recorded stay."""
        self.policy = self.pack.settings(overrides)
        self.overrides = dict(overrides)
        for diagnosis in self.diagnoses.values():
            identification.finish(self.pack, diagnosis, self.policy)
        self._log("policy_set", teacher, policy=self.overrides)
        if self.diagnoses:
            self._refresh()

    # Module 4
    def set_preferred(self, preferred):
        self.preferred = dict(preferred)
        self._refresh()

    # Module 5: the teacher's edits
    def _group(self, group_id):
        return next(g for g in self.groups if g["group_id"] == group_id)

    def move_student(self, student, from_group, to_group, teacher, rationale=""):
        source, target = self._group(from_group), self._group(to_group)
        source["student_ids"].remove(student)
        target["student_ids"].append(student)
        for group, change in ((source, "left"), (target, "joined")):
            group["teacher_edits"].append({"student": student, "change": change, "teacher": teacher, "rationale": rationale})
        self.groups = [g for g in self.groups if g["student_ids"]]
        self.plan = None
        self._log("student_moved", teacher, student=student, from_group=from_group, to_group=to_group, rationale=rationale)

    def set_priority(self, group_ids, teacher, rationale=""):
        if sorted(group_ids) != sorted(g["group_id"] for g in self.groups):
            raise ValueError("the priority list must name every group once")
        self.groups = [self._group(g) for g in group_ids]
        self.plan = None
        self._log("priority_set", teacher, order=group_ids, rationale=rationale)

    def teacher_feedback(self, recommendation_id, action, teacher, rationale=""):
        if action not in TEACHER_ACTIONS:
            raise ValueError(f"unknown action: {action}")
        self._log("teacher_feedback", teacher, recommendation_id=recommendation_id, action=action, rationale=rationale)

    # Module 6
    def _evidence_item_for(self, group):
        for student in group["student_ids"]:
            entry = self.diagnoses[student]["summary"].get(group["misconception_id"])
            if entry:
                return entry["questions"][0]
        # Every member was moved here by the teacher: practise on any question that samples this need.
        wanted = set(group["competency_need_ids"])
        return next((i["id"] for i in self.pack.items if wanted & set(i["competency_ids"])), self.pack.items[0]["id"])

    def build_plan(self, period_minutes=orchestration.DEFAULT_PERIOD_MINUTES):
        evidence = {g["group_id"]: self._evidence_item_for(g) for g in self.groups}
        taught = [g for g in self.groups if g["delivery"] == "teacher"]
        cards = [g for g in self.groups if g["delivery"] != "teacher"]
        self.plan = orchestration.plan_sessions(self.pack, taught, evidence, period_minutes, self.cohorts, cards)
        self._log("plan_recommended", periods=len(self.plan["periods"]))
        return self.plan

    def approve_plan(self, teacher):
        if not self.plan:
            raise ValueError("there is no plan to approve")
        self.plan["status"] = "approved"
        self.plan["approved_by"] = teacher
        for group in self.groups:
            group["status"] = "approved"
            for student in group["student_ids"]:
                self.profiles[student].record_intervention(DIAGNOSTIC, group["intervention_id"], group["competency_need_ids"], teacher)
        self._log("plan_approved", teacher)

    # Module 7
    def create_paper(self, attempt=1):
        if not self.plan or self.plan["status"] != "approved":
            raise ValueError("approve the plan before reassessing")
        self.paper = reassessment.build_paper(self.pack, attempt)
        self._log("v2_paper_created", attempt=attempt, items=len(self.paper))
        return self.paper

    def score_paper(self, sheets):
        """V2 sheets -> new evidence on each profile and the V1 against V2 comparison."""
        for sheet in sheets:
            if sheet["id"] not in self.diagnoses:
                continue
            diagnosis = identification.diagnose_student(self.pack, sheet, self.paper, self.policy)
            self.retests[sheet["id"]] = diagnosis
            self.profiles[sheet["id"]].add_traces(RETEST, diagnosis["traces"], self.paper)
        self.comparison = reassessment.compare_class(self.pack, self.diagnoses, self.retests, self.paper)
        self._log("v2_scored", students=len(self.retests))
        return self.comparison
