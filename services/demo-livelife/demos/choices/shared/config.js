// One place for the copy and the two destinations. Every design version reads this.
// Paths are relative to /demo-livelife/choices/ (the server injects <base href="/demo-livelife/choices/">).
// To point the buttons somewhere else, change the hrefs below. Nothing else needs to change.
window.AIDA = {
  brand: "AI Decoder Academy",
  brandShort: "AIDA",
  programme: "Discovering the Leader in Me",
  level: "Level 5",
  habit: "Habit 4: Think Win-Win",
  greeting: "Welcome, coach",
  question: "Where would you like to begin?",
  choices: [
    {
      id: "self",
      title: "Self assessment",
      short: "Reflect",
      body: "Reflect on how you facilitate Think Win-Win and plan your next class.",
      meta: ["8 situations", "Scores and a coaching plan"],
      cta: "Start assessment",
      href: "../../livelife/habit-4/teacher", // the teacher assessment, in the lesson page's glass UI
    },
    {
      id: "class",
      title: "Classroom content",
      short: "Teach",
      body: "Slides, videos and scenarios ready to teach Habit 4 today.",
      meta: ["3 phases", "Blog and video"],
      cta: "Open content",
      href: "../../livelife/habit-4", // the Habit 4 lesson
    },
    {
      id: "outcome",
      title: "Assessment outcome",
      short: "Results",
      body: "See the latest teacher assessment outcome.",
      meta: [],
      cta: "View outcome",
      href: "../../livelife/habit-4/teacher?view=outcome", // the latest teacher outcome (same page as Self assessment)
    },
  ],
};
