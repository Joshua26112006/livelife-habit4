"use client";

/**
 * The four phase views of the Habit 4 page. Each one fits the window with no page scroll: one card, one screen or one
 * question at a time, with the controls pinned under it. Nothing is saved or scored and nothing calls the server.
 */

import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { motion } from "framer-motion";
import type { LearnSection, SeededThinkCard, IdentifyQuestion, MasteryQuestion } from "@/lib/learnTypes";
import { LUMEN_LESSONS } from "@/lib/learn/lumenLessons";
import { H4_STORY, H4_SORT, H4_IDENTIFY, H4_MASTERY, H4_RETENTION } from "@/lib/learnContent/habit4";
import { H4_BRANCH } from "@/lib/learnContent/habit4Activities";
import VideoView from "@/components/learn/concept/VideoView";
import { Pic, Stepper, StoryScreen, BranchStory, SeesawSliders, BankAccount, SortActivity, AgreementBuilder, type Step } from "./Activities";

export type Resource = "blog" | "video";

/** A segmented switch whose glass pill slides to the chosen option. */
export function Seg<T extends string>({ id, label, options, value, onChange, className }: { id: string; label: string; options: readonly { id: T; label: string }[]; value: T; onChange: (v: T) => void; className?: string }) {
  return (
    <div className={`lg-seg ${className ?? ""}`} role="group" aria-label={label}>
      {options.map((o) => (
        <button key={o.id} type="button" aria-pressed={value === o.id} onClick={() => onChange(o.id)}>
          {value === o.id && <motion.span layoutId={`lg-seg-${id}`} className="lg-seg-pill" transition={{ type: "spring", stiffness: 460, damping: 36 }} />}
          <span>{o.label}</span>
        </button>
      ))}
    </div>
  );
}

/** The lesson card every phase sits in: a pill, the section title and optional tools, then the screen. */
export function Card({ pill, title, tools, children }: { pill: string; title: string; tools?: ReactNode; children: ReactNode }) {
  return (
    <section className="lg-card">
      <div className="lg-card-head">
        <span className="lg-pill">{pill}</span>
        <h2 className="lg-card-title">{title}</h2>
        {tools}
      </div>
      {children}
    </section>
  );
}

// ─── Engagement: one think card at a time ─────────────────────────────────────

function ThinkCard({ card }: { card: SeededThinkCard }) {
  const [picked, setPicked] = useState<number | null>(null);
  return (
    <div className="lg-two">
      <Pic src={card.imageUrl} />
      <div className="lg-col" style={{ justifyContent: "center" }}>
        <p className="lg-eyebrow">{card.eyebrow ?? "🤔 Think about it…"}</p>
        <p className="lg-ask">{card.question}</p>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {card.options.map((o, i) => (
            <button key={i} type="button" className="lg-opt" data-state={picked === i ? "picked" : undefined} onClick={() => setPicked(i)}>
              <span className="ltr">{"ABC"[i]}</span>{o.text}
            </button>
          ))}
        </div>
        {picked !== null
          ? <motion.p key={picked} className="lg-fb" initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}>{card.options[picked].hook}</motion.p>
          : <p className="lg-hint" style={{ margin: 0 }}>Pick the answer that feels right to you.</p>}
      </div>
    </div>
  );
}

export function EngagementView({ section, onDone }: { section: LearnSection; onDone: () => void }) {
  const steps: Step[] = useMemo(() => (section.thinkCards ?? []).map((c, i) => ({ title: `Card ${i + 1}`, node: <ThinkCard key={i} card={c} /> })), [section]);
  return (
    <Card pill="🔦 Engagement" title={section.title}>
      <Stepper key={section.id} steps={steps} onDone={onDone} doneLabel="On to Understanding" />
    </Card>
  );
}

// ─── Understanding: the story screens, the concept check, think it through, and the video ─────

// What goes where in the story. "story:<title>" is a story screen, the rest are activities.
const PLAN: Record<string, string[]> = {
  "h4-mindsets": ["story:A problem", "story:Three patterns", "story:Same moment", "sliders", "story:Courage and consideration", "story:The test", "story:Movie or park", "branch:0", "sort"],
  "h4-promises": ["story:Trust", "bank", "story:A promise", "story:Keepable", "story:When plans change", "story:Leo's book", "branch:0", "sort"],
  "h4-agreements": ["story:Together", "story:Five parts", "story:Try it", "story:Mia and Leo", "builder", "story:Keep it alive", "sort"],
};

function SpotQuestion({ q }: { q: IdentifyQuestion }) {
  const [picked, setPicked] = useState<number | null>(null);
  const answer = q.correct[0];
  return (
    <div className="lg-story" style={{ textAlign: "left", justifyContent: "center", gap: 12 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <span style={{ fontSize: 38 }}>{q.emoji}</span>
        <p className="lg-p" style={{ fontSize: 16 }}>{q.scenario}</p>
      </div>
      <p className="lg-ask">{q.prompt}</p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
        {q.options.map((o, i) => (
          <button key={i} type="button" className="lg-opt" disabled={picked !== null}
            data-state={picked === null ? undefined : i === answer ? "right" : i === picked ? "wrong" : undefined} onClick={() => setPicked(i)}>
            <span className="ltr">{"ABCD"[i]}</span>{o}
          </button>
        ))}
      </div>
      {picked !== null && <motion.p className="lg-fb" initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}><strong>{picked === answer ? "Yes! " : "Not quite. "}</strong>{q.explanation}</motion.p>}
    </div>
  );
}

function ThinkQuestion({ q, n }: { q: MasteryQuestion; n: number }) {
  const [show, setShow] = useState(false);
  return (
    <div className="lg-story" style={{ textAlign: "left", gap: 6 }}>
      <p className="lg-eyebrow">Think it through {n}</p>
      <p className="lg-ask">{q.question}</p>
      <textarea className="lg-area" placeholder="Type your answer here…" aria-label="Your answer" />
      <div style={{ flex: "none", display: "flex", gap: 10, alignItems: "flex-start" }}>
        <button type="button" className="lg-btn" style={{ height: 36, padding: "0 16px", flex: "none" }} onClick={() => setShow((s) => !s)}>{show ? "Hide model answer" : "Show model answer"}</button>
        {show && <motion.div className="lg-ans" initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}>{q.solution}</motion.div>}
      </div>
    </div>
  );
}

/**
 * Keeps the lesson's interactive scenes whole. The Lumen player draws a scene in a frame as big as the space it is
 * given, so a short, wide space crops it. Here the frame is laid out at a comfortable height and scaled to fit, so
 * nothing is cut off (the shared player itself is untouched).
 */
function ScaledVideo({ children }: { children: ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const root = ref.current;
    if (!root) return;
    const LAYOUT_H = 720;                      // the height the lesson's activities are laid out for
    const fit = () => {
      const iframe = root.querySelector("iframe") as HTMLIFrameElement | null;
      const stage = iframe?.parentElement as HTMLElement | null;
      if (!stage) return;
      stage.dataset.bg ??= stage.style.background;
      if (!iframe) { stage.style.background = stage.dataset.bg; return; }
      const w = stage.clientWidth, h = stage.clientHeight;
      if (!w || !h) return;
      const k = Math.min(1, h / LAYOUT_H);
      stage.style.background = "transparent";
      iframe.style.position = "absolute";
      iframe.style.left = "0"; iframe.style.top = "0";
      iframe.style.width = `${w / k}px`; iframe.style.height = `${h / k}px`;
      iframe.style.transformOrigin = "0 0"; iframe.style.transform = `scale(${k})`;
    };
    const ro = new ResizeObserver(fit);
    ro.observe(root);
    const mo = new MutationObserver(fit);
    mo.observe(root, { childList: true, subtree: true });
    fit();
    return () => { ro.disconnect(); mo.disconnect(); };
  }, []);
  return <div ref={ref} style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column", padding: "6px 12px 12px" }}>{children}</div>;
}

/** The Video tab: the lesson gets the whole window (the page hides its panels), with a way back and full screen. */
function VideoTheatre({ section, onBack }: { section: LearnSection; onBack: () => void }) {
  const card = useRef<HTMLElement>(null);
  const [isFull, setIsFull] = useState(false);
  useEffect(() => {
    const on = () => setIsFull(document.fullscreenElement === card.current);
    document.addEventListener("fullscreenchange", on);
    return () => document.removeEventListener("fullscreenchange", on);
  }, []);
  return (
    <section className="lg-card" ref={card}>
      <div className="lg-cinema-bar">
        <span className="lg-pill">🎬 Video</span>
        <h2 className="lg-card-title">{section.title}</h2>
        <button type="button" className="lg-icon-btn" onClick={onBack}>‹ Back to lesson</button>
        <button type="button" className="lg-icon-btn" onClick={() => (document.fullscreenElement ? void document.exitFullscreen() : void card.current?.requestFullscreen?.())}>
          {isFull ? "⤢ Exit full screen" : "⛶ Full screen"}
        </button>
      </div>
      <ScaledVideo><VideoView sectionId={section.id} /></ScaledVideo>
    </section>
  );
}

export function UnderstandingView({ section, resource, onResource, onDone }: { section: LearnSection; resource: Resource; onResource: (r: Resource) => void; onDone: () => void }) {
  const [mode, setMode] = useState<"learn" | "check" | "think">("learn");

  const learn: Step[] = useMemo(() => {
    const stories = H4_STORY[section.id] ?? [];
    const sort = H4_SORT[section.id];
    const out: Step[] = [];
    for (const entry of PLAN[section.id] ?? []) {
      if (entry.startsWith("story:")) {
        const s = stories.find((x) => x.title === entry.slice(6));
        if (s) out.push({ title: s.title, node: <StoryScreen kicker={s.kicker} headline={s.headline} picture={s.picture} body={s.body} /> });
      } else if (entry.startsWith("branch:")) {
        const d = H4_BRANCH[section.id]?.[Number(entry.slice(7))];
        if (d) out.push({ title: "Choose what happens", node: <BranchStory data={d} /> });
      } else if (entry === "sliders") out.push({ title: "Sliders", node: <SeesawSliders /> });
      else if (entry === "bank") out.push({ title: "Trust jar", node: <BankAccount /> });
      else if (entry === "builder") out.push({ title: "Build the agreement", node: <AgreementBuilder /> });
      else if (entry === "sort" && sort) out.push({ title: "Sort it", node: <SortActivity kicker="Your turn" headline="Can you *sort* them?" prompt={sort.prompt} buckets={sort.categories} items={sort.items} /> });
    }
    return out;
  }, [section.id]);

  const check: Step[] = useMemo(() => (H4_IDENTIFY[section.id] ?? []).map((q, i) => ({ title: `Question ${i + 1}`, node: <SpotQuestion q={q} /> })), [section.id]);
  const think: Step[] = useMemo(() => (H4_MASTERY[section.id] ?? []).map((q, i) => ({ title: `Question ${i + 1}`, node: <ThinkQuestion q={q} n={i + 1} /> })), [section.id]);

  if (resource === "video" && LUMEN_LESSONS[section.id]) return <VideoTheatre section={section} onBack={() => onResource("blog")} />;

  const modes = [{ id: "learn", label: "Conceptual" }, { id: "check", label: "Concept check" }, { id: "think", label: "Think it through" }] as const;
  const resources = (
    <Seg id={`res-${section.id}`} label="Blog or video" className="lg-inline-res" value={resource} onChange={onResource} options={[{ id: "blog", label: "Blog" }, { id: "video", label: "Video" }] as const} />
  );
  const tools = (
    <>
      {resource === "blog" && <Seg id={`mode-${section.id}`} label="Lesson part" value={mode} onChange={setMode} options={modes} />}
      {resources}
    </>
  );

  return (
    <Card pill="📖 Understanding" title={section.title} tools={tools}>
      {resource === "video" ? (
        LUMEN_LESSONS[section.id] ? (
          null
        ) : (
          <div className="lg-screen" style={{ alignItems: "center", justifyContent: "center", textAlign: "center", gap: 8 }}>
            <span style={{ fontSize: 52 }}>🎬</span>
            <h3>The video for this section is coming soon</h3>
            <p className="lg-note">Until then, the Blog has the full lesson.</p>
          </div>
        )
      ) : mode === "learn" ? (
        <Stepper key={`${section.id}-learn`} steps={learn} onDone={() => setMode("check")} doneLabel="On to the concept check" />
      ) : mode === "check" ? (
        <Stepper key={`${section.id}-check`} steps={check} onDone={() => setMode("think")} doneLabel="On to think it through" />
      ) : (
        <Stepper key={`${section.id}-think`} steps={think} onDone={onDone} doneLabel="On to Retention" />
      )}
    </Card>
  );
}

// ─── Retention: all the cards on screen, each flips in place, and the study guide ─────

interface FlashItem { q: string; a: string; img: string }

function FlashGrid({ cards, flipped, onFlip }: { cards: FlashItem[]; flipped: Record<number, boolean>; onFlip: (i: number) => void }) {
  return (
    <div className="lg-fgrid">
      {cards.map((c, i) => (
        <button key={i} type="button" className="lg-fc" data-flipped={!!flipped[i]} data-long={c.q.length > 70} onClick={() => onFlip(i)} aria-label={flipped[i] ? `Answer: ${c.a}. Tap to see the question.` : `Question: ${c.q}. Tap to see the answer.`}>
          <span className="lg-fc-in">
            <span className="lg-fc-face lg-fc-front">
              <Pic src={c.img} className="lg-fc-pic" />
              <span className="lg-fc-text">
                <span className="lg-fc-q">{c.q}</span>
                <span className="lg-fc-tap">Tap to flip</span>
              </span>
            </span>
            <span className="lg-fc-face lg-fc-back">
              <span className="lg-fc-label">Answer</span>
              <span className="lg-fc-a">{c.a}</span>
            </span>
          </span>
        </button>
      ))}
    </div>
  );
}

export function RetentionView({ section }: { section: LearnSection }) {
  const [view, setView] = useState<"cards" | "guide">("cards");
  const [zoom, setZoom] = useState(false);
  const [flipped, setFlipped] = useState<Record<number, boolean>>({});
  const seed = (H4_RETENTION[section.id] ?? null);
  const cards: FlashItem[] = useMemo(() => (seed?.cards ?? []).map((c) => ({ q: c.question, a: c.answer, img: c.imageUrl })), [seed]);
  const guide = seed?.summary.imageUrl;
  const allFlipped = cards.length > 0 && cards.every((_, i) => flipped[i]);

  const tools = (
    <Seg id={`rev-${section.id}`} label="Revision" value={view} onChange={setView} options={[{ id: "cards", label: "Flashcards" }, { id: "guide", label: "Study guide" }] as const} />
  );

  return (
    <Card pill="✨ Retention" title={section.title} tools={tools}>
      {view === "cards" ? (
        <>
          <div className="lg-screen" style={{ paddingBottom: 4 }}>
            <FlashGrid cards={cards} flipped={flipped} onFlip={(i) => setFlipped((f) => ({ ...f, [i]: !f[i] }))} />
          </div>
          <div className="lg-foot">
            <span className="lg-hint">Tap a card to flip it and check your answer.</span>
            <div style={{ display: "flex", gap: 10 }}>
              <button type="button" className="lg-btn" onClick={() => setFlipped(allFlipped ? {} : Object.fromEntries(cards.map((_, i) => [i, true])))}>{allFlipped ? "Flip all back" : "Flip all"}</button>
              <button type="button" className="lg-btn go" onClick={() => setView("guide")}>See the study guide</button>
            </div>
          </div>
        </>
      ) : (
        <>
          <div className="lg-screen" style={{ paddingBottom: 4 }}>
            {guide ? (
              <button type="button" className="lg-guide" onClick={() => setZoom(true)} aria-label="Open the study guide large">
                <span className="lg-guide-bg" style={{ backgroundImage: `url(${guide})` }} aria-hidden="true" />
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={guide} alt={`Study guide: ${section.title}`} />
              </button>
            ) : <p className="lg-note">The study guide is coming soon.</p>}
          </div>
          <div className="lg-foot"><span className="lg-hint">Tap the study guide to enlarge it.</span><button type="button" className="lg-btn go" onClick={() => setZoom(true)} disabled={!guide}>Open large</button></div>
        </>
      )}
      {zoom && guide && (
        <div className="lg-zoom" onClick={() => setZoom(false)} role="dialog" aria-label="Study guide, large" style={{ cursor: "zoom-out" }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={guide} alt={`Study guide: ${section.title}`} />
        </div>
      )}
    </Card>
  );
}
