"use client";

/**
 * Teacher assessment, in the lesson page's glass UI. Flow (the LiveLife Section 9 document): name or ID and school ->
 * all eight situations on ONE scrolling screen -> submit -> a thank-you with NO scores -> the outcome (a separate view).
 *
 * Nothing is marked here. It uses the teacher demo as it is: the questions come from `.../api/items` (no rubric), the
 * written answers go to the website's AI scorer (`kind: "teacher"`, off unless a person switches it on), and the
 * service works out the score, the rating and the recommendation and keeps the latest result (`.../api/submit`).
 * What the teacher types lives in this component only; nothing is saved in the browser.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { Card } from "../Views";
import { Pic, Headline } from "../Activities";
import { Arrow, Centered, Foot } from "../Assessment";

const API = "/demo-livelife/livelife-teacher/api";
const MAX_ANSWER = 800;
const INTRO_PIC = "/learn-seeds/h4-s1-think-2.webp";

interface Question { id: string; question: string }
interface Items { questions: Question[]; thank_you: string }
type Stage = "intro" | "form" | "sending" | "thanks" | "failed";

export default function TeacherAssessment({ onViewOutcome }: { onViewOutcome: () => void }) {
  const [items, setItems] = useState<Items | null>(null);
  const [loadFailed, setLoadFailed] = useState(false);
  const [stage, setStage] = useState<Stage>("intro");
  const [name, setName] = useState("");
  const [school, setSchool] = useState("");
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const busy = useRef(false);

  const load = useCallback(() => {
    setLoadFailed(false);
    fetch(`${API}/items`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error("items"))))
      .then((j: Items) => setItems(j))
      .catch(() => setLoadFailed(true));
  }, []);
  useEffect(() => { load(); }, [load]);

  const restart = () => { setStage("intro"); setName(""); setSchool(""); setAnswers({}); };

  // The eight answers go to the website's scorer as ONE call, as kind "teacher". Never throws: null means "no scores".
  const scoreAll = async () => {
    try {
      const body: Record<string, string> = {};
      Object.entries(answers).forEach(([k, v]) => { if (v.trim()) body[k] = v; });
      const r = await fetch("/api/demo-livelife-score", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ kind: "teacher", answers: body }) });
      if (!r.ok) return null;                        // off (404), busy (429) or an error: the outcome will say they were not scored
      const j = await r.json();
      return j && j.ok ? { results: j.results, summary: j.summary || null } : null;
    } catch { return null; }
  };

  const submit = async () => {
    if (busy.current) return;
    busy.current = true;
    setStage("sending");
    try {
      const scored = await scoreAll();
      const r = await fetch(`${API}/submit`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name, school, answers, scored }) });
      if (!r.ok) throw new Error("submit");
      setStage("thanks");
    } catch {
      setStage("failed");
    } finally {
      busy.current = false;
    }
  };

  const pill = "🧑‍🏫 Teacher assessment";

  if (!items) {
    return (
      <Card pill={pill} title="Habit 4: Think Win-Win">
        <Centered>
          {loadFailed ? (
            <>
              <h3 className="lg-as-h">This assessment can&apos;t start right now</h3>
              <p className="lg-note">Please try again in a moment.</p>
              <button type="button" className="lg-btn go" onClick={load}>Try again</button>
            </>
          ) : (
            <><span className="lg-as-spin" aria-hidden="true" /><p className="lg-note">Getting the situations ready…</p></>
          )}
        </Centered>
      </Card>
    );
  }

  const qs = items.questions;
  const filled = qs.filter((q) => (answers[q.id] ?? "").trim() !== "").length;

  if (stage === "intro") {
    const ready = name.trim() !== "" && school.trim() !== "";
    return (
      <Card pill={pill} title="Habit 4: Think Win-Win">
        <div className="lg-screen">
          <div className="lg-split">
            <Pic src={INTRO_PIC} />
            <div className="lg-split-text">
              <span className="lg-kick">Level 5 · Habit 4</span>
              <Headline text="Teacher *assessment*" />
              <p className="lg-p">{qs.length} short situations from a Habit 4 lesson. Answer each in a few sentences: say what you would actually do or say. This checks how ready you are to facilitate Habit 4 accurately and inclusively. There is no word count and no marks for grammar.</p>
              <div className="lg-as-form">
                <label className="lg-as-field"><span className="lg-as-label">Your name or ID</span>
                  <input className="lg-input" type="text" maxLength={60} autoComplete="off" value={name} onChange={(e) => setName(e.target.value)} />
                </label>
                <label className="lg-as-field"><span className="lg-as-label">Your school</span>
                  <input className="lg-input" type="text" maxLength={80} autoComplete="off" value={school} onChange={(e) => setSchool(e.target.value)} />
                </label>
              </div>
              <p className="lg-hint">Demo: please use made-up details, not your real name or school.</p>
            </div>
          </div>
        </div>
        <Foot onNext={() => setStage("form")} nextLabel="Start" nextDisabled={!ready} />
      </Card>
    );
  }

  if (stage === "form") {
    return (
      <Card pill={pill} title="Situations">
        <div className="lg-screen">
          <div className="lg-as-tform">
            {qs.map((q, i) => (
              <div key={q.id} className="lg-as-tq">
                <p className="lg-eyebrow">Situation {i + 1} of {qs.length}</p>
                <p className="lg-as-ask lg-as-scn" id={`tq-${q.id}`}>{q.question}</p>
                <textarea className="lg-area" maxLength={MAX_ANSWER} placeholder="Write what you would do or say…" aria-labelledby={`tq-${q.id}`}
                  value={answers[q.id] ?? ""} onChange={(e) => setAnswers((a) => ({ ...a, [q.id]: e.target.value }))} />
                <span className="lg-hint lg-as-tcount">{(answers[q.id] ?? "").length} / {MAX_ANSWER}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="lg-foot">
          <button type="button" className="lg-btn" onClick={() => setStage("intro")}><Arrow dir="left" />Back</button>
          <span className="lg-hint">{filled} of {qs.length} answered{filled < qs.length ? " (a blank one counts as no answer)" : ""}</span>
          <button type="button" className="lg-btn go" onClick={() => void submit()}>Submit<Arrow dir="right" /></button>
        </div>
      </Card>
    );
  }

  if (stage === "sending") {
    return (
      <Card pill={pill} title="Submitting">
        <Centered>
          <span className="lg-as-spin" aria-hidden="true" />
          <h3 className="lg-as-h">Submitting your answers…</h3>
          <p className="lg-note">This can take a few seconds. Please don&apos;t leave this page.</p>
        </Centered>
      </Card>
    );
  }

  if (stage === "failed") {
    return (
      <Card pill={pill} title="Submitting">
        <Centered>
          <span style={{ fontSize: 48 }} aria-hidden="true">😕</span>
          <h3 className="lg-as-h">We couldn&apos;t submit just now</h3>
          <p className="lg-note">Your answers are still here. Please try again.</p>
        </Centered>
        <Foot onBack={() => setStage("form")} onNext={() => void submit()} nextLabel="Try again" />
      </Card>
    );
  }

  return (
    <Card pill={pill} title="Thank you">
      <Centered>
        <span style={{ fontSize: 56 }} aria-hidden="true">🎉</span>
        <h3 className="lg-as-h">{items.thank_you}</h3>
        <p className="lg-note">The outcome is ready.</p>
      </Centered>
      <div className="lg-foot">
        <button type="button" className="lg-btn" onClick={restart}>Start again</button>
        <button type="button" className="lg-btn go" onClick={onViewOutcome}>View the outcome<Arrow dir="right" /></button>
      </div>
    </Card>
  );
}
