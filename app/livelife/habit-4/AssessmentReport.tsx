"use client";

/**
 * The student's scorecard, drawn in the lesson page's glass style. All the numbers are worked out by the demo service
 * (`/demo-livelife/livelife-student/api/outcome/<id>`); this file only draws them. Text from the server or from a model
 * is only ever rendered as text (React escapes it), never as markup. Three tabs keep every screen inside the card:
 * Summary, Competencies (a list with one competency opened at a time) and Next steps.
 */

import { useState } from "react";

export interface Outcome {
  student: { name: string; grade: string; date: string };
  overall: { score: number | null; max: number; raw: number | null; raw_max: number; rating: string | null; complete: boolean };
  knowledge: { score: number; max: number; correct: number; of: number; percent: number | null };
  situational: { score: number; max: number; scored: number; of: number; percent: number | null };
  competencies: { id: string; name: string; mark_percent: number | null; rating: string | null; note: string }[];
  strengths: string[];
  skills: string[];
  try_next: string;
  teacher_support: string;
  rating_guide: string;
}

export type ReportTab = "summary" | "competencies" | "next";

export const REPORT_TABS: readonly { id: ReportTab; label: string }[] = [
  { id: "summary", label: "Summary" },
  { id: "competencies", label: "Competencies" },
  { id: "next", label: "Next steps" },
];

const pct = (v: number | null) => (v == null ? "—" : `${v}%`);

function Tile({ label, main, sub }: { label: string; main: string; sub?: string }) {
  return (
    <div className="lg-as-tile">
      <span className="lg-as-tile-l">{label}</span>
      <b>{main}</b>
      {sub && <span className="lg-as-tile-s">{sub}</span>}
    </div>
  );
}

function Summary({ o }: { o: Outcome }) {
  const { overall: all, knowledge: k, situational: s } = o;
  return (
    <div className="lg-as-sum">
      <div className="lg-as-hero">
        <span className="lg-kick">Your Think Win-Win scorecard</span>
        <h3 className="lg-as-name">{o.student.name}</h3>
        <p className="lg-as-who">Grade {o.student.grade} · {o.student.date}</p>
        <span className="lg-as-label">Final score</span>
        <div className="lg-as-big">{all.score == null ? "—" : all.score}<small> / {all.max}</small></div>
        <span className="lg-as-badge" data-r={all.rating ?? "none"}>{all.rating ?? "Rating not available"}</span>
        {!all.complete && (
          <p className="lg-note" style={{ marginTop: 8 }}>
            Some of your written answers could not be scored, so there is no overall rating yet. Your teacher can look at them with you.
          </p>
        )}
      </div>
      <div className="lg-as-tiles">
        <Tile label="Knowledge Check" main={`${k.score} / ${k.max}`} sub={`${k.correct} of ${k.of} correct`} />
        <Tile
          label="Situational Check"
          main={`${s.score} / ${s.max}`}
          sub={s.percent == null ? "not scored" : `${pct(s.percent)}${s.scored < s.of ? ` (${s.scored} of ${s.of} scored)` : ""}`}
        />
        <Tile
          label="Total score"
          main={all.score == null ? "—" : `${all.score} / ${all.max}`}
          sub={all.raw == null ? "needs every situation scored" : `${all.raw} of ${all.raw_max} marks, out of 100`}
        />
      </div>
      <p className="lg-note lg-as-guide">{o.rating_guide}</p>
    </div>
  );
}

function Competencies({ o }: { o: Outcome }) {
  const [open, setOpen] = useState(0);
  const c = o.competencies[Math.min(open, o.competencies.length - 1)];
  return (
    <div className="lg-as-comp">
      <div className="lg-as-list" role="group" aria-label="Competencies">
        {o.competencies.map((x, i) => (
          <button key={x.id} type="button" className="lg-as-row" aria-pressed={i === open} onClick={() => setOpen(i)}>
            <span className="lg-as-row-n">{x.name}</span>
            <span className="lg-as-bar" aria-hidden="true"><i style={{ width: `${x.mark_percent ?? 0}%` }} /></span>
            <span className="lg-as-row-p">{pct(x.mark_percent)}</span>
          </button>
        ))}
      </div>
      {c && (
        <div className="lg-as-detail">
          <p className="lg-eyebrow">{c.id}</p>
          <h3 className="lg-as-dh">{c.name}</h3>
          <div className="lg-as-dline">
            <span className="lg-as-badge" data-r={c.rating ?? "none"}>{c.rating ?? "Not scored"}</span>
            <b>{pct(c.mark_percent)}</b>
          </div>
          <p className="lg-p lg-as-dnote">{c.note}</p>
        </div>
      )}
    </div>
  );
}

function NextSteps({ o }: { o: Outcome }) {
  return (
    <div className="lg-as-next">
      <section className="lg-as-box"><h4>Strengths</h4><ul className="lg-ul">{o.strengths.map((t, i) => <li key={i}>{t}</li>)}</ul></section>
      <section className="lg-as-box"><h4>Skills to practise</h4><ul className="lg-ul">{o.skills.map((t, i) => <li key={i}>{t}</li>)}</ul></section>
      <section className="lg-as-box"><h4>Try this next</h4><p className="lg-p">{o.try_next}</p></section>
      <section className="lg-as-box"><h4>Teacher support</h4><p className="lg-p">{o.teacher_support}</p></section>
    </div>
  );
}

export default function AssessmentReport({ o, tab }: { o: Outcome; tab: ReportTab }) {
  return (
    <div className="lg-screen" key={tab}>
      {tab === "summary" && <Summary o={o} />}
      {tab === "competencies" && <Competencies o={o} />}
      {tab === "next" && <NextSteps o={o} />}
    </div>
  );
}
