"""LiveLife Habit 4 STUDENT assessment (demos/livelife-student), built to the LiveLife document
the LiveLife source document, with the 9th MCQ and the /100 grading: the 9 MCQ keys
and marking (2 marks each, /18), the score out of 100 (knowledge /18 + situations /32 = /50, doubled) and the rating from it,
the thank-you page that shows no marks, the scorecard by random id, flags that are stored but never shown to the child, the
single-user store, and that the page never receives an answer key.  Run from services/demo-livelife:  python -m pytest test_cases"""
import importlib.util
import sys
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server  # noqa: E402

client = TestClient(server.create_app())
BASE = "/demo-livelife/livelife-student"

KEYS = {"K1": "C", "K2": "B", "K3": "C", "K4": "C", "K5": "B", "K6": "C", "K7": "A", "K8": "C",   # the document, Section 1 A
        "K9": "A"}                                                                                  # K9: added for this demo
WRONG = {k: "D" for k in KEYS}                                                                      # D is never a key
S_IDS = ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"]


def backend():
    """A private copy of backend.py, to test its pure functions and its store directly."""
    spec = importlib.util.spec_from_file_location("ll_backend_copy", ROOT / "demos" / "livelife-student" / "backend.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def scored(scores, **extra):
    """The scorer's reply for this student: one entry per scenario (a None score = could not score)."""
    res = {}
    for sid, sc in zip(S_IDS, scores):
        res[sid] = {"score": sc, "evidence": f"evidence {sid}", "tip": f"tip {sid}", "flag": False}
    out = {"results": res}
    out.update(extra)
    return out


def submit(scores=(3,) * 8, mcq=None, name="Asha", grade="8", answers=None, **kw):
    body = {"name": name, "grade": grade, "mcq": KEYS if mcq is None else mcq,
            "answers": answers or {s: f"my answer {s}" for s in S_IDS},
            "scored": scored(scores, **kw) if scores is not None else None}
    return client.post(f"{BASE}/api/submit", json=body)


def outcome_of(resp):
    assert resp.status_code == 200, resp.text
    return client.get(f"{BASE}/api/outcome/{resp.json()['id']}").json()


# --------------------------------------------------------------------------------------------- serving and items
def test_the_demo_is_mounted_and_its_pages_are_served():
    assert "livelife-student" in client.get("/health").json()["demos"]
    page = client.get(f"{BASE}/")
    assert page.status_code == 200 and '<base href="/demo-livelife/livelife-student/">' in page.text
    out = client.get(f"{BASE}/outcome.html?id=abc")
    assert out.status_code == 200 and '<base href="/demo-livelife/livelife-student/">' in out.text
    assert client.get(f"{BASE}/backend.py").status_code == 404          # code is never sent


def test_items_hold_the_9_mcqs_and_8_scenarios_and_no_answer_key():
    r = client.get(f"{BASE}/api/items")
    j = r.json()
    assert [q["id"] for q in j["mcqs"]] == list(KEYS)
    assert [s["id"] for s in j["scenarios"]] == S_IDS
    assert j["thank_you"] == "Thank you for completing the Habit 4: Think Win-Win assessment. Your answers have been submitted."
    for q in j["mcqs"]:
        assert set(q) == {"id", "stem", "options"} and set(q["options"]) == {"A", "B", "C", "D"}
    for rationale in ("A Win-Win solution considers both", "One person gets their way", "Consideration includes understanding",
                      "These are the five chapter components", "observable, specific and linked",
                      "Giving up what matters to you so the other person always gets their way"):
        assert rationale.lower() not in r.text.lower()
    assert '"key"' not in r.text and '"why"' not in r.text and '"competency"' not in r.text


def test_the_documents_questions_are_worded_as_given():
    j = client.get(f"{BASE}/api/items").json()
    assert j["mcqs"][0]["stem"] == "What does Think Win-Win mean?"
    assert j["mcqs"][0]["options"]["C"] == "We look for a solution that considers what matters to both of us."
    assert j["scenarios"][4]["question"].startswith("In a discussion, your classmate says something you disagree with. Write one sentence")
    assert j["scenarios"][6]["question"].startswith("You and a classmate want to share a game console.")


def test_the_ninth_question_is_the_approved_lose_win_one():
    j = client.get(f"{BASE}/api/items").json()
    k9 = j["mcqs"][8]
    assert k9["id"] == "K9"
    assert k9["stem"] == ("Every break, you let your friend choose the game because you do not want an argument, even when you "
                          "would like a turn. Which mindset does this most closely show?")
    assert k9["options"] == {"A": "Lose-Win", "B": "Win-Lose", "C": "Win-Win", "D": "Interdependent Living"}


# --------------------------------------------------------------------------------------------- knowledge check
def test_mcq_marking_uses_the_keys_two_marks_each_out_of_18():
    b = backend()
    assert {q["id"]: q["key"] for q in b.MCQS} == KEYS
    full = b.mark_knowledge(KEYS)
    assert full["score"] == 18 and full["max"] == 18 and full["correct"] == 9 and full["of"] == 9 and full["percent"] == 100
    assert b.mark_knowledge(WRONG)["score"] == 0
    one = b.mark_knowledge(dict(WRONG, K1="C"))
    assert one["score"] == 2 and one["correct"] == 1 and one["percent"] == 11          # 11.1% for display
    assert b.mark_knowledge(dict(WRONG, K9="A"))["score"] == 2                          # the new ninth question counts too
    assert b.mark_knowledge(dict(KEYS, K5="D"))["score"] == 16


def test_mcq_blank_unknown_and_lowercase_choices():
    b = backend()
    k = b.mark_knowledge({"K1": "c", "K2": "", "K3": "Z", "K99": "A"})
    assert k["marks"]["K1"]["correct"] is True              # lower case still reads as C
    assert k["marks"]["K2"]["correct"] is False and k["marks"]["K3"]["correct"] is False
    assert k["score"] == 2 and k["correct"] == 1
    assert b.mark_knowledge({})["score"] == 0


# --------------------------------------------------------------------------------------------- ratings and percentages
def mcq_with(n_correct):
    """Nine choices of which the first n are right (D is never a key)."""
    return {k: (KEYS[k] if i < n_correct else "D") for i, k in enumerate(KEYS)}


def scores_totalling(total):
    """Eight situation scores (0-4 each) that add up to `total`."""
    out, left = [], total
    for _ in range(8):
        s = min(4, left)
        out.append(s)
        left -= s
    return tuple(out)


@pytest.mark.parametrize("n_correct,scen_total,raw,final,rating", [
    (9, 32, 50, 100, "Strong"),         # full marks
    (9, 28, 46, 92, "Strong"),
    (9, 25, 43, 86, "Strong"),          # 86 is the first even score at or above the 85 cut-off
    (9, 24, 42, 84, "Secure"),
    (3, 29, 35, 70, "Secure"),          # exactly 70
    (3, 28, 34, 68, "Building"),
    (2, 32, 36, 72, "Secure"),
    (1, 32, 34, 68, "Building"),
    (0, 32, 32, 64, "Building"),        # a perfect situational check with 0 on knowledge: no longer Strong
    (9, 8, 26, 52, "Building"),         # a perfect knowledge check with a weak situational check: no longer Emerging
    (5, 20, 30, 60, "Building"),
    (0, 25, 25, 50, "Building"),        # exactly 50
    (0, 24, 24, 48, "Emerging"),
    (0, 0, 0, 0, "Emerging"),
])
def test_final_score_out_of_100_and_the_final_rating(n_correct, scen_total, raw, final, rating):
    o = outcome_of(submit(scores_totalling(scen_total), mcq=mcq_with(n_correct)))
    assert o["knowledge"] == {"score": 2 * n_correct, "max": 18, "correct": n_correct, "of": 9,
                              "percent": int(n_correct * 100 / 9 + 0.5)}
    assert o["situational"]["score"] == scen_total and o["situational"]["max"] == 32 and o["situational"]["scored"] == 8
    assert o["overall"] == {"score": final, "max": 100, "raw": raw, "raw_max": 50, "rating": rating, "complete": True}


def test_every_raw_mark_counts_double_so_the_hundred_is_twice_the_fifty():
    b = backend()
    assert b.RAW_MAX == 50 and b.KNOWLEDGE_MAX == 18 and b.SITUATIONAL_MAX == 32 and b.FINAL_MAX == 100
    assert b.final_score(18, [4] * 8) == 100 and b.final_score(0, [0] * 8) == 0
    assert b.final_score(18, [3] * 8) == 84 and b.final_score(0, [4] * 8) == 64 and b.final_score(18, [1] * 8) == 52
    assert b.final_score(2, [4, 4, 4, 4, 4, 4, 4, 3]) == 2 * (2 + 31)


def test_rating_bands_use_the_lower_bound_so_there_are_no_gaps():
    b = backend()
    for score, label in [(0, "Emerging"), (49.9, "Emerging"), (50, "Building"), (69.9, "Building"), (70, "Secure"),
                         (84, "Secure"), (84.9, "Secure"), (85, "Strong"), (100, "Strong")]:
        assert b.rating_for(score) == label, score
    assert b.rating_for(b.final_score(9 * 2, [3] * 8)) == "Secure"              # 84
    assert b.rating_for(b.final_score(9 * 2, [4, 3, 3, 3, 3, 3, 3, 3])) == "Strong"   # 86


def test_each_competency_has_its_own_mark_and_rating():
    o = outcome_of(submit((4, 3, 2, 1, 0, 4, 3, 2)))
    cards = {c["id"]: c for c in o["competencies"]}
    assert [cards[s]["mark_percent"] for s in S_IDS] == [100, 75, 50, 25, 0, 100, 75, 50]
    assert [cards[s]["rating"] for s in S_IDS] == ["Strong", "Secure", "Building", "Emerging", "Emerging", "Strong", "Secure", "Building"]
    assert cards["S1"]["name"] == "Think Win-Win understanding" and cards["S7"]["name"] == "Win-Win Agreement components"
    assert cards["S3"]["note"] == "evidence S3 tip S3"


def test_the_scorecard_carries_everything_the_document_lists():
    o = outcome_of(submit((3,) * 8, name="  Asha   Rao ", grade="8"))
    assert o["student"] == {"name": "Asha Rao", "grade": "8", "date": date.today().isoformat()}
    for k in ("overall", "knowledge", "situational", "competencies", "strengths", "skills", "try_next", "teacher_support", "rating_guide"):
        assert k in o
    assert o["rating_guide"] == ("Rating guide: Emerging = below 50%; Building = 50–69%; Secure = 70–84%; Strong = 85–100%. "
                                 "These demo thresholds are provisional and should be confirmed by LiveLife.")
    assert len(o["competencies"]) == 8


# --------------------------------------------------------------------------------------------- the thank-you page shows no marks
def test_submit_answers_with_only_an_id_and_no_marks():
    r = submit((4,) * 8)
    assert r.status_code == 200 and set(r.json()) == {"id"}
    assert len(r.json()["id"]) >= 20
    for word in ("score", "percent", "rating", "Strong", "mark"):
        assert word not in r.text


def test_an_unknown_or_malformed_scorecard_id_is_a_404():
    for bad in ("nope", "x" * 16, "../../etc/passwd", "a" * 100):
        assert client.get(f"{BASE}/api/outcome/{bad}").status_code == 404
    assert client.get(f"{BASE}/api/outcome/AAAAAAAAAAAAAAAAAAAAAA").status_code == 404


def test_name_and_grade_are_required():
    assert submit(name="   ").status_code == 422
    assert submit(grade="").status_code == 422
    assert submit(name="n" * 41).status_code == 422
    assert submit(grade="g" * 13).status_code == 422


# --------------------------------------------------------------------------------------------- unscored answers and flags
def test_when_an_answer_could_not_be_scored_there_is_no_final_rating_and_no_made_up_mark():
    o = outcome_of(submit((4, None, 4, 4, 4, 4, 4, 4)))
    assert o["overall"] == {"score": None, "max": 100, "raw": None, "raw_max": 50, "rating": None, "complete": False}
    assert o["knowledge"]["score"] == 18                                          # the Knowledge Check still shows
    assert o["situational"]["scored"] == 7 and o["situational"]["score"] == 28
    s2 = next(c for c in o["competencies"] if c["id"] == "S2")
    assert s2["mark_percent"] is None and s2["rating"] is None and "could not score" in s2["note"]


def test_when_the_scorer_was_off_the_knowledge_check_still_shows_and_the_page_says_nothing_false():
    o = outcome_of(submit(None, mcq=KEYS))
    assert o["knowledge"]["score"] == 18
    assert o["overall"]["rating"] is None and o["situational"]["scored"] == 0 and o["situational"]["percent"] is None
    assert all(c["mark_percent"] is None for c in o["competencies"])
    assert o["strengths"] and o["skills"] and o["try_next"] and o["teacher_support"]     # never an empty card


def test_a_flag_is_stored_for_the_educator_but_never_sent_to_the_child():
    b = backend()
    body = b.SubmitIn(name="Asha", grade="8", mcq={}, answers={"S5": "rude words"},
                      scored=b.ScoredIn(results={"S5": b.Scored(score=0, evidence="e", tip="t", flag=True),
                                                 "S1": b.Scored(score=3, evidence="e", tip="t", flag=True)}))
    oid = b.submit(body)
    import json
    oid = json.loads(oid.body)["id"]
    rec = b.private_record(oid)
    assert rec["flagged_for_educator_review"] == ["S5"]          # only a real 0 keeps its flag
    assert rec["answers"]["S5"] == "rude words"
    shown = json.dumps(b.outcome(oid).body.decode())
    assert "flag" not in shown.lower() and "educator" not in shown.lower() and "rude words" not in shown


def test_a_blank_zero_is_not_flagged():
    b = backend()
    import json
    body = b.SubmitIn(name="A", grade="8", scored=b.ScoredIn(results={"S1": b.Scored(score=0, evidence="No answer", tip="t", flag=False)}))
    oid = json.loads(b.submit(body).body)["id"]
    assert b.private_record(oid)["flagged_for_educator_review"] == []


# --------------------------------------------------------------------------------------------- summary
def test_the_ai_summary_is_used_when_valid_and_a_fallback_when_not():
    ai = {"strengths": ["You listened.", "You were fair.", "third is dropped"], "skills": ["Check agreements."],
          "try_next": "Ask first.", "teacher_support": "Practise turns."}
    o = outcome_of(submit((3,) * 8, summary=ai))
    assert o["strengths"] == ["You listened.", "You were fair."] and o["skills"] == ["Check agreements."]
    assert o["try_next"] == "Ask first." and o["teacher_support"] == "Practise turns."
    bad = outcome_of(submit((4, 4, 4, 4, 1, 4, 4, 4), summary={"strengths": [], "skills": ["x"], "try_next": "", "teacher_support": ""}))
    assert any("evidence" in s for s in bad["strengths"])                       # built from the strong competencies
    assert any("Respectful communication" in s for s in bad["skills"])         # the weakest one
    assert "Respectful communication" in bad["teacher_support"]


# --------------------------------------------------------------------------------------------- inputs and store
def test_out_of_range_scores_and_overlong_text_are_refused_or_cut():
    assert submit((9,) * 8).status_code == 422
    long = "x" * 301
    r = client.post(f"{BASE}/api/submit", json={"name": "A", "grade": "8", "scored": {"results": {"S1": {"score": 2, "evidence": long}}}})
    assert r.status_code == 422
    o = outcome_of(submit((2,) * 8, answers={"S1": "y" * 5000}))
    assert o["overall"]["rating"] == "Building" and o["overall"]["score"] == 68          # (18 + 16) x 2


def test_unknown_items_in_what_the_page_sends_are_ignored():
    res = {sid: {"score": 3, "evidence": "e", "tip": "t"} for sid in S_IDS}
    res["S9"] = {"score": 4, "evidence": "e", "tip": "t"}
    r = client.post(f"{BASE}/api/submit", json={"name": "A", "grade": "8", "mcq": {"K99": "A"}, "scored": {"results": res}})
    o = outcome_of(r)
    assert o["situational"]["score"] == 24 and o["knowledge"]["score"] == 0


def test_single_user_a_new_submission_replaces_the_last_scorecard():
    first = submit((4,) * 8, name="First Student").json()["id"]
    assert client.get(f"{BASE}/api/outcome/{first}").status_code == 200
    second = submit((2,) * 8, name="Second Student").json()["id"]
    assert client.get(f"{BASE}/api/outcome/{first}").status_code == 404              # replaced by the newer one
    assert client.get(f"{BASE}/api/outcome/{second}").json()["student"]["name"] == "Second Student"


def test_the_store_keeps_only_the_newest_results():
    b = backend()
    b.MAX_STORED = 3
    ids = [b._remember({"outcome": {"n": i}}) for i in range(5)]
    assert b.private_record(ids[0]) is None and b.private_record(ids[1]) is None
    assert [b.private_record(i)["outcome"]["n"] for i in ids[2:]] == [2, 3, 4]
    assert len(set(ids)) == 5 and all(len(i) >= 20 for i in ids)


def test_the_page_scripts_never_write_server_text_as_markup():
    for name in ("app.js", "outcome.js"):
        js = (ROOT / "demos" / "livelife-student" / name).read_text(encoding="utf-8")
        assert "innerHTML" not in js and "insertAdjacentHTML" not in js and "document.write" not in js, name
