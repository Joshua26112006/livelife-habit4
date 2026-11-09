"""Synthetic sample files for the Probability pack. Not real student data."""
import json
import re
from pathlib import Path

from ...bulk import to_csv
from ...samples import paper_columns

STUDENTS = Path(__file__).resolve().parents[3] / "demos" / "adaptive-engine" / "sample_sheets.json"
KEEPS_BELIEF = {"P04": "MC-N"}
BARE_ANSWERS = {"P05"}


def _v2_answer(item, student):
    if item["type"] == "argue":
        parts = re.search(r"has (\d+) equal", item["text"]).group(1)
        return f"No. {parts} equal parts, so count the parts, not the colours"
    belief = KEEPS_BELIEF.get(student)
    if belief:
        predicted = next((s["value"] for s in item["signatures"] if s["belief"] == belief and "value" in s), None)
        if predicted is not None:
            return f"I think it is {predicted}"
    correct = item["correct"]
    return str(correct) if student in BARE_ANSWERS else f"favourable outcomes over all outcomes = {correct.numerator * 2}/{correct.denominator * 2} = {correct}"


def sample(pack, round_name):
    columns, items = paper_columns(pack, round_name)
    sheets = json.loads(STUDENTS.read_text())["students"]
    if round_name == "v1":
        return to_csv(columns, [[s["id"]] + [s["answers"].get(i["id"], "") for i in items] for s in sheets])
    return to_csv(columns, [[s["id"]] + [_v2_answer(i, s["id"]) for i in items] for s in sheets])
