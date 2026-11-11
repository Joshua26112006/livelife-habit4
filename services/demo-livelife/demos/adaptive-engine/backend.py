"""Adaptive Teaching Engine API. Mounted at /demo-livelife/adaptive-engine/api/.

One class, one workflow: create, bulk upload, then one feed per module. This service holds the rules and the saved class. It has no
API key: the site's /api/adaptive/<module> routes fetch a module's AI tasks from here, run them, and post the replies back, and
ai_tasks.py validates every reply. A class id is long and random because there is no sign-in yet: synthetic data only until there is.

NB: no `from __future__ import annotations` here (server.py loads this file without putting it in sys.modules, and pydantic
then cannot resolve string annotations on the request models).
"""
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from adaptive_engine import bulk, samples, workflow as wf
from adaptive_engine.packs import all_packs

router = APIRouter()
SAMPLE_PAPER = Path(bulk.__file__).resolve().parent / "sample_papers" / "probability-5q"

NO_STORE = {"Cache-Control": "no-store"}
CLASS_ID = re.compile(r"^[A-Za-z0-9_-]{16,40}$")
ROUNDS = ("v1", "v2")


def _ok(body):
    return JSONResponse(body, headers=NO_STORE)


def _error(message, status):
    return JSONResponse({"error": message}, status_code=status, headers=NO_STORE)


def _with_class(class_id, action):
    """Load the class and run one step, turning expected failures into plain messages."""
    workflow = wf.load(class_id) if CLASS_ID.match(class_id) else None
    if workflow is None:
        return _error("Class not found.", 404)
    try:
        return _ok(action(workflow))
    except (wf.WorkflowError, bulk.UploadError, ValueError, KeyError, StopIteration, sqlite3.IntegrityError) as err:
        return _error(str(err) or "That step could not be completed.", 409)


class NewClass(BaseModel):
    """pack is a subject pack's key, or "generic" for any uploaded paper. class_code groups runs of the same class across
    subjects (default: from the name)."""
    pack: str
    name: str = Field(min_length=1, max_length=60)
    class_code: str = Field(default="", max_length=40)
    policy: Dict[str, Any] = Field(default_factory=dict)


class Settings(BaseModel):
    """Class rules to try: see adaptive_engine/policy.py. Send the full set of overrides each time; {} goes back to the pack's."""
    policy: Dict[str, Any] = Field(default_factory=dict)
    teacher: str = Field(default="teacher", max_length=40)


class ModuleRun(BaseModel):
    results: Dict[str, Any] = Field(default_factory=dict)
    status: str = Field(default="off", max_length=12)


class Probe(BaseModel):
    student: str = Field(max_length=40)
    code: str = Field(max_length=30)
    outcome: str = Field(max_length=12)
    teacher: str = Field(default="teacher", max_length=40)


class Move(BaseModel):
    student: str = Field(max_length=40)
    from_group: str = Field(max_length=60)
    to_group: str = Field(max_length=60)
    teacher: str = Field(default="teacher", max_length=40)
    rationale: str = Field(default="", max_length=300)


class Priority(BaseModel):
    group_ids: List[str] = Field(max_length=100)
    teacher: str = Field(default="teacher", max_length=40)


class Approve(BaseModel):
    teacher: str = Field(default="teacher", max_length=40)


@router.get("/subjects")
def subjects():
    """Every registered subject pack and its map: competencies, misconceptions, questions and review state."""
    return _ok({key: pack.describe() for key, pack in all_packs().items()})


@router.post("/classes")
def create_class(body: NewClass):
    try:
        return _ok({"class_id": wf.create(body.pack, body.name.strip(), body.policy, body.class_code.strip() or None).class_id})
    except wf.WorkflowError as err:
        return _error(str(err), 400)


@router.get("/classes/{class_id}")
def class_status(class_id: str):
    return _with_class(class_id, lambda w: w.status())


@router.post("/classes/{class_id}/paper")
async def paper(class_id: str, request: Request):
    """The question paper for a generic class: the questions JSON, with expected answers where the teacher has them."""
    data = await request.body()
    if len(data) > bulk.MAX_BYTES:
        return _error("The paper is larger than 2 MB.", 413)
    return _with_class(class_id, lambda w: w.set_paper(data))


class Answers(BaseModel):
    answers: Dict[str, str] = Field(max_length=200)
    teacher: str = Field(default="teacher", max_length=40)


@router.post("/classes/{class_id}/answers")
def answers(class_id: str, body: Answers):
    """The teacher's expected answers for a generic class, by item id (Q1, Q2i, ...)."""
    return _with_class(class_id, lambda w: w.set_answers(body.answers, body.teacher))


@router.get("/records/{code}")
def records(code: str):
    """Everything kept for one class across its papers and subjects: per paper, the thinking errors and groups; per student, results."""
    if not re.fullmatch(r"[A-Za-z0-9_ -]{1,40}", code):
        return _error("Class not found.", 404)
    found = wf.class_records(code)
    return _ok(found) if found else _error("Class not found.", 404)


@router.post("/classes/{class_id}/upload/{round_name}")
async def upload(class_id: str, round_name: str, request: Request, filename: str = "answers.csv"):
    if round_name not in ROUNDS:
        return _error("Unknown round.", 404)
    data = await request.body()
    return _with_class(class_id, lambda w: w.upload(round_name, data, filename))


@router.get("/classes/{class_id}/{module}/tasks")
def module_tasks(class_id: str, module: str):
    if module not in wf.MODULES:
        return _error("Unknown module.", 404)
    return _with_class(class_id, lambda w: {"tasks": w.tasks(module)})


@router.post("/classes/{class_id}/{module}/run")
def module_run(class_id: str, module: str, body: ModuleRun):
    if module not in wf.MODULES:
        return _error("Unknown module.", 404)
    return _with_class(class_id, lambda w: w.run(module, body.results, body.status))


def _teacher_step(class_id, stage, kind, payload):
    def step(w):
        w._need(stage)
        w.record(kind, payload)
        return w.status()
    return _with_class(class_id, step)


@router.post("/classes/{class_id}/settings")
def settings(class_id: str, body: Settings):
    return _with_class(class_id, lambda w: w.settings(body.policy, body.teacher))


@router.post("/classes/{class_id}/probes")
def probe(class_id: str, body: Probe):
    return _teacher_step(class_id, "identified", "probe", body.model_dump())


@router.post("/classes/{class_id}/groups/move")
def move(class_id: str, body: Move):
    return _teacher_step(class_id, "grouped", "move", body.model_dump())


@router.post("/classes/{class_id}/groups/priority")
def priority(class_id: str, body: Priority):
    return _teacher_step(class_id, "grouped", "priority", body.model_dump())


@router.post("/classes/{class_id}/plan/approve")
def approve(class_id: str, body: Approve):
    return _teacher_step(class_id, "planned", "approve", body.model_dump())


@router.get("/files/{pack}/{round_name}")
def files(pack: str, round_name: str, sample: bool = False):
    """A blank template, or a synthetic sample, for one paper. For "generic", the sample question paper and students' answers."""
    if pack == wf.GENERIC:
        name = {"paper": "questions.json", "v1": "students.json"}.get(round_name)
        if not sample or name is None:
            return _error("Unknown file.", 404)
        text = (SAMPLE_PAPER / name).read_text()
        return Response(text, media_type="application/json", headers={"Content-Disposition": f'attachment; filename="sample-{name}"', **NO_STORE})
    chapter = all_packs().get(pack)
    if chapter is None or round_name not in ROUNDS or (sample and chapter.sample is None):
        return _error("Unknown file.", 404)
    text = chapter.sample(chapter, round_name) if sample else samples.template(chapter, round_name)
    is_json = text.lstrip()[:1] in ("{", "[")
    name = f"{pack}-{round_name}-{'sample' if sample else 'template'}.{'json' if is_json else 'csv'}"
    return Response(text, media_type="application/json" if is_json else "text/csv", headers={"Content-Disposition": f'attachment; filename="{name}"', **NO_STORE})
