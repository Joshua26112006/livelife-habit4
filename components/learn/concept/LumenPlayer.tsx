"use client";

import React, { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import type { LumenAction, LumenLesson, LumenScene, LumenSlideElement } from "@/lib/learn/lumenLessons";

// Plays a Lumen lesson (an exported lesson folder) like a video: slides and interactive
// widgets in order, each scene's actions run one by one — narration audio, spotlights on slide
// elements, and highlight/state messages posted into the widget iframe.

const WIDGET_MESSAGES: Record<string, string> = {
  widget_highlight:  "HIGHLIGHT_ELEMENT",
  widget_annotation: "ANNOTATE_ELEMENT",
  widget_reveal:     "REVEAL_ELEMENT",
  widget_setState:   "SET_WIDGET_STATE",
};

// Lumen widgets read one of two message shapes ({type,target,state,content} or
// {action,payload}); send both in one message.
function widgetMessage(a: Extract<LumenAction, { target?: string }>) {
  const type = WIDGET_MESSAGES[a.type];
  const elementId = a.target?.replace(/^#/, "");
  return {
    type, action: type, target: a.target, state: a.state, content: a.content,
    payload: { ...(a.state ?? {}), elementId, id: elementId, target: a.target, text: a.content, highlight: true },
  };
}

interface Props {
  base: string;
  onViewed?: () => void;
}

export default function LumenPlayer({ base, onViewed }: Props) {
  const [lesson, setLesson]         = useState<LumenLesson | null>(null);
  const [failed, setFailed]         = useState(false);
  const [sceneIdx, setSceneIdx]     = useState(0);
  const [step, setStep]             = useState(0);
  const [playing, setPlaying]       = useState(false);
  const [started, setStarted]       = useState(false);
  const [loadedSrc, setLoadedSrc]   = useState<string | null>(null);
  const [spotlight, setSpotlight]   = useState<string | null>(null);
  const [laser, setLaser]           = useState<string | null>(null);
  const [subtitle, setSubtitle]     = useState("");
  const [note, setNote]             = useState<string | null>(null);
  const [discussion, setDiscussion] = useState<{ topic: string; prompt?: string } | null>(null);

  const audioRef      = useRef<HTMLAudioElement | null>(null);
  const audioActionId = useRef<string | null>(null);
  const iframeRef     = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    let cancelled = false;
    fetch(`${base}/lesson.json`)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((l: LumenLesson) => { if (!cancelled) setLesson(l); })
      .catch(() => { if (!cancelled) setFailed(true); });
    return () => { cancelled = true; };
  }, [base]);

  useEffect(() => () => { audioRef.current?.pause(); }, []);

  useEffect(() => {
    if (!note) return;
    const t = setTimeout(() => setNote(null), 5000);
    return () => clearTimeout(t);
  }, [note]);

  const scene: LumenScene | undefined = lesson?.scenes[sceneIdx];
  const ready = scene?.type === "slide" || (scene?.type === "interactive" && loadedSrc === scene.src);

  const goTo = useCallback((i: number) => {
    audioRef.current?.pause();
    audioActionId.current = null;
    setSceneIdx(i);
    setStep(0);
    setSpotlight(null);
    setLaser(null);
    setNote(null);
    setSubtitle("");
    setDiscussion(null);
  }, []);

  // Run the current action; each one moves `step` on when it is done.
  useEffect(() => {
    if (!lesson || !scene || !playing || !ready) return;
    const timers: ReturnType<typeof setTimeout>[] = [];
    const next = (ms = 0) => timers.push(setTimeout(() => setStep((s) => s + 1), ms));

    if (step >= scene.actions.length) {
      timers.push(setTimeout(() => {
        if (sceneIdx < lesson.scenes.length - 1) goTo(sceneIdx + 1);
        else setPlaying(false);
      }, 1200));
      return () => timers.forEach(clearTimeout);
    }

    const action = scene.actions[step];
    let audio: HTMLAudioElement | null = null;

    if (action.type === "spotlight") {
      setSpotlight(action.elementId);
      setLaser(null);
      next(300);
    } else if (action.type === "laser") {
      setLaser(action.elementId);
      next(300);
    } else if (action.type === "speech") {
      setSubtitle(action.text);
      const fallbackMs = Math.max(2500, action.text.split(/\s+/).length * 380);
      if (!action.audioRef) {
        next(fallbackMs);
      } else {
        audio = audioRef.current ?? (audioRef.current = new Audio());
        if (audioActionId.current !== action.id) {
          audio.src = `${base}/${action.audioRef}`;
          audioActionId.current = action.id;
        }
        audio.onended = () => next(400);
        audio.onerror = () => next(fallbackMs);
        audio.play().catch(() => setPlaying(false));
      }
    } else if (action.type === "discussion") {
      setDiscussion({ topic: action.topic, prompt: action.prompt });
      setPlaying(false);
      setStep((s) => s + 1);
    } else if (action.type.startsWith("widget_")) {
      const a = action as Extract<LumenAction, { target?: string }>;
      iframeRef.current?.contentWindow?.postMessage(widgetMessage(a), "*");
      if (a.content) setNote(a.content);
      next(1800);
    } else {
      next();
    }

    return () => {
      timers.forEach(clearTimeout);
      if (audio) { audio.onended = null; audio.onerror = null; audio.pause(); }
    };
  }, [lesson, scene, sceneIdx, step, playing, ready, base, goTo]);

  function togglePlay() {
    if (!started) { setStarted(true); onViewed?.(); }
    setDiscussion(null);
    if (lesson && !playing && sceneIdx === lesson.scenes.length - 1 && step >= (scene?.actions.length ?? 0)) goTo(0);
    setPlaying((p) => !p);
  }

  if (failed) {
    return <Centered>Couldn&apos;t load this lesson. Please try again in a moment.</Centered>;
  }
  if (!lesson || !scene) {
    return <Centered>Loading lesson…</Centered>;
  }

  const totalSeconds = lesson.scenes.flatMap((s) => s.actions).reduce((t, a) => t + (a.type === "speech" ? a.duration ?? 0 : 0), 0);

  return (
    <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column", padding: 16, gap: 10 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <span style={{ fontFamily: "'Nunito',sans-serif", fontWeight: 800, fontSize: 14, color: "#1E293B" }}>🎬 {lesson.title}</span>
        <span style={{ fontFamily: "'Outfit',sans-serif", fontSize: 12, fontWeight: 600, color: "#94A3B8", marginLeft: "auto" }}>
          Scene {sceneIdx + 1}/{lesson.scenes.length} · {scene.title}
        </span>
      </div>

      {/* Stage */}
      <div style={{ flex: 1, minHeight: 0, position: "relative", borderRadius: 16, overflow: "hidden", background: "#0F172A" }}>
        {scene.type === "slide" ? (
          <SlideCanvas canvas={scene.canvas} spotlight={spotlight} laser={laser} />
        ) : (
          <iframe
            key={scene.src}
            ref={iframeRef}
            src={`${base}/${scene.src}`}
            title={scene.title}
            sandbox="allow-scripts allow-pointer-lock"
            onLoad={() => setLoadedSrc(scene.src)}
            style={{ width: "100%", height: "100%", border: 0, display: "block", background: "#fff" }}
          />
        )}

        {note && (
          <div style={{ position: "absolute", top: 12, left: 12, maxWidth: 320, padding: "8px 12px", borderRadius: 10, background: "rgba(124,58,237,0.95)", color: "#fff", fontFamily: "'DM Sans',sans-serif", fontSize: 13, lineHeight: 1.4, boxShadow: "0 6px 18px rgba(15,23,42,0.3)", pointerEvents: "none" }}>
            {note}
          </div>
        )}

        {discussion && (
          <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", background: "rgba(15,23,42,0.6)" }}>
            <div style={{ maxWidth: 440, margin: 16, padding: 24, borderRadius: 18, background: "#fff", boxShadow: "0 12px 40px rgba(0,0,0,0.3)" }}>
              <div style={{ fontFamily: "'Outfit',sans-serif", fontSize: 11, fontWeight: 700, color: "#7C3AED", textTransform: "uppercase", letterSpacing: 0.6, marginBottom: 8 }}>Think about it</div>
              <div style={{ fontFamily: "'Nunito',sans-serif", fontWeight: 800, fontSize: 17, color: "#1E293B", marginBottom: 8 }}>{discussion.topic}</div>
              {discussion.prompt && <div style={{ fontFamily: "'DM Sans',sans-serif", fontSize: 14, color: "#475569", lineHeight: 1.5 }}>{discussion.prompt}</div>}
              <button onClick={() => { setDiscussion(null); setPlaying(true); }} style={{ marginTop: 16, padding: "8px 16px", borderRadius: 10, border: "none", background: "#4F46E5", color: "#fff", fontFamily: "'Nunito',sans-serif", fontWeight: 800, fontSize: 13, cursor: "pointer" }}>
                Got it
              </button>
            </div>
          </div>
        )}

        {!started && (
          <button
            onClick={togglePlay}
            style={{ position: "absolute", inset: 0, border: "none", cursor: "pointer", background: "rgba(15,23,42,0.55)", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 12 }}
          >
            <span style={{ width: 72, height: 72, borderRadius: "50%", background: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 28, color: "#4F46E5", boxShadow: "0 8px 30px rgba(0,0,0,0.35)" }}>▶</span>
            <span style={{ fontFamily: "'Nunito',sans-serif", fontWeight: 800, fontSize: 18, color: "#fff" }}>{lesson.title}</span>
            <span style={{ fontFamily: "'Outfit',sans-serif", fontSize: 12, color: "rgba(255,255,255,0.75)" }}>
              {lesson.scenes.length} scenes · about {Math.max(1, Math.round(totalSeconds / 60))} min
            </span>
          </button>
        )}
      </div>

      {/* Subtitle */}
      <div style={{ display: "flex", alignItems: "flex-start", gap: 10, minHeight: 44 }}>
        {lesson.teacher.avatar && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={`${base}/${lesson.teacher.avatar}`} alt="" style={{ width: 36, height: 36, borderRadius: "50%", objectFit: "cover", flexShrink: 0, border: `2px solid ${lesson.teacher.color}` }} />
        )}
        <div style={{ flex: 1, maxHeight: 64, overflowY: "auto", fontFamily: "'DM Sans',sans-serif", fontSize: 13, lineHeight: 1.5, color: "#334155" }}>
          {subtitle || <span style={{ color: "#94A3B8" }}>{scene.type === "interactive" ? "Try the activity — you can drag, click and explore." : " "}</span>}
        </div>
      </div>

      {/* Controls */}
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <ControlButton label="Previous scene" disabled={sceneIdx === 0} onClick={() => goTo(sceneIdx - 1)}>⏮</ControlButton>
        <ControlButton label={playing ? "Pause" : "Play"} onClick={togglePlay} primary>{playing ? "⏸" : "▶"}</ControlButton>
        <ControlButton label="Next scene" disabled={sceneIdx === lesson.scenes.length - 1} onClick={() => goTo(sceneIdx + 1)}>⏭</ControlButton>
        <div style={{ flex: 1, display: "flex", gap: 4, marginLeft: 8 }}>
          {lesson.scenes.map((s, i) => (
            <button
              key={i}
              title={s.title}
              aria-label={`Scene ${i + 1}: ${s.title}`}
              onClick={() => goTo(i)}
              style={{
                flex: 1, height: 6, borderRadius: 3, border: "none", cursor: "pointer", padding: 0,
                background: i < sceneIdx ? "#818CF8" : i === sceneIdx ? "#4F46E5" : "#E2E8F0",
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function Centered({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'DM Sans',sans-serif", fontSize: 14, color: "#64748B" }}>
      {children}
    </div>
  );
}

function ControlButton({ children, label, onClick, disabled, primary }: { children: React.ReactNode; label: string; onClick: () => void; disabled?: boolean; primary?: boolean }) {
  return (
    <button
      aria-label={label}
      title={label}
      onClick={onClick}
      disabled={disabled}
      style={{
        width: primary ? 40 : 34, height: primary ? 40 : 34, borderRadius: "50%", border: "1.5px solid #E2E8F0",
        background: primary ? "#4F46E5" : "#fff", color: primary ? "#fff" : "#475569",
        fontSize: primary ? 16 : 13, cursor: disabled ? "default" : "pointer", opacity: disabled ? 0.4 : 1,
        display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
      }}
    >
      {children}
    </button>
  );
}

// ── Slide rendering (Lumen canvas: 1000-wide viewport, absolute elements) ──────────

function SlideCanvas({ canvas, spotlight, laser }: { canvas: Extract<LumenScene, { type: "slide" }>["canvas"]; spotlight: string | null; laser: string | null }) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(0);
  const vw = canvas.viewportSize;
  const vh = canvas.viewportSize * canvas.viewportRatio;

  useLayoutEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const fit = () => setScale(Math.min(el.clientWidth / vw, el.clientHeight / vh));
    fit();
    const ro = new ResizeObserver(fit);
    ro.observe(el);
    return () => ro.disconnect();
  }, [vw, vh]);

  const lit = spotlight ? canvas.elements.find((e) => e.id === spotlight) : undefined;
  const pointed = laser ? canvas.elements.find((e) => e.id === laser) : undefined;

  return (
    <div ref={wrapRef} style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ width: vw * scale, height: vh * scale, position: "relative", overflow: "hidden", borderRadius: 8 }}>
        <div className="lumen-slide" style={{ position: "absolute", left: 0, top: 0, width: vw, height: vh, transform: `scale(${scale})`, transformOrigin: "0 0", background: canvas.background?.color ?? "#fff" }}>
          <style>{`.lumen-slide p{margin:0}.lumen-slide .katex-display{margin:0}`}</style>
          {canvas.elements.map((e) => <SlideElement key={e.id} el={e} />)}
          {lit && (
            <div style={{
              position: "absolute", left: lit.left - 8, top: lit.top - 8, width: lit.width + 16, height: Math.max(lit.height ?? 0, 4) + 16,
              borderRadius: 10, border: "3px solid #FBBF24", boxShadow: "0 0 0 2000px rgba(15,23,42,0.45)",
              transition: "all 0.35s ease", pointerEvents: "none",
            }} />
          )}
          {pointed && (
            <div style={{
              position: "absolute", left: pointed.left + pointed.width / 2 - 9, top: pointed.top + (pointed.height ?? 0) / 2 - 9,
              width: 18, height: 18, borderRadius: "50%", background: "#EF4444",
              boxShadow: "0 0 0 6px rgba(239,68,68,0.35), 0 0 18px 6px rgba(239,68,68,0.6)",
              transition: "all 0.35s ease", pointerEvents: "none",
            }} />
          )}
        </div>
      </div>
    </div>
  );
}

function SlideElement({ el }: { el: LumenSlideElement }) {
  const box: React.CSSProperties = {
    position: "absolute", left: el.left, top: el.top, width: el.width, height: el.height,
    transform: el.rotate ? `rotate(${el.rotate}deg)` : undefined,
  };

  if (el.type === "text") {
    return (
      <div
        style={{ ...box, color: el.defaultColor, fontFamily: "'DM Sans','Segoe UI',sans-serif", fontSize: 16, lineHeight: 1.4, overflowWrap: "break-word" }}
        dangerouslySetInnerHTML={{ __html: el.content ?? "" }}
      />
    );
  }
  if (el.type === "latex") {
    return (
      <div
        style={{ ...box, color: el.color, display: "flex", alignItems: "center", justifyContent: el.align === "left" ? "flex-start" : el.align === "right" ? "flex-end" : "center" }}
        dangerouslySetInnerHTML={{ __html: el.html ?? "" }}
      />
    );
  }
  if (el.type === "table" && el.data) {
    const border = `${el.outline?.width ?? 1}px ${el.outline?.style ?? "solid"} ${el.outline?.color ?? "#d1d5db"}`;
    return (
      <table style={{ ...box, borderCollapse: "collapse", tableLayout: "fixed", fontFamily: "'DM Sans','Segoe UI',sans-serif", fontSize: 14, color: "#333" }}>
        {el.colWidths && (
          <colgroup>{el.colWidths.map((w, i) => <col key={i} style={{ width: `${w * 100}%` }} />)}</colgroup>
        )}
        <tbody>
          {el.data.map((row, r) => (
            <tr key={r}>
              {row.map((cell) => {
                const s = cell.style ?? {};
                return (
                  <td
                    key={cell.id}
                    colSpan={cell.colspan}
                    rowSpan={cell.rowspan}
                    style={{
                      border, padding: "2px 8px", overflowWrap: "break-word",
                      fontWeight: s.bold ? 700 : undefined, fontStyle: s.em ? "italic" : undefined,
                      textDecoration: s.underline ? "underline" : undefined, color: s.color,
                      background: s.backcolor, fontSize: s.fontsize, textAlign: (s.align as React.CSSProperties["textAlign"]) ?? "left",
                    }}
                  >
                    {cell.text}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    );
  }
  if (el.type === "shape" && el.path) {
    const [w, h] = el.viewBox ?? [1, 1];
    return (
      <svg style={{ ...box, overflow: "visible" }} viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
        <path d={el.path} fill={el.fill ?? "none"} />
      </svg>
    );
  }
  if (el.type === "line" && el.start && el.end) {
    const [x1, y1] = el.start;
    const [x2, y2] = el.end;
    const sw = el.width;
    const color = el.color ?? "#333";
    const dash = el.style === "dashed" ? `${sw * 4} ${sw * 2}` : el.style === "dotted" ? `${sw} ${sw * 2}` : undefined;
    const ends = [{ x: x1, y: y1, fx: x2, fy: y2, kind: el.points?.[0] }, { x: x2, y: y2, fx: x1, fy: y1, kind: el.points?.[1] }];
    return (
      <svg style={{ position: "absolute", left: el.left, top: el.top, overflow: "visible" }} width={Math.max(Math.abs(x2 - x1), 1)} height={Math.max(Math.abs(y2 - y1), 1)}>
        <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={color} strokeWidth={sw} strokeDasharray={dash} />
        {ends.map((p, i) => {
          if (p.kind === "dot") return <circle key={i} cx={p.x} cy={p.y} r={sw * 1.6} fill={color} />;
          if (p.kind === "arrow") {
            const a = Math.atan2(p.y - p.fy, p.x - p.fx);
            const s = sw * 3.5;
            const pts = [[p.x, p.y], [p.x - s * Math.cos(a - 0.45), p.y - s * Math.sin(a - 0.45)], [p.x - s * Math.cos(a + 0.45), p.y - s * Math.sin(a + 0.45)]];
            return <polygon key={i} points={pts.map((q) => q.join(",")).join(" ")} fill={color} />;
          }
          return null;
        })}
      </svg>
    );
  }
  return null;
}
