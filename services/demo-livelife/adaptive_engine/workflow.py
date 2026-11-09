"""The class workflow: upload, each module in turn, teacher decisions, re-test, profiles.

Each step is saved as an event, and a class is rebuilt by replaying its events, so a class can stop at any stage and pick up days
later. Parallel papers are deterministic, so replay gives the same result. Local SQLite here; a real deployment swaps `_db`.
"""
import json
import os
import secrets
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from . import ai_tasks, bulk, insights
from .cycle import ClassCycle
from .packs import all_packs

STAGES = ("created", "uploaded", "identified", "mapped", "grouped", "planned", "approved", "paper_ready", "v2_uploaded", "scored", "profiled")
# module: (stage it needs, stage it leads to)
MODULES = {"m3": ("uploaded", "identified"), "m3-insight": ("identified", "identified"), "m4": ("identified", "mapped"), "m5": ("mapped", "grouped"), "m6": ("grouped", "planned"),
           "m7-paper": ("approved", "paper_ready"), "m7-score": ("v2_uploaded", "scored"), "m8": ("scored", "profiled")}
_LOCK = threading.Lock()


class WorkflowError(ValueError):
    """The step cannot run at this stage."""


def _db():
    path = Path(os.environ.get("ADAPTIVE_DB") or Path(__file__).resolve().parents[1] / "data" / "adaptive.sqlite3")
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE IF NOT EXISTS events (class_id TEXT, seq INTEGER, kind TEXT, payload TEXT, at TEXT, PRIMARY KEY (class_id, seq))")
    return connection


class Workflow:
    def __init__(self, class_id):
        self.class_id, self.pack, self.name, self.cycle = class_id, None, "", None
        self.stage, self.seq = "created", 0
        self.v1_sheets, self.v2_sheets = [], []
        self.upload_reports, self.ai, self.rationale = {}, {}, {}
        self.materials, self.group_reasons, self.paper_flags, self.narrative, self.insights = {}, {}, {}, {}, {}

    # ---- applying events (no side effects, so replay is safe)
    def _apply(self, kind, payload, at):
        self.seq += 1
        if kind != "create":
            self.cycle.clock = lambda: at
        getattr(self, f"_on_{kind.replace('-', '_')}")(payload)

    def _on_create(self, p):
        self.pack, self.name = all_packs()[p["pack"]], p["name"]
        self.pack_key = p["pack"]
        self.cycle = ClassCycle(self.pack, self.class_id, allow_draft=True)

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

    def _on_m3_insight(self, p):
        self.ai["m3-insight"] = p.get("status", "off")
        self.insights = ai_tasks.apply_insights(insights.question_view(self.pack, self.cycle.diagnoses), self._results(p))

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
            connection = _db()
            with connection:
                connection.execute("INSERT INTO events VALUES (?,?,?,?,?)", (self.class_id, self.seq, kind, json.dumps(payload), at))
            connection.close()

    def _need(self, *stages):
        if self.stage not in stages:
            raise WorkflowError(f"This step is not available at stage '{self.stage}'.")

    # ---- what the API calls
    def question_ids(self, round_name):
        items = self.pack.items if round_name == "v1" else self.cycle.paper
        return [i["id"] for i in items]

    def upload(self, round_name, data, filename):
        self._need("created" if round_name == "v1" else "paper_ready")
        parsed = bulk.parse_upload(data, filename, self.question_ids(round_name))
        report = {"students": len(parsed["sheets"]), "rejected": parsed["rejected"], "warnings": parsed["warnings"],
                  "blank_answers": sum(1 for s in parsed["sheets"] for a in s["answers"].values() if not a)}
        self.record("upload", {"round": round_name, "sheets": parsed["sheets"], "report": report})
        return report

    def tasks(self, module):
        self._need(MODULES[module][0])
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
        self._need(MODULES[module][0])
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
        return {"ai": self.ai.get("m3"), "ai_insight": self.ai.get("m3-insight"), "ai_failed_students": self.ai.get("m3_failed", 0), "class": class_view,
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
        feeds = {m: self.feed(m) for m, (_, done) in MODULES.items() if m != "m3-insight" and reached >= STAGES.index(done)}
        return {"class_id": self.class_id, "name": self.name, "pack": self.pack_key, "subject_map": self.pack.describe(), "stage": self.stage, "uploads": self.upload_reports, "feeds": feeds,
                "v2_columns": self.question_ids("v2") if reached >= STAGES.index("paper_ready") else None}


def create(pack_key, name):
    if pack_key not in all_packs():
        raise WorkflowError("Unknown chapter.")
    workflow = Workflow(secrets.token_urlsafe(18))
    workflow.record("create", {"pack": pack_key, "name": name})
    return workflow


def load(class_id):
    """Rebuild a class from its saved events, or None."""
    connection = _db()
    rows = connection.execute("SELECT kind, payload, at FROM events WHERE class_id=? ORDER BY seq", (class_id,)).fetchall()
    connection.close()
    if not rows:
        return None
    workflow = Workflow(class_id)
    for kind, payload, at in rows:
        workflow._apply(kind, json.loads(payload), at)
    return workflow
