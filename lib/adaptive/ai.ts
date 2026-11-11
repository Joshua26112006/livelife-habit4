/**
 * The AI step behind each /api/adaptive/<module> route. The key lives here, on the site; the Python service holds the rules, the
 * prompts and the class. Each route fetches its module's tasks, runs them, and posts the raw replies back, where they are validated.
 * If AI is off or a call fails, the module still runs on its rules and says so.
 */
import { createLimiter } from "@/lib/livelifeDemo/limits";

// Two tiers. Each task says which it needs: "reasoning" for working out answers, judging written answers, naming thinking
// errors and their fixes, and each student's next steps; "fast" for the rest (short explanations and summaries).
const MODEL = process.env.DEMO_LIVELIFE_MODEL || "openai/gpt-4o";
const REASONING_MODEL = process.env.DEMO_LIVELIFE_REASONING_MODEL || "anthropic/claude-opus-5.5";
const REASONING_EFFORT = process.env.DEMO_LIVELIFE_REASONING_EFFORT || "high";
// Thinking tokens count toward max_tokens, so a reasoning task gets this much on top of the room its reply needs.
const REASONING_BUDGET = 16000;
const API_URL = process.env.DEMO_LIVELIFE_API_URL || "https://openrouter.ai/api/v1/chat/completions";
const SERVICE = (process.env.DEMO_SERVICE_URL || "http://localhost:8080").replace(/\/+$/, "");
const ENGINE = `${SERVICE}/demo-livelife/adaptive-engine/api`;
const CLASS_ID = /^[A-Za-z0-9_-]{16,40}$/;
const CONCURRENCY = 4;
const MAX_TASKS = 220;

// One unit is one model call. A class of 40 is about 40 calls for marking and a few per module.
const limiter = createLimiter({ perAddressPerHour: 500, perDay: 2000 });

type JsonTask = { id: string; kind: "json"; system: string; user: string; max_tokens: number; tier?: "reasoning" | "fast" };
type Task = JsonTask;

function aiEnabled(): boolean {
  return process.env.DEMO_LIVELIFE_SCORE === "1" && Boolean(process.env.OPENROUTER_API_KEY || process.env.OPENAI_API_KEY);
}

const ATTEMPTS = 3;

/** A dropped connection or a provider hiccup should not cost a whole module its AI step. A reasoning task the reasoning
 * model keeps refusing or failing gets one last try on the fast model, so the step still runs. */
async function chat(task: Task): Promise<Record<string, unknown>> {
  for (let attempt = 1; ; attempt += 1) {
    try {
      return await chatOnce(task);
    } catch (err) {
      if (attempt >= ATTEMPTS) {
        if (task.tier !== "reasoning") throw err;
        console.error("[adaptive] reasoning model failed; using the fast model", err instanceof Error ? err.message.slice(0, 60) : "error");
        return chatOnce({ ...task, tier: "fast" });
      }
      await new Promise(done => setTimeout(done, 800 * attempt));
    }
  }
}

/** The JSON object in a reply, even when a model wraps it in a code fence or a sentence. */
function parseReply(content: string): Record<string, unknown> {
  try {
    return JSON.parse(content);
  } catch {
    const start = content.indexOf("{"), end = content.lastIndexOf("}");
    if (start < 0 || end <= start) throw new Error("no JSON in reply");
    return JSON.parse(content.slice(start, end + 1));
  }
}

async function chatOnce(task: Task): Promise<Record<string, unknown>> {
  const reasoning = task.tier === "reasoning";
  const res = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${process.env.OPENROUTER_API_KEY || process.env.OPENAI_API_KEY}` },
    body: JSON.stringify({
      model: reasoning ? REASONING_MODEL : MODEL,
      ...(reasoning ? { reasoning: { effort: REASONING_EFFORT } } : { temperature: 0 }),
      response_format: { type: "json_object" },
      max_tokens: task.max_tokens + (reasoning ? REASONING_BUDGET : 0),
      messages: [{ role: "system", content: task.system }, { role: "user", content: task.user }],
    }),
    signal: AbortSignal.timeout(reasoning ? 240_000 : 90_000),
  });
  if (!res.ok) throw new Error(`provider ${res.status}`);
  const body = await res.json();
  const choice = body.choices?.[0];
  // A refused or empty reply is a failure, not an empty answer: otherwise the step would look done with nothing in it.
  if (!choice?.message?.content) throw new Error(`no reply (${choice?.finish_reason ?? "unknown"})`);
  return parseReply(choice.message.content);
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
        results[task.id] = await chat(task);
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
