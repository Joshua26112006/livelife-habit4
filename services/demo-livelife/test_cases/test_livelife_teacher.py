"""LiveLife Habit 4 TEACHER assessment (demos/livelife-teacher) and the front page (demos/livelife-home), built to the LiveLife
Section 9 document: the eight questions, the scoring maths, the recommendation rules (the outcome form's proposed thresholds),
critical concerns, the thank-you page that shows no scores, the outcome by id and "the latest", and the SINGLE-USER store.
Run from services/demo-livelife:  python -m pytest test_cases"""
import importlib.util
import json
import sys
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server  # noqa: E402

client = TestClient(server.create_app())
T = "/demo-livelife/livelife-teacher"
C_IDS = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"]
HIGHLY, REC, COACH, NOT = "Highly recommend", "Recommend", "Recommend with coaching", "Not recommend at this time"


def backend():
    """A private copy of the teacher backend.py, to test its pure functions and its store directly."""
    spec = importlib.util.spec_from_file_location("ll_teacher_copy", ROOT / "demos" / "livelife-teacher" / "backend.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def scored(scores, critical=(), **extra):
    res = {}
    for cid, sc in zip(C_IDS, scores):
        res[cid] = {"score": sc, "evidence": f"evidence {cid}", "coaching": f"coaching {cid}" if (sc is not None and sc <= 2) else "",
                    "critical": cid in critical}
    out = {"results": res}
    out.update(extra)
    return out


def submit(scores=(3,) * 8, critical=(), name="Mr Sample", school="Demo School", **kw):
    body = {"name": name, "school": school, "answers": {c: f"answer {c}" for c in C_IDS},
            "scored": scored(scores, critical, **kw) if scores is not None else None}
    return client.post(f"{T}/api/submit", json=body)


def outcome_of(resp):
    assert resp.status_code == 200, resp.text
    return client.get(f"{T}/api/outcome/{resp.json()['id']}").json()


# --------------------------------------------------------------------------------------------- serving, items, front page
def test_the_pages_are_served_and_the_front_page_links_all_three():
    health = client.get("/health").json()["demos"]
    assert "livelife-teacher" in health and "livelife-home" in health
    page = client.get(f"{T}/")
    assert page.status_code == 200 and '<base href="/demo-livelife/livelife-teacher/">' in page.text
    out = client.get(f"{T}/outcome.html")
    assert out.status_code == 200 and '<base href="/demo-livelife/livelife-teacher/">' in out.text
    assert client.get(f"{T}/backend.py").status_code == 404
    home = client.get("/demo-livelife/livelife-home/")
    assert home.status_code == 200
    for href in ('href="../livelife-student/"', 'href="../livelife-teacher/"', 'href="../livelife-teacher/outcome.html"'):
        assert href in home.text
    for label in ("Student assessment", "Teacher assessment", "Teacher assessment outcome"):
        assert label in home.text


def test_items_are_the_eight_questions_and_nothing_that_helps_a_scorer():
    r = client.get(f"{T}/api/items")
    j = r.json()
    assert [q["id"] for q in j["questions"]] == C_IDS
    assert j["questions"][0]["question"].startswith("Student says: “Think Win-Win means I should let my friend choose")
    assert j["questions"][2]["question"] == "A learner says their family cannot afford the clothing discussed. Others begin commenting. How do you respond?"
    assert j["thank_you"] == ("Thank you for completing the Habit 4: Think Win-Win teacher assessment. We appreciate your time and responses. "
                              "Your assessment has been submitted. You may now continue.")
    for word in ("rubric", "indicator", "Highly demonstrated", "Expected"):
        assert word.lower() not in r.text.lower()


# --------------------------------------------------------------------------------------------- scoring maths
@pytest.mark.parametrize("scores,total,pct,rating", [
    ((4,) * 8, 32, 100, "Highly demonstrated"),
    ((3, 4, 3, 4, 4, 4, 4, 2), 28, 88, "Highly demonstrated"),     # 87.5% shows as 88; average 3.5 rounds half up to 4
    ((3,) * 8, 24, 75, "Demonstrated"),
    ((3, 3, 3, 3, 3, 3, 3, 2), 23, 72, "Demonstrated"),             # 71.875
    ((2,) * 8, 16, 50, "Partially demonstrated"),
    ((1,) * 8, 8, 25, "Limited"),
    ((0,) * 8, 0, 0, "No evidence / critical concern"),
])
def test_score_percent_and_overall_rating(scores, total, pct, rating):
    o = outcome_of(submit(scores))
    assert o["score"]["total"] == total and o["score"]["max"] == 32 and o["score"]["complete"] is True
    assert o["score"]["percent"] == pct and o["score"]["overall_rating"] == rating


def test_each_competency_has_score_mark_and_rating():
    o = outcome_of(submit((4, 3, 2, 1, 0, 4, 3, 2)))
    cards = {c["id"]: c for c in o["competencies"]}
    assert [cards[c]["mark_percent"] for c in C_IDS] == [100, 75, 50, 25, 0, 100, 75, 50]
    assert [cards[c]["rating"] for c in C_IDS] == ["Highly demonstrated", "Demonstrated", "Partially demonstrated", "Limited",
                                                     "No evidence / critical concern", "Highly demonstrated", "Demonstrated", "Partially demonstrated"]
    assert cards["C1"]["name"] == "Concept accuracy" and cards["C3"]["name"] == "Safety and inclusion"
    assert cards["C3"]["rationale"] == "evidence C3" and cards["C3"]["coaching"] == "coaching C3"
    assert cards["C1"]["coaching"] == ""                              # no coaching line for a 4


# --------------------------------------------------------------------------------------------- the recommendation rules
@pytest.mark.parametrize("scores,expected", [
    ((4,) * 8, HIGHLY),
    ((3, 4, 3, 4, 4, 4, 4, 2), HIGHLY),         # exactly 87.5% with C1 and C3 at 75%
    ((3, 3, 3, 3, 3, 3, 3, 3), REC),           # exactly 75%
    ((4, 4, 4, 4, 4, 4, 3, 0), REC),           # 84.4%, a blank-ish 0 elsewhere does not touch the C1/C3 rule
    ((3, 2, 3, 2, 3, 2, 3, 2), COACH),         # 62.5%
    ((2, 4, 4, 4, 4, 4, 4, 2), COACH),         # 87.5% but C1 is 50%: coaching, not recommend
    ((4, 4, 2, 4, 4, 4, 4, 4), COACH),         # 93.8% but C3 is 50%
    ((2,) * 8, COACH),                         # exactly 50%
    ((1, 4, 4, 4, 4, 4, 4, 4), NOT),           # 90.6% but C1 = 1: the stricter rule wins over coaching
    ((4, 4, 0, 4, 4, 4, 4, 4), NOT),           # C3 = 0
    ((2, 2, 2, 2, 2, 2, 2, 1), NOT),           # 46.9%, under 50
])
def test_recommendation_by_the_outcome_forms_thresholds(scores, expected):
    assert outcome_of(submit(scores))["recommendation"] == expected


def test_the_recommendation_function_edges():
    b = backend()
    assert b.recommend(87.5, 3, 3, False) == HIGHLY and b.recommend(87.49, 3, 3, False) == REC
    assert b.recommend(75.0, 3, 3, False) == REC and b.recommend(74.99, 3, 3, False) == COACH
    assert b.recommend(50.0, 2, 2, False) == COACH and b.recommend(49.99, 4, 4, False) == NOT
    assert b.recommend(100.0, 4, 1, False) == NOT and b.recommend(100.0, 0, 4, False) == NOT
    assert b.recommend(100.0, 4, 4, True) == NOT        # a critical concern, whatever the total


def test_a_critical_concern_is_always_zero_forces_not_recommend_and_is_shown():
    o = outcome_of(submit((4, 4, 4, 4, 4, 0, 4, 4), critical=("C6",)))     # the scoring route always sends a critical item as a 0
    c6 = next(c for c in o["competencies"] if c["id"] == "C6")
    assert c6["critical"] is True and c6["score"] == 0
    assert o["critical"] == {"flagged": True, "items": ["C6"]}
    assert o["recommendation"] == NOT and "critical" in o["recommendation_why"].lower()


def test_a_critical_flag_on_a_good_score_is_ignored_only_a_real_zero_counts():
    o = outcome_of(submit((3,) * 8, critical=("C2",)))      # the page sent critical with a 3: not a real 0
    assert o["critical"]["flagged"] is False and o["recommendation"] == REC


def test_a_blank_zero_is_not_a_critical_concern_but_a_zero_in_c1_or_c3_still_means_not_recommend():
    o = outcome_of(submit((0, 4, 4, 4, 4, 4, 4, 4)))        # a blank C1 is a 0, not critical
    assert o["critical"]["flagged"] is False
    assert o["recommendation"] == NOT and "C1" in o["recommendation_why"]


def test_when_an_answer_could_not_be_scored_there_is_no_recommendation_and_no_made_up_mark():
    o = outcome_of(submit((4, 4, None, 4, 4, 4, 4, 4)))
    assert o["score"]["percent"] is None and o["score"]["overall_rating"] is None and o["score"]["complete"] is False
    assert o["recommendation"] is None and o["recommendation_why"] is None
    c3 = next(c for c in o["competencies"] if c["id"] == "C3")
    assert c3["mark_percent"] is None and c3["rating"] is None and "could not be scored" in c3["rationale"]


def test_a_critical_concern_still_forces_not_recommend_when_other_answers_could_not_be_scored():
    o = outcome_of(submit((4, None, 4, 4, 4, 4, 0, 4), critical=("C7",)))
    assert o["recommendation"] == NOT and o["critical"]["items"] == ["C7"]


def test_when_the_scorer_was_off_the_outcome_still_has_something_calm_to_show():
    o = outcome_of(submit(None))
    assert o["score"]["scored"] == 0 and o["recommendation"] is None
    assert o["strengths"] and o["growth"] and o["coaching_plan"]


# --------------------------------------------------------------------------------------------- what the page shows
def test_the_outcome_carries_what_the_form_lists_and_no_evaluator_section():
    o = outcome_of(submit((3,) * 8, name="  Mr   Sample ", school="Demo School"))
    assert o["teacher"] == {"name": "Mr Sample", "school": "Demo School", "date": date.today().isoformat(), "version": "demo-1"}
    for k in ("score", "recommendation", "competencies", "strengths", "growth", "coaching_plan", "guide", "guide_note", "conversion"):
        assert k in o
    assert [g["label"] for g in o["guide"]] == [HIGHLY, REC, COACH, NOT]
    assert "(score ÷ 4) × 100" in o["conversion"] and "(total score ÷ 32) × 100" in o["conversion"]
    blob = json.dumps(o).lower()
    for word in ("evaluator", "signature", "acknowledgement"):
        assert word not in blob


def test_the_ai_summary_is_used_when_valid_and_a_fallback_when_not():
    ai = {"strengths": ["Hears both needs."], "growth": ["Check agreement."], "coaching_plan": ["Use the scaffold."]}
    o = outcome_of(submit((3,) * 8, summary=ai))
    assert o["strengths"] == ["Hears both needs."] and o["growth"] == ["Check agreement."] and o["coaching_plan"] == ["Use the scaffold."]
    bad = outcome_of(submit((4, 4, 4, 4, 1, 4, 4, 4), summary={"strengths": [], "growth": [], "coaching_plan": []}))
    assert any("C1 Concept accuracy" in s for s in bad["strengths"])           # built from the strong competencies
    assert any("C5 Win-Win Agreement teaching" in g for g in bad["growth"])    # the weakest one
    assert any(p.startswith("C5:") for p in bad["coaching_plan"]) and any("Reassess C5" in p for p in bad["coaching_plan"])


def test_a_partial_ai_summary_keeps_its_lists_and_fills_only_the_empty_ones():
    # a strong teacher: the AI names strengths and, rightly, no growth areas or coaching steps
    o = outcome_of(submit((4,) * 8, summary={"strengths": ["Clear and respectful facilitation."], "growth": [], "coaching_plan": []}))
    assert o["strengths"] == ["Clear and respectful facilitation."]
    assert o["growth"] == ["No competency scored below Demonstrated in the answers given."]
    assert o["coaching_plan"] == ["Continue with the usual support; reassess if the programme changes."]


# --------------------------------------------------------------------------------------------- thank-you shows no scores
def test_submit_answers_with_only_an_id_and_no_scores():
    r = submit((4,) * 8)
    assert r.status_code == 200 and set(r.json()) == {"id"} and len(r.json()["id"]) >= 20
    for word in ("score", "percent", "recommend", "rating"):
        assert word not in r.text.lower()


def test_name_and_school_are_required_and_limited():
    assert submit(name="   ").status_code == 422
    assert submit(school="").status_code == 422
    assert submit(name="n" * 61).status_code == 422
    assert submit(school="s" * 81).status_code == 422


# --------------------------------------------------------------------------------------------- single user
def test_only_the_latest_result_exists_a_new_submission_replaces_the_last():
    first = submit((4,) * 8, name="First Teacher")
    first_id = first.json()["id"]
    assert client.get(f"{T}/api/outcome/{first_id}").json()["teacher"]["name"] == "First Teacher"
    second = submit((2,) * 8, name="Second Teacher")
    assert client.get(f"{T}/api/outcome/{first_id}").status_code == 404                 # replaced
    latest = client.get(f"{T}/api/outcome/latest").json()
    assert latest["teacher"]["name"] == "Second Teacher"
    assert client.get(f"{T}/api/outcome/{second.json()['id']}").json() == latest


def test_the_latest_is_a_404_before_anyone_has_submitted_and_bad_ids_are_404():
    b = backend()
    resp = b.outcome_latest()
    assert resp.status_code == 404
    for bad in ("nope", "x" * 16, "../../etc/passwd", "a" * 100, "AAAAAAAAAAAAAAAAAAAAAA"):
        assert client.get(f"{T}/api/outcome/{bad}").status_code == 404


def test_the_answers_and_critical_flags_are_kept_for_a_reviewer_but_not_in_the_outcome_json():
    b = backend()
    body = b.SubmitIn(name="T", school="S", answers={"C3": "shame them in front of the class"},
                      scored=b.ScoredIn(results={"C3": b.Scored(score=0, evidence="e", coaching="c", critical=True)}))
    oid = json.loads(b.submit(body).body)["id"]
    rec = b.private_record(oid)
    assert rec["critical_for_reviewer"] == ["C3"] and rec["answers"]["C3"].startswith("shame them")
    shown = b.outcome(oid).body.decode()
    assert "shame them" not in shown and "answers" not in shown


def test_out_of_range_scores_and_overlong_text_are_refused_or_cut():
    assert submit((9,) * 8).status_code == 422
    r = client.post(f"{T}/api/submit", json={"name": "T", "school": "S", "scored": {"results": {"C1": {"score": 2, "evidence": "e" * 301}}}})
    assert r.status_code == 422
    o = outcome_of(submit((2,) * 8))
    assert o["recommendation"] == COACH


def test_unknown_items_in_what_the_page_sends_are_ignored():
    res = {c: {"score": 3, "evidence": "e"} for c in C_IDS}
    res["C9"] = {"score": 4, "evidence": "e"}
    o = outcome_of(client.post(f"{T}/api/submit", json={"name": "T", "school": "S", "scored": {"results": res}}))
    assert o["score"]["total"] == 24


def test_the_page_scripts_never_write_server_text_as_markup():
    for name in ("app.js", "outcome.js"):
        js = (ROOT / "demos" / "livelife-teacher" / name).read_text(encoding="utf-8")
        assert "innerHTML" not in js and "insertAdjacentHTML" not in js and "document.write" not in js, name
    home = (ROOT / "demos" / "livelife-home" / "index.html").read_text(encoding="utf-8")
    assert "<script" not in home
