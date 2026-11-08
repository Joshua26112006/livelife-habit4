import {
  KEYS,
  capFromFound,
  MAX_ANSWER_CHARS,
  S7_CAP_AT,
  S7_CAP_NOTE,
  isKey,
  systemPrompt,
  type ScenarioKey,
} from "@/lib/livelifeDemo/rubrics";
import {
  TEACHER_BLANK,
  TEACHER_KEYS,
  TEACHER_MAX_ANSWER,
  isTeacherKey,
  processTeacherReply,
  teacherSystemPrompt,
  type TeacherKey,
} from "@/lib/livelifeDemo/teacher";
import { createLimiter } from "@/lib/livelifeDemo/limits";

/**
 * LiveLife Habit 4 DEMO — AI scoring of ONE person's eight written answers in one model call: a STUDENT's scenarios
 * S1–S8 (kind "student", the default) or a TEACHER's situational questions C1–C8 (kind "teacher"), plus the notes and
 * summary for their scorecard / outcome.
 *
 * THIS ROUTE IS PUBLIC (no login: the demo at /demo-livelife/ has none) AND SPENDS MONEY, so it is deliberately narrow:
 *   - OFF unless a person sets DEMO_LIVELIFE_SCORE=1 (404 otherwise).
 *   - It scores ONLY the fixed items in lib/livelifeDemo/rubrics.ts (students) and lib/livelifeDemo/teacher.ts (teachers).
 *     The request is just the texts and which of the two kinds; it never carries a prompt, a rubric or a model.
 *   - Text is capped; a blank answer scores 0 without being sent to the model.
 *   - Per-address and whole-route daily caps (lib/livelifeDemo/limits.ts), counted in PEOPLE (one call = one person).
 *   - There is no billing code in this demo, so the per-address and daily caps are the only spend guard.
 *     Use a key with a low spend limit.
 *   - Answers are never logged or stored here.
 *   - The model's reply is parsed and clamped; anything unusable becomes score null ("could
 *     not score"), never an invented mark.
 * No child-safety check and no human review here, by design for the demo.
 * BEFORE REAL CHILDREN USE THIS: add the safety check (lib/aidaSafeguarding.ts) and a teacher
 * review or a login.
 */

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 45;

// The marking needs a stronger model than gpt-4o-mini: that one gave level 4 to a bare "Win-Lose." for S2 and read
// several of the rubric's own named level-2 answers as 1. Any OpenAI-compatible endpoint works; the default is OpenRouter.
const MODEL = process.env.DEMO_LIVELIFE_MODEL || "openai/gpt-4o";
const API_URL = process.env.DEMO_LIVELIFE_API_URL || "https://openrouter.ai/api/v1/chat/completions";
const limiter = createLimiter();

interface ChatBody {
  model: string;
  temperature: number;
  response_format: { type: "json_object" };
  max_tokens: number;
  messages: { role: "system" | "user"; content: string }[];
}
/** One chat-completion call to the configured endpoint. Throws on any non-200. */
async function chat(body: ChatBody): Promise<{ choices: { message?: { content?: string } }[] }> {
  const key = process.env.OPENROUTER_API_KEY || process.env.OPENAI_API_KEY;
  if (!key) throw new Error("no API key");
  const res = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${key}` },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(40_000),
  });
  if (!res.ok) throw new Error(`provider ${res.status}`);
  return res.json();
}

function json(body: unknown, status = 200): Response {
  return Response.json(body, { status, headers: { "Cache-Control": "no-store" } });
}

function callerAddress(req: Request): string {
  // The LAST entry is the one the host's proxy appended; earlier ones can be forged.
  const xff = req.headers.get("x-forwarded-for");
  if (xff) {
    const parts = xff.split(",").map(s => s.trim()).filter(Boolean);
    if (parts.length) return parts[parts.length - 1];
  }
  return "unknown";
}

const clean = (s: unknown, max: number): string =>
  typeof s === "string" ? s.replace(/\s+/g, " ").trim().slice(0, max) : "";

interface Result { score: number | null; evidence: string; tip: string; flag: boolean; blank?: boolean }

const BLANK: Result = {
  score: 0,
  evidence: "No answer was written, so there is no evidence yet.",
  tip: "Try writing even one idea next time, then you can build on it.",
  flag: false,
  blank: true,
};

export async function POST(req: Request) {
  if (process.env.DEMO_LIVELIFE_SCORE !== "1") return new Response("Not found", { status: 404 });

  let answers: Record<string, unknown>;
  let kindRaw: unknown;
  try {
    const parsed = (await req.json()) as { answers?: unknown; kind?: unknown } | null;
    const a = parsed?.answers;
    if (typeof a !== "object" || a === null || Array.isArray(a)) return json({ ok: false, error: "bad_request" }, 400);
    answers = a as Record<string, unknown>;
    kindRaw = parsed?.kind;
  } catch {
    return json({ ok: false, error: "bad_request" }, 400);
  }

  // Which of the two fixed sets of questions: students (the default) or teachers.
  if (kindRaw !== undefined && kindRaw !== "student" && kindRaw !== "teacher") return json({ ok: false, error: "unknown_kind" }, 400);
  const teacher = kindRaw === "teacher";
  const allKeys: readonly string[] = teacher ? TEACHER_KEYS : KEYS;
  const keyOk = (k: string) => (teacher ? isTeacherKey(k) : isKey(k));
  const maxChars = teacher ? TEACHER_MAX_ANSWER : MAX_ANSWER_CHARS;

  const texts: Record<string, string> = {};
  for (const k of Object.keys(answers)) {
    if (!keyOk(k)) return json({ ok: false, error: "unknown_item" }, 400);
    const v = answers[k];
    if (v !== undefined && typeof v !== "string") return json({ ok: false, error: "bad_answer" }, 400);
    if (typeof v === "string" && v.trim().length > maxChars) return json({ ok: false, error: "too_long" }, 400);
    texts[k] = clean(v, maxChars);
  }

  const results: Record<string, unknown> = {};
  const toScore: string[] = [];
  for (const k of allKeys) {
    if (texts[k]) toScore.push(k);
    else results[k] = teacher ? { ...TEACHER_BLANK } : { ...BLANK };
  }

  // Nothing written at all: the lowest level for everything, no model call, no allowance used.
  if (toScore.length === 0) return json({ ok: true, results, summary: null });

  const taken = limiter.take(callerAddress(req));
  if (!taken.ok) return json({ ok: false, error: "rate_limited" }, 429);

  try {
    const completion = await chat({
      model: MODEL,
      temperature: 0,
      response_format: { type: "json_object" },
      max_tokens: teacher ? 2400 : 1800,
      messages: [
        { role: "system", content: teacher ? teacherSystemPrompt(toScore as TeacherKey[]) : systemPrompt(toScore as ScenarioKey[]) },
        { role: "user", content: toScore.map(k => `${k} answer:\n"""\n${texts[k]}\n"""`).join("\n\n") },
      ],
    });

    const parsed = JSON.parse(completion.choices[0]?.message?.content ?? "{}") as Record<string, unknown>;

    // ── TEACHER: score, evidence, coaching and the separate critical-concern flag ──
    if (teacher) {
      const out = processTeacherReply(parsed, toScore as TeacherKey[]);
      return json({ ok: true, results: { ...results, ...out.results }, summary: out.summary });
    }

    // ── STUDENT ──
    const modelResults = (typeof parsed.results === "object" && parsed.results !== null ? parsed.results : {}) as Record<string, Record<string, unknown>>;
    if (Object.keys(modelResults).length === 0) throw new Error("no results");

    for (const k of toScore as ScenarioKey[]) {
      const r = modelResults[k];
      const n = Number(r?.score);
      if (!r || r.score === null || r.score === undefined || !Number.isFinite(n)) {
        results[k] = { score: null, evidence: "", tip: "", flag: false };
        continue;
      }
      let score = Math.min(4, Math.max(0, Math.round(n)));
      // The marker listed the rubric parts it found written down; the score may not exceed what they allow.
      const cap = capFromFound(k, r.found);
      if (cap !== null && score > cap) score = cap;
      let tip = clean(r.tip, 150);
      let flag = r.flag === true && score === 0; // a flag only ever goes with a real 0

      if (k === "S7") {
        if (r.consequence === "harmful") {
          score = 0;
          flag = true;
        } else if (r.consequence === "punitive" && score > S7_CAP_AT) {
          // a punitive or unrelated consequence caps the item at 2 with a gentle note.
          score = S7_CAP_AT;
          tip = (tip ? tip + " " : "") + S7_CAP_NOTE;
        }
      }
      results[k] = { score, evidence: clean(r.evidence, 200), tip, flag };
    }

    // The summary is optional: the page falls back to its own lines if it is missing or malformed.
    let summary: { strengths: string[]; skills: string[]; try_next: string; teacher_support: string } | null = null;
    const s = parsed.summary as Record<string, unknown> | undefined;
    if (s && typeof s === "object") {
      const list = (v: unknown, n: number) =>
        Array.isArray(v) ? v.map(x => clean(x, 160)).filter(Boolean).slice(0, n) : [];
      const strengths = list(s.strengths, 2);
      const skills = list(s.skills, 2);
      const try_next = clean(s.try_next, 200);
      const teacher_support = clean(s.teacher_support, 200);
      if (strengths.length && skills.length && try_next && teacher_support) summary = { strengths, skills, try_next, teacher_support };
    }

    return json({ ok: true, results, summary });
  } catch (err) {
    // The person's text is never logged: only that scoring failed.
    console.error("[demo-livelife-score] could not score", err instanceof Error ? err.name : "error");
    return json({ ok: false, error: "could_not_score" });
  }
}
