import { redirect } from "next/navigation";

// The teacher's bulk-upload workflow is served by the Python service, like the other demo screens.
export default function AdaptivePage() {
  redirect("/demo-livelife/adaptive-engine/");
}
