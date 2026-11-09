"""Adaptive Teaching Engine Modules 4 to 8 and the class cycle, against the concept document's acceptance criteria.
Module 3 is covered in test_probability_engine.py.  Run from services/demo-livelife:  python -m pytest test_cases"""
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server  # noqa: E402
from adaptive_engine import ClassCycle  # noqa: E402
from adaptive_engine.identification import apply_probe, diagnose_student  # noqa: E402
from adaptive_engine.interventions import map_student, teaching_card  # noqa: E402
from adaptive_engine.orchestration import plan_sessions  # noqa: E402
from adaptive_engine.packs.probability import PACK  # noqa: E402
from adaptive_engine.packs.probability.knowledge_base import INTERVENTIONS  # noqa: E402
from adaptive_engine.profile import LearnerProfile  # noqa: E402

SHEETS = json.loads((ROOT / "demos/adaptive-engine/sample_sheets.json").read_text())["students"]
SHEET = {s["id"]: s for s in SHEETS}
API = "/demo-livelife/adaptive-engine/api"
client = TestClient(server.create_app())


def cycle(allow_draft=True, **kwargs):
    c = ClassCycle(PACK, "c1", allow_draft=allow_draft, **kwargs)
    c.run_diagnostic(SHEETS)
    return c


def approved_cycle():
    c = cycle()
    c.build_plan()
    c.approve_plan("t1")
    return c


# Module 3 additions
def test_uncertain_hypothesis_triggers_a_probe_not_a_label():
    p06 = diagnose_student(PACK, SHEET["P06"])
    record = next(h for h in p06["hypotheses"] if h["misconception_id"] == "MC-L")
    assert (record["status"], record["follow_up_action"], record["confidence"]) == ("likely", "probe", "medium")
    assert record["competency_ids"] == ["PROB-02"] and record["evidence"]


@pytest.mark.parametrize("outcome, action", [("supports", "group"), ("rules_out", "teacher_review")])
def test_probe_result_updates_the_route(outcome, action):
    diagnosis = apply_probe(PACK, diagnose_student(PACK, SHEET["P06"]), "MC-L", outcome)
    assert diagnosis["next"]["action"] == action


def test_probe_rejects_unknown_input():
    diagnosis = diagnose_student(PACK, SHEET["P06"])
    with pytest.raises(ValueError):
        apply_probe(PACK, diagnosis, "MC-L", "maybe")
    with pytest.raises(ValueError):
        apply_probe(PACK, diagnosis, "MC-U", "supports")


# Module 4
def test_unapproved_interventions_are_never_recommended_by_default():
    mapping = map_student(PACK, diagnose_student(PACK, SHEET["P02"]))
    assert mapping["primary"]["recommended"] is None and mapping["primary"]["candidates"]


def test_draft_preview_ranks_by_matching_evidence_and_stays_labelled():
    p03 = map_student(PACK, diagnose_student(PACK, SHEET["P03"]), allow_draft=True)["primary"]
    assert p03["recommended"] == "INT-PROB-04"  # two dice questions outweigh one coin question
    assert p03["review_status"] == "draft"


def test_student_with_two_needs_keeps_the_second_for_later():
    p04 = map_student(PACK, diagnose_student(PACK, SHEET["P04"]), allow_draft=True)
    assert p04["primary"]["misconception_id"] == "MC-N"
    assert [s["misconception_id"] for s in p04["secondary"]] == ["MC-A"]


def test_card_lists_what_experts_have_not_written():
    card = teaching_card(PACK, "INT-PROB-01")
    assert card["steps"] and card["exit_check"] and card["teacher_guidance"] and card["student_task"]
    assert card["awaiting_expert_draft"] == ["objective"]


def test_every_mapped_intervention_exists_and_durations_are_ordered():
    assert all(i in INTERVENTIONS for ids in PACK.intervention_map.values() for i in ids)
    assert all(e["duration_minutes"][0] <= e["duration_minutes"][1] for e in INTERVENTIONS.values())


# Module 5
def test_groups_are_by_need_in_teaching_order_and_only_proposed():
    groups = cycle().groups
    assert [g["misconception_id"] for g in groups] == ["MC-L", "MC-O", "MC-N", "MC-U"]
    assert all(g["status"] == "proposed" for g in groups)


def test_group_labels_describe_need_not_ability():
    banned = ("weak", "low", "slow", "ability", "remedial")
    assert not any(word in g["need"].lower() for g in cycle().groups for word in banned)


def test_large_group_splits_to_the_cap():
    sheets = [{"id": f"S{i}", "answers": SHEET["P02"]["answers"]} for i in range(5)]
    c = ClassCycle(PACK, "c", allow_draft=True, max_group_size=2)
    c.run_diagnostic(sheets)
    assert [len(g["student_ids"]) for g in c.groups] == [2, 2, 1]


def test_teacher_can_move_a_student_and_reprioritise_and_it_is_audited():
    c = cycle()
    ids = [g["group_id"] for g in c.groups]
    c.move_student("P03", ids[1], ids[0], "t1", "seen in class")
    assert "P03" in c.groups[0]["student_ids"]
    assert ids[1] not in [g["group_id"] for g in c.groups]  # emptied groups go
    remaining = [g["group_id"] for g in c.groups][::-1]
    c.set_priority(remaining, "t1")
    assert [g["group_id"] for g in c.groups] == remaining
    assert {"student_moved", "priority_set"} <= {e["event"] for e in c.audit if e["actor"] == "t1"}


def test_priority_list_must_be_complete():
    with pytest.raises(ValueError):
        cycle().set_priority(["nope"], "t1")


# Module 6
def test_one_group_at_a_time_and_overflow_moves_to_a_later_period():
    groups = [{"group_id": f"G{i}", "intervention_id": "INT-PROB-04"} for i in range(3)]
    plan = plan_sessions(PACK, groups, {g["group_id"]: "T4" for g in groups}, period_minutes=45)
    assert [[s["teacher_with"] for s in p["direct_teaching"]] for p in plan["periods"]] == [["G0"], ["G1"], ["G2"]]
    first = plan["periods"][0]
    assert first["deferred_to_later_period"]
    slots = first["direct_teaching"]
    assert all(a["end"] <= b["start"] for a, b in zip(slots, slots[1:]))
    assert slots[-1]["end"] <= first["exit_ticket"][0]


def test_plan_gives_each_group_practice_with_an_answer_key():
    plan = cycle().build_plan()
    assert plan["status"] == "recommended"
    for card in plan["cards"].values():
        assert len(card["practice"]) == 2 and set(card["answer_key"]) == {p["id"] for p in card["practice"]}


def test_edit_after_planning_clears_the_plan():
    c = cycle()
    c.build_plan()
    c.set_priority([g["group_id"] for g in c.groups][::-1], "t1")
    assert c.plan is None


def test_period_too_short_is_rejected():
    with pytest.raises(ValueError):
        plan_sessions(PACK, [{"group_id": "G", "intervention_id": "INT-PROB-04"}], {"G": "T4"}, period_minutes=10)


# Module 7
@pytest.mark.parametrize("item", PACK.items, ids=lambda i: i["id"])
@pytest.mark.parametrize("attempt", [1, 2, 3])
def test_parallel_items_are_new_and_keep_the_competency(item, attempt):
    new = PACK.parallel_item(item, attempt)
    assert new["text"] != item["text"] and new["competency_ids"] == item["competency_ids"]
    assert new == PACK.parallel_item(item, attempt)  # regenerable
    if item["type"] != "argue":
        assert 0 < new["correct"] < 1 and new["correct"] not in [s["value"] for s in new["signatures"] if "value" in s]


def test_reassessment_targets_the_competency_of_the_need():
    items = approved_cycle().create_reassessment()
    assert "PROB-02" in items["P02"]["competency_ids"]  # MC-L first showed on T1, which does not sample PROB-02
    assert "PROB-07" in items["P04"]["competency_ids"]


def test_reassessment_needs_an_approved_plan():
    with pytest.raises(ValueError):
        cycle().create_reassessment()


@pytest.mark.parametrize("answer, outcome, step", [
    ("favourable over total = {c}", "demonstrated", "leave_group"),
    ("{c}", "insufficient", "reasoning_probe"),
    ("", "needs_review", "teacher_review"),
])
def test_reassessment_outcomes(answer, outcome, step):
    c = approved_cycle()
    item = c.create_reassessment()["P02"]
    result = c.submit_reassessment({"P02": answer.format(c=item["correct"])})[0]
    assert (result["outcome"], result["next_step"]) == (outcome, step)


# Module 8
def test_profile_adds_evidence_and_never_overwrites():
    c = approved_cycle()
    before = len(c.profiles["P02"].evidence)
    item = c.create_reassessment()["P02"]
    c.submit_reassessment({"P02": f"favourable over total = {item['correct']}"})
    profile = c.profiles["P02"]
    assert len(profile.evidence) == before + len(item["competency_ids"])
    assert {"diagnostic", "reassessment-1"} == {e["session"] for e in profile.evidence}


def test_status_moves_from_not_yet_to_demonstrated_and_is_on_the_timeline():
    c = approved_cycle()
    item = c.create_reassessment()["P02"]
    competency = item["competency_ids"][0]
    assert c.profiles["P02"].view()["competencies"][competency]["status"] != "demonstrated"
    c.submit_reassessment({"P02": f"favourable over total = {item['correct']}"})
    view = c.profiles["P02"].view()
    assert view["competencies"][competency]["status"] == "demonstrated"
    assert view["competencies"][competency]["next_action"] == "spaced_review"
    assert any(t["competency_id"] == competency and t["to"] == "demonstrated" for t in view["timeline"])


def _trace(result, working=True, belief=None):
    findings = [{"belief": belief, "confidence": "high"}] if belief else []
    return {"q": "T", "working": "w", "result": result, "shows_working": working, "findings": findings}


ITEM = {"competency_ids": ["PROB-07"]}


@pytest.mark.parametrize("traces, status, next_action", [
    ([], "not_assessed", "assess"),
    ([_trace("blank")], "not_assessed", "assess"),
    ([_trace("correct")], "demonstrated", "advance"),
    ([_trace("correct", working=False)], "developing", "probe_further"),
    ([_trace("wrong", belief="SLIP-F")], "developing", "practice"),
    ([_trace("wrong", belief="MC-N")], "not_yet_demonstrated", "reteach"),
    ([_trace("wrong", belief="UNMAPPED")], "needs_review", "review_with_teacher"),
    ([_trace("correct"), _trace("wrong", belief="MC-N")], "needs_review", "review_with_teacher"),
])
def test_status_rules(traces, status, next_action):
    profile = LearnerProfile(PACK, "S")
    for n, trace in enumerate(traces):
        profile.add_traces(f"s{n}", [trace], [ITEM])
    state = profile.view()["competencies"]["PROB-07"]
    assert (state["status"], state["next_action"]) == (status, next_action)


def test_mastery_on_one_point_is_not_high_confidence():
    profile = LearnerProfile(PACK, "S")
    profile.add_traces("s0", [_trace("correct")], [ITEM])
    assert profile.view()["competencies"]["PROB-07"]["confidence"] == "medium"
    profile.add_traces("s1", [_trace("correct")], [ITEM])
    assert profile.view()["competencies"]["PROB-07"]["confidence"] == "high"


# The loop, and governance
def test_every_stage_and_teacher_decision_is_audited_with_a_version():
    c = approved_cycle()
    c.teacher_feedback("INT-PROB-01", "override", "t1", "class already covered this")
    events = [e["event"] for e in c.audit]
    assert {"diagnostic_analysed", "groups_proposed", "plan_recommended", "plan_approved", "teacher_feedback"} <= set(events)
    assert all(e["pack_version"] == PACK.version for e in c.audit)
    with pytest.raises(ValueError):
        c.teacher_feedback("x", "shrug", "t1")


def test_demo_loop_runs_modules_three_to_eight():
    res = client.get(f"{API}/demo-loop")
    assert res.status_code == 200 and res.headers["cache-control"] == "no-store"
    body = res.json()
    assert {o["student"]: o["outcome"] for o in body["outcomes"]} == {
        "P02": "demonstrated", "P03": "partial", "P04": "persistent", "P05": "insufficient", "P06": "demonstrated"}
    assert body["plan"]["status"] == "approved"
    assert body["next_cycle"]["leave_group"] == ["P02", "P06"]
