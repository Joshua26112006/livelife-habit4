"""The class workflow: upload, each module in turn, teacher decisions, re-test, profiles.

Each step is saved as an event, and a class is rebuilt by replaying its events, so a class can stop at any stage and pick up days
later. Parallel papers are deterministic, so replay gives the same result. Events and the class records live in store.py
(Firestore when configured, local SQLite otherwise).

Two kinds of run:
  a subject pack   the pack holds the questions, answers and known thinking errors (Modules 3 to 8, with the re-test)
  "generic"        any paper: the teacher uploads the questions (and answers, if they have them), then the students' working.
                   generic.py works out missing answers, marks the working and names the class's few thinking errors, and
                   builds a pack for this paper, so Modules 3 to 6 run as for any pack. No re-test yet.
"""
import re
import secrets
import threading
from datetime import datetime, timezone

from . import ai_tasks, bulk, generic, insights, policy, store
from .cycle import ClassCycle
from .packs import all_packs

GENERIC = "generic"
STAGES = ("created", "paper_set", "uploaded", "keyed", "read", "identified", "mapped", "grouped", "planned", "approved", "paper_ready", "v2_uploaded",
          "scored", "profiled")
# module: (stage it needs, stage it leads to)
MODULES = {"m3": ("uploaded", "identified"), "m3-key": ("uploaded", "keyed"), "m3-read": ("keyed", "read"), "m3-errors": ("read", "identified"), "m3-actions": ("identified", "identified"),
           "m3-insight": ("identified", "identified"), "m4": ("identified", "mapped"), "m5": ("mapped", "grouped"), "m6": ("grouped", "planned"),
           "m7-paper": ("approved", "paper_ready"), "m7-score": ("v2_uploaded", "scored"), "m8": ("scored", "profiled")}
GENERIC_ONLY = ("m3-key", "m3-read", "m3-errors", "m3-actions")
PACK_ONLY = ("m3", "m7-paper", "m7-score", "m8")
FEEDS = ("m3", "m4", "m5", "m6", "m7-paper", "m7-score", "m8")
SETTINGS_OPEN = ("created", "paper_set", "uploaded", "keyed", "read", "identified", "mapped", "grouped")
_LOCK = threading.Lock()


class WorkflowError(ValueError):
    """The step cannot run at this stage."""


def class_code(name):
    """The class a run belongs to, as a stable key across subjects: '10 B', '10-b' and '10b' are the same class, 10B."""
    return re.sub(r"[^A-Za-z0-9]+", "", name).upper()[:40] or "CLASS"


class Workflow:
    def __init__(self, class_id):
        self.class_id, self.pack, self.name, self.cycle = class_id, None, "", None
        self.generic, self.paper, self.read_sheets, self.overrides, self.class_code, self.pack_key = False, None, [], {}, "", ""
        self.actions = {}
        self.stage, self.seq = "created", 0
        self.v1_sheets, self.v2_sheets = [], []
        self.upload_reports, self.ai, self.rationale = {}, {}, {}
        self.materials, self.group_reasons, self.paper_flags, self.narrative, self.insights = {}, {}, {}, {}, {}

    # ---- applying events (no side effects, so replay is safe)
    def _apply(self, kind, payload, at):
        self.seq += 1
        self.at = at
        if self.cycle:
            self.cycle.clock = lambda: at
        getattr(self, f"_on_{kind.replace('-', '_')}")(payload)

    def _new_cycle(self):
        self.cycle = ClassCycle(self.pack, self.class_id, allow_draft=True, policy=self.overrides)
        self.cycle.clock = lambda at=self.at: at

    def _on_create(self, p):
        self.name, self.pack_key, self.overrides = p["name"], p["pack"], dict(p.get("policy") or {})
        self.class_code = p.get("class_code") or class_code(p["name"])
        self.generic = p["pack"] == GENERIC
        if not self.generic:
            self.pack = all_packs()[p["pack"]]
            self._new_cycle()

    # generic runs: the paper, then three AI steps
    def _on_paper(self, p):
        self.paper = p["paper"]
        self.pack = generic.build_pack(self.paper, {}, paper_id=self.class_id)
        self._new_cycle()
        self.stage = "paper_set"

    def _on_m3_key(self, p):
        self.ai["m3-key"] = p.get("status", "off")
        self.paper = generic.apply_key(self.paper, self._results(p))
        self.pack = generic.build_pack(self.paper, {}, paper_id=self.class_id)
        self._new_cycle()
        self.stage = "keyed"

    def _on_answers(self, p):
        self.paper = generic.set_answers(self.paper, p["answers"])
        self.pack = generic.build_pack(self.paper, {}, paper_id=self.class_id)
        self._new_cycle()

    def _on_m3_read(self, p):
        self.ai["m3"] = p.get("status", "off")
        self.read_sheets, self.ai["m3_failed"] = generic.apply_reading(self.paper, self.v1_sheets, self._results(p))
        self.stage = "read"

    def _on_m3_errors(self, p):
        self.ai["m3-errors"] = p.get("status", "off")
        self.catalogue, sheets = generic.apply_errors(self.paper, self.read_sheets, self._results(p))
        self.pack = generic.build_pack(self.paper, self.catalogue, sheets, paper_id=self.class_id)
        self._new_cycle()
        self.cycle.run_diagnostic(sheets)
        self.stage = "identified"

    def _on_upload(self, p):
        if p["round"] == "v1":
            self.v1_sheets, self.stage = p["sheets"], "uploaded"
        else:
            self.v2_sheets, self.stage = p["sheets"], "v2_uploaded"
        self.upload_reports[p["round"]] = p["report"]

    def _results(self, p):
        return p.get("results") or {}

    def _on_m3(self, p):
        self.ai["m3"] = p.get("status", "off")
        sheets, self.ai["m3_failed"] = ai_tasks.apply_marking(self.pack, self.v1_sheets, self.pack.items, self._results(p))
        self.cycle.run_diagnostic(sheets)
        self.stage = "identified"

    def _on_m3_actions(self, p):
        self.ai["m3-actions"] = p.get("status", "off")
        self.actions = generic.apply_actions(self.cycle.diagnoses, self._results(p))

    def _on_m3_insight(self, p):
        self.ai["m3-insight"] = p.get("status", "off")
        self.insights = ai_tasks.apply_insights(insights.question_view(self.pack, self.cycle.diagnoses), self._results(p))

    def _on_settings(self, p):
        self.overrides = dict(p["policy"])
        if not self.cycle:
            return
        self.cycle.set_policy(p["policy"], p.get("teacher", "teacher"))
        if self.stage in ("mapped", "grouped"):
            # Groups were formed under the old rules: find the fixes and form groups again.
            self.stage, self.group_reasons = "identified", {}

    def _on_probe(self, p):
        self.cycle.record_probe(p["student"], p["code"], p["outcome"], p["teacher"])

    def _on_m4(self, p):
        self.ai["m4"] = p.get("status", "off")
        preferred, self.rationale = ai_tasks.apply_interventions(self.cycle, self._results(p))
        self.cycle.set_preferred(preferred)
        self.stage = "mapped"

    def _on_m5(self, p):
        self.ai["m5"] = p.get("status", "off")
        self.group_reasons = ai_tasks.apply_clusters(self.cycle, self._results(p))
        self.stage = "grouped"

    def _on_move(self, p):
        self.cycle.move_student(p["student"], p["from_group"], p["to_group"], p["teacher"], p.get("rationale", ""))

    def _on_priority(self, p):
        self.cycle.set_priority(p["group_ids"], p["teacher"], p.get("rationale", ""))

    def _on_m6(self, p):
        self.ai["m6"] = p.get("status", "off")
        self.cycle.build_plan()
        self.materials = ai_tasks.apply_materials(self.cycle.plan, self._results(p))
        self.stage = "planned"

    def _on_approve(self, p):
        self.cycle.approve_plan(p["teacher"])
        self.stage = "approved"

    def _on_m7_paper(self, p):
        self.ai["m7-paper"] = p.get("status", "off")
        self.cycle.create_paper()
        self.paper_flags = ai_tasks.apply_paper(self.cycle.paper, self._results(p))
        self.stage = "paper_ready"

    def _on_m7_score(self, p):
        self.ai["m7-score"] = p.get("status", "off")
        sheets, self.ai["m7_failed"] = ai_tasks.apply_marking(self.pack, self.v2_sheets, self.cycle.paper, self._results(p))
        self.cycle.score_paper(sheets)
        self.stage = "scored"

    def _on_m8(self, p):
        self.ai["m8"] = p.get("status", "off")
        self.narrative = ai_tasks.apply_profile(self.cycle.comparison, self._results(p))
        self.stage = "profiled"

    # ---- recording events
    def record(self, kind, payload):
        at = datetime.now(timezone.utc).isoformat()
        with _LOCK:
            self._apply(kind, payload, at)
            saved = store.get()
            with saved.batch():
                saved.append_event(self.class_id, self.seq, kind, payload, at)
                self._save_records(saved, at)

    # ---- class and student records, for work across papers and subjects (see store.py for the layout)
    def _save_records(self, saved, at):
        base = f"classes/{self.class_code}"
        saved.set_doc(base, {"class_code": self.class_code, "name": self.name, "updated_at": at}, merge=True)
        assessment = {"run_id": self.class_id, "class_code": self.class_code, "kind": GENERIC if self.generic else "pack", "pack": self.pack_key,
                      "subject": self.pack.subject if self.pack else {}, "stage": self.stage, "ai": self.ai, "updated_at": at,
                      "questions": self._paper_view()}
        if STAGES.index(self.stage) < STAGES.index("identified"):
            saved.set_doc(f"{base}/assessments/{self.class_id}", assessment, merge=True)
            return
        rows = self.cycle.class_view()["misconceptions"]
        assessment["thinking_errors"] = [{"code": r["code"], "name": r["name"], "kind": r["kind"], "thinks": self.pack.misconceptions[r["code"]]["belief"],
                                          "looks_like": self.pack.misconceptions[r["code"]].get("looks_like", ""), "students": r["students"],
                                          "share_percent": r["share_percent"], "owners": r["owners"], "fixes": r["remedies"], "fix": self._fix(r["code"])}
                                         for r in rows]
        assessment["groups"] = [{"group_id": g["group_id"], "need": g["need"], "code": g["misconception_id"], "students": g["student_ids"],
                                 "owners": g.get("owners", []), "delivery": g.get("delivery")} for g in self.cycle.groups] if STAGES.index(self.stage) >= STAGES.index("grouped") else []
        saved.set_doc(f"{base}/assessments/{self.class_id}", assessment)
        marks = {i["id"]: i.get("marks") for i in self.pack.items}
        for diagnosis in self.cycle.diagnoses.values():
            student = diagnosis["student"]
            answers = self._answers(diagnosis)
            judged = [a for a in answers if a["level"] != "blank"]
            correct = [a for a in answers if a["level"] in insights.SOUND]
            total_marks = sum(m for m in marks.values() if m) or None
            saved.set_doc(f"{base}/students/{student}", {"student_id": student, "class_code": self.class_code, "updated_at": at}, merge=True)
            saved.set_doc(f"{base}/students/{student}/assessments/{self.class_id}", {
                "run_id": self.class_id, "class_code": self.class_code, "subject": self.pack.subject, "updated_at": at,
                "score": {"correct": len(correct), "answered": len(judged), "questions": len(answers),
                          "marks": round(sum(marks[a["q"]] or 0 for a in correct), 2) if total_marks else None, "out_of": round(total_marks, 2) if total_marks else None},
                "answers": [{"q": a["q"], "result": a["result"], "level": a["level"], "label": a["label"], "error_code": a["error"],
                             "evidence": next((f["evidence"] for f in a["findings"]), ""), "working": a["working"]} for a in answers],
                "thinking_errors": [{"code": code, "name": self.pack.misconceptions[code]["name"], "kind": self.pack.misconceptions[code]["kind"],
                                     "status": entry["status"], "questions": entry["questions"]}
                                    for code, entry in diagnosis["summary"].items() if code in self.pack.misconceptions],
                "next": diagnosis["next"],
                "actions": self.actions.get(student),
            })

    def _need(self, *stages):
        if self.stage not in stages:
            raise WorkflowError(f"This step is not available at stage '{self.stage}'.")

    # ---- what the API calls
    def settings(self, overrides, teacher="teacher"):
        """Change this class's rules. Open until the plan is built; after that, groups are being taught."""
        self._need(*SETTINGS_OPEN)
        found = policy.problems(overrides, set(self.pack.misconceptions) if self.pack else None)
        if found:
            raise WorkflowError("; ".join(found))
        policy.resolve(self.pack.policy if self.pack else {}, overrides)  # raises if the combination does not hold
        self.record("settings", {"policy": overrides, "teacher": teacher})
        return self.status()

    def questions(self, round_name):
        return self.pack.items if round_name == "v1" else self.cycle.paper

    def question_ids(self, round_name):
        return [i["id"] for i in self.questions(round_name)]

    def set_paper(self, data):
        """A generic run's question paper: the questions, and the expected answers where the teacher has them."""
        if not self.generic:
            raise WorkflowError("This class uses a subject pack, which already has its questions.")
        self._need("created")
        try:
            import json
            parsed = generic.parse_paper(json.loads(data.decode("utf-8-sig")) if isinstance(data, (bytes, bytearray)) else data)
        except ValueError as err:
            raise WorkflowError(f"The question paper could not be used: {err}") from err
        self.record("paper", {"paper": parsed})
        return self.status()

    def set_answers(self, answers, teacher="teacher"):
        """The teacher's expected answers: to fill gaps, or to correct any the AI step worked out. Open until marking starts."""
        if not self.generic:
            raise WorkflowError("This class uses a subject pack, which already has its answers.")
        self._need("paper_set", "uploaded", "keyed")
        try:
            generic.set_answers(self.paper, answers)
        except ValueError as err:
            raise WorkflowError(str(err)) from err
        self.record("answers", {"answers": answers, "teacher": teacher})
        return self.status()

    def upload(self, round_name, data, filename):
        if self.generic and round_name != "v1":
            raise WorkflowError("A re-test is not part of an uploaded paper yet.")
        self._need(("paper_set" if self.generic else "created") if round_name == "v1" else "paper_ready")
        parsed = bulk.parse_upload(data, filename, self.questions(round_name))
        report = {"students": len(parsed["sheets"]), "rejected": parsed["rejected"], "warnings": parsed["warnings"],
                  "blank_answers": sum(1 for s in parsed["sheets"] for a in s["answers"].values() if not a)}
        self.record("upload", {"round": round_name, "sheets": parsed["sheets"], "report": report})
        return report

    def _check_module(self, module):
        if self.generic and module in PACK_ONLY:
            raise WorkflowError("This step is for subject packs. An uploaded paper is read with m3-key, m3-read and m3-errors; there is no re-test yet.")
        if not self.generic and module in GENERIC_ONLY:
            raise WorkflowError("This step is for uploaded papers.")
        self._need(MODULES[module][0])

    def tasks(self, module):
        self._check_module(module)
        if module == "m3-key":
            return generic.key_tasks(self.paper)
        if module == "m3-read":
            return generic.read_tasks(self.paper, self.v1_sheets)
        if module == "m3-errors":
            return generic.error_tasks(self.paper, self.read_sheets)
        if module == "m3-actions":
            return generic.action_tasks(self.paper, self.pack, self.cycle.diagnoses)
        if module == "m3":
            return ai_tasks.marking_tasks(self.pack, self.v1_sheets, self.pack.items)
        if module == "m3-insight":
            return ai_tasks.insight_tasks(self.pack, insights.question_view(self.pack, self.cycle.diagnoses))
        if module == "m4":
            return ai_tasks.intervention_tasks(self.pack, self.cycle)
        if module == "m5":
            return ai_tasks.cluster_tasks(self.cycle)
        if module == "m6":
            return ai_tasks.material_tasks(self.pack, self.cycle.build_plan())
        if module == "m7-paper":
            from .reassessment import build_paper
            return ai_tasks.paper_tasks(self.pack, build_paper(self.pack))
        if module == "m7-score":
            return ai_tasks.marking_tasks(self.pack, self.v2_sheets, self.cycle.paper)
        return ai_tasks.profile_tasks(self.pack, self.cycle.comparison)

    def run(self, module, results, status):
        self._check_module(module)
        self.record(module, {"results": results, "status": status})
        return self.feed(module)

    # ---- the feeds
    def feed(self, module):
        return getattr(self, f"_feed_{module.replace('-', '_')}")()

    def _feed_m3(self):
        cycle = self.cycle
        questions = insights.question_view(self.pack, cycle.diagnoses)
        for question in questions:
            found = self.insights.get(question["id"], {})
            question["callout"] = found.get("callout", "")
            for way in question["ways"]:
                way["think"] = found.get("ways", {}).get(way["id"], way["think"])
        class_view = cycle.class_view()
        for row in class_view["misconceptions"]:
            row["examples"] = insights.examples(questions, row["code"])
            row["why"] = self.pack.misconceptions[row["code"]]["belief"]
            row["looks_like"] = self.pack.misconceptions[row["code"]].get("looks_like", "")
            row["fix"] = self._fix(row["code"])
        return {"ai": self.ai.get("m3"), "ai_actions": self.ai.get("m3-actions"), "actions": self.actions, "ai_insight": self.ai.get("m3-insight"), "ai_failed_students": self.ai.get("m3_failed", 0), "class": class_view,
                "overview": insights.overview(self.pack, cycle.diagnoses, questions), "questions": questions,
                "students": [{k: d[k] for k in ("student", "summary", "next", "teacher", "hypotheses", "two_explanations")} | {"answers": self._answers(d)}
                             for d in cycle.diagnoses.values()]}

    def _answers(self, diagnosis):
        rows = []
        for trace in diagnosis["traces"]:
            level, code = insights.answer_level(self.pack, trace)
            rows.append({"q": trace["q"], "result": trace["result"], "working": trace["working"], "findings": trace["findings"], "level": level, "error": code,
                         "label": self.pack.misconceptions[code]["name"] if code else insights.LEVEL_LABELS[level]})
        return rows

    def _feed_m3_insight(self):
        return self._feed_m3()

    def _feed_m3_key(self):
        return {"ai": self.ai.get("m3-key"), "paper": self._paper_view()}

    def _feed_m3_read(self):
        return {"ai": self.ai.get("m3"), "ai_failed_students": self.ai.get("m3_failed", 0)}

    def _feed_m3_errors(self):
        return self._feed_m3()

    def _feed_m3_actions(self):
        return self._feed_m3()

    def _fix(self, code):
        """How one thinking error is fixed: teaching steps, a class activity, and a question that checks it."""
        entry = self.pack.misconceptions[code]
        intervention = next((self.pack.interventions[i] for i in self.pack.intervention_map.get(code, ()) if i in self.pack.interventions), {})
        return {"steps": list(intervention.get("steps") or []), "activity": entry.get("activity") or intervention.get("objective"),
                "check": entry.get("exit_check") or intervention.get("exit_check"), "teacher": entry.get("teacher"), "student": entry.get("student")}

    def _paper_view(self):
        if not self.pack:
            return []
        return [{"id": i["id"], "number": i.get("number"), "part": i.get("part"), "text": i["text"], "marks": i.get("marks"),
                 "answer": str(i.get("correct") or i.get("answer") or i.get("key") or ""), "answer_source": i.get("answer_source")} for i in self.pack.items]

    def _feed_m4(self):
        rows = [{"student": m["student"], "primary": m["primary"], "secondary": m["secondary"]} for m in self.cycle.mappings]
        titles = {i: e["title"] for i, e in self.pack.interventions.items()}
        return {"ai": self.ai.get("m4"), "mappings": rows, "titles": titles, "why": self.rationale}

    def _feed_m5(self):
        return {"ai": self.ai.get("m5"), "groups": self.cycle.groups, "cohorts": self.cycle.cohorts, "reasons": self.group_reasons,
                "owners": self.cycle.class_view()["misconceptions"], "titles": {i: e["title"] for i, e in self.pack.interventions.items()}}

    def _feed_m6(self):
        return {"ai": self.ai.get("m6"), "plan": self.cycle.plan, "materials": self.materials, "needs": {g["group_id"]: g["need"] for g in self.cycle.groups},
                "groups": {g["group_id"]: g["student_ids"] for g in self.cycle.groups}}

    def _feed_m7_paper(self):
        return {"ai": self.ai.get("m7-paper"), "flags": self.paper_flags,
                "paper": [{"id": i["id"], "text": i["text"], "answer": str(i.get("correct", "Reasoned answer")), "parallel_of": i["parallel_of"]} for i in self.cycle.paper]}

    def _feed_m7_score(self):
        return {"ai": self.ai.get("m7-score"), "ai_failed_students": self.ai.get("m7_failed", 0), "comparison": self.cycle.comparison,
                "answers": {s: self._answers(d) for s, d in self.cycle.retests.items()}}

    def _feed_m8(self):
        views = {s: p.view() for s, p in self.cycle.profiles.items()}
        for view in views.values():
            view.pop("evidence_log")
        return {"ai": self.ai.get("m8"), "profiles": views, "narrative": self.narrative, "comparison": self.cycle.comparison, "audit": self.cycle.audit}

    def status(self):
        reached = STAGES.index(self.stage)
        feeds = {m: self.feed(m) for m in FEEDS if reached >= STAGES.index(MODULES[m][1])}
        return {"class_id": self.class_id, "name": self.name, "class_code": self.class_code, "pack": self.pack_key, "generic": self.generic,
                "subject_map": self.pack.describe() if self.pack else None, "paper": self._paper_view(), "stage": self.stage,
                "policy": self.cycle.policy if self.cycle else policy.resolve({}, self.overrides), "policy_overrides": self.overrides,
                "settings_open": self.stage in SETTINGS_OPEN, "uploads": self.upload_reports, "feeds": feeds, "ai": self.ai,
                "v2_columns": self.question_ids("v2") if reached >= STAGES.index("paper_ready") else None}


def create(pack_key, name, overrides=None, code=None):
    if pack_key != GENERIC and pack_key not in all_packs():
        raise WorkflowError("Unknown chapter.")
    pack = all_packs().get(pack_key)
    found = policy.problems(overrides or {}, set(pack.misconceptions) if pack else None)
    if found:
        raise WorkflowError("; ".join(found))
    try:
        policy.resolve(pack.policy if pack else {}, overrides)
    except ValueError as err:
        raise WorkflowError(str(err)) from err
    workflow = Workflow(secrets.token_urlsafe(18))
    workflow.record("create", {"pack": pack_key, "name": name, "class_code": class_code(code or name), **({"policy": overrides} if overrides else {})})
    return workflow


def load(class_id):
    """Rebuild a class from its saved events, or None."""
    rows = store.get().events(class_id)
    if not rows:
        return None
    workflow = Workflow(class_id)
    for kind, payload, at in rows:
        workflow._apply(kind, payload, at)
    return workflow


def class_records(code):
    """Everything kept for one class: its papers and, per student, their results on each. For work across subjects."""
    saved, base = store.get(), f"classes/{class_code(code)}"
    record = saved.get_doc(base)
    if record is None:
        return None
    students = {sid: {**doc, "assessments": saved.list_docs(f"{base}/students/{sid}/assessments")} for sid, doc in saved.list_docs(f"{base}/students").items()}
    return {**record, "assessments": saved.list_docs(f"{base}/assessments"), "students": students}
