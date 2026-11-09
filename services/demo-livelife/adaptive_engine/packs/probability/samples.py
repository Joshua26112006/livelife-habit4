"""Synthetic sample files for the Probability pack. Not real student data."""
import json
import re
from pathlib import Path

from ...bulk import to_csv
from ...samples import paper_columns

STUDENTS = Path(__file__).resolve().parents[3] / "demos" / "adaptive-engine" / "sample_sheets.json"
KEEPS_BELIEF = {"P04": "MC-N"}
BARE_ANSWERS = {"P05"}


def _v2_answer(item, student, keeps=KEEPS_BELIEF, bare=BARE_ANSWERS):
    if item["type"] == "argue":
        parts = re.search(r"has (\d+) equal", item["text"]).group(1)
        return f"No. {parts} equal parts, so count the parts, not the colours"
    belief = keeps.get(student)
    if belief:
        predicted = next((s["value"] for s in item["signatures"] if s["belief"] == belief and "value" in s), None)
        if predicted is not None:
            return f"I think it is {predicted}"
    correct = item["correct"]
    return str(correct) if student in bare else f"favourable outcomes over all outcomes = {correct.numerator * 2}/{correct.denominator * 2} = {correct}"


def sample(pack, round_name):
    columns, items = paper_columns(pack, round_name)
    sheets = json.loads(STUDENTS.read_text())["students"]
    if round_name == "v1":
        return to_csv(columns, [[s["id"]] + [s["answers"].get(i["id"], "") for i in items] for s in sheets])
    return to_csv(columns, [[s["id"]] + [_v2_answer(i, s["id"]) for i in items] for s in sheets])


# The three-question check: how each of 30 sample students answered the card, coins and die.
SHORT_WAYS = {
    "Q1": {"OK": "4 kings out of 52 cards\nP = 4/52 = 1/13", "ONLY": "1/13", "SLIP": "4 kings, 52 cards\nP = 4/52 = 1/12", "ONE": "1 king in the deck\nP = 1/52", "CAT": "king or not a king\nP = 1/2", "B": ""},
    "Q2": {"OK": "HH, HT, TH, TT\none head: HT, TH\nP = 2/4 = 1/2", "ONLY": "1/2", "RW": "head or tail\nso 1/2", "ORDER": "HH, HT, TT\none head: HT\nP = 1/3", "CAT": "two heads, one head,\nno head\nP = 1/3", "B": ""},
    "Q3": {"CMP": "no six: 5 x 5 = 25 of 36\nP = 1 - 25/36 = 11/36", "LIST": "row 6 + column 6\n(6,6) counted once\n11/36", "ADD": "1/6 + 1/6 = 2/6\n= 1/3", "CAT": "six or no six\nP = 1/2", "B": ""},
}
SHORT_CLASS = ("S01 OK OK CMP,S02 OK OK CMP,S03 OK OK LIST,S04 OK OK CMP,S05 OK OK ADD,S06 OK OK ADD,S07 OK OK ADD,S08 OK ORDER ADD,S09 OK ORDER ADD,S10 OK ORDER LIST,"
               "S11 OK ORDER CMP,S12 OK OK ADD,S13 OK ONLY CMP,S14 OK ORDER ADD,S15 OK OK LIST,S16 OK OK B,S17 ONLY OK CMP,S18 ONLY ONLY ADD,S19 CAT CAT CAT,S20 CAT CAT CAT,"
               "S21 CAT CAT CAT,S22 CAT RW CAT,S23 CAT CAT CAT,S24 CAT RW CAT,S25 ONE ORDER ADD,S26 ONE ORDER ADD,S27 ONE OK CAT,S28 SLIP RW B,S29 SLIP CAT B,S30 B B B")
SHORT_KEEPS = {"S19": "MC-L", "S20": "MC-L", "S25": "MC-A", "S26": "MC-A"}
SHORT_BARE = {"S13", "S18"}


def short_sample(pack, round_name):
    columns, items = paper_columns(pack, round_name)
    rows = [line.split() for line in SHORT_CLASS.split(",")]
    if round_name == "v1":
        return to_csv(columns, [[r[0]] + [SHORT_WAYS[q][way] for q, way in zip(("Q1", "Q2", "Q3"), r[1:])] for r in rows])
    return to_csv(columns, [[r[0]] + [_v2_answer(i, r[0], SHORT_KEEPS, SHORT_BARE) for i in items] for r in rows])
