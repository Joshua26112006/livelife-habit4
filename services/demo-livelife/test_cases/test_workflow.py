"""The class workflow through its API: bulk upload, one feed per module, teacher decisions, V2 and comparison, and saved state.
Run from services/demo-livelife:  python -m pytest test_cases"""
import io
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server  # noqa: E402
from adaptive_engine import ai_tasks, bulk, samples  # noqa: E402
from adaptive_engine.pack import ChapterPack  # noqa: E402
from adaptive_engine.packs import all_packs  # noqa: E402
from adaptive_engine.packs.probability import PACK as PROBABILITY  # noqa: E402

API = "/demo-livelife/adaptive-engine/api"
client = TestClient(server.create_app())
MODULE_ORDER = ["m3", "m4", "m5", "m6"]


@pytest.fixture(autouse=True)
def database(tmp_path, monkeypatch):
    monkeypatch.setenv("ADAPTIVE_DB", str(tmp_path / "test.sqlite3"))


def new_class(pack="probability"):
    return client.post(f"{API}/classes", json={"pack": pack, "name": "10A"}).json()["class_id"]


def sample_bytes(pack, round_name):
    return client.get(f"{API}/files/{pack}/{round_name}", params={"sample": True}).content


def upload(cid, round_name, data, filename="a.csv"):
    return client.post(f"{API}/classes/{cid}/upload/{round_name}", params={"filename": filename}, content=data)


def run(cid, module, results=None, status="off"):
    return client.post(f"{API}/classes/{cid}/{module}/run", json={"results": results or {}, "status": status})


def status(cid):
    return client.get(f"{API}/classes/{cid}").json()


def through_plan(pack="probability", marks=None):
    cid = new_class(pack)
    assert upload(cid, "v1", sample_bytes(pack, "v1")).status_code == 200
    assert run(cid, "m3", marks).status_code == 200
    for module in MODULE_ORDER[1:]:
        assert run(cid, module).status_code == 200
    return cid


def through_v2(pack="probability", marks=None, v2_marks=None):
    cid = through_plan(pack, marks)
    assert client.post(f"{API}/classes/{cid}/plan/approve", json={}).status_code == 200
    assert run(cid, "m7-paper").status_code == 200
    assert upload(cid, "v2", sample_bytes(pack, "v2")).status_code == 200
    assert run(cid, "m7-score", v2_marks).status_code == 200
    return cid


def habit4_marks(cid, module="m3", score=4):
    tasks = client.get(f"{API}/classes/{cid}/{module}/tasks").json()["tasks"]
    return {t["id"]: {q: {"score": score, "evidence": "seen", "flag": False} for q in t["answers"]} for t in tasks if t["kind"] == "rubric"}


# Upload
def test_upload_reports_students_and_moves_on():
    cid = new_class()
    report = upload(cid, "v1", sample_bytes("probability", "v1")).json()
    assert report["students"] == 6 and report["blank_answers"] == 1
    assert status(cid)["stage"] == "uploaded"


def csv_with(rows, questions=("T1", "T2")):
    return "\n".join([",".join(("student_id", *questions)), *rows]).encode()


def test_bad_rows_are_reported_not_dropped():
    parsed = bulk.parse_upload(csv_with(["s1,1/2,1/3", "bad id,1/2,1/3", "s1,1/2,1/3", ",1/2,1/3"]), "a.csv", ["T1", "T2"])
    assert [s["id"] for s in parsed["sheets"]] == ["s1"]
    assert [r["row"] for r in parsed["rejected"]] == [3, 4, 5]


def test_spreadsheet_dates_are_caught():
    parsed = bulk.parse_upload(csv_with(["s1,10-Apr,1/3"]), "a.csv", ["T1", "T2"])
    assert parsed["sheets"][0]["answers"]["T1"] == "" and "date" in parsed["warnings"][0]["message"]


@pytest.mark.parametrize("data, message", [
    (b"", "empty"),
    (b"name,T1,T2\na,1,2", "student_id"),
    (b"student_id,T1\na,1", "Missing: T2"),
    (b"student_id,T1,T2,T3\na,1,2,3", "Unexpected: T3"),
])
def test_unusable_files_say_why(data, message):
    with pytest.raises(bulk.UploadError, match=message):
        bulk.parse_upload(data, "a.csv", ["T1", "T2"])


def test_excel_upload_including_a_fraction_turned_into_a_date():
    import datetime

    from openpyxl import Workbook
    book = Workbook()
    book.active.append(["student_id", "T1", "T2"])
    book.active.append(["s1", datetime.date(2026, 4, 10), "1/3"])
    out = io.BytesIO()
    book.save(out)
    parsed = bulk.parse_upload(out.getvalue(), "a.xlsx", ["T1", "T2"])
    assert parsed["sheets"][0]["answers"] == {"T1": "", "T2": "1/3"} and parsed["warnings"]


def test_one_workbook_can_hold_both_papers():
    from openpyxl import Workbook
    book = Workbook()
    book.active.append(["notes"])
    book.create_sheet().append(["student_id", "T1"])
    book.worksheets[1].append(["s1", "1/2"])
    book.create_sheet().append(["student_id", "T1-P1"])
    book.worksheets[2].append(["s1", "3/4"])
    out = io.BytesIO()
    book.save(out)
    assert bulk.parse_upload(out.getvalue(), "a.xlsx", ["T1"])["sheets"][0]["answers"] == {"T1": "1/2"}
    assert bulk.parse_upload(out.getvalue(), "a.xlsx", ["T1-P1"])["sheets"][0]["answers"] == {"T1-P1": "3/4"}


def test_second_v1_upload_is_refused():
    cid = new_class()
    upload(cid, "v1", sample_bytes("probability", "v1"))
    assert upload(cid, "v1", sample_bytes("probability", "v1")).status_code == 409


# Stage order
def test_modules_run_only_in_order():
    cid = new_class()
    upload(cid, "v1", sample_bytes("probability", "v1"))
    assert run(cid, "m5").status_code == 409
    assert client.get(f"{API}/classes/{cid}/m4/tasks").status_code == 409


def test_unknown_module_and_class():
    cid = new_class()
    assert client.get(f"{API}/classes/{cid}/m99/tasks").status_code == 404
    assert client.get(f"{API}/classes/{'z' * 20}").status_code == 404


# Saved state
def test_class_survives_being_reloaded_at_every_stage():
    cid = through_plan()
    first = status(cid)
    assert first["stage"] == "planned" and status(cid) == first


# Module 3 and its AI
def test_habit4_needs_ai_or_goes_to_the_teacher():
    cid = new_class("habit4")
    upload(cid, "v1", sample_bytes("habit4", "v1"))
    feed = run(cid, "m3", status="off").json()
    assert all(len(s["teacher"]) >= 8 for s in feed["students"])


def test_habit4_marks_drive_the_diagnosis():
    cid = new_class("habit4")
    upload(cid, "v1", sample_bytes("habit4", "v1"))
    marks = habit4_marks(cid)
    marks["H03"]["S5"]["score"] = 1
    feed = run(cid, "m3", marks, "ok").json()
    h03 = next(s for s in feed["students"] if s["student"] == "H03")
    assert h03["next"]["target"] == "WW-DISMISS"


@pytest.mark.parametrize("bad", ["4", 7, -1, True, None])
def test_invalid_marks_are_ignored(bad):
    sheets = [{"id": "s", "answers": {"S1": "text"}}]
    item = [{"id": "S1", "type": "scenario"}]
    merged, _ = ai_tasks.apply_marking(all_packs()["habit4"], sheets, item, {"s": {"S1": {"score": bad, "evidence": "x"}}})
    assert merged[0]["answers"]["S1"]["score"] is None


def test_ai_may_only_choose_from_the_catalogue():
    cid = new_class()
    upload(cid, "v1", csv_rows_with_unknown_answer())
    invented = {"read:X": {"answers": {"T1": {"code": "MADE-UP", "why": "x"}}}}
    feed = run(cid, "m3", invented, "ok").json()
    assert "UNMAPPED" in feed["students"][0]["summary"]


def test_valid_ai_reading_is_medium_and_only_prompts_a_probe():
    cid = new_class()
    upload(cid, "v1", csv_rows_with_unknown_answer())
    tasks = client.get(f"{API}/classes/{cid}/m3/tasks").json()["tasks"]
    assert [t["id"] for t in tasks] == ["read:X"] and "Catalogue" in tasks[0]["user"]
    feed = run(cid, "m3", {"read:X": {"answers": {"T1": {"code": "MC-L", "why": "counts colours"}}}}, "ok").json()
    student = feed["students"][0]
    assert student["summary"]["MC-L"]["highs"] == 0 and student["next"]["action"] == "probe"


def csv_rows_with_unknown_answer():
    columns = ["student_id"] + [q["id"] for q in PROBABILITY.items]
    row = ["X", "7/9"] + [""] * (len(columns) - 2)
    return bulk.to_csv(columns, [row]).encode()


def test_probe_result_is_saved():
    cid = new_class()
    upload(cid, "v1", sample_bytes("probability", "v1"))
    run(cid, "m3")
    assert client.post(f"{API}/classes/{cid}/probes", json={"student": "P06", "code": "MC-L", "outcome": "supports"}).status_code == 200
    p06 = next(s for s in status(cid)["feeds"]["m3"]["students"] if s["student"] == "P06")
    assert p06["next"]["action"] == "group"


# Modules 4 to 6
def test_ai_choice_outside_the_list_is_ignored():
    cid = new_class()
    upload(cid, "v1", sample_bytes("probability", "v1"))
    run(cid, "m3")
    feed = run(cid, "m4", {"MC-O": {"choice": "INT-INVENTED", "why": "x"}}, "ok").json()
    assert next(m for m in feed["mappings"] if m["student"] == "P03")["primary"]["recommended"] == "INT-PROB-04"


def test_ai_choice_within_the_list_is_used_with_its_reason():
    cid = new_class()
    upload(cid, "v1", sample_bytes("probability", "v1"))
    run(cid, "m3")
    feed = run(cid, "m4", {"MC-O": {"choice": "INT-PROB-03", "why": "Coins came first."}}, "ok").json()
    assert next(m for m in feed["mappings"] if m["student"] == "P03")["primary"]["recommended"] == "INT-PROB-03"
    assert feed["why"]["MC-O"] == "Coins came first."


def test_labelling_language_from_ai_is_dropped():
    assert ai_tasks.safe_text("This group of weak students") == ""
    assert ai_tasks.safe_text("Needs practice listing outcomes") == "Needs practice listing outcomes"


def test_every_student_is_in_a_group_or_cohort():
    cid = through_plan()
    feed = status(cid)["feeds"]["m5"]
    placed = {s for g in feed["groups"] for s in g["student_ids"]} | {s for c in feed["cohorts"] for s in c["student_ids"]}
    assert placed == {f"P0{i}" for i in range(1, 7)}
    assert {c["cohort_id"] for c in feed["cohorts"]} == {"extension", "probe"}


def test_teacher_edits_only_before_planning():
    cid = new_class()
    upload(cid, "v1", sample_bytes("probability", "v1"))
    for module in ("m3", "m4", "m5"):
        run(cid, module)
    ids = [g["group_id"] for g in status(cid)["feeds"]["m5"]["groups"]]
    assert client.post(f"{API}/classes/{cid}/groups/priority", json={"group_ids": ids[::-1]}).status_code == 200
    assert [g["group_id"] for g in status(cid)["feeds"]["m5"]["groups"]] == ids[::-1]
    run(cid, "m6")
    assert client.post(f"{API}/classes/{cid}/groups/priority", json={"group_ids": ids}).status_code == 409


def test_plan_includes_students_without_a_group():
    assert through_plan() and status(through_plan())["feeds"]["m6"]["plan"]["independent_cohorts"]


def test_ai_material_is_labelled_a_draft():
    cid = new_class()
    upload(cid, "v1", sample_bytes("probability", "v1"))
    for module in ("m3", "m4", "m5"):
        run(cid, module)
    groups = list(status(cid)["feeds"]["m5"]["groups"])
    reply = {groups[0]["group_id"]: {"teacher_script": ["Say this."], "worksheet": ["Do this."], "exit_ticket": "One question."}}
    feed = run(cid, "m6", reply, "ok").json()
    assert feed["materials"][groups[0]["group_id"]]["label"].startswith("AI draft")


# Modules 7 and 8
def test_paper_needs_an_approved_plan():
    assert run(through_plan(), "m7-paper").status_code == 409


def test_v2_paper_is_one_paper_for_the_class_with_new_questions():
    cid = through_plan()
    client.post(f"{API}/classes/{cid}/plan/approve", json={})
    feed = run(cid, "m7-paper").json()
    v1_text = {q["text"] for q in PROBABILITY.items}
    assert len(feed["paper"]) == 10 and not v1_text & {i["text"] for i in feed["paper"]}


def test_v2_compares_with_v1():
    cid = through_v2()
    comparison = status(cid)["feeds"]["m7-score"]["comparison"]
    rows = {s["student"]: s for s in comparison["students"]}
    assert rows["P02"]["no_longer_seen"] == ["MC-L"] and rows["P02"]["still_seen"] == []
    assert rows["P04"]["still_seen"] == ["MC-N"]
    assert rows["P02"]["v2_percent"] > rows["P02"]["v1_percent"]


def test_v2_adds_evidence_and_keeps_v1():
    cid = through_v2()
    feed = run(cid, "m8").json()
    timeline = feed["profiles"]["P02"]["timeline"]
    assert {t["session"] for t in timeline} == {"diagnostic", "v2"}
    assert any(t["to"] == "demonstrated" and t["session"] == "v2" for t in timeline)
    assert feed["audit"] and status(cid)["stage"] == "profiled"


def test_habit4_runs_end_to_end():
    cid = new_class("habit4")
    upload(cid, "v1", sample_bytes("habit4", "v1"))
    marks = habit4_marks(cid)
    marks["H03"]["S5"]["score"] = 1
    run(cid, "m3", marks, "ok")
    for module in ("m4", "m5", "m6"):
        assert run(cid, module).status_code == 200
    client.post(f"{API}/classes/{cid}/plan/approve", json={})
    run(cid, "m7-paper")
    upload(cid, "v2", sample_bytes("habit4", "v2"))
    v2 = habit4_marks(cid, "m7-score")
    run(cid, "m7-score", v2, "ok")
    assert run(cid, "m8").status_code == 200
    rows = {s["student"]: s for s in status(cid)["feeds"]["m8"]["comparison"]["students"]}
    assert rows["H03"]["no_longer_seen"] == ["WW-DISMISS"]


def test_invalid_ai_summary_keys_are_ignored():
    comparison = {"students": [{"student": "A"}]}
    out = ai_tasks.apply_profile(comparison, {"summary": {"class_summary": "Fine.", "students": {"A": "Practise listing.", "Z": "Not in class."}}})
    assert out == {"class_summary": "Fine.", "students": {"A": "Practise listing."}}


def test_templates_match_their_papers():
    packs = all_packs()
    assert samples.template(packs["habit4"], "v1").startswith("student_id,K1")
    assert samples.template(packs["probability"], "v2").startswith("student_id,T1-P1")


def test_engine_source_is_not_served():
    assert client.get("/demo-livelife/adaptive-engine/backend.py").status_code == 404


# Generic engine, strong subject layer
ENGINE_FILES = [f for f in (ROOT / "adaptive_engine").glob("*.py")]


@pytest.mark.parametrize("path", ENGINE_FILES, ids=lambda p: p.name)
def test_engine_holds_no_subject_knowledge(path):
    text = path.read_text().lower()
    for word in ("habit", "probab", "win-win", "ncert", "mc-", "ww-", "dice", "coins"):
        assert word not in text, f"{path.name} mentions {word}"


def test_every_pack_describes_its_subject():
    for pack in all_packs().values():
        subject = pack.describe()
        assert all(subject["subject"].get(k) for k in ("subject", "board", "grade", "chapter", "source"))
        assert pack.brief and pack.upload_hint and pack.sample
        assert all(set(m["competency_ids"]) <= set(pack.competencies) for m in subject["misconceptions"].values())
        assert all(set(q["competency_ids"]) <= set(pack.competencies) for q in subject["questions"])


def test_subjects_are_listed_for_the_screen():
    body = client.get(f"{API}/subjects").json()
    assert set(body) == {"habit4", "probability", "probability-short"} and body["probability"]["subject"]["board"] == "CBSE"
    assert body["habit4"]["interventions"]["approved"] == 0


def test_every_ai_call_carries_its_subject():
    cid = new_class()
    upload(cid, "v1", csv_rows_with_unknown_answer())
    task = client.get(f"{API}/classes/{cid}/m3/tasks").json()["tasks"][0]
    assert "NCERT Chapter 14" in task["system"]
    cid = through_plan()
    client.post(f"{API}/classes/{cid}/plan/approve", json={})
    assert "NCERT Chapter 14" in client.get(f"{API}/classes/{cid}/m7-paper/tasks").json()["tasks"][0]["system"]


def _tiny_pack():
    """A made-up subject, to show a new chapter needs no engine change."""
    def read(item, raw):
        trace = {"q": item["id"], "working": raw, "steps": {}, "findings": [], "shows_working": True}
        if not raw:
            trace["result"] = "blank"
        elif raw == item["key"]:
            trace["result"] = "correct"
        else:
            trace["result"] = "wrong"
            trace["findings"].append(dict(belief="GAP", step="Answer", confidence="high", evidence=raw))
        return trace

    def parallel(item, attempt):
        return {**item, "id": f'{item["id"]}-P{attempt}', "text": item["text"] + " (new)", "parallel_of": item["id"]}

    intervention = {"title": "Reteach", "objective": None, "steps": ["Show it."], "duration_minutes": (5, 10), "assets": [], "item_types": ["q"],
                    "exit_check": None, "review_status": "approved", "version": "1"}
    return ChapterPack("c", "1", {"C1": {"name": "Skill", "prerequisites": []}},
                       [{"id": f"Q{n}", "text": f"Q{n}", "type": "q", "template": "q", "competency_ids": ["C1"], "key": "a"} for n in (1, 2)],
                       {"GAP": {"name": "Gap", "belief": "b", "kind": "belief", "competency_ids": ["C1"], "student": "s", "teacher": "t", "content": "c", "exit_check": "e"}},
                       ("GAP",), {"GAP": "Probe?"}, {}, {"INT": intervention}, {"GAP": ["INT"]}, read, parallel)


def test_a_new_subject_runs_through_every_module_with_no_engine_change():
    from adaptive_engine import ClassCycle
    cycle = ClassCycle(_tiny_pack(), "c")
    cycle.run_diagnostic([{"id": "A", "answers": {"Q1": "x", "Q2": "x"}}, {"id": "B", "answers": {"Q1": "a", "Q2": "a"}}])
    assert cycle.groups[0]["student_ids"] == ["A"] and cycle.cohorts[0]["student_ids"] == ["B"]
    cycle.build_plan()
    cycle.approve_plan("t")
    paper = cycle.create_paper()
    result = cycle.score_paper([{"id": "A", "answers": {i["id"]: "a" for i in paper}}])
    assert result["students"][0]["no_longer_seen"] == ["GAP"]
    assert cycle.profiles["A"].view()["competencies"]["C1"]["status"] == "demonstrated"


# The class picture: the short check must reproduce the agreed sample analysis exactly
def short_feed():
    cid = new_class("probability-short")
    upload(cid, "v1", sample_bytes("probability-short", "v1"))
    return run(cid, "m3").json()


def ways(question):
    out = {}
    for way in question["ways"]:
        out[way["level"]] = out.get(way["level"], 0) + way["count"]
    return out


def test_sample_analysis_overview():
    assert short_feed()["overview"] == {"students": 30, "answers_read": 90, "thinking_errors": 3, "right_answer_wrong_reason": 3}


def test_sample_analysis_per_question():
    q1, q2, q3 = short_feed()["questions"]
    assert (q1["sound"], q2["sound"], q3["sound"]) == (18, 14, 9)
    assert ways(q1) == {"secure": 16, "shown": 2, "slip": 5, "wrong": 6, "blank": 1}
    assert ways(q2) == {"secure": 12, "shown": 2, "wrong": 15, "blank": 1}
    assert ways(q3) == {"secure": 9, "wrong": 17, "blank": 4}


def test_sample_analysis_who_fixes_it():
    rows = {r["code"]: r for r in short_feed()["class"]["misconceptions"]}
    assert {c: len(r["students"]) for c, r in rows.items()} == {"MC-L": 9, "MC-O": 7, "MC-A": 10, "DECK": 3, "SLIP-F": 2}
    assert rows["MC-A"]["owners"][0] == "content" and rows["MC-L"]["owners"][0] == "content"
    assert rows["MC-O"]["owners"][0] == "teacher" and rows["DECK"]["owners"][0] == "teacher"
    assert rows["SLIP-F"]["owners"] == ["student"]


def test_same_wrong_value_with_different_thinking_stays_apart():
    q2 = short_feed()["questions"][1]
    third = [w for w in q2["ways"] if w["level"] == "wrong" and w["sample"].endswith("1/3")]
    assert {w["error"] for w in third} == {"MC-O", "MC-L"}


def test_right_answer_wrong_reason_is_not_sound():
    feed = short_feed()
    rw = next(w for w in feed["questions"][1]["ways"] if w["sample"] == "head or tail\nso 1/2")
    assert rw["level"] == "wrong" and rw["count"] == 3 and rw["think"].startswith("Right answer, wrong reason")


def test_missing_fact_is_practice_not_a_probe():
    feed = short_feed()
    s27 = next(s for s in feed["students"] if s["student"] == "S27")
    assert s27["summary"]["DECK"]["status"] == "gap"


def test_student_owned_needs_get_a_card_not_teacher_time():
    cid = new_class("probability-short")
    upload(cid, "v1", sample_bytes("probability-short", "v1"))
    for module in ("m3", "m4", "m5", "m6"):
        assert run(cid, module).status_code == 200
    feed = status(cid)["feeds"]
    taught = {s["teacher_with"] for p in feed["m6"]["plan"]["periods"] for s in p["direct_teaching"]}
    for group in feed["m5"]["groups"]:
        assert (group["group_id"] in taught) == (group["delivery"] == "teacher")
    assert all(g["group_id"] in feed["m6"]["plan"]["cards"] for g in feed["m5"]["groups"])


def test_ai_insight_replaces_the_rule_wording_only_for_known_ways():
    cid = new_class("probability-short")
    upload(cid, "v1", sample_bytes("probability-short", "v1"))
    run(cid, "m3")
    tasks = client.get(f"{API}/classes/{cid}/m3-insight/tasks").json()["tasks"]
    assert [t["id"] for t in tasks] == ["Q1", "Q2", "Q3"] and "NCERT Chapter 14" in tasks[0]["system"]
    way = status(cid)["feeds"]["m3"]["questions"][0]["ways"][0]["id"]
    feed = run(cid, "m3-insight", {"Q1": {"ways": {way: "They counted the kings.", "made-up": "x"}, "callout": "Most got it."}}, "ok").json()
    q1 = feed["questions"][0]
    assert q1["callout"] == "Most got it." and q1["ways"][0]["think"] == "They counted the kings."
    assert status(cid)["stage"] == "identified"


def test_short_check_runs_end_to_end_and_compares():
    cid = through_v2("probability-short")
    assert run(cid, "m8").status_code == 200
    rows = {s["student"]: s for s in status(cid)["feeds"]["m8"]["comparison"]["students"]}
    assert rows["S08"]["no_longer_seen"] and rows["S08"]["v2_percent"] == 100
    assert "MC-A" in rows["S25"]["still_seen"]
    assert status(cid)["feeds"]["m7-score"]["answers"]["S08"][0]["level"] == "secure"

