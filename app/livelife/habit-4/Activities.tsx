"use client";

/**
 * The building blocks of the Habit 4 screens: the step-through (Stepper) and the interactive activities.
 * Everything is sized to fit one window with no page scroll: pictures flex into the space that is left, long lists
 * become one item at a time, and the Back / Next controls are pinned under the content.
 * Feedback is animated reactions only: faces change, cards bounce, colours shift. No points, scores or ranks,
 * nothing is saved, and nothing calls the server. Content: lib/learnContent/habit4Activities.ts.
 */

import { useState, type CSSProperties, type ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { H4_BANK, H4_AGREEMENT, type BranchStoryData } from "@/lib/learnContent/habit4Activities";

const GOOD = "#10B981";
const BAD = "#EF4444";
const MEH = "#F59E0B";

/** "Two people, *one plan*": the starred words are highlighted. */
export function Headline({ text }: { text: string }) {
  const parts = text.split("*");
  return <h2 className="lg-h">{parts.map((p, i) => (i % 2 === 1 ? <em key={i}>{p}</em> : <span key={i}>{p}</span>))}</h2>;
}

// ─── Stepper: dots, the current screen, and Back / Next pinned underneath ─────

/** A picture that is always shown whole. A soft blurred copy of it fills any spare space around it. */
export function Pic({ src, className = "lg-pic" }: { src: string; className?: string }) {
  return (
    <span className={className} style={{ ["--pic" as string]: `url("${src}")` } as CSSProperties}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={src} alt="" />
    </span>
  );
}

export interface Step { title: string; node: ReactNode }

function Arrow({ dir }: { dir: "left" | "right" }) {
  return (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {dir === "left" ? <path d="M12.5 4.5 7 10l5.5 5.5" /> : <path d="M7.5 4.5 13 10l-5.5 5.5" />}
    </svg>
  );
}

export function Stepper({ steps, onDone, doneLabel = "Continue" }: { steps: Step[]; onDone?: () => void; doneLabel?: string }) {
  const [i, setI] = useState(0);
  const idx = Math.min(i, steps.length - 1);
  const last = idx === steps.length - 1;
  return (
    <>
      <div className="lg-screen" key={idx}>{steps[idx]?.node}</div>
      <div className="lg-foot">
        <button type="button" className="lg-btn" onClick={() => setI(Math.max(0, idx - 1))} disabled={idx === 0}><Arrow dir="left" />Back</button>
        <div className="lg-steps" aria-label={`Step ${idx + 1} of ${steps.length}`}>
          {steps.map((_, k) => <span key={k} className="lg-step" data-on={k === idx} />)}
          <span style={{ marginLeft: 6 }}>{idx + 1} of {steps.length}</span>
        </div>
        <button type="button" className="lg-btn go" onClick={() => (last ? onDone?.() : setI(idx + 1))} disabled={last && !onDone}>
          {last ? doneLabel : "Next"}<Arrow dir="right" />
        </button>
      </div>
    </>
  );
}

// ─── A story screen: badge, headline, a picture that takes the space left, then the story ────

export function StoryScreen({ kicker, headline, picture, body }: { kicker: string; headline: string; picture: string; body: string }) {
  return (
    <div className="lg-split">
      <Pic src={picture} />
      <div className="lg-split-text">
        <span className="lg-kick">{kicker}</span>
        <Headline text={headline} />
        <p className="lg-p">{body}</p>
      </div>
    </div>
  );
}

// ─── Choose what happens ──────────────────────────────────────────────────────

export function BranchStory({ data }: { data: BranchStoryData }) {
  const [picked, setPicked] = useState<number | null>(null);
  const outcome = picked === null ? null : data.choices[picked].outcome;
  const tone = outcome ? (outcome.tone === "good" ? GOOD : outcome.tone === "bad" ? BAD : MEH) : "#CBD5E1";

  return (
    <div className="lg-two" style={{ gridTemplateColumns: "minmax(0, 1.15fr) minmax(0, 0.85fr)" }}>
      <div className="lg-col">
        <span className="lg-kick" style={{ alignSelf: "flex-start" }}>{data.kicker}</span>
        <div style={{ textAlign: "left" }}><Headline text={data.headline} /></div>
        <p className="lg-p">{data.setup}</p>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {data.choices.map((c, i) => (
            <motion.button key={i} type="button" className="lg-opt" data-state={picked === i ? "picked" : undefined} whileTap={{ scale: 0.98 }} onClick={() => setPicked(i)}>
              <span className="ltr">{"ABC"[i]}</span>{c.label}
            </motion.button>
          ))}
        </div>
      </div>
      <div className="lg-col" style={{ justifyContent: "center" }}>
        <AnimatePresence mode="wait">
          {outcome ? (
            <motion.div key={picked} initial={{ opacity: 0, y: 12, scale: 0.97 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0 }}
              style={{ borderRadius: 18, border: `2px solid ${tone}`, background: "#fff", padding: "14px 16px", textAlign: "center" }}>
              <div style={{ display: "flex", justifyContent: "center", gap: 26, marginBottom: 6 }}>
                {outcome.faces.map((f, k) => (
                  <motion.div key={k} initial={{ scale: 0.3, rotate: -12 }} animate={{ scale: 1, rotate: 0 }} transition={{ type: "spring", stiffness: 260, damping: 12, delay: k * 0.12 }}>
                    <div style={{ fontSize: 44, lineHeight: 1 }}>{f}</div>
                    <div style={{ fontSize: 12, fontWeight: 800, color: "#4a5278" }}>{outcome.names[k]}</div>
                  </motion.div>
                ))}
              </div>
              <span className="lg-tag" style={{ background: tone }}>{outcome.tag}</span>
              <p className="lg-p" style={{ marginTop: 8 }}>{outcome.text}</p>
              {outcome.tone === "good"
                ? <p style={{ margin: "8px 0 0", fontWeight: 800, fontSize: 13.5, color: "#047857" }}>{data.goodNote}</p>
                : <p className="lg-hint" style={{ margin: "8px 0 0" }}>Try another choice to see what changes.</p>}
            </motion.div>
          ) : (
            <motion.p key="none" className="lg-hint" style={{ textAlign: "center", fontSize: 14 }} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              Pick a choice to see what happens.
            </motion.p>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

// ─── Courage and consideration sliders ────────────────────────────────────────

function readSeesaw(c: number, k: number) {
  if (c >= 60 && k >= 60) return { tag: "Win-Win", tone: GOOD, me: "😄", friend: "😄", text: "You say what you need and you care what your friend needs. Both people feel heard." };
  if (c >= 60 && k < 40) return { tag: "Win-Lose", tone: BAD, me: "😄", friend: "😕", text: "You stand up for yourself, but your friend's needs are left out." };
  if (c < 40 && k >= 60) return { tag: "Lose-Win", tone: BAD, me: "😕", friend: "😄", text: "You care about your friend, but you give up what matters to you." };
  if (c < 40 && k < 40) return { tag: "Nobody is heard", tone: MEH, me: "😐", friend: "😐", text: "Neither need gets said or listened to. The problem is still there." };
  return { tag: "Keep going", tone: "#94A3B8", me: "🤔", friend: "🤔", text: "Move the sliders towards the high end to see what Win-Win looks like." };
}

export function SeesawSliders() {
  const [courage, setCourage] = useState(50);
  const [consideration, setConsideration] = useState(50);
  const r = readSeesaw(courage, consideration);
  const tilt = ((consideration - courage) / 100) * 12;

  const slider = (label: string, value: number, set: (n: number) => void, color: string) => (
    <label style={{ display: "block" }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13.5, fontWeight: 800 }}>
        <span>{label}</span><span style={{ color: "#4a5278", fontWeight: 700 }}>{value < 40 ? "low" : value < 60 ? "some" : "high"}</span>
      </div>
      <input type="range" min={0} max={100} step={5} value={value} onChange={(e) => set(Number(e.target.value))} style={{ width: "100%", accentColor: color, margin: "2px 0 0" }} />
    </label>
  );

  return (
    <div className="lg-story">
      <span className="lg-kick">Try it</span>
      <Headline text="Move the *sliders*" />
      <p className="lg-p">Same problem, different mindset. Change how much you speak up and how much you consider your friend.</p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18, textAlign: "left" }}>
        {slider("I say what I need", courage, setCourage, "#7C3AED")}
        {slider("I consider my friend", consideration, setConsideration, "#0891B2")}
      </div>
      <div style={{ position: "relative", flex: 1, minHeight: 56 }}>
        <motion.div animate={{ rotate: tilt }} transition={{ type: "spring", stiffness: 120, damping: 14 }}
          style={{ position: "absolute", left: "12%", right: "12%", top: "58%", height: 9, borderRadius: 6, background: "#94A3B8" }}>
          <motion.div key={r.me + r.tag + "a"} animate={{ scale: [1, 1.14, 1] }} transition={{ duration: 0.4 }} style={{ position: "absolute", left: -4, top: -44, fontSize: 38 }}>{r.me}</motion.div>
          <motion.div key={r.friend + r.tag + "b"} animate={{ scale: [1, 1.14, 1] }} transition={{ duration: 0.4 }} style={{ position: "absolute", right: -4, top: -44, fontSize: 38 }}>{r.friend}</motion.div>
        </motion.div>
        <div style={{ position: "absolute", left: "50%", top: "64%", transform: "translateX(-50%)", width: 0, height: 0, borderLeft: "14px solid transparent", borderRight: "14px solid transparent", borderBottom: "26px solid #64748B" }} />
        <span style={{ position: "absolute", left: "12%", bottom: 0, fontSize: 12, fontWeight: 800, color: "#4a5278" }}>Me</span>
        <span style={{ position: "absolute", right: "12%", bottom: 0, fontSize: 12, fontWeight: 800, color: "#4a5278" }}>My friend</span>
      </div>
      <motion.div key={r.tag} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} style={{ flex: "none", borderRadius: 14, border: `2px solid ${r.tone}`, padding: "8px 12px", background: "#fff", display: "flex", alignItems: "center", gap: 10, textAlign: "left" }}>
        <span className="lg-tag" style={{ background: r.tone, flex: "none" }}>{r.tag}</span>
        <span style={{ fontSize: 13.5, lineHeight: 1.45 }}>{r.text}</span>
      </motion.div>
    </div>
  );
}

// ─── Tap sorting, one statement at a time (also the agreement builder) ────────

interface SortItem { text: string; answer: string }

export function SortActivity({ kicker, headline, prompt, buckets, items, renderDone }: {
  kicker: string; headline: string; prompt: string; buckets: string[]; items: SortItem[];
  renderDone?: (picked: Record<number, string>) => ReactNode;
}) {
  const [cur, setCur] = useState(0);
  const [picked, setPicked] = useState<Record<number, string>>({});
  const [wrong, setWrong] = useState<string | null>(null);
  const done = cur >= items.length;
  const item = items[Math.min(cur, items.length - 1)];

  function choose(b: string) {
    if (b === item.answer) {
      setPicked((p) => ({ ...p, [cur]: b }));
      setWrong(null);
      window.setTimeout(() => setCur((c) => c + 1), 900);
    } else {
      setWrong(b);
    }
  }
  const right = picked[cur] === item.answer;

  if (done) {
    return (
      <div className="lg-story" style={{ justifyContent: "center", alignItems: "center" }}>
        <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ type: "spring", stiffness: 240, damping: 12 }}
          style={{ fontWeight: 800, fontSize: 20, color: "#047857", fontFamily: "var(--sans)" }}>🎉 All sorted!</motion.div>
        {renderDone ? renderDone(picked) : <p className="lg-p">Every one is in the right place. Tap Next to continue.</p>}
      </div>
    );
  }

  return (
    <div className="lg-story">
      <span className="lg-kick">{kicker}</span>
      <Headline text={headline} />
      <p className="lg-p">{prompt}</p>
      <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column", justifyContent: "center", gap: 14 }}>
        <AnimatePresence mode="wait">
          <motion.div key={cur} initial={{ opacity: 0, x: 24 }} animate={wrong ? { opacity: 1, x: [0, -8, 8, -5, 5, 0] } : { opacity: 1, x: 0 }} exit={{ opacity: 0, x: -24 }} transition={{ duration: 0.3 }}
            style={{ alignSelf: "center", maxWidth: 560, width: "100%", padding: "16px 20px", borderRadius: 18, background: right ? "#ecfdf5" : "#fff", border: `2px solid ${right ? GOOD : wrong ? "#FCA5A5" : "rgba(27,34,80,0.1)"}`, fontSize: 18, fontWeight: 700, lineHeight: 1.4 }}>
            {item.text}
          </motion.div>
        </AnimatePresence>
        <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 8 }}>
          {buckets.map((b) => (
            <motion.button key={b} type="button" whileTap={{ scale: 0.94 }} disabled={right} onClick={() => choose(b)}
              style={{ padding: "8px 16px", borderRadius: 99, border: "1.5px solid", fontWeight: 800, fontSize: 13.5, cursor: right ? "default" : "pointer",
                borderColor: right && b === item.answer ? GOOD : wrong === b ? BAD : "rgba(27,34,80,0.18)", background: right && b === item.answer ? GOOD : wrong === b ? BAD : "#fff", color: (right && b === item.answer) || wrong === b ? "#fff" : "#2f3763" }}>
              {b}
            </motion.button>
          ))}
        </div>
        <div className="lg-hint" style={{ textAlign: "center", minHeight: 18 }}>
          {right ? "Yes! That is right." : wrong ? "Not quite. Try another." : `${cur + 1} of ${items.length}. Tap the right answer.`}
        </div>
      </div>
    </div>
  );
}

// ─── Section 3: build the agreement ───────────────────────────────────────────

export function AgreementBuilder() {
  const { parts, lines, scenario } = H4_AGREEMENT;
  return (
    <SortActivity kicker="Build it" headline="Make a *Win-Win Agreement*" prompt={scenario} buckets={parts} items={lines}
      renderDone={() => (
        <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} style={{ width: "100%", maxWidth: 600, textAlign: "left", border: "2px solid #10b981", borderRadius: 18, background: "#fff", padding: "10px 16px", boxShadow: "0 8px 22px rgba(16,185,129,0.18)" }}>
          <div style={{ textAlign: "center", fontWeight: 800, color: "#047857", marginBottom: 4 }}>🤝 Mia and Leo&apos;s Win-Win Agreement</div>
          {parts.map((p) => {
            const l = lines.find((x) => x.answer === p);
            return <div key={p} style={{ fontSize: 13, lineHeight: 1.45, padding: "3px 0", borderTop: "1px solid rgba(27,34,80,0.08)" }}><strong style={{ color: "#4338ca" }}>{p}:</strong> {l?.text}</div>;
          })}
        </motion.div>
      )} />
  );
}

// ─── Section 2: the Emotional Bank Account (trust jar) ────────────────────────

export function BankAccount() {
  const [used, setUsed] = useState<Record<number, boolean>>({});
  const [trust, setTrust] = useState(50);
  const [last, setLast] = useState("");

  function tap(i: number) {
    if (used[i]) return;
    const a = H4_BANK[i];
    setUsed((u) => ({ ...u, [i]: true }));
    setTrust((t) => Math.max(5, Math.min(100, t + (a.kind === "deposit" ? 14 : -16))));
    setLast(a.kind === "deposit" ? "Deposit! Trust grows." : "Withdrawal. Trust shrinks.");
  }
  const mood = trust < 30 ? { face: "😟", label: "Trust is low", color: BAD } : trust < 65 ? { face: "🙂", label: "Trust is growing", color: MEH } : { face: "😄", label: "Trust is strong", color: GOOD };

  return (
    <div className="lg-story">
      <span className="lg-kick">Try it</span>
      <Headline text="Fill the *trust jar*" />
      <p className="lg-p">Tap what a friend might do. Deposits build trust and withdrawals break it. It is a way of thinking, not a score.</p>
      <div style={{ flex: 1, minHeight: 0, display: "flex", alignItems: "center", justifyContent: "center", gap: 22 }}>
        <motion.div key={mood.face} initial={{ scale: 0.5, rotate: -10 }} animate={{ scale: 1, rotate: 0 }} transition={{ type: "spring", stiffness: 260, damping: 11 }} style={{ fontSize: 56, lineHeight: 1 }}>{mood.face}</motion.div>
        <div style={{ width: 58, height: "min(100%, 108px)", minHeight: 70, borderRadius: "12px 12px 20px 20px", border: "3px solid #94A3B8", background: "rgba(255,255,255,0.7)", position: "relative", overflow: "hidden" }}>
          <motion.div animate={{ height: `${trust}%` }} transition={{ type: "spring", stiffness: 90, damping: 14 }} style={{ position: "absolute", bottom: 0, left: 0, right: 0, background: `linear-gradient(180deg, ${mood.color}AA, ${mood.color})` }} />
        </div>
        <div style={{ textAlign: "left", minWidth: 140 }}>
          <div style={{ fontWeight: 800, fontSize: 16, color: mood.color, fontFamily: "var(--sans)" }}>{mood.label}</div>
          <div className="lg-hint" style={{ minHeight: 18 }}>{last}</div>
          <button type="button" className="lg-btn" style={{ height: 32, padding: "0 14px", fontSize: 12.5, marginTop: 4 }} onClick={() => { setUsed({}); setTrust(50); setLast(""); }}>Start again</button>
        </div>
      </div>
      <div style={{ flex: "none", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
        {H4_BANK.map((a, i) => (
          <motion.button key={i} type="button" className="lg-opt" whileTap={{ scale: 0.96 }} onClick={() => tap(i)} disabled={!!used[i]}
            data-state={used[i] ? (a.kind === "deposit" ? "right" : "wrong") : undefined} style={{ padding: "7px 10px", fontSize: 13 }}>
            {used[i] ? (a.kind === "deposit" ? "⬆ " : "⬇ ") : ""}{a.text}
          </motion.button>
        ))}
      </div>
    </div>
  );
}
