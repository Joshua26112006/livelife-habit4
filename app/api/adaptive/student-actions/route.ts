import { runModule } from "@/lib/adaptive/ai";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 300;

export const POST = (req: Request) => runModule(req, "m3-actions");
