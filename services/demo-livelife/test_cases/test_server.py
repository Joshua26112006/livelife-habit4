"""The demo service: serves each demos/<name>/ folder, mounts an optional backend, never leaks code or escapes a folder,
and a broken demo never stops the others. Run from services/demo-livelife:  python -m pytest test_cases"""
import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server  # noqa: E402

GOOD_BACKEND = "from fastapi import APIRouter\nrouter = APIRouter()\n@router.get('/ping')\ndef ping():\n    return {'pong': True}\n"


def make(tmp_path: Path) -> TestClient:
    d = tmp_path / "demos"
    (d / "alpha").mkdir(parents=True)
    (d / "alpha" / "index.html").write_text("<html><head><title>a</title></head><body>alpha</body></html>", encoding="utf-8")
    (d / "alpha" / "style.css").write_text("body{}", encoding="utf-8")
    (d / "alpha" / "backend.py").write_text(GOOD_BACKEND, encoding="utf-8")
    (d / "alpha" / ".secret").write_text("nope", encoding="utf-8")
    (d / "alpha" / "sub").mkdir()
    (d / "alpha" / "sub" / "index.html").write_text("<html><head></head><body>sub</body></html>", encoding="utf-8")
    (d / "beta").mkdir()
    (d / "beta" / "index.html").write_text("<html><body>beta</body></html>", encoding="utf-8")
    (d / "broken").mkdir()
    (d / "broken" / "index.html").write_text("<html><body>broken page still served</body></html>", encoding="utf-8")
    (d / "broken" / "backend.py").write_text("raise RuntimeError('boom')\n", encoding="utf-8")
    (d / "quitter").mkdir()
    (d / "quitter" / "backend.py").write_text("import sys\nsys.exit(1)\n", encoding="utf-8")
    (d / "Bad Name").mkdir()
    (d / "Bad Name" / "index.html").write_text("x", encoding="utf-8")
    (tmp_path / "outside.txt").write_text("outside", encoding="utf-8")
    return TestClient(server.create_app(d))


def test_health_lists_only_valid_demo_names(tmp_path):
    r = make(tmp_path).get("/health")
    assert r.status_code == 200 and r.json()["demos"] == ["alpha", "beta", "broken", "quitter"]


def test_a_demo_is_served_with_its_files_and_no_login(tmp_path):
    c = make(tmp_path)
    assert "alpha" in c.get("/demo-livelife/alpha").text
    assert "alpha" in c.get("/demo-livelife/alpha/").text
    assert c.get("/demo-livelife/alpha/style.css").text == "body{}"
    assert "sub" in c.get("/demo-livelife/alpha/sub").text
    assert "beta" in c.get("/demo-livelife/beta").text


def test_html_gets_a_base_tag_so_relative_links_survive_the_dropped_trailing_slash(tmp_path):
    c = make(tmp_path)
    assert '<base href="/demo-livelife/alpha/">' in c.get("/demo-livelife/alpha").text
    assert '<base href="/demo-livelife/beta/">' in c.get("/demo-livelife/beta").text   # no <head> in the file


def test_a_page_with_its_own_base_tag_is_left_alone(tmp_path):
    c = make(tmp_path)
    (tmp_path / "demos" / "beta" / "index.html").write_text('<html><head><base href="/x/"></head></html>', encoding="utf-8")
    assert c.get("/demo-livelife/beta").text.count("<base") == 1


def test_a_backend_is_mounted_under_the_demos_api(tmp_path):
    assert make(tmp_path).get("/demo-livelife/alpha/api/ping").json() == {"pong": True}


def test_a_broken_backend_is_skipped_and_the_others_still_answer(tmp_path):
    c = make(tmp_path)
    assert c.get("/demo-livelife/alpha/api/ping").status_code == 200
    assert "broken page still served" in c.get("/demo-livelife/broken").text
    assert c.get("/demo-livelife/broken/api/anything").status_code == 404


def test_code_and_hidden_files_are_never_sent(tmp_path):
    c = make(tmp_path)
    assert c.get("/demo-livelife/alpha/backend.py").status_code == 404
    assert c.get("/demo-livelife/alpha/.secret").status_code == 404


def test_no_way_out_of_a_demo_folder(tmp_path):
    c = make(tmp_path)
    for p in ("/demo-livelife/alpha/../outside.txt", "/demo-livelife/alpha/%2e%2e/outside.txt", "/demo-livelife/alpha/..%2foutside.txt",
              "/demo-livelife/alpha/%2e%2e%2foutside.txt", "/demo-livelife/alpha/..%5coutside.txt", "/demo-livelife/..%2fdemos/alpha/index.html"):
        r = c.get(p)
        assert r.status_code == 404 and "outside" not in r.text, p


def test_unknown_or_invalid_demo_names_are_404(tmp_path):
    c = make(tmp_path)
    for p in ("/demo-livelife/nope", "/demo-livelife/Bad%20Name", "/demo-livelife/nope/x.html"):
        assert c.get(p).status_code == 404, p


def test_the_demo_list_and_nothing_else_at_the_prefix(tmp_path):
    r = make(tmp_path).get("/demo-livelife")
    assert r.status_code == 200 and "/demo-livelife/alpha/" in r.json()["demos"]


def test_the_real_sample_demo_works():
    c = TestClient(server.app)
    assert "Hello from" in c.get("/demo-livelife/hello").text
    assert c.get("/demo-livelife/hello/api/ping").json() == {"message": "hello"}
    assert c.get("/demo-livelife/hello/style.css").status_code == 200
