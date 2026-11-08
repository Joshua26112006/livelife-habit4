/**
 * LiveLife - Habit 4 TEACHER assessment, on its own address (/livelife/habit-4/teacher).
 *
 * The same glass interface as the student lesson page (/livelife/habit-4), for coaches: the assessment and the latest
 * outcome. No sign-in, nothing saved. Submitting calls
 * /api/demo-livelife-score with kind "teacher" (a paid AI call, off unless a person sets DEMO_LIVELIFE_SCORE=1)
 * and the demo service's teacher API; opening the page costs nothing.
 */
import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import TeacherClient from "./TeacherClient";

// One typeface, as on the lesson page. glass.css reads it as --font-sans and falls back to a clean sans.
const sans = Plus_Jakarta_Sans({ subsets: ["latin"], weight: ["400", "500", "600", "700", "800"], variable: "--font-sans", display: "swap" });

export const metadata: Metadata = {
  title: "Habit 4: Teacher assessment · Discovering the Leader in Me",
};

export default function LiveLifeTeacherPage() {
  return (
    <div className={sans.variable}>
      <TeacherClient />
    </div>
  );
}
