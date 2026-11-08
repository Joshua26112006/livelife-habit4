// Content types for the Habit 4 lesson. (In the full product these live beside the content of every chapter;
// this demo repo keeps only the shapes that Habit 4 uses.)

export interface SeededThinkCardOption {
  text: string;
  hook: string;
}

export interface SeededThinkCard {
  question: string;
  imageUrl: string;        // populated after one-time generation via /api/learn/seed-images
  imageMissing?: boolean;  // the file is gone: see lib/learnMissingAssets.ts
  imagePrompt: string;     // used by seed-images route
  options: SeededThinkCardOption[];
  /** Overrides the default "🤔 Think about it..." eyebrow — plants a subtle
      continuity cue between cards in a progressive sequence. */
  eyebrow?: string;
}


export interface LearnSection {
  id: string;
  title: string;
  description: string;
  topic: string;
  emoji: string;
  thinkCards?: SeededThinkCard[];
}

export interface LearnChapter {
  id: string;
  title: string;
  subject: string;
  gradeLevel: string;
  emoji: string;
  gradient: string;
  sections: LearnSection[];
}


export interface MasteryStep {
  label: string;        // scaffolding shown to the student, e.g. "Total outcomes"
  answer: string;       // value that must appear in the working, e.g. "8" or "3/8"
  accept?: string[];    // extra accepted literal forms
}

export interface MasteryQuestion {
  conceptTitle: string;              // matches the section's concept-card title
  source: string;                    // e.g. "NCERT Ex 14.1, Q8"
  question: string;                  // the ask (context folded in)
  kind?: "numeric" | "conceptual";   // default "numeric"
  steps?: MasteryStep[];             // numeric: ordered working steps (last = final answer)
  keywords?: string[];               // conceptual: key terms the answer must mention
  solution: string;                  // worked solution / model answer
}


export interface RetentionCard { question: string; answer: string; imageConcept: string; imageUrl: string; }
export interface RetentionSummary { imageConcept: string; imageUrl: string; }
export interface RetentionSeed { cards: RetentionCard[]; summary: RetentionSummary; }

// ─── Concept card types ───────────────────────────────────────────────────────

export type ConceptVisual = { type: "none" };

export interface ConceptCard {
  title: string;
  hook: string;        // 1 punchy sentence shown large
  body: string[];      // 1–3 explanation paragraphs
  visual: ConceptVisual;
  tip?: string;        // optional amber tip box
  imagePrompt?: string; // the prompt the card picture was made from
  imageUrl?: string;
}

export interface SectionConceptCards {
  cards: ConceptCard[];
}

// ─── Spot It (concept-check) types ────────────────────────────────────────────
// One question per concept card — the interactive "identify the event" checkpoint
// that sits between Learn and Practice in the Concept phase.

export interface IdentifyQuestion {
  conceptTitle: string;   // which concept card this checks (shown as a chip)
  emoji: string;          // scenario emoji
  scenario: string;       // the real-life setup
  prompt: string;         // the question asked
  options: string[];      // tap options
  correct: number[];      // index(es) of correct option(s)
  multi?: boolean;        // true => "tap all that apply" (favourable-outcomes style)
  explanation: string;    // shown after answering — the "why"
}


export interface BarData {
  value: number;
  label: string;
  color: "purple" | "cyan" | "orange" | "green";
}

// Each TextPart[] is one display line; a BlogVisual can be multiple lines of parts.
export type TextPart = {
  text: string;
  bold?: boolean;
  color?: "accent" | "success" | "highlight";
};

export type BlogVisual =
  | { type: "bars"; bars: BarData[] }
  | { type: "equation"; lines: TextPart[][] };

export interface BlogStep {
  method: string;
  instruction: string;
  visual: BlogVisual;
  why: string;
  // Optional per-step illustration (student + mascot, step title/labels baked
  // into the image itself) — matches the reference project's step-solver
  // style. Falls back to the SVG `visual` above when absent.
  imageUrl?: string;
}

export interface BlogProblem {
  title: string;
  problem: string;
  steps: BlogStep[];
  imagePrompt?: string; // Pixar scene for the problem (generated via seed-problem-images)
  imageUrl?: string;    // populated after one-time generation
}

export interface SectionBlogContent {
  keyFacts: {
    what: string;
    formula: string;
    example: string;
    tip: string;
  };
  problems: BlogProblem[];
}
