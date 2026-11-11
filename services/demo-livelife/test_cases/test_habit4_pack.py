"""A subject written only as data (Habit 4), and the engine's own reader for choice, numeric and written questions.
Run from services/demo-livelife:  python -m pytest test_cases"""
import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from adaptive_engine import ClassCycle  # noqa: E402
from adaptive_engine.identification import diagnose_student  # noqa: E402
from adaptive_engine.interventions import map_student  # noqa: E402
from adaptive_engine.loader import PackError, build  # noqa: E402
from adaptive_engine.packs import all_packs  # noqa: E402
from adaptive_engine.profile import LearnerProfile  # noqa: E402

DATA = json.loads((ROOT / "adaptive_engine/packs/habit4/pack.json").read_text())
PACK = all_packs()["habit4"]
ITEM = {i["id"]: i for i in PACK.items}
KEYS = {i["id"]: i["key"] for i in PACK.items if i["format"] == "choice"}
WRITTEN = [i["id"] for i in PACK.items if i["format"] == "written"]


def rubric(score, flag=False, text="An answer."):
    return {"text": text, "score": score, "evidence": "seen", "flag": flag}


def sheet(sid="X", mcq=None, scores=None):
    answers = {**KEYS, **(mcq or {})}
    answers.update({s: rubric((scores or {}).get(s, 4)) for s in WRITTEN})
    return {"id": sid, "answers": answers}


# The pack is data, and it matches the real assessment
def test_habit4_names_a_few_explainable_thinking_errors():
    beliefs = [e for e in PACK.misconceptions.values() if e["kind"] == "belief"]
    assert len(beliefs) == 3 and all(e["looks_like"] and e["teacher"] for e in beliefs)
    assert PACK.misconceptions["WW-NAMES"]["kind"] == "fact"  # not knowing a name is a gap, not a thinking error


def test_habit4_has_no_code():
    assert sorted(p.name for p in (ROOT / "adaptive_engine/packs/habit4").iterdir() if p.suffix == ".py") == []


def test_exported_questions_match_the_assessment():
    spec = importlib.util.spec_from_file_location("assessment_source", ROOT / "demos/livelife-student/backend.py")
    source = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(source)
    assert {q["id"]: (q["stem"], q["key"], q["options"]) for q in source.MCQS} == {i: (ITEM[i]["text"], ITEM[i]["key"], ITEM[i]["options"]) for i in KEYS}
    assert {s["id"]: s["question"] for s in source.SCENARIOS} == {i: ITEM[i]["text"] for i in WRITTEN}


def test_every_wrong_option_is_mapped_and_every_rubric_is_present():
    for qid, key in KEYS.items():
        assert set(ITEM[qid]["distractors"]) == set(ITEM[qid]["options"]) - {key}
    assert all(ITEM[q]["rubric"]["levels_text"] and ITEM[q]["rubric"]["elements"] for q in WRITTEN)


@pytest.mark.parametrize("break_it, message", [
    (lambda d: d["items"][0]["distractors"].update({"A": "NOPE"}), "unknown misconception NOPE"),
    (lambda d: d["items"][0].update({"format": "essay"}), "format must be"),
    (lambda d: d["items"][0].update({"key": "Z"}), "key is not one of the options"),
    (lambda d: d["intervention_map"].update({"WW-NAMES": ["INT-NOPE"]}), "unknown intervention INT-NOPE"),
    (lambda d: d["teaching_order"].append("NOPE"), "teaching order: unknown code"),
    (lambda d: d.pop("brief"), "missing 'brief'"),
    (lambda d: d["misconceptions"]["WW-NOT-ASKING"].pop("looks_like"), "WW-NOT-ASKING: say what it looks like"),
    (lambda d: d["misconceptions"].update({f"X{n}": {**d["misconceptions"]["WW-NOT-ASKING"]} for n in range(3)}), "6 thinking errors; keep to 5"),
])
def test_a_broken_pack_is_refused_with_the_reason(break_it, message):
    data = copy.deepcopy(DATA)
    break_it(data)
    with pytest.raises(PackError, match=message):
        build(data)


def test_all_knowledge_is_draft_so_nothing_is_recommended_by_default():
    diagnosis = diagnose_student(PACK, sheet(mcq={"K5": "C"}, scores={"S5": 1}))
    assert map_student(PACK, diagnosis)["primary"]["recommended"] is None


# The engine's reader: choice and written
@pytest.mark.parametrize("raw, result, beliefs", [("C", "correct", []), ("c ", "correct", []), ("B", "wrong", ["WW-SOMEONE-LOSES"]), ("", "blank", []), ("Z", "unreadable", [])])
def test_choice_reading(raw, result, beliefs):
    trace = PACK.read(ITEM["K1"], raw)
    assert (trace["result"], [f["belief"] for f in trace["findings"]]) == (result, beliefs)


@pytest.mark.parametrize("answer, result, beliefs", [
    (rubric(4), "correct", []), (rubric(3), "correct", []), (rubric(2), "wrong", ["H4-PARTIAL"]), (rubric(1), "wrong", ["WW-NOT-ASKING"]),
    (rubric(0), "irrelevant", []), (rubric(0, flag=True), "flagged_for_review", []), (rubric(None), "unreadable", []),
    (rubric(4, text=""), "blank", []), ("text with no score yet", "unreadable", []),
])
def test_written_reading(answer, result, beliefs):
    trace = PACK.read(ITEM["S5"], answer)
    assert (trace["result"], [f["belief"] for f in trace["findings"]]) == (result, beliefs)


def test_written_low_plus_matching_choice_is_confirmed():
    diagnosis = diagnose_student(PACK, sheet(mcq={"K5": "C"}, scores={"S5": 1}))
    assert diagnosis["summary"]["WW-NOT-ASKING"]["status"] == "confirmed" and diagnosis["next"]["target"] == "WW-NOT-ASKING"


def test_choice_alone_groups_the_student_as_a_candidate():
    diagnosis = diagnose_student(PACK, sheet(mcq={"K8": "B"}))
    assert diagnosis["next"]["action"] == "group" and diagnosis["next"]["evidence"] == "candidate"


def test_choice_alone_triggers_a_probe_when_the_class_asks_for_confirmed_evidence():
    diagnosis = diagnose_student(PACK, sheet(mcq={"K8": "B"}), policy=PACK.settings({"group_from": "confirmed"}))
    assert diagnosis["next"]["action"] == "probe" and diagnosis["next"]["probe"]


def test_stronger_evidence_is_grouped_before_weaker():
    # WW-SOMEONE-LOSES is earlier in teaching order but rests on one answer; WW-LOOSE-PROMISE is confirmed on two.
    diagnosis = diagnose_student(PACK, sheet(mcq={"K1": "B", "K6": "A"}, scores={"S6": 1}))
    assert diagnosis["next"]["target"] == "WW-LOOSE-PROMISE" and diagnosis["next"]["held_for_later"] == ["WW-SOMEONE-LOSES"]


def test_rubric_level_with_two_meanings_needs_a_probe_unless_settled():
    assert diagnose_student(PACK, sheet(scores={"S2": 1}))["two_explanations"]["S2"]["probe"]
    assert diagnose_student(PACK, sheet(mcq={"K1": "B"}, scores={"S2": 1}))["two_explanations"]["S2"]["settled_by"] == "WW-SOMEONE-LOSES"


def test_partly_shown_means_practice_not_reteaching():
    assert diagnose_student(PACK, sheet(scores={"S3": 2}))["next"] == {"action": "practice", "target": ["H4-PARTIAL"]}


def test_flagged_answer_goes_to_the_teacher_and_is_no_misconception():
    answers = sheet()["answers"]
    answers["S7"] = rubric(0, flag=True)
    diagnosis = diagnose_student(PACK, {"id": "X", "answers": answers})
    assert diagnosis["teacher"] == ["S7"] and diagnosis["summary"] == {} and diagnosis["next"] == {"action": "teacher_review"}


def test_choice_and_written_answer_together_demonstrate_a_competency():
    profile = LearnerProfile(PACK, "X")
    profile.add_traces("diagnostic", diagnose_student(PACK, sheet())["traces"], PACK.items)
    state = profile.view()["competencies"]["S1"]
    assert (state["status"], state["next_action"]) == ("demonstrated", "advance")


# Parallel questions come from the variant bank
@pytest.mark.parametrize("competency", WRITTEN)
def test_parallel_questions_are_new_and_never_reuse_a_retest_as_practice(competency):
    item = ITEM[competency]
    retests = {PACK.parallel(item, a)["text"] for a in (1, 2)}
    practice = {PACK.parallel(item, a)["text"] for a in (100, 101)}
    assert len(retests) == 2 and len(practice) == 2 and not retests & practice and item["text"] not in retests | practice
    assert PACK.parallel(item, 1)["rubric"] == item["rubric"] and PACK.parallel(item, 1)["id"] == f"{competency}-P1"


def test_choice_item_retests_with_a_written_question_on_its_competency():
    new = PACK.parallel(ITEM["K5"], 1)
    assert new["format"] == "written" and new["competency_ids"] == ["S5"] and new["parallel_of"] == "K5"


def test_v2_paper_holds_the_items_with_a_bank():
    assert [i["id"] for i in PACK.retest_items] == WRITTEN


# The engine's reader: numeric, for any subject that writes its questions as data
NUMERIC = {
    "id": "N1", "text": "A shirt costs 400 and is sold at 25% off. Find the price.", "format": "numeric", "competency_ids": ["C1"], "answer": "300",
    "accept": ["300.0"], "steps": [{"label": "Discount", "value": "100"}, {"label": "Price", "value": "300"}],
    "errors": [{"value": "100", "code": "OFF", "why": "gave the discount, not the price"}, {"value": "500", "code": "ADD", "why": "added the discount"}],
    "slip_code": "SLIP",
}


def numeric_pack():
    entry = lambda kind: {"name": kind, "belief": kind, "looks_like": kind, "kind": kind, "competency_ids": ["C1"], "student": "s", "teacher": "t", "content": "c", "exit_check": "e"}
    intervention = {"title": "T", "objective": None, "steps": ["s"], "duration_minutes": [5, 10], "assets": [], "item_types": [], "exit_check": None, "review_status": "approved", "version": "1"}
    return build({"chapter_id": "pct", "version": "1", "subject": {"subject": "Maths", "board": "B", "grade": "8", "chapter": "Percent", "source": "S"},
                  "brief": "Grade 8 percentages.", "competencies": {"C1": {"name": "Find a price after discount", "prerequisites": []}},
                  "misconceptions": {"OFF": entry("belief"), "ADD": entry("belief"), "SLIP": entry("slip")}, "teaching_order": ["OFF", "ADD"],
                  "interventions": {"I": intervention}, "intervention_map": {"OFF": ["I"], "ADD": ["I"], "SLIP": ["I"]},
                  "items": [NUMERIC, {**NUMERIC, "id": "N2"}]})


@pytest.mark.parametrize("raw, result, beliefs, steps", [
    ("discount = 400 x 25/100 = 100, price = 400 - 100 = 300", "correct", [], {"Discount": "ok", "Price": "ok"}),
    ("300", "correct", [], {"Discount": "not shown", "Price": "ok"}),
    ("25% of 400 is 100", "wrong", ["OFF"], {"Discount": "ok", "Price": "not shown"}),
    ("400 + 100 = 500", "wrong", ["ADD"], {"Discount": "ok", "Price": "not shown"}),
    ("300 = 310", "wrong", ["SLIP"], {"Discount": "not shown", "Price": "ok"}),
    ("250", "wrong", ["UNMAPPED"], {"Discount": "not shown", "Price": "not shown"}),
    ("", "blank", [], {}),
    ("no idea", "unreadable", [], {}),
])
def test_numeric_reading(raw, result, beliefs, steps):
    trace = numeric_pack().read(NUMERIC, raw)
    assert (trace["result"], [f["belief"] for f in trace["findings"]], trace["steps"]) == (result, beliefs, steps)


def test_a_data_only_subject_runs_through_the_modules():
    pack = numeric_pack()
    cycle = ClassCycle(pack, "c")
    cycle.run_diagnostic([{"id": "A", "answers": {"N1": "25% of 400 is 100", "N2": "the discount is 100"}}, {"id": "B", "answers": {"N1": "300", "N2": "300"}}])
    assert cycle.diagnoses["A"]["next"] == {"action": "group", "target": "OFF", "held_for_later": [], "evidence": "confirmed"}
    assert cycle.groups[0]["student_ids"] == ["A"] and cycle.cohorts[0]["student_ids"] == ["B"]
