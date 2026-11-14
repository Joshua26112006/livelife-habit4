# LiveLife · Habit 4 demo

A standalone, runnable demo of the LiveLife "Habit 4: Think Win-Win" lesson, made so someone can see its look
and feel and try it end to end.

| Screen | Address (after `npm run dev`) |
|---|---|
| Coach landing page (start here) | http://localhost:3000 |
| Habit 4 lesson: 3 phases (Engagement, Understanding, Retention), each section with a blog and a video | http://localhost:3000/livelife/habit-4 |
| Generated content (think cards, blog, quiz, flashcards) | http://localhost:3000/demo-livelife/livelife-content-generation/ |

## Run it

You need Node 20+ and Python 3.10+.

```
npm install
pip install -r services/demo-livelife/requirements.txt
npm run dev
```

`npm run dev` starts two things together: the website (Next.js, port 3000) and a small Python service (port 8080)
that serves the landing page and the generated-content page, and that the website forwards `/demo-livelife/*` to.
If a port is busy: `WEB_PORT=3100 DEMO_PORT=8090 npm run dev`.

Python service tests: `npm run test:demo`.

## What is in the lesson

Three sections (Mindsets, Promises, Agreements). Each one has:

- **Engagement:** think cards.
- **Understanding:** the lesson as a **blog** with its activities, or as a short interactive **video** (the Lumen player).
- **Retention:** flashcards and a study guide.

## No database, no login, no AI calls

- Nothing here connects to a database, an accounts system, an AI provider or any storage service, and there is no
  sign-in. Nothing you do on the pages is saved.
- The lesson content (text, activities, images, videos) is plain files in this repo: `lib/learnContent/habit4*.ts`,
  `public/learn-seeds/`, `public/learn/habit-4-think-win-win/`. Only Habit 4 content is included; no other chapter or subject.
- The only network request the pages make for their look is the Plus Jakarta Sans font from Google on first load.

## What is in the repo

- `app/livelife/habit-4/` the lesson screen
- `components/learn/concept/` the Lumen video player
- `lib/learnContent/` the Habit 4 content; `lib/learn/lumenLessons.ts` the three video lessons
- `services/demo-livelife/` the Python service: the landing page and the generated-content page
- `public/` images and the Lumen lesson videos for the three Habit 4 sections
