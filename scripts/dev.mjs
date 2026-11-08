// Starts both halves of the demo with one command: the Python demo service and the Next.js site.
// Usage: npm run dev   (or: npm run start  after  npm run build)
// Ports (defaults 3000 and 8080) can be changed:  WEB_PORT=3100 DEMO_PORT=8090 npm run dev
import { spawn } from "node:child_process";

const prod = process.argv.includes("--prod");
const web = process.env.WEB_PORT || "3000";
const demo = process.env.DEMO_PORT || "8080";
const py = process.env.PYTHON || (process.platform === "win32" ? "python" : "python3");
const isWin = process.platform === "win32";
const env = { ...process.env, PORT: demo, DEMO_SERVICE_URL: `http://localhost:${demo}` };

const procs = [
  spawn(py, ["services/demo-livelife/server.py"], { stdio: "inherit", env }),
  spawn(isWin ? "npx.cmd" : "npx", ["next", prod ? "start" : "dev", "-p", web], { stdio: "inherit", shell: isWin, env }),
];
const stop = () => procs.forEach(p => { try { p.kill(); } catch {} });
process.on("SIGINT", () => { stop(); process.exit(0); });
process.on("exit", stop);
procs.forEach(p => p.on("exit", code => { if (code) { stop(); process.exit(code); } }));
console.log(`\nDemo starting. Open http://localhost:${web}\n`);
