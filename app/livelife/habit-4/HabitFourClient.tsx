"use client";

/**
 * Habit 4: Think Win-Win on its own page (/livelife/habit-4), as a glass interface that never scrolls: a top bar,
 * a collapsible section sidebar, the lesson card with its four phases, and a Learning resources column.
 *
 * No sign-in, no points or rank widget, and nothing here is saved. The three lesson
 * sections call no server; only the fourth, the student assessment (Assessment.tsx), talks to the demo service and
 * the demo's AI scorer. The views live in Views.tsx, the activities in Activities.tsx, the look in glass.css, the content in
 * lib/learnContent/habit4.ts and habit4Activities.ts.
 */

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { H4_CHAPTER } from "@/lib/learnContent/habit4";
import { LUMEN_LESSONS } from "@/lib/learn/lumenLessons";
import { EngagementView, UnderstandingView, RetentionView, type Resource } from "./Views";
import AssessmentView from "./Assessment";
import "./glass.css";

type PhaseKey = "think_cards" | "understanding" | "retention";
const PHASES: { key: PhaseKey; emoji: string; name: string; color: string }[] = [
  { key: "think_cards", emoji: "🔦", name: "Engagement", color: "#D97706" },
  { key: "understanding", emoji: "📖", name: "Understanding", color: "#4F46E5" },
  { key: "retention", emoji: "✨", name: "Retention", color: "#059669" },
];
const COLLAPSE_KEY = "lg-h4-sidebar-collapsed";
// The fourth section is the student assessment: it has its own steps instead of the three phases.
const ASSESS = "h4-assessment";

export default function HabitFourClient() {
  const chapter = H4_CHAPTER;
  const [sectionId, setSectionId] = useState(chapter.sections[0].id);
  const [phase, setPhase] = useState<PhaseKey>("think_cards");
  const [resource, setResource] = useState<Resource>("blog");
  const [collapsed, setCollapsed] = useState(false);
  const [visited, setVisited] = useState<Record<string, PhaseKey[]>>({});
  const [z, setZ] = useState(1);
  // The assessment is mounted the first time it is opened and then kept (hidden), so a half-finished attempt
  // survives a look at a lesson and back. It also means the questions are only fetched if someone opens it.
  const [assessOpened, setAssessOpened] = useState(false);

  // The layout is designed for about 1400 x 700. Scale the whole interface to the window, so type, buttons and
  // pictures grow on big screens (and shrink a little on small ones). The glass.css `zoom` reads --z.
  useEffect(() => {
    const fit = () => setZ(Math.max(0.85, Math.min(1.5, Math.min(window.innerWidth / 1366, window.innerHeight / 700))));
    fit();
    window.addEventListener("resize", fit);
    return () => window.removeEventListener("resize", fit);
  }, []);

  // Remember the sidebar choice. Storage can be blocked, so every access is guarded.
  useEffect(() => {
    try { setCollapsed(window.localStorage.getItem(COLLAPSE_KEY) === "1"); } catch { /* ignore */ }
  }, []);
  function toggleSidebar() {
    setCollapsed((c) => {
      try { window.localStorage.setItem(COLLAPSE_KEY, c ? "0" : "1"); } catch { /* ignore */ }
      return !c;
    });
  }

  // A phase counts as visited once it has been opened (only for the dots in the sidebar; nothing is saved).
  useEffect(() => {
    if (sectionId === ASSESS) return;
    setVisited((v) => (v[sectionId]?.includes(phase) ? v : { ...v, [sectionId]: [...(v[sectionId] ?? []), phase] }));
  }, [sectionId, phase]);

  const section = chapter.sections.find((s) => s.id === sectionId) ?? chapter.sections[0];
  const isAssess = sectionId === ASSESS;
  useEffect(() => { if (isAssess) setAssessOpened(true); }, [isAssess]);
  const total = chapter.sections.length;   // the Student assessment is not counted: it is not a lesson section
  const done = chapter.sections.filter((s) => (visited[s.id]?.length ?? 0) === PHASES.length).length;
  const goPhase = (p: PhaseKey) => setPhase(p);
  // The Video tab is a theatre: the panels step aside so the lesson gets the whole window.
  const theatre = !isAssess && phase === "understanding" && resource === "video" && !!LUMEN_LESSONS[section.id];

  return (
    <div className="lg-root" data-phase={isAssess ? "assessment" : phase} data-cinema={theatre} style={{ ["--z" as string]: z }}>
      <div className="lg-bg" aria-hidden="true" />
      <div className="lg-frame">
        <header className="lg-panel lg-top">
          <div className="lg-mark" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="9" /><path d="m15.6 8.4-2.1 5.1-5.1 2.1 2.1-5.1z" /></svg>
          </div>
          <div className="lg-heading">
            <span className="lg-programme">Discovering the Leader in Me</span>
            <h1>Habit 4: Think Win-Win</h1>
          </div>
          <div className="lg-chips" aria-label="About this chapter">
            <span className="lg-chip">Level 5</span>
            <span className="lg-chip">{total} sections</span>
            <span className="lg-chip">{PHASES.length} phases</span>
          </div>
          <div className="lg-tools">
            <button type="button" className="lg-icon-btn" aria-label="Full screen"
              onClick={() => (document.fullscreenElement ? void document.exitFullscreen() : void document.documentElement.requestFullscreen?.())}>
              <svg viewBox="0 0 20 20" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M3.5 7.5v-4h4M16.5 7.5v-4h-4M3.5 12.5v4h4M16.5 12.5v4h-4" /></svg>
            </button>
          </div>
        </header>

        <div className="lg-body">
          <aside className="lg-panel lg-side" data-collapsed={collapsed} aria-label="Sections">
            <div className="lg-side-head">
              <button type="button" className="lg-collapse" aria-pressed={collapsed} aria-label={collapsed ? "Open the section list" : "Collapse the section list"} title={collapsed ? "Open sections" : "Collapse sections"} onClick={toggleSidebar}>
                {collapsed ? "›" : "‹"}
              </button>
            </div>
            <div className="lg-unit">
              <div className="lg-unit-badge" aria-hidden="true">{chapter.emoji}</div>
              <div><h2>Think Win-Win</h2><p>Habit 4 · Level 5</p></div>
            </div>
            <div className="lg-prog" aria-label={`${done} of ${total} sections explored`}>
              <i><b style={{ width: `${(done / total) * 100}%` }} /></i><span>{done}/{total}</span>
            </div>
            <div className="lg-label">Sections</div>
            <div className="lg-secs">
              {chapter.sections.map((s) => (
                <button key={s.id} type="button" className="lg-sec" aria-current={s.id === sectionId} title={s.title}
                  onClick={() => { setSectionId(s.id); setPhase("think_cards"); setResource("blog"); }}>
                  <span className="lg-sec-ic" aria-hidden="true">{s.emoji}</span>
                  <span className="lg-sec-t">
                    <span>{s.title}</span>
                    <span className="lg-dots" aria-hidden="true">
                      {PHASES.map((p) => <i key={p.key} className="lg-dot" style={{ color: p.color }} data-on={!!visited[s.id]?.includes(p.key)} />)}
                    </span>
                  </span>
                </button>
              ))}
              <button type="button" className="lg-sec" aria-current={isAssess} title="Student assessment" onClick={() => setSectionId(ASSESS)}>
                <span className="lg-sec-ic" aria-hidden="true">📝</span>
                <span className="lg-sec-t">
                  <span>Student assessment</span>
                </span>
              </button>
            </div>
            <div className="lg-credit">A Live Life Education programme</div>
          </aside>

          <main className="lg-panel lg-main">
            {assessOpened && <div className="lg-as-host" hidden={!isAssess}><AssessmentView /></div>}
            {!isAssess && (
              <>
                <div className="lg-phases" role="tablist" aria-label="Phases">
                  {PHASES.map((p) => (
                    <button key={p.key} type="button" role="tab" className="lg-phase" aria-selected={phase === p.key} style={{ ["--ph-c" as string]: p.color }} onClick={() => goPhase(p.key)}>
                      {phase === p.key && <motion.span layoutId="lg-phase-pill" className="lg-phase-pill" transition={{ type: "spring", stiffness: 420, damping: 34 }} />}
                      <span><span aria-hidden="true">{p.emoji}</span>{p.name}</span>
                    </button>
                  ))}
                </div>
                {phase === "think_cards" && <EngagementView key={section.id} section={section} onDone={() => { setResource("blog"); goPhase("understanding"); }} />}
                {phase === "understanding" && <UnderstandingView key={section.id} section={section} resource={resource} onResource={setResource} onDone={() => goPhase("retention")} />}
                {phase === "retention" && <RetentionView key={section.id} section={section} />}
              </>
            )}
          </main>

          {isAssess ? null : (
            <aside className="lg-panel lg-right" aria-label="Learning resources">
              <h3><span aria-hidden="true">📚</span> Learning resources</h3>
              <div className="lg-res">
                <button type="button" aria-pressed={phase === "understanding" && resource === "blog"} onClick={() => { setResource("blog"); goPhase("understanding"); }}>
                  <span className="ic" aria-hidden="true">📝</span>Blog
                </button>
                <button type="button" aria-pressed={phase === "understanding" && resource === "video"} onClick={() => { setResource("video"); goPhase("understanding"); }}>
                  <span className="ic" aria-hidden="true">🎬</span>Video
                </button>
              </div>
              <p className="lg-note">Blog is the lesson with its activities. Video plays the lesson as a short interactive video.</p>
            </aside>
          )}
        </div>
      </div>
    </div>
  );
}
