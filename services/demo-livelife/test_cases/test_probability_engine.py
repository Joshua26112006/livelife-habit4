"""Probability engine: the six demonstration verdicts from the strategy doc (section 6), the rules around them, and the API.
Run from services/demo-livelife:  python -m pytest test_cases"""
import json
import sys
from fractions import Fraction as F
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server  # noqa: E402
import adaptive_engine  # noqa: E402
from adaptive_engine.clustering import owners_for  # noqa: E402
from adaptive_engine.identification import diagnose_student  # noqa: E402
from adaptive_engine.packs.probability import PACK  # noqa: E402
from adaptive_engine.packs.probability.reader import read_answer, read_values  # noqa: E402

SHEETS = json.loads((ROOT / "demos/adaptive-engine/sample_sheets.json").read_text())["students"]
TEST = PACK.items
Q = {q["id"]: q for q in TEST}
client = TestClient(server.create_app())


def analyse_sheets(sheets):
    return adaptive_engine.analyse_sheets(PACK, sheets)


@pytest.fixture(scope="module")
def students():
    return {s["student"]: s for s in analyse_sheets(SHEETS)["students"]}


def findings(qid, text):
    return {f["belief"]: f["confidence"] for f in read_answer(Q[qid], text)["findings"]}


def test_p01_all_correct_gets_extension(students):
    assert students["P01"]["next"] == {"action": "extension"}
    assert students["P01"]["summary"] == {}


def test_p02_label_belief_confirmed_on_seven_questions_all_high(students):
    mc_l = students["P02"]["summary"]["MC-L"]
    assert (mc_l["status"], len(mc_l["questions"]), mc_l["highs"]) == ("confirmed", 7, 7)
    assert students["P02"]["next"]["target"] == "MC-L"


def test_p03_order_confirmed_and_settles_the_two_explanations(students):
    p03 = students["P03"]
    assert p03["summary"]["MC-O"]["questions"] == ["T3", "T4", "T5"]
    assert p03["next"]["target"] == "MC-O"
    assert "MC-L" not in p03["summary"]  # a written list with a reversed pair missing is order, not categories


def test_p04_routes_to_earliest_belief_and_keeps_the_other(students):
    next_step = students["P04"]["next"]
    assert (next_step["target"], next_step["held_for_later"]) == ("MC-N", ["MC-A"])


def test_p05_slips_are_not_beliefs(students):
    summary = students["P05"]["summary"]
    assert summary["MC-U"]["status"] == "confirmed"
    assert summary["SLIP-F"]["questions"] == ["T2"] and summary["SLIP-E"]["questions"] == ["T4"]
    assert students["P05"]["next"]["target"] == "MC-U"


def test_p06_bare_answers_are_only_likely_and_blank_goes_to_teacher(students):
    p06 = students["P06"]
    assert p06["summary"]["MC-L"]["status"] == "likely"
    assert p06["summary"]["MC-L"]["highs"] == 0
    assert p06["next"]["action"] == "probe" and p06["next"]["probe"]
    assert p06["teacher"] == ["T4"]


@pytest.mark.parametrize("text, expected", [
    ("1/2 + 1/2 = 1", F(1)),
    ("1", F(1)),
    ("P = 0", F(0)),
    ("65%", F(13, 20)),
    ("1 + 0.35 = 1.35", F(27, 20)),
    ("1-1/4", F(1, 4)),
    ("1 -1/4", F(1, 4)),
    ("x = -1/2", F(-1, 2)),
    ("P = 4/10, total = 10", F(2, 5)),
])
def test_final_value_is_read(text, expected):
    num, den = read_values(text)[-1]
    assert num / den == expected


def test_divide_by_zero_is_not_a_value():
    assert read_values("3/0") == []
    assert read_answer(Q["T1"], "3/0")["result"] == "unreadable"


def test_percent_answer_can_be_correct():
    assert read_answer(Q["T8"], "65%")["result"] == "correct"


def test_answer_label_alone_is_not_working():
    assert findings("T1", "Ans: 2/3") == {"MC-L": "medium"}
    assert findings("T1", "colours so 2/3") == {"MC-L": "high"}


def test_value_outside_range_is_flagged_on_any_question():
    assert findings("T2", "6/5")["MC-R"] == "high"
    assert findings("T8", "1 + 0.35 = 1.35")["MC-R"] == "high"


def test_coin_listing_with_all_outcomes_plus_noise_counts_as_complete():
    trace = read_answer(Q["T3"], "HH HT TH TT HHH so 2/4")
    assert trace["steps"]["Sample space"] == "all 4 outcomes listed" and trace["result"] == "correct"


def test_unmapped_answer_goes_to_teacher_and_never_to_extension():
    result = diagnose_student(PACK, {"id": "X", "answers": {**SHEETS[0]["answers"], "T1": "7/9"}})
    assert result["summary"]["UNMAPPED"]["status"] == "unmapped"
    assert result["teacher"] == ["T1"]
    assert result["next"] == {"action": "teacher_review"}


def test_all_blank_sheet_is_teacher_review_and_not_counted_wrong():
    result = diagnose_student(PACK, {"id": "X", "answers": {}})
    assert result["next"] == {"action": "teacher_review"}
    assert result["summary"] == {} and len(result["teacher"]) == len(TEST)


@pytest.mark.parametrize("text, result", [
    ("Yes she is right, three colours so 1/3", "wrong"),
    ("No, 4 parts so 2/4", "correct"),
    ("2/4", "correct"),
    ("No", "correct_reason_unclear"),
    ("I don't know", "argument_unclear"),
])
def test_argument_question(text, result):
    assert read_answer(Q["T7"], text)["result"] == result


def test_unclear_argument_goes_to_teacher():
    sheet = {"id": "X", "answers": {**SHEETS[0]["answers"], "T7": "maybe"}}
    assert diagnose_student(PACK, sheet)["teacher"] == ["T7"]


def test_templates_compute_the_documented_answers():
    expected = dict(T1=F(4, 10), T2=F(3, 6), T3=F(2, 4), T4=F(4, 36), T5=F(11, 36), T6=F(8, 11), T8=F(13, 20), T9=F(3, 4), T10=F(4, 9))
    assert {qid: Q[qid]["correct"] for qid in expected} == expected


@pytest.mark.parametrize("code, share, owners", [
    ("MC-L", F(25, 100), ["content", "teacher", "student"]),
    ("MC-L", F(24, 100), ["teacher", "student"]),
    ("MC-L", F(10, 100), ["teacher", "student"]),
    ("MC-L", F(9, 100), ["student"]),
    ("SLIP-F", F(90, 100), ["student"]),
])
def test_fix_owner_thresholds(code, share, owners):
    assert owners_for(PACK, code, share) == owners


def test_class_view_on_the_sample():
    view = analyse_sheets(SHEETS)["class"]
    rows = {row["code"]: row for row in view["misconceptions"]}
    assert rows["MC-L"]["students"] == ["P02", "P06"]
    assert rows["MC-L"]["owners"] == ["content", "teacher", "student"]
    assert set(rows["SLIP-F"]["remedies"]) == {"student"}
    assert rows["MC-U"]["owners"] == ["teacher", "student"]  # 1 of 6 is 16.7%
    assert rows["MC-U"]["awaiting_expert_draft"] == []
    assert view["proposed_groups"]["MC-L"] == ["P02"]
    assert view["extension"] == ["P01"]
    assert view["teacher_queue"] == [{"student": "P06", "questions": ["T4"]}]
    assert view["unmapped_answers"] == 0


def test_undrafted_remedy_is_flagged_when_content_owns_it():
    p05_alone = [s for s in SHEETS if s["id"] == "P05"]
    rows = {row["code"]: row for row in analyse_sheets(p05_alone)["class"]["misconceptions"]}
    assert rows["MC-U"]["awaiting_expert_draft"] == ["content"]
    assert rows["MC-U"]["remedies"]["content"] is None


def test_engine_source_is_not_served():
    assert client.get("/demo-livelife/adaptive-engine/backend.py").status_code == 404
