"""Demo service: serves every folder under demos/ at /demo-livelife/<name>/. NO login, NO database, NO secrets.
A demo folder holds static files (html, css, js, images) and, optionally, a backend.py with a FastAPI `router`
that is mounted at /demo-livelife/<name>/api/. A folder whose backend fails to load is skipped and logged; the others keep working.
The website forwards /demo-livelife/* here (next.config.mjs, DEMO_SERVICE_URL). Start: python server.py  (PORT from the host)."""
import importlib.util
import logging
import os
import re
import socket
from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response

log = logging.getLogger("demo_livelife")
PREFIX = "/demo-livelife"
HERE = Path(__file__).resolve().parent
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")   # a demo folder name: lower-case letters, digits, - and _
HIDDEN_SUFFIXES = {".py", ".pyc", ".pyo"}             # code is never sent to the browser
BASE_RE = re.compile(r"<base\b", re.I)
HEAD_RE = re.compile(r"<head[^>]*>", re.I)


def _is_demo_dir(p: Path) -> bool:
    return p.is_dir() and NAME_RE.match(p.name) is not None


def _load_backend(name: str, folder: Path):
    """The demo's `router` from folder/backend.py, or None. Never raises: a broken demo must not stop the others."""
    file = folder / "backend.py"
    if not file.is_file():
        return None
    try:
        spec = importlib.util.spec_from_file_location(f"demo_livelife_backend_{name.replace('-', '_')}", file)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        router = getattr(mod, "router", None)
        if not isinstance(router, APIRouter):
            log.error("demo %s skipped: backend.py has no `router = APIRouter()`", name)
            return None
        return router
    except BaseException as e:   # SystemExit included: a demo that calls exit() must not end the service
        log.error("demo %s: backend not loaded (%s: %s)", name, type(e).__name__, e)
        return None


def _safe_file(folder: Path, rel: str) -> Path | None:
    """The file inside `folder` for the URL path `rel`, or None. Refuses anything outside the folder, hidden names and code files."""
    parts = [p for p in rel.split("/") if p != ""]
    if any(p in (".", "..") or p.startswith(".") or "\\" in p or "\x00" in p for p in parts):
        return None
    target = folder.joinpath(*parts) if parts else folder
    try:
        resolved = target.resolve()
        resolved.relative_to(folder.resolve())
    except (ValueError, OSError):
        return None
    if resolved.is_dir():
        resolved = resolved / "index.html"
    if not resolved.is_file() or resolved.suffix.lower() in HIDDEN_SUFFIXES:
        return None
    return resolved


def _html_with_base(path: Path, name: str) -> Response:
    """The website drops a trailing slash (/demo-livelife/x/ -> /demo-livelife/x), which would break a page's relative
    links (style.css). A <base> tag pointing at the folder keeps them working. Skipped if the page sets its own."""
    text = path.read_text(encoding="utf-8", errors="replace")
    if not BASE_RE.search(text):
        tag = f'<base href="{PREFIX}/{name}/">'
        m = HEAD_RE.search(text)
        text = text[: m.end()] + tag + text[m.end():] if m else tag + text
    return HTMLResponse(text, headers={"Cache-Control": "no-cache"})


def create_app(demos_dir: Path | None = None) -> FastAPI:
    demos = Path(demos_dir) if demos_dir else HERE / "demos"
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    names = sorted(p.name for p in demos.iterdir() if _is_demo_dir(p)) if demos.is_dir() else []

    @app.get("/health")
    def health():
        return {"ok": True, "demos": names}

    for name in names:   # backends first, so /demo-livelife/<name>/api/... wins over the static route below
        router = _load_backend(name, demos / name)
        if router is not None:
            app.include_router(router, prefix=f"{PREFIX}/{name}/api")

    @app.get(PREFIX)
    def index():
        return JSONResponse({"demos": [f"{PREFIX}/{n}/" for n in names]})

    @app.get(PREFIX + "/{name}")
    @app.get(PREFIX + "/{name}/{rest:path}")
    def serve(name: str, rest: str = ""):
        if name not in names:
            return JSONResponse({"detail": "Not found"}, status_code=404)
        f = _safe_file(demos / name, rest)
        if f is None:
            return JSONResponse({"detail": "Not found"}, status_code=404)
        if f.suffix.lower() in (".html", ".htm"):
            return _html_with_base(f, name)
        return FileResponse(f, headers={"Cache-Control": "no-cache"})

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    # One socket for IPv4 AND IPv6: a host's health check may be IPv4 while its private network (the website's forwarding) is IPv6.
    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("::", int(os.environ.get("PORT", "8080"))))
    uvicorn.Server(uvicorn.Config(app, proxy_headers=True, forwarded_allow_ips="*")).run(sockets=[sock])
