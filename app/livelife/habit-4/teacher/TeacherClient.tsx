"use client";

/**
 * Habit 4 teacher assessment on its own page (/livelife/habit-4/teacher): the same glass shell as the student lesson
 * page (background, top bar, collapsible sidebar, glass card) with two sidebar items of its own, "Assessment" and
 * "Latest outcome". The page never scrolls (the eight situations scroll inside the card).
 *
 * Like the student assessment it marks nothing itself: it uses the teacher demo's API and the demo scorer (see
 * TeacherAssessment.tsx). Public, no sign-in, nothing saved in the browser. `?view=outcome` opens the latest outcome
 * directly (the coach page's "Assessment outcome" button).
 */

import { useEffect, useState } from "react";
import TeacherAssessment from "./TeacherAssessment";
import TeacherOutcome from "./TeacherOutcome";
import "../glass.css";

type View = "assess" | "outcome";

export default function TeacherClient() {
  const [view, setView] = useState<View>("assess");
  const [collapsed, setCollapsed] = useState(false);
  const [z, setZ] = useState(1);
  const [refresh, setRefresh] = useState(0);              // bumped each time the outcome view is opened, so it reloads
  const [outcomeOpened, setOutcomeOpened] = useState(false);

  // Same scaling as the lesson page: designed for about 1400 x 700, scaled to the window (glass.css `zoom` reads --z).
  useEffect(() => {
    const fit = () => setZ(Math.max(0.85, Math.min(1.5, Math.min(window.innerWidth / 1366, window.innerHeight / 700))));
    fit();
    window.addEventListener("resize", fit);
    return () => window.removeEventListener("resize", fit);
  }, []);

  const open = (v: View) => {
    if (v === "outcome") { setOutcomeOpened(true); setRefresh((r) => r + 1); }
    setView(v);
  };

  // The coach page's "Assessment outcome" button opens this page with ?view=outcome.
  useEffect(() => {
    if (new URLSearchParams(window.location.search).get("view") === "outcome") open("outcome");
  }, []);

  return (
    <div className="lg-root" data-phase="assessment" style={{ ["--z" as string]: z }}>
      <div className="lg-bg" aria-hidden="true" />
      <div className="lg-frame">
        <header className="lg-panel lg-top">
          <div className="lg-mark" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="9" /><path d="m15.6 8.4-2.1 5.1-5.1 2.1 2.1-5.1z" /></svg>
          </div>
          <div className="lg-heading">
            <span className="lg-programme">Discovering the Leader in Me</span>
            <h1>Habit 4: Teacher assessment</h1>
          </div>
          <div className="lg-chips" aria-label="About this assessment">
            <span className="lg-chip">Level 5</span>
            <span className="lg-chip">8 situations</span>
          </div>
          <div className="lg-tools">
            <a className="lg-icon-btn" href="/demo-livelife/choices/" style={{ textDecoration: "none" }}>Home</a>
            <button type="button" className="lg-icon-btn" aria-label="Full screen"
              onClick={() => (document.fullscreenElement ? void document.exitFullscreen() : void document.documentElement.requestFullscreen?.())}>
              <svg viewBox="0 0 20 20" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M3.5 7.5v-4h4M16.5 7.5v-4h-4M3.5 12.5v4h4M16.5 12.5v4h-4" /></svg>
            </button>
          </div>
        </header>

        <div className="lg-body">
          <aside className="lg-panel lg-side" data-collapsed={collapsed} aria-label="Sections">
            <div className="lg-side-head">
              <button type="button" className="lg-collapse" aria-pressed={collapsed} aria-label={collapsed ? "Open the section list" : "Collapse the section list"} title={collapsed ? "Open sections" : "Collapse sections"} onClick={() => setCollapsed((c) => !c)}>
                {collapsed ? "›" : "‹"}
              </button>
            </div>
            <div className="lg-unit">
              <div className="lg-unit-badge" aria-hidden="true">🧑‍🏫</div>
              <div><h2>Teacher assessment</h2><p>Habit 4 · Level 5</p></div>
            </div>
            <div className="lg-label">Sections</div>
            <div className="lg-secs">
              <button type="button" className="lg-sec" aria-current={view === "assess"} title="Assessment" onClick={() => open("assess")}>
                <span className="lg-sec-ic" aria-hidden="true">📝</span>
                <span className="lg-sec-t"><span>Assessment</span></span>
              </button>
              <button type="button" className="lg-sec" aria-current={view === "outcome"} title="Latest outcome" onClick={() => open("outcome")}>
                <span className="lg-sec-ic" aria-hidden="true">📊</span>
                <span className="lg-sec-t"><span>Latest outcome</span></span>
              </button>
            </div>
            <div className="lg-credit">A Live Life Education programme</div>
          </aside>

          <main className="lg-panel lg-main">
            <div className="lg-as-host" hidden={view !== "assess"}><TeacherAssessment onViewOutcome={() => open("outcome")} /></div>
            {outcomeOpened && <div className="lg-as-host" hidden={view !== "outcome"}><TeacherOutcome refresh={refresh} onTake={() => open("assess")} /></div>}
          </main>
        </div>
      </div>
    </div>
  );
}
