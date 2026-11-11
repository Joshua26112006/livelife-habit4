"""Class rules as settings: when students are clubbed by thinking error, who fixes each error, and changing them on a class.
Run from services/demo-livelife:  python -m pytest test_cases"""
import copy
import json
import sys
from fractions import Fraction as F
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server  # noqa: E402
from adaptive_engine import policy  # noqa: E402
from adaptive_engine.clustering import owners_for  # noqa: E402
from adaptive_engine.loader import PackError, build  # noqa: E402
from adaptive_engine.packs.probability import PACK  # noqa: E402

API = "/demo-livelife/adaptive-engine/api"
client = TestClient(server.create_app())
HABIT4 = json.loads((ROOT / "adaptive_engine/packs/habit4/pack.json").read_text())


@pytest.fixture(autouse=True)
def database(tmp_path, monkeypatch):
    monkeypatch.setenv("ADAPTIVE_DB", str(tmp_path / "test.sqlite3"))


def analysed_class(pack="probability", rules=None):
    cid = client.post(f"{API}/classes", json={"pack": pack, "name": "10A", "policy": rules or {}}).json()["class_id"]
    sample = client.get(f"{API}/files/{pack}/v1", params={"sample": True}).content
    client.post(f"{API}/classes/{cid}/upload/v1", params={"filename": "a.csv"}, content=sample)
    client.post(f"{API}/classes/{cid}/m3/run", json={})
    return cid


def state(cid):
    return client.get(f"{API}/classes/{cid}").json()


def settings(cid, rules):
    return client.post(f"{API}/classes/{cid}/settings", json={"policy": rules})


# The rules themselves
def test_defaults_group_at_once_and_keep_the_documented_thresholds():
    assert PACK.settings() == {"group_from": "candidate", "content_share": 25, "teacher_share": 10, "max_group_size": 12, "owners": {}}
    assert policy.groupable(PACK.settings()) == ("confirmed", "likely", "candidate")
    assert policy.groupable(PACK.settings({"group_from": "confirmed"})) == ("confirmed",)


def test_class_overrides_pack_and_owners_merge_code_by_code():
    rules = policy.resolve({"content_share": 30, "owners": {"A": ["teacher"], "B": ["student"]}},
                           {"content_share": 40, "owners": {"B": "auto", "C": ["student", "content"]}})
    assert rules["content_share"] == 40
    assert rules["owners"] == {"A": ["teacher"], "C": ["content", "student"]}  # "auto" drops B; owners kept in a fixed order


@pytest.mark.parametrize("rules", [
    {"group_from": "maybe"}, {"content_share": 120}, {"teacher_share": -1}, {"max_group_size": 0}, {"max_group_size": 2.5},
    {"owners": {"MC-L": ["principal"]}}, {"owners": {"MC-L": []}}, {"owners": {"NOPE": ["teacher"]}}, {"colour": "red"},
])
def test_bad_rules_are_named(rules):
    assert policy.problems(rules, set(PACK.misconceptions))


def test_teacher_share_above_content_share_is_refused():
    with pytest.raises(ValueError):
        PACK.settings({"teacher_share": 30, "content_share": 20})


# Who fixes it
def test_thresholds_move_with_the_rules():
    rules = PACK.settings({"content_share": 50, "teacher_share": 5})
    assert owners_for(PACK, "MC-L", F(30, 100), rules) == ["teacher", "student"]
    assert owners_for(PACK, "MC-L", F(6, 100), rules) == ["teacher", "student"]
    assert owners_for(PACK, "MC-L", F(50, 100), rules) == ["content", "teacher", "student"]


def test_named_owners_win_over_the_share_even_for_a_slip():
    rules = PACK.settings({"owners": {"MC-L": ["teacher"], "SLIP-F": ["teacher", "student"]}})
    assert owners_for(PACK, "MC-L", F(90, 100), rules) == ["teacher"]
    assert owners_for(PACK, "SLIP-F", F(1, 100), rules) == ["teacher", "student"]


def test_a_pack_can_name_owners_in_pack_json():
    data = copy.deepcopy(HABIT4)
    data["policy"] = {"group_from": "likely", "owners": {"WW-LOOSE-PROMISE": ["content", "student"]}}
    pack = build(data)
    assert pack.settings()["group_from"] == "likely" and owners_for(pack, "WW-LOOSE-PROMISE", F(1, 100)) == ["content", "student"]


def test_a_pack_with_bad_rules_does_not_load():
    data = copy.deepcopy(HABIT4)
    data["policy"] = {"owners": {"WW-TYPO": ["teacher"]}}
    with pytest.raises(PackError, match="WW-TYPO"):
        build(data)


# Trying rules on a class
def test_class_can_start_with_its_own_rules():
    cid = analysed_class(rules={"group_from": "confirmed"})
    body = state(cid)
    assert body["policy"]["group_from"] == "confirmed" and body["policy_overrides"] == {"group_from": "confirmed"}
    assert any(s["next"]["action"] == "probe" for s in body["feeds"]["m3"]["students"])


def test_bad_rules_on_a_new_class_are_refused():
    res = client.post(f"{API}/classes", json={"pack": "probability", "name": "10A", "policy": {"group_from": "maybe"}})
    assert res.status_code == 400 and "group_from" in res.json()["error"]


def test_changing_rules_reroutes_students_and_the_change_is_saved():
    cid = analysed_class()
    p06 = lambda: next(s for s in state(cid)["feeds"]["m3"]["students"] if s["student"] == "P06")
    assert p06()["next"]["action"] == "group"
    assert settings(cid, {"group_from": "confirmed"}).status_code == 200
    assert p06()["next"]["action"] == "probe"  # state() reloads the class from its saved events
    assert settings(cid, {}).status_code == 200
    assert p06()["next"]["action"] == "group"


def test_naming_an_owner_shows_in_who_fixes_it():
    cid = analysed_class()
    settings(cid, {"owners": {"MC-L": ["student"]}})
    row = next(r for r in state(cid)["feeds"]["m3"]["class"]["misconceptions"] if r["code"] == "MC-L")
    assert (row["owners"], row["owner_source"], list(row["remedies"])) == (["student"], "set", ["student"])


def test_changing_rules_after_grouping_sends_the_class_back_to_regroup():
    cid = analysed_class()
    for module in ("m4", "m5"):
        client.post(f"{API}/classes/{cid}/{module}/run", json={})
    assert state(cid)["stage"] == "grouped"
    settings(cid, {"owners": {"MC-L": ["student"]}})
    body = state(cid)
    assert body["stage"] == "identified" and "m5" not in body["feeds"]
    for module in ("m4", "m5"):
        assert client.post(f"{API}/classes/{cid}/{module}/run", json={}).status_code == 200
    group = next(g for g in state(cid)["feeds"]["m5"]["groups"] if g["misconception_id"] == "MC-L")
    assert group["owners"] == ["student"] and group["delivery"] == "practice_card"


def test_smaller_groups_split_the_class():
    cid = analysed_class()
    for module in ("m4", "m5"):
        client.post(f"{API}/classes/{cid}/{module}/run", json={})
    settings(cid, {"max_group_size": 1})
    for module in ("m4", "m5"):
        client.post(f"{API}/classes/{cid}/{module}/run", json={})
    assert all(len(g["student_ids"]) == 1 for g in state(cid)["feeds"]["m5"]["groups"])


def test_rules_are_locked_once_the_plan_is_built():
    cid = analysed_class()
    for module in ("m4", "m5", "m6"):
        client.post(f"{API}/classes/{cid}/{module}/run", json={})
    res = settings(cid, {"group_from": "confirmed"})
    assert res.status_code == 409 and not state(cid)["settings_open"]


def test_bad_rules_on_a_class_are_refused_and_not_saved():
    cid = analysed_class()
    assert settings(cid, {"teacher_share": 40, "content_share": 20}).status_code == 409
    assert settings(cid, {"owners": {"MC-L": ["principal"]}}).status_code == 409
    assert state(cid)["policy_overrides"] == {}
