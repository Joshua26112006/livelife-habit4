"""The Habit 4 pack: reading real assessment output into Modules 3 to 8, and class submissions.
Run from services/demo-livelife:  python -m pytest test_cases"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from adaptive_engine.identification import diagnose_student  # noqa: E402
from adaptive_engine.interventions import map_student  # noqa: E402
from adaptive_engine.packs.habit4 import PACK, parallel_item, read_answer, to_sheet  # noqa: E402
from adaptive_engine.packs.habit4.knowledge_base import DISTRACTORS, INTERVENTIONS, LEVEL_ONE_PATTERNS, PARALLEL_SCENARIOS  # noqa: E402
from adaptive_engine.profile import LearnerProfile  # noqa: E402

ITEM = {i["id"]: i for i in PACK.items}
KEYS = {i["id"]: i["key"] for i in PACK.items if i["type"] == "mcq"}
SCENARIOS = [i["id"] for i in PACK.items if i["type"] == "scenario"]


def rubric(score, flag=False, text="An answer."):
    return {"text": text, "score": score, "evidence": "seen", "flag": flag}


def sheet(sid="X", mcq=None, scores=None):
    answers = {**KEYS, **(mcq or {})}
    answers.update({s: rubric((scores or {}).get(s, 4)) for s in SCENARIOS})
    return {"id": sid, "answers": answers}


def test_pack_reads_the_assessment_as_its_one_source():
    assert list(PACK.competencies) == SCENARIOS == [f"S{i}" for i in range(1, 9)]
    assert len(KEYS) == 9
    assert PACK.competencies["S1"]["name"] == "Think Win-Win understanding"


def test_every_wrong_option_and_mapping_is_defined():
    for qid, key in KEYS.items():
        assert set(DISTRACTORS[qid]) == set(ITEM[qid]["options"]) - {key}
    known = set(PACK.misconceptions)
    assert all(code in known for options in DISTRACTORS.values() for code in options.values())
    assert all(code in known for codes in LEVEL_ONE_PATTERNS.values() for code in codes)
    assert all(i in INTERVENTIONS for ids in PACK.intervention_map.values() for i in ids)
    assert all(code in PACK.intervention_map for code in known)


def test_all_knowledge_is_draft_so_nothing_is_recommended_by_default():
    assert {e["review_status"] for e in INTERVENTIONS.values()} == {"draft"}
    diagnosis = diagnose_student(PACK, sheet(mcq={"K5": "C"}, scores={"S5": 1}))
    assert map_student(PACK, diagnosis)["primary"]["recommended"] is None


@pytest.mark.parametrize("raw, result, beliefs", [
    ("C", "correct", []),
    ("c ", "correct", []),
    ("B", "wrong", ["WW-GIVE-IN"]),
    ("", "blank", []),
    ("Z", "unreadable", []),
])
def test_knowledge_check_reading(raw, result, beliefs):
    trace = read_answer(ITEM["K1"], raw)
    assert (trace["result"], [f["belief"] for f in trace["findings"]]) == (result, beliefs)


@pytest.mark.parametrize("answer, result, beliefs", [
    (rubric(4), "correct", []),
    (rubric(3), "correct", []),
    (rubric(2), "wrong", ["H4-PARTIAL"]),
    (rubric(1), "wrong", ["WW-DISMISS"]),
    (rubric(0), "irrelevant", []),
    (rubric(0, flag=True), "flagged_for_review", []),
    (rubric(None), "unreadable", []),
    (rubric(4, text=""), "blank", []),
    ("text with no score yet", "unreadable", []),
])
def test_rubric_reading(answer, result, beliefs):
    trace = read_answer(ITEM["S5"], answer)
    assert (trace["result"], [f["belief"] for f in trace["findings"]]) == (result, beliefs)


def test_written_low_plus_matching_choice_is_confirmed():
    diagnosis = diagnose_student(PACK, sheet(mcq={"K5": "C"}, scores={"S5": 1}))
    assert diagnosis["summary"]["WW-DISMISS"]["status"] == "confirmed"
    assert diagnosis["next"]["target"] == "WW-DISMISS"


def test_choice_alone_only_triggers_a_probe():
    diagnosis = diagnose_student(PACK, sheet(mcq={"K8": "B"}))
    assert diagnosis["next"]["action"] == "probe" and diagnosis["next"]["probe"]


def test_rubric_level_with_two_meanings_needs_a_probe_unless_settled():
    open_case = diagnose_student(PACK, sheet(scores={"S1": 1}))
    assert open_case["two_explanations"]["S1"]["settled_by"] is None and open_case["two_explanations"]["S1"]["probe"]
    settled = diagnose_student(PACK, sheet(mcq={"K1": "B"}, scores={"S1": 1}))
    assert settled["two_explanations"]["S1"]["settled_by"] == "WW-GIVE-IN"


def test_partly_shown_means_practice_not_reteaching():
    assert diagnose_student(PACK, sheet(scores={"S3": 2}))["next"] == {"action": "practice", "target": ["H4-PARTIAL"]}


def test_flagged_answer_goes_to_the_teacher_and_is_no_misconception():
    answers = sheet()["answers"]
    answers["S7"] = rubric(0, flag=True)
    diagnosis = diagnose_student(PACK, {"id": "X", "answers": answers})
    assert diagnosis["teacher"] == ["S7"] and diagnosis["summary"] == {} and diagnosis["next"] == {"action": "teacher_review"}


def test_full_marks_get_extension():
    assert diagnose_student(PACK, sheet())["next"] == {"action": "extension"}


def test_choice_and_written_answer_together_demonstrate_a_competency():
    profile = LearnerProfile(PACK, "X")
    diagnosis = diagnose_student(PACK, sheet())
    profile.add_traces("diagnostic", diagnosis["traces"], PACK.items)
    state = profile.view()["competencies"]["S1"]
    assert (state["status"], state["next_action"]) == ("demonstrated", "advance")


@pytest.mark.parametrize("competency", SCENARIOS)
def test_parallel_scenarios_are_new_and_never_reuse_a_retest_as_practice(competency):
    item = ITEM[competency]
    retests = {parallel_item(item, a)["text"] for a in (1, 2)}
    practice = {parallel_item(item, a)["text"] for a in (100, 101)}
    assert len(retests) == 2 and len(practice) == 2 and not retests & practice and item["text"] not in retests | practice
    assert parallel_item(item, 1)["competency_ids"] == [competency]
    assert len(PARALLEL_SCENARIOS[competency]) == 4


def test_knowledge_check_item_retests_with_a_written_situation():
    assert parallel_item(ITEM["K5"], 1)["type"] == "scenario"


def test_stored_submission_converts_to_a_sheet():
    converted = to_sheet("s", {"mcq": {"K1": "A"}, "answers": {"S1": "t"}, "results": {"S1": {"score": 3, "evidence": "e", "flag": False}}})
    assert converted == {"id": "s", "answers": {"K1": "A", "S1": {"text": "t", "score": 3, "evidence": "e", "flag": False}}}
