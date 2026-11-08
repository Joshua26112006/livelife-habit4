# Demo service

A small Python (FastAPI) service for the LiveLife demo. No login, no database, no secrets.

Anything in `demos/<name>/` is served at `/demo-livelife/<name>/`. The Next.js site forwards `/demo-livelife/*`
to this service (see `next.config.mjs`), so everything is reachable from one address.

## Folders
- `demos/choices/` the coach landing page (start here)
- `demos/livelife-home/` the three-button front page
- `demos/livelife-student/` and `demos/livelife-teacher/` the assessments' small APIs and their static scorecard pages
- `demos/hello/` a minimal example

## Add your own demo
1. Create `demos/<your-name>/` (lower-case letters, digits, `-` or `_`; max 64 characters).
2. Put an `index.html` in it, plus any CSS, JS and images. **Use relative links** (`style.css`, `api/ping`), never a link that starts with `/`.
3. Need a backend? Add `backend.py` with `router = APIRouter()` (see `demos/hello/backend.py`). It is mounted at `/demo-livelife/<your-name>/api/`. One file only; read your own files with `Path(__file__).parent`.

## Rules
- Public and no sign-in: keep real student data, real company data, keys and passwords out of this folder.
- Your Python runs in the same process as the others. No endless loops, no heavy work on import. If a backend fails to load, it is skipped and the others keep working.
- `.py` files and files starting with `.` are never sent to the browser.

## Run it
```
pip install -r requirements.txt
python server.py        # http://localhost:8080/demo-livelife/<name>/
```
From the repo root, `npm run dev` starts this service and the website together.

## Tests
`python -m pytest test_cases` (from this folder; needs `fastapi` and `httpx`).
