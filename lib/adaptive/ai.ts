/**
 * The AI step behind each /api/adaptive/<module> route. The key lives here, on the site; the Python service holds the rules, the
 * prompts and the class. Each route fetches its module's tasks, runs them, and posts the raw replies back, where they are validated.
 * If AI is off or a call fails, the module still runs on its rules and says so.
 */
import { createLimiter } from "@/lib/livelifeDemo/limits";

const MODEL = process.env.DEMO_LIVELIFE_MODEL || "openai/gpt-4o";
const API_URL = process.env.DEMO_LIVELIFE_API_URL || "https://openrouter.ai/api/v1/chat/completions";
const SERVICE = (process.env.DEMO_SERVICE_URL || "http://localhost:8080").replace(/\/+$/, "");
const ENGINE = `${SERVICE}/demo-livelife/adaptive-engine/api`;
const CLASS_ID = /^[A-Za-z0-9_-]{16,40}$/;
const CONCURRENCY = 4;
const MAX_TASKS = 220;

// One unit is one model call. A class of 40 is about 40 calls for marking and a few per module.
const limiter = createLimiter({ perAddressPerHour: 500, perDay: 2000 });

type JsonTask = { id: string; kind: "json"; system: string; user: string; max_tokens: number };
type Task = JsonTask;

function aiEnabled(): boolean {
  return process.env.DEMO_LIVELIFE_SCORE === "1" && Boolean(process.env.OPENROUTER_API_KEY || process.env.OPENAI_API_KEY);
}

const ATTEMPTS = 3;

/** A dropped connection or a provider hiccup should not cost a whole module its AI step. */
async function chat(system: string, user: string, maxTokens: number): Promise<Record<string, unknown>> {
  for (let attempt = 1; ; attempt += 1) {
    try {
      return await chatOnce(system, user, maxTokens);
    } catch (err) {
      if (attempt >= ATTEMPTS) throw err;
      await new Promise(done => setTimeout(done, 800 * attempt));
    }
  }
}

async function chatOnce(system: string, user: string, maxTokens: number): Promise<Record<string, unknown>> {
  const res = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${process.env.OPENROUTER_API_KEY || process.env.OPENAI_API_KEY}` },
    body: JSON.stringify({
      model: MODEL,
      temperature: 0,
      response_format: { type: "json_object" },
      max_tokens: maxTokens,
      messages: [{ role: "system", content: system }, { role: "user", content: user }],
    }),
    signal: AbortSignal.timeout(90_000),
  });
  if (!res.ok) throw new Error(`provider ${res.status}`);
  const body = await res.json();
  return JSON.parse(body.choices?.[0]?.message?.content ?? "{}");
}

async function runAll(tasks: Task[], address: string) {
  const results: Record<string, unknown> = {};
  let failed = 0;
  let next = 0;
  const worker = async () => {
    while (next < tasks.length) {
      const task = tasks[next++];
      try {
        if (!limiter.take(address).ok) throw new Error("rate limited");
        results[task.id] = await chat(task.system, task.user, task.max_tokens);
      } catch (err) {
        failed += 1;
        // Student text is never logged.
        console.error("[adaptive] task failed", err instanceof Error ? err.message.slice(0, 60) : "error");
      }
    }
  };
  await Promise.all(Array.from({ length: CONCURRENCY }, worker));
  const status = failed === 0 ? "ok" : failed === tasks.length ? "failed" : "partial";
  return { results, status };
}

const reply = (body: unknown, status = 200) => Response.json(body, { status, headers: { "Cache-Control": "no-store" } });

export async function runModule(req: Request, module: string): Promise<Response> {
  let classId: unknown;
  try {
    classId = ((await req.json()) as { classId?: unknown } | null)?.classId;
  } catch {
    return reply({ error: "Bad request." }, 400);
  }
  if (typeof classId !== "string" || !CLASS_ID.test(classId)) return reply({ error: "Class not found." }, 404);
  const base = `${ENGINE}/classes/${classId}/${module}`;

  const tasksRes = await fetch(`${base}/tasks`, { cache: "no-store" });
  const tasksBody = await tasksRes.json();
  if (!tasksRes.ok) return reply(tasksBody, tasksRes.status);
  const tasks = tasksBody.tasks as Task[];
  if (tasks.length > MAX_TASKS) return reply({ error: `Too many answer sheets to mark at once (limit ${MAX_TASKS}).` }, 413);

  const address = req.headers.get("x-forwarded-for")?.split(",").pop()?.trim() || "local";
  const run = aiEnabled() && tasks.length ? await runAll(tasks, address) : { results: {}, status: aiEnabled() ? "ok" : "off" };

  const res = await fetch(`${base}/run`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(run) });
  return reply(await res.json(), res.status);
}
