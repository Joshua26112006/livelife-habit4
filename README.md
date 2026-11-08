# LiveLife · Habit 4 demo

A standalone, runnable demo of the LiveLife "Habit 4: Think Win-Win" experience, made so someone can see its look
and feel and try it end to end.

It has four things to see:

| Screen | Address (after `npm run dev`) |
|---|---|
| Coach landing page (start here) | http://localhost:3000 |
| Habit 4 lesson (3 phases: Engagement, Understanding, Retention, with videos) + **student assessment** | http://localhost:3000/livelife/habit-4 |
| **Teacher assessment** | http://localhost:3000/livelife/habit-4/teacher |
| Latest teacher result | http://localhost:3000/livelife/habit-4/teacher?view=outcome |

## Run it

You need Node 20+ and Python 3.10+.

```
npm install
pip install -r services/demo-livelife/requirements.txt
npm run dev
```

`npm run dev` starts two things together: the website (Next.js, port 3000) and a small Python service (port 8080)
that the website forwards `/demo-livelife/*` to. If a port is busy: `WEB_PORT=3100 DEMO_PORT=8090 npm run dev`.

Tests: `npm test` (website helpers) and `npm run test:demo` (the Python service).

## Is there a database? No.

- **No database, no login, no accounts.** Nothing here connects to a database, an accounts system or any storage service.
- **What happens to a submitted assessment:** the Python service keeps only the **latest** student result and the
  **latest** teacher result **in its own memory**. A new submission replaces the old one. If you stop or restart the
  service, they are gone. That is by design for a single-person demo.
- **The "scorecard / outcome" link** just reads that in-memory result back.
- **The lesson content** (text, activities, images, videos) is plain files in this repo: `lib/learnContent/habit4*.ts`,
  `public/learn-seeds/`, `public/learn/habit-4-think-win-win/`. Only Habit 4 content is included; no other chapter or subject.
- **A real deployment would differ:** it would store results in a database and keep them per student. This demo
  deliberately does not.

## AI marking (optional)

The written answers can be marked by an AI model. This is **off by default**, and the demo works without it
(answers are collected, but the written answers get no marks).

To turn it on, copy `.env.example` to `.env.local`, set `DEMO_LIVELIFE_SCORE=1` and add an `OPENROUTER_API_KEY`
(a key with a low spend limit is wise: the page is public once deployed). The route is
`app/api/demo-livelife-score/route.ts`; it has per-address and daily caps and only ever scores the fixed questions.
Answers are sent to the AI provider to be marked and are not logged or stored here.

## Not ready for real children

This is a demo. It has no safeguarding check on what is typed and no teacher review of AI marks. Both would be
required before real students use it.

## What is in the repo

- `app/livelife/habit-4/` the lesson, student assessment and teacher assessment screens
- `app/api/demo-livelife-score/` the AI marking route
- `lib/livelifeDemo/` the marking rubrics and rate limits
- `services/demo-livelife/` the Python service: landing page, home page and the two assessments' small API
- `public/` images and the Lumen lesson videos for the three Habit 4 sections
