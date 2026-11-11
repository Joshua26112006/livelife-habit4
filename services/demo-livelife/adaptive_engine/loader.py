"""Loading a subject pack written as data, and checking it before the engine trusts it.

A subject team writes pack.json (and, optionally, sample_v1 and sample_v2 beside it, as .json in the handwriting reader's
format or as .csv); nothing else is needed.
"""
import json
from pathlib import Path

from .pack import ChapterPack
from .policy import problems as policy_problems
from .reading import FORMATS

REQUIRED = ("chapter_id", "version", "subject", "brief", "competencies", "misconceptions", "teaching_order", "interventions", "intervention_map", "items")
KINDS = ("belief", "slip", "fact")
# A teacher has to be able to hold every thinking error in mind and explain it. More than this and they are restating wrong
# answers, not naming causes: merge them. Slips and missing facts do not count.
MAX_THINKING_ERRORS = 5


class PackError(ValueError):
    """The pack cannot be used as written."""


def validate(data):
    """Every reference must resolve, so a typo is caught when the pack loads, not in a classroom."""
    problems = [f"missing '{k}'" for k in REQUIRED if k not in data]
    if problems:
        raise PackError("; ".join(problems))
    codes, competencies, interventions = set(data["misconceptions"]), set(data["competencies"]), set(data["interventions"])
    for code, entry in data["misconceptions"].items():
        if entry.get("kind") not in KINDS:
            problems.append(f"{code}: kind must be one of {', '.join(KINDS)}")
        problems += [f"{code}: unknown competency {c}" for c in entry.get("competency_ids", []) if c not in competencies]
    beliefs = [c for c, e in data["misconceptions"].items() if e.get("kind") == "belief"]
    if len(beliefs) > MAX_THINKING_ERRORS:
        problems.append(f"{len(beliefs)} thinking errors; keep to {MAX_THINKING_ERRORS} a teacher can explain, and merge the rest")
    problems += [f"{c}: say what it looks like in answers ('looks_like'), in words a teacher would use" for c in beliefs
                 if not str(data["misconceptions"][c].get("looks_like") or "").strip()]
    for comp, entry in [*data["competencies"].items(), *data["misconceptions"].items()]:
        if any(not (isinstance(x, dict) and x.get("where") and x.get("example")) for x in entry.get("real_world", [])):
            problems.append(f"{comp}: each real_world entry needs 'where' and 'example'")
    problems += policy_problems(data.get("policy", {}), codes)
    problems += [f"teaching order: unknown code {c}" for c in data["teaching_order"] if c not in codes]
    for code, ids in data["intervention_map"].items():
        if code not in codes:
            problems.append(f"intervention map: unknown code {code}")
        problems += [f"intervention map: unknown intervention {i}" for i in ids if i not in interventions]
    seen = set()
    for item in data["items"]:
        where = item.get("id", "?")
        if where in seen:
            problems.append(f"{where}: duplicate id")
        seen.add(where)
        if item.get("format") not in FORMATS:
            problems.append(f"{where}: format must be one of {', '.join(FORMATS)}")
        problems += [f"{where}: unknown competency {c}" for c in item.get("competency_ids", []) if c not in competencies] or \
            ([f"{where}: needs at least one competency"] if not item.get("competency_ids") else [])
        used = list(item.get("distractors", {}).values()) + [c for level in item.get("levels", {}).values() for c in level] + \
            [e["code"] for e in item.get("errors", [])] + ([item["slip_code"]] if item.get("slip_code") else [])
        problems += [f"{where}: unknown misconception {c}" for c in used if c not in codes]
        if item.get("format") == "choice" and item.get("key") not in item.get("options", {}):
            problems.append(f"{where}: key is not one of the options")
        if item.get("format") == "numeric" and "answer" not in item:
            problems.append(f"{where}: numeric items need an answer")
        if item.get("variants") and not (item["variants"].get("retest") and item["variants"].get("practice")):
            problems.append(f"{where}: variants need both 'retest' and 'practice' lists")
    if problems:
        raise PackError("; ".join(problems))


def build(data, folder=None):
    validate(data)
    folder = Path(folder) if folder else None
    def sample_file(round_name):
        return next((folder / f"sample_{round_name}.{ext}" for ext in ("json", "csv") if (folder / f"sample_{round_name}.{ext}").exists()), None)

    has_samples = folder is not None and sample_file("v1") is not None

    def sample(_pack, round_name):
        return sample_file(round_name).read_text()

    return ChapterPack(
        chapter_id=data["chapter_id"], version=data["version"], competencies=data["competencies"], items=data["items"],
        misconceptions=data["misconceptions"], teaching_order=tuple(data["teaching_order"]), probes=data.get("probes", {}),
        separating_probes={frozenset(x["codes"]): x["probe"] for x in data.get("separating_probes", [])},
        interventions={k: {**v, "duration_minutes": tuple(v["duration_minutes"])} for k, v in data["interventions"].items()},
        intervention_map=data["intervention_map"], subject=data["subject"], brief=data["brief"], upload_hint=data.get("upload_hint", ""),
        extension_task=data.get("extension_task", ""), sample=sample if has_samples else None, policy=data.get("policy", {}),
    )


def load(path):
    path = Path(path)
    try:
        return build(json.loads(path.read_text()), path.parent)
    except PackError as err:
        raise PackError(f"{path.parent.name}: {err}") from err
