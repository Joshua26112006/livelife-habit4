// Interactive activities for the Habit 4 Conceptual screens (app/livelife/habit-4/Activities.tsx draws them).
// Pure data, so the LiveLife expert can read and change the wording without touching any component.
// Scenarios come from the production brief (Maya and Arjun, Leo's book, the shared console, Mia and Leo).
// Wording is ORIGINAL and illustrative; FOR SME REVIEW. No points, scores or ranks anywhere.

export interface BranchOutcome {
  tag: string;                       // short label shown on the result, e.g. "Win-Lose"
  tone: "good" | "bad" | "meh";      // colour only
  faces: [string, string];           // how each person feels, as emoji
  names: [string, string];
  text: string;                      // what happened and why
}
export interface BranchStoryData {
  kicker: string;
  headline: string;                  // *star* marks the highlighted word
  setup: string;
  choices: { label: string; outcome: BranchOutcome }[];
  goodNote: string;                  // shown after the best choice
}

export const H4_BRANCH: Record<string, BranchStoryData[]> = {
  "h4-mindsets": [
    {
      kicker: "Choose what happens",
      headline: "Movie or park? *You* decide",
      setup: "Maya says, \"Let's go to the movie!\" Arjun says, \"I hoped we'd go to the park.\" Both want a fun day out together. What should they do?",
      choices: [
        { label: "Maya decides, because she asked first", outcome: { tag: "Win-Lose", tone: "bad", faces: ["😄", "😕"], names: ["Maya", "Arjun"],
          text: "One wish wins and the other is never explored. Arjun goes along, but he does not feel heard." } },
        { label: "Arjun gives in so there is no argument", outcome: { tag: "Lose-Win", tone: "bad", faces: ["😄", "😶"], names: ["Maya", "Arjun"],
          text: "The argument is avoided, but Arjun gave up what mattered to him and feels unheard." } },
        { label: "They ask what each one enjoys, then brainstorm", outcome: { tag: "Win-Win", tone: "good", faces: ["😄", "😄"], names: ["Maya", "Arjun"],
          text: "Listening first shows both people matter. Park today and movie next time, or something they both enjoy." } },
      ],
      goodNote: "That is the Win-Win way: listen, brainstorm, then check that it is fair and both agree.",
    },
  ],
  "h4-promises": [
    {
      kicker: "Choose what happens",
      headline: "Leo can't finish the *book*",
      setup: "Leo promised his friend he would return a book today, but he has not finished reading it. What should Leo do?",
      choices: [
        { label: "Hide the book and say nothing", outcome: { tag: "Withdrawal", tone: "bad", faces: ["😬", "😟"], names: ["Leo", "Friend"],
          text: "His friend waits and worries. Hiding a problem makes it bigger and trust shrinks." } },
        { label: "Wait until the day is over, then explain", outcome: { tag: "Withdrawal", tone: "meh", faces: ["😅", "😕"], names: ["Leo", "Friend"],
          text: "Explaining is better than hiding, but waiting means his friend had no chance to plan." } },
        { label: "Tell his friend early, say sorry and agree a new day", outcome: { tag: "Deposit", tone: "good", faces: ["😊", "😊"], names: ["Leo", "Friend"],
          text: "Honest, early and with a new plan: \"I can't finish today. Could I return it tomorrow?\" Trust stays strong." } },
      ],
      goodNote: "Speaking up early, saying sorry and making a new plan protects trust.",
    },
  ],
};

export interface BankAction { text: string; kind: "deposit" | "withdrawal" }
export const H4_BANK: BankAction[] = [
  { text: "Keep a promise you made", kind: "deposit" },
  { text: "Listen without interrupting", kind: "deposit" },
  { text: "Say sorry and make a new plan", kind: "deposit" },
  { text: "Be kind when a friend is sad", kind: "deposit" },
  { text: "Break a promise and say nothing", kind: "withdrawal" },
  { text: "Ignore a friend who is talking to you", kind: "withdrawal" },
  { text: "Make a promise you know you can't keep", kind: "withdrawal" },
  { text: "Laugh at a friend's idea", kind: "withdrawal" },
];

// Section 3 agreement builder: one sentence belongs in each tile (Mia wants blocks, Leo wants a board game).
export const H4_AGREEMENT = {
  scenario: "Mia wants to build with blocks. Leo wants to play a board game. Build their Win-Win Agreement: for each sentence, tap the part it belongs to.",
  parts: ["Desired Results", "Guidelines", "Resources", "Accountability", "Consequences"],
  lines: [
    { text: "Both of us enjoy playing and nobody feels left out.", answer: "Desired Results" },
    { text: "We take turns: blocks first, then the board game.", answer: "Guidelines" },
    { text: "The block set, the board game and a kitchen timer.", answer: "Resources" },
    { text: "At the end of the day we check that both turns happened.", answer: "Accountability" },
    { text: "If a turn is missed, we talk and give it back tomorrow.", answer: "Consequences" },
  ],
};
