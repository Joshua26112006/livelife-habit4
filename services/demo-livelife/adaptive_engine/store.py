"""Where classes are kept: Firestore when it is configured, otherwise a local SQLite file with the same layout.

Two kinds of data:
  runs/{run_id}                                          one analysis of one paper: its saved steps (events), replayed to rebuild it
  runs/{run_id}/events/{seq}
  classes/{class_code}                                   a class, across every subject and paper
  classes/{class_code}/assessments/{run_id}              one paper for that class: the paper, its thinking errors, groups, who fixes what
  classes/{class_code}/students/{student_id}             a student in that class
  classes/{class_code}/students/{student_id}/assessments/{run_id}
                                                         that student's answers, results and thinking errors on that paper
The class-and-student records are written after every step and never read back to rebuild a run, so they can be reshaped
for later cross-subject work without touching the engine.

Firestore is used when FIRESTORE_PROJECT_ID is set (credentials from GOOGLE_APPLICATION_CREDENTIALS, a service-account key
file, as the Google client expects). Otherwise ADAPTIVE_DB names the SQLite file (default services/demo-livelife/data/).
"""
import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path


class LocalStore:
    """SQLite with documents addressed by Firestore-style paths, so both stores hold the same records."""

    def __init__(self, path=None):
        self.path = Path(path or os.environ.get("ADAPTIVE_DB") or Path(__file__).resolve().parents[1] / "data" / "adaptive.sqlite3")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._open = None

    @contextmanager
    def batch(self):
        """One connection and one transaction for a step's writes."""
        if self._open is not None:
            yield
            return
        self._open = self._raw()
        try:
            with self._open:
                yield
        finally:
            self._open.close()
            self._open = None

    def _raw(self):
        connection = sqlite3.connect(self.path)
        connection.execute("CREATE TABLE IF NOT EXISTS events (class_id TEXT, seq INTEGER, kind TEXT, payload TEXT, at TEXT, PRIMARY KEY (class_id, seq))")
        connection.execute("CREATE TABLE IF NOT EXISTS docs (path TEXT PRIMARY KEY, parent TEXT, data TEXT)")
        return connection

    @contextmanager
    def _connection(self):
        if self._open is not None:
            yield self._open
            return
        connection = self._raw()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def append_event(self, run_id, seq, kind, payload, at):
        with self._connection() as connection:
            connection.execute("INSERT INTO events VALUES (?,?,?,?,?)", (run_id, seq, kind, json.dumps(payload), at))

    def events(self, run_id):
        with self._connection() as connection:
            rows = connection.execute("SELECT kind, payload, at FROM events WHERE class_id=? ORDER BY seq", (run_id,)).fetchall()
        return [(kind, json.loads(payload), at) for kind, payload, at in rows]

    def set_doc(self, path, data, merge=False):
        with self._connection() as connection:
            if merge:
                row = connection.execute("SELECT data FROM docs WHERE path=?", (path,)).fetchone()
                data = {**(json.loads(row[0]) if row else {}), **data}
            connection.execute("INSERT OR REPLACE INTO docs VALUES (?,?,?)", (path, path.rsplit("/", 1)[0], json.dumps(data)))

    def get_doc(self, path):
        with self._connection() as connection:
            row = connection.execute("SELECT data FROM docs WHERE path=?", (path,)).fetchone()
        return json.loads(row[0]) if row else None

    def list_docs(self, collection):
        with self._connection() as connection:
            rows = connection.execute("SELECT path, data FROM docs WHERE parent=? ORDER BY path", (collection,)).fetchall()
        return {path.rsplit("/", 1)[1]: json.loads(data) for path, data in rows}


class FirestoreStore:
    """The same records in Firestore. Event payloads are kept as JSON text: they are only replayed, and Firestore does not
    allow every shape a payload can take (lists inside lists)."""

    def __init__(self, client):
        self.client = client

    @contextmanager
    def batch(self):
        yield

    def _doc(self, path):
        return self.client.document(path)

    def append_event(self, run_id, seq, kind, payload, at):
        self._doc(f"runs/{run_id}/events/{seq:06d}").set({"seq": seq, "kind": kind, "payload": json.dumps(payload), "at": at})

    def events(self, run_id):
        docs = self.client.collection(f"runs/{run_id}/events").order_by("seq").stream()
        return [(d["kind"], json.loads(d["payload"]), d["at"]) for d in (doc.to_dict() for doc in docs)]

    def set_doc(self, path, data, merge=False):
        self._doc(path).set(data, merge=merge)

    def get_doc(self, path):
        snapshot = self._doc(path).get()
        return snapshot.to_dict() if snapshot.exists else None

    def list_docs(self, collection):
        return {doc.id: doc.to_dict() for doc in self.client.collection(collection).stream()}


_override = None


def use(store):
    """Tests and tools may set the store directly."""
    global _override
    _override = store


def get():
    if _override is not None:
        return _override
    project = os.environ.get("FIRESTORE_PROJECT_ID")
    if project:
        from google.cloud import firestore  # only needed when Firestore is configured
        return FirestoreStore(firestore.Client(project=project))
    return LocalStore()
