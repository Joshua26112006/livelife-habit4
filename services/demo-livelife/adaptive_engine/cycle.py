"""One class through Modules 3 to 8, with the teacher's controls and an audit trail.

Stages keep explicit contracts; this class only sequences them and records every recommendation and human decision. Storage
is left to the host platform: nothing here touches a database.
"""
from datetime import datetime, timezone

from . import clustering, identification, interventions, orchestration, reassessment
from .profile import LearnerProfile

TEACHER_ACTIONS = ("accept", "edit", "override", "dismiss")
DIAGNOSTIC = "diagnostic"


class ClassCycle:
    def __init__(self, pack, class_id, allow_draft=False, max_group_size=clustering.DEFAULT_MAX_GROUP_SIZE):
        self.pack = pack
        self.class_id = class_id
        self.allow_draft = allow_draft
        self.max_group_size = max_group_size
        self.diagnoses, self.profiles = {}, {}
        self.mappings, self.groups, self.plan, self.reassessment_items, self.outcomes = [], [], None, {}, []
        self.audit = []

    def _log(self, event, actor="system", **details):
        self.audit.append({"at": datetime.now(timezone.utc).isoformat(), "event": event, "actor": actor,
                           "class_id": self.class_id, "pack_version": self.pack.version, **details})

    def _refresh(self):
        self.mappings = [interventions.map_student(self.pack, d, self.allow_draft) for d in self.diagnoses.values()]
        self.groups = clustering.build_groups(self.pack, self.mappings, self.max_group_size)
        self.plan = None
        self._log("groups_proposed", groups=[g["group_id"] for g in self.groups])

    # Module 3
    def run_diagnostic(self, sheets):
        for sheet in sheets:
            diagnosis = identification.diagnose_student(self.pack, sheet)
            self.diagnoses[sheet["id"]] = diagnosis
            profile = self.profiles.setdefault(sheet["id"], LearnerProfile(self.pack, sheet["id"]))
            profile.add_traces(DIAGNOSTIC, diagnosis["traces"], self.pack.items)
        self._log("diagnostic_analysed", students=len(sheets))
        self._refresh()

    def record_probe(self, student, code, outcome, teacher):
        identification.apply_probe(self.pack, self.diagnoses[student], code, outcome)
        self._log("probe_recorded", teacher, student=student, misconception=code, outcome=outcome)
        self._refresh()

    def class_view(self):
        return clustering.diagnose_class(self.pack, list(self.diagnoses.values()))

    # Modules 4 and 5: the teacher's edits
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
        first = group["student_ids"][0]
        return self.diagnoses[first]["summary"][group["misconception_id"]]["questions"][0]

    def build_plan(self, period_minutes=orchestration.DEFAULT_PERIOD_MINUTES):
        evidence = {g["group_id"]: self._evidence_item_for(g) for g in self.groups}
        self.plan = orchestration.plan_sessions(self.pack, self.groups, evidence, period_minutes)
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
                self.profiles[student].record_intervention(
                    DIAGNOSTIC, group["intervention_id"], group["competency_need_ids"], teacher)
        self._log("plan_approved", teacher)

    # Module 7
    def create_reassessment(self, attempt=1):
        if not self.plan or self.plan["status"] != "approved":
            raise ValueError("approve the plan before reassessing")
        self.reassessment_items = {}
        for group in self.groups:
            for student in group["student_ids"]:
                self.reassessment_items[student] = reassessment.build_item(
                    self.pack, self.diagnoses[student], group["misconception_id"], attempt)
        self._log("reassessment_created", attempt=attempt, students=len(self.reassessment_items))
        return self.reassessment_items

    # Modules 7 and 8
    def submit_reassessment(self, answers, session="reassessment-1"):
        """answers: {student: raw text}. Each result is added to that student's profile as new evidence."""
        results = []
        for student, raw in answers.items():
            item = self.reassessment_items[student]
            result = reassessment.read_outcome(self.pack, item, raw)
            self.profiles[student].add_traces(session, [result["trace"]], [item])
            results.append(result)
        self.outcomes.extend(results)
        self._log("reassessment_scored", session=session, students=len(results))
        return results

    def next_cycle(self):
        """Who leaves their group, and who needs another pass."""
        by_step = {}
        for result in self.outcomes:
            by_step.setdefault(result["next_step"], []).append(result["student"])
        return by_step
