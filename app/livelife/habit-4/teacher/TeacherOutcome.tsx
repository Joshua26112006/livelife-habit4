"use client";

/**
 * The Teacher Assessment Outcome, drawn in the lesson page's glass style. Everything shown is worked out by the demo
 * service (`/demo-livelife/livelife-teacher/api/outcome/latest`): the score, the rating, the recommendation and the
 * critical-concern flag. This file only draws it. Text from the server or from a model is only ever rendered as text
 * (React escapes it), never as markup. Three tabs keep every screen inside the card.
 */

import { useEffect, useState } from "react";
import { Card, Seg } from "../Views";
import { Centered, Foot } from "../Assessment";

export interface TeacherOutcomeData {
  teacher: { name: string; school: string; date: string; version: string };
  score: { total: number; max: number; scored: number; of: number; percent: number | null; overall_rating: string | null; complete: boolean };
  recommendation: string | null;
  recommendation_why: string | null;
  critical: { flagged: boolean; items: string[] };
  competencies: { id: string; name: string; score: number | null; mark_percent: number | null; rating: string | null; rationale: string; coaching: string; critical: boolean }[];
  strengths: string[];
  growth: string[];
  coaching_plan: string[];
  guide_note: string;
  guide: { label: string; rule: string }[];
  conversion: string;
}

type Tab = "summary" | "competencies" | "plan";
const TABS: readonly { id: Tab; label: string }[] = [
  { id: "summary", label: "Summary" },
  { id: "competencies", label: "Competencies" },
  { id: "plan", label: "Coaching plan" },
];

const pct = (v: number | null) => (v == null ? "—" : `${v}%`);

function Summary({ o }: { o: TeacherOutcomeData }) {
  const s = o.score;
  return (
    <div className="lg-as-tsum">
      {o.critical.flagged && (
        <div className="lg-as-alert" role="alert">
          Critical safety or inclusion concern flagged for review ({o.critical.items.join(", ")}). Coaching and reassessment are required whatever the total score.
        </div>
      )}
      <div className="lg-as-tgrid">
        <div className="lg-as-hero">
          <span className="lg-kick">Teacher assessment outcome</span>
          <h3 className="lg-as-name">{o.teacher.name}</h3>
          <p className="lg-as-who">{o.teacher.school} · {o.teacher.date}</p>
          <span className="lg-as-label">Overall performance</span>
          <div className="lg-as-big">{s.percent == null ? "—" : s.percent}<small>{s.percent == null ? "" : " %"}</small></div>
          <span className="lg-as-badge" data-r={s.overall_rating ?? "none"}>{s.overall_rating ?? "Rating not available"}</span>
          <p className="lg-note" style={{ marginTop: 8 }}>
            Score {s.total} / {s.max}{s.complete ? "" : ` · ${s.scored} of ${s.of} scored`}
          </p>
        </div>
        <div className="lg-as-reco">
          <h4>Recommendation</h4>
          <div className="lg-as-reco-list">
            {o.guide.map((g) => {
              const on = o.recommendation === g.label;
              return (
                <div key={g.label} className="lg-as-reco-item" data-on={on}>
                  <span className="lg-as-box-tick" aria-hidden="true">{on ? "✓" : ""}</span>
                  <div><b>{g.label}</b><span>{g.rule}</span></div>
                </div>
              );
            })}
          </div>
          <p className="lg-note">
            {o.recommendation_why ?? "No recommendation yet: some responses could not be scored, so the thresholds can't be applied."}
          </p>
        </div>
      </div>
    </div>
  );
}

function Competencies({ o }: { o: TeacherOutcomeData }) {
  const [open, setOpen] = useState(0);
  const c = o.competencies[Math.min(open, o.competencies.length - 1)];
  return (
    <div className="lg-as-comp">
      <div className="lg-as-list" role="group" aria-label="Competencies">
        {o.competencies.map((x, i) => (
          <button key={x.id} type="button" className="lg-as-row" aria-pressed={i === open} onClick={() => setOpen(i)}>
            <span className="lg-as-row-n">{x.name}</span>
            <span className="lg-as-bar" aria-hidden="true"><i style={{ width: `${x.mark_percent ?? 0}%` }} /></span>
            <span className="lg-as-row-p">{x.score == null ? "—" : `${x.score}/4`}</span>
          </button>
        ))}
      </div>
      {c && (
        <div className="lg-as-detail">
          <p className="lg-eyebrow">{c.id}</p>
          <h3 className="lg-as-dh">{c.name}</h3>
          <div className="lg-as-dline">
            <span className="lg-as-badge" data-r={c.rating ?? "none"}>{c.rating ?? "Not scored"}</span>
            <b>{c.score == null ? "—" : `${c.score} / 4`}</b>
            <span className="lg-as-who" style={{ margin: 0 }}>{pct(c.mark_percent)}</span>
          </div>
          <p className="lg-p lg-as-dnote">{c.rationale}</p>
          {c.coaching && <p className="lg-fb"><strong>Coaching: </strong>{c.coaching}</p>}
          {c.critical && <p className="lg-as-alert" role="alert">Critical concern: flagged for review.</p>}
        </div>
      )}
    </div>
  );
}

function Plan({ o }: { o: TeacherOutcomeData }) {
  return (
    <div className="lg-as-next lg-as-next3">
      <section className="lg-as-box"><h4>Strengths evidenced</h4><ul className="lg-ul">{o.strengths.map((t, i) => <li key={i}>{t}</li>)}</ul></section>
      <section className="lg-as-box"><h4>Priority growth areas</h4><ul className="lg-ul">{o.growth.map((t, i) => <li key={i}>{t}</li>)}</ul></section>
      <section className="lg-as-box"><h4>Coaching and reassessment plan</h4><ul className="lg-ul">{o.coaching_plan.map((t, i) => <li key={i}>{t}</li>)}</ul></section>
    </div>
  );
}

/** Loads the latest teacher outcome each time `refresh` changes (the page opens this view, or a new one was submitted). */
export default function TeacherOutcome({ refresh, onTake }: { refresh: number; onTake: () => void }) {
  const [o, setO] = useState<TeacherOutcomeData | null>(null);
  const [state, setState] = useState<"loading" | "none" | "ready">("loading");
  const [tab, setTab] = useState<Tab>("summary");

  useEffect(() => {
    let live = true;
    setState("loading"); setTab("summary");
    fetch("/demo-livelife/livelife-teacher/api/outcome/latest", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error("none"))))
      .then((j: TeacherOutcomeData) => { if (live) { setO(j); setState("ready"); } })
      .catch(() => { if (live) { setO(null); setState("none"); } });
    return () => { live = false; };
  }, [refresh]);

  const pill = "📊 Assessment outcome";
  if (state !== "ready" || !o) {
    return (
      <Card pill={pill} title="Latest outcome">
        <Centered>
          {state === "loading" ? (
            <><span className="lg-as-spin" aria-hidden="true" /><p className="lg-note">Getting the latest outcome…</p></>
          ) : (
            <>
              <span style={{ fontSize: 48 }} aria-hidden="true">📭</span>
              <h3 className="lg-as-h">No teacher assessment has been submitted yet</h3>
              <p className="lg-note">When a teacher completes the assessment, the outcome appears here. This demo keeps only the latest result.</p>
            </>
          )}
        </Centered>
        {state === "none" && <Foot onNext={onTake} nextLabel="Take the assessment" />}
      </Card>
    );
  }
  return (
    <Card pill={pill} title="Teacher assessment outcome" tools={<Seg id="t-tab" label="Outcome sections" options={TABS} value={tab} onChange={setTab} />}>
      <div className="lg-screen" key={tab}>
        {tab === "summary" && <Summary o={o} />}
        {tab === "competencies" && <Competencies o={o} />}
        {tab === "plan" && <Plan o={o} />}
      </div>
      <div className="lg-foot">
        <span className="lg-hint">{o.conversion}</span>
        <span className="lg-hint">Demo: only the latest result is kept.</span>
      </div>
    </Card>
  );
}
