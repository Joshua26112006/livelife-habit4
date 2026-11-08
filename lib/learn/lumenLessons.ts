// Lumen lessons shown in the "Video" tab of the Habit 4 page, keyed by section id.
// Each folder (lesson.json, scene files, audio/, avatar.png) lives under public/learn/habit-4-think-win-win/.
export const LUMEN_LESSONS: Record<string, string> = {
  "h4-mindsets":                   "/learn/habit-4-think-win-win/h4-mindsets/lumen",
  "h4-promises":                   "/learn/habit-4-think-win-win/h4-promises/lumen",
  "h4-agreements":                 "/learn/habit-4-think-win-win/h4-agreements/lumen",
};

type LumenAction =
  | { id: string; type: "speech"; text: string; audioRef?: string; duration?: number }
  | { id: string; type: "spotlight" | "laser"; elementId: string }
  | { id: string; type: "discussion"; topic: string; prompt?: string }
  | { id: string; type: `widget_${string}`; target?: string; state?: Record<string, unknown>; content?: string };

export interface LumenSlideElement {
  id: string;
  type: "text" | "shape" | "line" | "latex" | string;
  left: number;
  top: number;
  width: number;
  height?: number;
  rotate?: number;
  content?: string;
  defaultColor?: string;
  path?: string;
  viewBox?: [number, number];
  fill?: string;
  start?: [number, number];
  end?: [number, number];
  style?: string;
  color?: string;
  points?: [string, string];
  html?: string;
  align?: string;
  colWidths?: number[];
  data?: LumenTableCell[][];
  outline?: { width?: number; style?: string; color?: string };
}

export interface LumenTableCell {
  id: string;
  colspan?: number;
  rowspan?: number;
  text: string;
  style?: { bold?: boolean; em?: boolean; underline?: boolean; color?: string; backcolor?: string; fontsize?: string; align?: string };
}

export type LumenScene =
  | {
      type: "slide";
      title: string;
      canvas: { viewportSize: number; viewportRatio: number; background?: { color?: string }; elements: LumenSlideElement[] };
      actions: LumenAction[];
    }
  | { type: "interactive"; title: string; src: string; actions: LumenAction[] };

export interface LumenLesson {
  title: string;
  teacher: { name: string; color: string; avatar: string | null };
  scenes: LumenScene[];
}

export type { LumenAction };
