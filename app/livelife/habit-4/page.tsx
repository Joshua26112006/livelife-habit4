/**
 * LiveLife - Habit 4: Think Win-Win, on its own address (/livelife/habit-4).
 *
 * A standalone page: no sign-in and no points widget. The lesson sections are static content and call nothing
 * under /api, so opening the page costs nothing. The lesson content lives in lib/learnContent/habit4.ts.
 */
import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import HabitFourClient from "./HabitFourClient";

// One typeface for the whole page. glass.css reads it as --font-sans and falls back to a clean sans, never a serif.
const sans = Plus_Jakarta_Sans({ subsets: ["latin"], weight: ["400", "500", "600", "700", "800"], variable: "--font-sans", display: "swap" });

export const metadata: Metadata = {
  title: "Habit 4: Think Win-Win · Discovering the Leader in Me",
};

export default function LiveLifeHabitFourPage() {
  return (
    <div className={sans.variable}>
      <HabitFourClient />
    </div>
  );
}
