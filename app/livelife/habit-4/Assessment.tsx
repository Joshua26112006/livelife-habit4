"use client";

/**
 * Student assessment: the fourth section of the Habit 4 lesson page, in the same glass UI as the lessons.
 * Flow (the LiveLife student document): name and grade -> Part 1, nine questions, one at a time -> Part 2, eight
 * situations, one at a time -> submit -> a thank-you with NO marks -> the scorecard (three tabs).
 *
 * Nothing is marked here. It uses the demo service as it is: the questions come from `.../api/items` (no answer key),
 * the written answers go to the website's AI scorer `/api/demo-livelife-score` (off unless a person switches it on),
 * the service marks the questions and keeps the latest result (`.../api/submit`, `.../api/outcome/<id>`).
 * What the student types lives in this component only; nothing is saved in the browser.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { Card, Seg } from "./Views";
import { Pic, Headline } from "./Activities";
import AssessmentReport, { REPORT_TABS, type Outcome, type ReportTab } from "./AssessmentReport";

const API = "/demo-livelife/livelife-student/api";
const MAX_ANSWER = 600;
const INTRO_PIC = "/learn-seeds/h4-s3-concept-3.webp";

interface Mcq { id: string; stem: string; options: Record<string, string> }
interface Scenario { id: string; question: string }
interface Items { mcqs: Mcq[]; scenarios: Scenario[]; thank_you: string }
type Stage = "intro" | "ask" | "sending" | "thanks" | "report" | "failed";

export function Arrow({ dir }: { dir: "left" | "right" }) {
  return (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {dir === "left" ? <path d="M12.5 4.5 7 10l5.5 5.5" /> : <path d="M7.5 4.5 13 10l-5.5 5.5" />}
    </svg>
  );
}

/** Back / dots / Next pinned under the screen, exactly as the lessons do it. */
export function Foot({ onBack, onNext, nextLabel = "Next", nextDisabled, n, total }: { onBack?: () => void; onNext: () => void; nextLabel?: string; nextDisabled?: boolean; n?: number; total?: number }) {
  return (
    <div className="lg-foot">
      {onBack ? <button type="button" className="lg-btn" onClick={onBack}><Arrow dir="left" />Back</button> : <span />}
      {n != null && total != null && (
        <div className="lg-steps" aria-label={`Question ${n} of ${total}`}>
          {Array.from({ length: total }, (_, k) => <span key={k} className="lg-step" data-on={k === n - 1} />)}
          <span style={{ marginLeft: 6 }}>{n} of {total}</span>
        </div>
      )}
      <button type="button" className="lg-btn go" onClick={onNext} disabled={nextDisabled}>{nextLabel}<Arrow dir="right" /></button>
    </div>
  );
}

export function Centered({ children }: { children: React.ReactNode }) {
  return <div className="lg-screen"><div className="lg-as-center">{children}</div></div>;
}

export default function AssessmentView() {
  const [items, setItems] = useState<Items | null>(null);
  const [loadFailed, setLoadFailed] = useState(false);
  const [stage, setStage] = useState<Stage>("intro");
  const [i, setI] = useState(0);                       // which question (0..total-1) while stage is "ask"
  const [name, setName] = useState("");
  const [grade, setGrade] = useState("");
  const [mcq, setMcq] = useState<Record<string, string>>({});
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [oid, setOid] = useState("");
  const [outcome, setOutcome] = useState<Outcome | null>(null);
  const [outcomeFailed, setOutcomeFailed] = useState(false);
  const [tab, setTab] = useState<ReportTab>("summary");
  const busy = useRef(false);

  const load = useCallback(() => {
    setLoadFailed(false);
    fetch(`${API}/items`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error("items"))))
      .then((j: Items) => setItems(j))
      .catch(() => setLoadFailed(true));
  }, []);
  useEffect(() => { load(); }, [load]);

  const restart = () => {
    setStage("intro"); setI(0); setName(""); setGrade(""); setMcq({}); setAnswers({});
    setOid(""); setOutcome(null); setOutcomeFailed(false); setTab("summary");
  };

  // The written answers go to the website's scorer as ONE call. Never throws: null means "no scores".
  const scoreAll = async () => {
    try {
      const body: Record<string, string> = {};
      Object.entries(answers).forEach(([k, v]) => { if (v.trim()) body[k] = v; });
      const r = await fetch("/api/demo-livelife-score", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ answers: body }) });
      if (!r.ok) return null;                        // off (404), busy (429) or an error: the scorecard will say they were not scored
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
      const r = await fetch(`${API}/submit`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ class_id: new URLSearchParams(window.location.search).get("class") ?? "", student_id: new URLSearchParams(window.location.search).get("student") ?? "", name, grade, mcq, answers, scored }) });
      if (!r.ok) throw new Error("submit");
      const j = await r.json();
      setOid(j.id);
      setStage("thanks");
    } catch {
      setStage("failed");
    } finally {
      busy.current = false;
    }
  };

  const openScorecard = () => {
    setStage("report"); setOutcome(null); setOutcomeFailed(false); setTab("summary");
    fetch(`${API}/outcome/${encodeURIComponent(oid)}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error("outcome"))))
      .then((o: Outcome) => setOutcome(o))
      .catch(() => setOutcomeFailed(true));
  };

  const pill = "📝 Student assessment";

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
            <><span className="lg-as-spin" aria-hidden="true" /><p className="lg-note">Getting your questions ready…</p></>
          )}
        </Centered>
      </Card>
    );
  }

  const nM = items.mcqs.length;
  const total = nM + items.scenarios.length;

  // ── intro ──
  if (stage === "intro") {
    const ready = name.trim() !== "" && grade.trim() !== "";
    return (
      <Card pill={pill} title="Habit 4: Think Win-Win">
        <div className="lg-screen">
          <div className="lg-split">
            <Pic src={INTRO_PIC} />
            <div className="lg-split-text">
              <span className="lg-kick">Level 5 · Habit 4</span>
              <Headline text="Think *Win-Win*" />
              <p className="lg-p">Part 1 is {nM} quick questions. Part 2 is {items.scenarios.length} real-life situations to answer in your own words. Then you can see your scorecard. Write what you really think: there is no trick, and spelling doesn&apos;t matter.</p>
              <div className="lg-as-form">
                <label className="lg-as-field"><span className="lg-as-label">Your name</span>
                  <input className="lg-input" type="text" maxLength={40} autoComplete="off" value={name} onChange={(e) => setName(e.target.value)} />
                </label>
                <label className="lg-as-field lg-as-grade"><span className="lg-as-label">Your grade</span>
                  <input className="lg-input" type="text" maxLength={12} autoComplete="off" placeholder="e.g. 8" value={grade} onChange={(e) => setGrade(e.target.value)} />
                </label>
              </div>
              <p className="lg-hint">Demo: please use made-up details, not your real name or school.</p>
            </div>
          </div>
        </div>
        <Foot onNext={() => { setI(0); setStage("ask"); }} nextLabel="Start" nextDisabled={!ready} />
      </Card>
    );
  }

  // ── Part 1 and Part 2, one at a time ──
  if (stage === "ask") {
    const isMcq = i < nM;
    const q = isMcq ? items.mcqs[i] : null;
    const s = isMcq ? null : items.scenarios[i - nM];
    const last = i === total - 1;
    const answered = isMcq ? !!mcq[q!.id] : true;    // a situation may be left blank: it then counts as no answer
    const text = s ? answers[s.id] ?? "" : "";
    return (
      <Card pill={pill} title={isMcq ? "Part 1 · Knowledge check" : "Part 2 · Situations"}>
        <motion.div className="lg-screen" key={i} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }}>
          <div className="lg-as-q">
            <p className="lg-eyebrow">{isMcq ? `Question ${i + 1} of ${nM}` : `Situation ${i - nM + 1} of ${items.scenarios.length}`}</p>
            {q && (
              <>
                <p className="lg-as-ask">{q.stem}</p>
                <div className="lg-as-opts" role="radiogroup" aria-label={q.stem}>
                  {Object.keys(q.options).map((letter) => (
                    <button key={letter} type="button" role="radio" aria-checked={mcq[q.id] === letter} className="lg-opt"
                      data-state={mcq[q.id] === letter ? "picked" : undefined} onClick={() => setMcq((m) => ({ ...m, [q.id]: letter }))}>
                      <span className="ltr">{letter}</span>{q.options[letter]}
                    </button>
                  ))}
                </div>
              </>
            )}
            {s && (
              <>
                <p className="lg-as-ask lg-as-scn">{s.question}</p>
                <textarea className="lg-area" maxLength={MAX_ANSWER} placeholder="Write your answer here…" aria-label="Your answer" value={text}
                  onChange={(e) => setAnswers((a) => ({ ...a, [s.id]: e.target.value }))} />
                <div className="lg-as-count"><span className="lg-hint">A short answer is fine. If you leave it blank it can&apos;t be scored.</span><span className="lg-hint">{text.length} / {MAX_ANSWER}</span></div>
              </>
            )}
          </div>
        </motion.div>
        <Foot onBack={() => (i === 0 ? setStage("intro") : setI(i - 1))} onNext={() => (last ? void submit() : setI(i + 1))}
          nextLabel={last ? "Submit" : "Next"} nextDisabled={!answered} n={i + 1} total={total} />
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
        <Foot onBack={() => { setI(total - 1); setStage("ask"); }} onNext={() => void submit()} nextLabel="Try again" />
      </Card>
    );
  }

  if (stage === "thanks") {
    return (
      <Card pill={pill} title="Thank you">
        <Centered>
          <span style={{ fontSize: 56 }} aria-hidden="true">🎉</span>
          <h3 className="lg-as-h">{items.thank_you}</h3>
          <p className="lg-note">Your scorecard is ready.</p>
        </Centered>
        <div className="lg-foot">
          <button type="button" className="lg-btn" onClick={restart}>Start again</button>
          <button type="button" className="lg-btn go" onClick={openScorecard}>View my scorecard<Arrow dir="right" /></button>
        </div>
      </Card>
    );
  }

  // ── scorecard ──
  return (
    <Card pill={pill} title="Your scorecard"
      tools={outcome ? <Seg id="as-tab" label="Scorecard sections" options={REPORT_TABS} value={tab} onChange={setTab} /> : undefined}>
      {outcome ? (
        <>
          <AssessmentReport o={outcome} tab={tab} />
          <div className="lg-foot">
            <button type="button" className="lg-btn" onClick={restart}>Start again</button>
            <span className="lg-hint">Demo: only the latest result is kept.</span>
          </div>
        </>
      ) : (
        <>
          <Centered>
            {outcomeFailed ? (
              <>
                <h3 className="lg-as-h">We can&apos;t find this scorecard</h3>
                <p className="lg-note">A newer assessment may have replaced it (this demo keeps only the latest result), or the demo was restarted. Please take the assessment again.</p>
              </>
            ) : (
              <><span className="lg-as-spin" aria-hidden="true" /><p className="lg-note">Getting your scorecard…</p></>
            )}
          </Centered>
          {outcomeFailed && <div className="lg-foot"><span /><button type="button" className="lg-btn go" onClick={restart}>Take the assessment</button></div>}
        </>
      )}
    </Card>
  );
}
