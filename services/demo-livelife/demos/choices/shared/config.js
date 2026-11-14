// One place for the copy and the destination. Every design version reads this.
// Paths are relative to /demo-livelife/choices/ (the server injects <base href="/demo-livelife/choices/">).
// To point the button somewhere else, change the href below. Nothing else needs to change.
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
      id: "class",
      title: "Classroom content",
      short: "Teach",
      body: "Slides, videos and scenarios ready to teach Habit 4 today.",
      meta: ["3 phases", "Blog and video"],
      cta: "Open content",
      href: "../../livelife/habit-4", // the Habit 4 lesson
    },
  ],
};
