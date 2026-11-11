"""Any uploaded paper: questions are the reference, expected answers what a sound answer reaches, students' working what is
analysed. Then the class and student records, in the local store and in Firestore (against a stand-in client).
Run from services/demo-livelife:  python -m pytest test_cases"""
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server  # noqa: E402
from adaptive_engine import generic, store  # noqa: E402
from adaptive_engine import workflow as wf  # noqa: E402

API = "/demo-livelife/adaptive-engine/api"
client = TestClient(server.create_app())
SAMPLE = ROOT / "adaptive_engine/sample_papers/probability-5q"
KEY = {"Q1": "3/8", "Q2i": "1/12", "Q2ii": "15/16", "Q3": "1/26", "Q4": "5/12", "Q5i": "9/10", "Q5ii": "1/10", "Q5iii": "1/5"}


@pytest.fixture(autouse=True)
def database(tmp_path, monkeypatch):
    monkeypatch.setenv("ADAPTIVE_DB", str(tmp_path / "test.sqlite3"))
    store.use(None)
    yield
    store.use(None)


def paper(questions=None):
    return generic.parse_paper(questions or json.loads((SAMPLE / "questions.json").read_text()))


# The paper
def test_parts_become_items_and_marks_are_shared():
    items = {i["id"]: i for i in paper()["questions"]}
    assert list(items) == ["Q1", "Q2i", "Q2ii", "Q3", "Q4", "Q5i", "Q5ii", "Q5iii"]
    assert items["Q2ii"]["part"] == "ii" and items["Q2ii"]["text"].endswith("(ii) a 2-digit number")
    assert round(items["Q5iii"]["marks"] * 3, 6) == 5 and items["Q1"]["marks"] == 1
    assert all(i["answer"] is None for i in items.values())


@pytest.mark.parametrize("answer, expected", [
    ("(i) 1/12 (ii) 15/16", {"Q2i": "1/12", "Q2ii": "15/16"}),
    ({"i": "1/12", "ii": "15/16"}, {"Q2i": "1/12", "Q2ii": "15/16"}),
    ("(i) 1/12", {"Q2i": "1/12", "Q2ii": None}),
])
def test_expected_answers_can_come_with_the_paper(answer, expected):
    items = paper([{"questionNumber": 2, "questionText": "Cards 5 to 100. (i) a square (ii) two-digit", "answer": answer}])["questions"]
    assert {i["id"]: i["answer"] for i in items} == expected
    assert {i["id"]: i["answer_source"] for i in items if i["answer"]} == {k: "paper" for k, v in expected.items() if v}


@pytest.mark.parametrize("body, message", [
    ([], "list of questions"), ({"questions": "x"}, "list of questions"), ([{"questionNumber": 1}], "questionText is missing"),
    ([{"questionNumber": 1, "questionText": "a"}, {"questionNumber": 1, "questionText": "b"}], "appears twice"),
])
def test_a_bad_paper_names_the_problem(body, message):
    with pytest.raises(generic.PaperError, match=message):
        generic.parse_paper(body)


# The answer key
def test_missing_answers_are_worked_out_and_labelled():
    p = paper()
    tasks = generic.key_tasks(p)
    assert [t["id"] for t in tasks] == ["key:1", "key:2", "key:3", "key:4", "key:5"] and "Q2i, Q2ii" in tasks[1]["user"]
    keyed = generic.apply_key(p, {"key:1": {"working": "3 of 8", "answers": {"Q1": "3/8", "NOPE": "1"}}, "key:2": {"answers": {"Q2i": ""}}})
    q1 = keyed["questions"][0]
    assert (q1["answer"], q1["answer_source"], q1["answer_how"]) == ("3/8", "ai", "3 of 8") and keyed["questions"][1]["answer"] is None


def test_the_teacher_corrects_or_fills_the_key():
    p = generic.apply_key(paper(), {"key:2": {"answers": {"Q2i": "1/10"}}})
    fixed = generic.set_answers(p, {"Q2i": "1/12", "Q1": "3/8"})
    assert {i["id"]: (i["answer"], i["answer_source"]) for i in fixed["questions"][:2]} == {"Q1": ("3/8", "teacher"), "Q2i": ("1/12", "teacher")}
    with pytest.raises(generic.PaperError, match="Q9"):
        generic.set_answers(p, {"Q9": "1"})


def test_no_key_task_when_the_paper_has_every_answer():
    assert generic.key_tasks(paper([{"questionNumber": 1, "questionText": "2 + 2?", "answer": "4"}])) == []


# Reading the working
def keyed():
    p = paper()
    return {**p, "questions": [{**i, "answer": KEY[i["id"]], "answer_source": "paper"} for i in p["questions"]]}


def sheet(**answers):
    return {"id": "s", "answers": {**{q: "" for q in KEY}, **answers}}


def test_values_decide_right_or_wrong_and_the_ai_only_explains():
    claims = {"s": {"answers": {"Q1": {"result": "correct"}, "Q3": {"result": "wrong", "what_went_wrong": "x"},
                                "Q4": {"result": "wrong", "step": "Favourable", "what_went_wrong": "Counted the sums, not the pairs.", "shown": True}}}}
    read, failed = generic.apply_reading(keyed(), [sheet(Q1="P = 3/5", Q3="2/52 = 1/26", Q4="P = 5/11")], claims)
    a = read[0]["answers"]
    assert a["Q1"]["result"] == "wrong" and a["Q1"]["evidence"] == "wrote 3/5; expected 3/8"   # the AI said correct; 3/5 is not 3/8
    assert a["Q3"]["result"] == "correct"                                                        # the AI said wrong; 1/26 is right
    assert (a["Q4"]["step"], a["Q4"]["evidence"], a["Q4"]["shown"]) == ("Favourable", "Counted the sums, not the pairs.", True)
    assert a["Q2i"]["result"] == "" and failed == 0


def test_equivalent_values_are_right():
    read, _ = generic.apply_reading(keyed(), [sheet(Q1="3/8 = 0.375", Q2ii="90/96 = 45/48", Q5iii="18/90 = 20%")], {})
    assert {q: read[0]["answers"][q]["result"] for q in ("Q1", "Q2ii", "Q5iii")} == {"Q1": "correct", "Q2ii": "correct", "Q5iii": "correct"}


def test_words_with_no_ai_go_to_the_teacher_and_count_as_a_failed_student():
    p = paper([{"questionNumber": 1, "questionText": "Why is the sky blue?", "answer": "Scattering of light"}])
    read, failed = generic.apply_reading(p, [{"id": "s", "answers": {"Q1": "Because of the sea"}}], {})
    assert read[0]["answers"]["Q1"]["result"] == "unreadable" and failed == 1


def test_labelling_words_from_the_ai_are_dropped():
    read, _ = generic.apply_reading(keyed(), [sheet(Q1="3/5")], {"s": {"answers": {"Q1": {"result": "wrong", "what_went_wrong": "A weak student guessed."}}}})
    assert read[0]["answers"]["Q1"]["evidence"] == "wrote 3/5; expected 3/8"


# A few thinking errors
def wrong_sheets():
    read, _ = generic.apply_reading(keyed(), [sheet(Q1="3/5", Q3="4/52 = 1/13", Q4="15/36 = 5/6"), {**sheet(Q5i="90/90 = 1"), "id": "t"}], {})
    return read


def error_reply(errors, answers):
    return {"errors": {"errors": errors, "answers": answers}}


E = {"name": "Counts outcomes that don't fit", "thinks": "\"If it looks like it, it counts.\"", "looks_like": "Counts all kings for red kings.",
     "teacher": "Tick each outcome against the question.", "student": "Check each one.", "steps": ["List", "Tick", "Count"]}


def test_errors_are_named_and_answers_grouped_under_them():
    rows = generic.error_tasks(keyed(), wrong_sheets())[0]["user"].splitlines()
    assert [r.split(" | ")[0] for r in rows] == ["A1", "A2", "A3", "A4"] and rows[3].startswith("A4 | Q5i:")
    catalogue, sheets = generic.apply_errors(keyed(), wrong_sheets(), error_reply(
        [{**E, "name": "Compares with the other colour"}, E], {"A1": "1", "A2": "E2", "A4": 2, "A3": "slip"}))
    assert [e["name"] for e in catalogue.values()] == ["Compares with the other colour", "Counts outcomes that don't fit"]
    codes = {(s["id"], q): a.get("code") for s in sheets for q, a in s["answers"].items() if a.get("code")}
    assert codes == {("s", "Q1"): "E1", ("s", "Q3"): "E2", ("t", "Q5i"): "E2", ("s", "Q4"): "SLIP"}


def test_at_most_five_errors_and_an_error_with_no_answers_is_dropped():
    catalogue, _ = generic.apply_errors(keyed(), wrong_sheets(), error_reply([E] * 7, {"A1": "6", "A2": "2"}))
    assert list(catalogue) == ["E1"]  # number 6 is beyond the limit; numbers 1, 3, 4 and 5 explain nothing


def test_an_incomplete_error_or_an_unknown_answer_is_ignored():
    catalogue, sheets = generic.apply_errors(keyed(), wrong_sheets(), error_reply([{"name": "Vague"}], {"A1": "1", "A99": "1"}))
    assert catalogue == {} and all(a.get("code") is None for s in sheets for a in s["answers"].values())


# The whole flow, through the API, with AI replies given directly
def run(cid, module, results):
    return client.post(f"{API}/classes/{cid}/{module}/run", json={"results": results, "status": "ok"})


def analysed(paper_bytes=None):
    cid = client.post(f"{API}/classes", json={"pack": "generic", "name": "10 B"}).json()["class_id"]
    assert client.post(f"{API}/classes/{cid}/paper", content=paper_bytes or (SAMPLE / "questions.json").read_bytes()).status_code == 200
    assert client.post(f"{API}/classes/{cid}/upload/v1", params={"filename": "students.json"}, content=(SAMPLE / "students.json").read_bytes()).status_code == 200
    replies = {}
    for q, a in KEY.items():
        replies.setdefault(f"key:{q[1]}", {"answers": {}})["answers"][q] = a
    assert run(cid, "m3-key", replies).status_code == 200
    assert run(cid, "m3-read", {}).status_code == 200
    errors = [{**E, "name": "Compares with the other outcomes"}, {**E, "name": "Miscounts a range"}, E]
    # The wrong answers in order: student2 Q1, Q2i, Q2ii, Q3, Q4, Q5i, then student3 Q2ii, Q5ii
    answers = {"A1": "1", "A2": "2", "A3": "2", "A4": "3", "A5": "slip", "A6": "3", "A7": "3", "A8": "3"}
    feed = run(cid, "m3-errors", error_reply(errors, answers)).json()
    return cid, feed


def test_uploaded_paper_runs_to_a_class_picture():
    cid, feed = analysed()
    rows = {r["name"]: r["students"] for r in feed["class"]["misconceptions"]}
    assert rows == {"Counts outcomes that don't fit": ["student2", "student3"], "Compares with the other outcomes": ["student2"],
                    "Miscounts a range": ["student2"], "Slip in the last step": ["student2"]}
    nxt = {s["student"]: s["next"]["action"] for s in feed["students"]}
    assert nxt == {"student1": "extension", "student2": "group", "student3": "group"}
    body = client.get(f"{API}/classes/{cid}").json()
    assert body["generic"] and body["class_code"] == "10B" and body["paper"][0]["answer_source"] == "ai"
    for module in ("m4", "m5", "m6"):
        assert run(cid, module, {}).status_code == 200


def test_answers_given_with_the_paper_need_no_key():
    questions = json.loads((SAMPLE / "questions.json").read_text())
    for q in questions:
        q["answer"] = {1: "3/8", 2: "(i) 1/12 (ii) 15/16", 3: "1/26", 4: "5/12", 5: "(i) 9/10 (ii) 1/10 (iii) 1/5"}[q["questionNumber"]]
    cid = client.post(f"{API}/classes", json={"pack": "generic", "name": "10B"}).json()["class_id"]
    client.post(f"{API}/classes/{cid}/paper", content=json.dumps(questions).encode())
    client.post(f"{API}/classes/{cid}/upload/v1", content=(SAMPLE / "students.json").read_bytes())
    assert client.get(f"{API}/classes/{cid}/m3-key/tasks").json()["tasks"] == []


def test_teacher_answers_through_the_api_and_after_marking_they_are_locked():
    cid = client.post(f"{API}/classes", json={"pack": "generic", "name": "10B"}).json()["class_id"]
    client.post(f"{API}/classes/{cid}/paper", content=(SAMPLE / "questions.json").read_bytes())
    body = client.post(f"{API}/classes/{cid}/answers", json={"answers": {"Q1": "3/8"}}).json()
    assert body["paper"][0]["answer_source"] == "teacher"
    assert client.post(f"{API}/classes/{cid}/answers", json={"answers": {"Q9": "1"}}).status_code == 409
    done, _ = analysed()
    assert client.post(f"{API}/classes/{done}/answers", json={"answers": {"Q1": "1/2"}}).status_code == 409


def test_steps_out_of_order_or_for_packs_are_refused():
    cid = client.post(f"{API}/classes", json={"pack": "generic", "name": "10B"}).json()["class_id"]
    assert client.post(f"{API}/classes/{cid}/upload/v1", content=(SAMPLE / "students.json").read_bytes()).status_code == 409  # paper first
    assert client.post(f"{API}/classes/{cid}/paper", content=b'{"questions": []}').status_code == 409
    client.post(f"{API}/classes/{cid}/paper", content=(SAMPLE / "questions.json").read_bytes())
    assert client.get(f"{API}/classes/{cid}/m3/tasks").status_code == 409
    pack_class = client.post(f"{API}/classes", json={"pack": "habit4", "name": "10B"}).json()["class_id"]
    assert client.post(f"{API}/classes/{pack_class}/paper", content=(SAMPLE / "questions.json").read_bytes()).status_code == 409


# The records: per class, per paper, per student, across subjects
def test_class_and_student_records_are_kept_across_papers():
    first, _ = analysed()
    habit = client.post(f"{API}/classes", json={"pack": "habit4", "name": "10b"}).json()["class_id"]
    client.post(f"{API}/classes/{habit}/upload/v1", content=client.get(f"{API}/files/habit4/v1", params={"sample": True}).content)
    client.post(f"{API}/classes/{habit}/m3/run", json={})
    body = client.get(f"{API}/records/10-b").json()
    assert set(body["assessments"]) == {first, habit}
    paper_record = body["assessments"][first]
    assert len(paper_record["thinking_errors"]) == 4 and paper_record["questions"][1]["id"] == "Q2i"
    s2 = body["students"]["student2"]["assessments"][first]
    assert s2["score"] == {"correct": 2, "answered": 8, "questions": 8, "marks": round(5 / 3 * 2, 2), "out_of": 13.0}
    assert {e["name"] for e in s2["thinking_errors"]} >= {"Compares with the other outcomes", "Miscounts a range"}
    assert "H01" in body["students"]  # the Habit 4 sample's students are in the same class
    assert client.get(f"{API}/records/NOPE").status_code == 404


class FakeFirestore:
    """Just enough of google.cloud.firestore.Client: document(path).set/get, collection(path).stream/order_by."""

    def __init__(self):
        self.docs = {}

    def document(self, path):
        outer = self

        class Doc:
            id = path.rsplit("/", 1)[1]

            def set(self, data, merge=False):
                outer.docs[path] = {**(outer.docs.get(path, {}) if merge else {}), **json.loads(json.dumps(data))}

            def get(self):
                found = outer.docs.get(path)
                return type("Snap", (), {"exists": found is not None, "to_dict": lambda self: found})()

            def to_dict(self):
                return outer.docs[path]
        return Doc()

    def collection(self, path):
        outer = self

        class Col:
            def __init__(self, key=None):
                self.key = key

            def order_by(self, field):
                return Col(field)

            def stream(self):
                docs = [outer.document(p) for p in outer.docs if p.rsplit("/", 1)[0] == path]
                return sorted(docs, key=lambda d: d.to_dict()[self.key]) if self.key else docs
        return Col()


def test_the_same_flow_writes_firestore_documents():
    fake = FakeFirestore()
    store.use(store.FirestoreStore(fake))
    cid, _ = analysed()
    assert wf.load(cid).stage == "identified"  # rebuilt from the events kept in Firestore
    assert f"classes/10B/students/student2/assessments/{cid}" in fake.docs and f"runs/{cid}/events/000001" in fake.docs
    assert wf.class_records("10 B")["students"]["student3"]["assessments"][cid]["next"]["action"] == "group"


# Which model: judgement goes to the reasoning model
def test_judgement_steps_use_the_reasoning_model():
    p = paper()
    assert {t["tier"] for t in generic.key_tasks(p)} == {"reasoning"}
    assert generic.read_tasks(keyed(), [sheet(Q1="3/5")])[0]["tier"] == "fast"  # numbers are compared by rule; the model only explains
    words = generic.parse_paper([{"questionNumber": 1, "questionText": "Why is the sky blue?", "answer": "Scattering of light"}])
    assert generic.read_tasks(words, [{"id": "s", "answers": {"Q1": "Because of the sea"}}])[0]["tier"] == "reasoning"
    assert generic.error_tasks(keyed(), wrong_sheets())[0]["tier"] == "reasoning"
    from adaptive_engine import ai_tasks
    from adaptive_engine.packs import all_packs
    habit = all_packs()["habit4"]
    assert ai_tasks.marking_tasks(habit, [{"id": "s", "answers": {"S1": "We both choose."}}], habit.items)[0]["tier"] == "reasoning"


# Each thinking error comes with its fix
def test_each_error_carries_its_fix():
    full = {**E, "steps": ["List every card", "Tick the ones that fit", "Count the ticks", "Check with a second method"],
            "activity": "Sort a real deck into fits / does not fit.", "check": "P(a black king)? Answer 1/26."}
    catalogue, sheets = generic.apply_errors(keyed(), wrong_sheets(), error_reply([full], {"A2": "1"}))
    pack = generic.build_pack(keyed(), catalogue, sheets)
    assert pack.misconceptions["E1"]["exit_check"] == "P(a black king)? Answer 1/26." and pack.misconceptions["E1"]["activity"].startswith("Sort")
    assert pack.interventions["INT-E1"]["steps"][3] == "Check with a second method"


def test_fix_and_actions_reach_the_feed_and_the_records():
    cid, feed = analysed()
    row = next(r for r in feed["class"]["misconceptions"] if r["code"] == "E1")
    assert row["fix"]["steps"] == E["steps"] and row["fix"]["teacher"] == E["teacher"]
    tasks = client.get(f"{API}/classes/{cid}/m3-actions/tasks").json()["tasks"]
    assert [t["id"] for t in tasks] == ["actions:1"] and "student2" in tasks[0]["user"] and "student1" not in tasks[0]["user"]
    reply = {"actions:1": {"students": {"student2": {"actions": ["Q1: put all 8 balls at the bottom.", "Q2: count 5 to 100 as 96 cards."], "try_next": "P(red) with 2 red, 4 blue?"},
                                        "student9": {"actions": ["x"]}, "student3": {"actions": ["You are a weak student."]}}}}
    feed = run(cid, "m3-actions", reply).json()
    assert set(feed["actions"]) == {"student2"} and feed["actions"]["student2"]["actions"][1].startswith("Q2")
    body = client.get(f"{API}/records/10B").json()
    s2 = body["students"]["student2"]["assessments"][cid]
    assert s2["actions"]["try_next"] == "P(red) with 2 red, 4 blue?"
    assert body["assessments"][cid]["thinking_errors"][0]["fix"]["steps"]
