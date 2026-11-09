"""Scored assessment sheets per class and student, so the class-level modules have a whole class to work with.

In memory and bounded, like the rest of this demo: everything is lost on a restart. A class id must be long and random because
the service has no sign-in; student ids are opaque codes, never names. A real deployment replaces this with a database.
"""
import re
import threading
from collections import OrderedDict

CLASS_ID = re.compile(r"^[A-Za-z0-9_-]{16,40}$")
STUDENT_ID = re.compile(r"^[A-Za-z0-9_-]{1,40}$")
MAX_CLASSES = 50
MAX_STUDENTS_PER_CLASS = 200
MAX_VERSIONS_PER_STUDENT = 5


def valid_ids(class_id, student_id):
    return bool(CLASS_ID.match(class_id or "") and STUDENT_ID.match(student_id or ""))


class SubmissionStore:
    def __init__(self):
        self._classes = OrderedDict()
        self._lock = threading.Lock()

    def add(self, class_id, student_id, submission):
        """Keep this attempt beside the student's earlier ones. False when the class is full."""
        with self._lock:
            roster = self._classes.setdefault(class_id, {})
            self._classes.move_to_end(class_id)
            while len(self._classes) > MAX_CLASSES:
                self._classes.popitem(last=False)
            if student_id not in roster and len(roster) >= MAX_STUDENTS_PER_CLASS:
                return False
            versions = roster.setdefault(student_id, [])
            versions.append(submission)
            del versions[:-MAX_VERSIONS_PER_STUDENT]
            return True

    def latest(self, class_id):
        """Each student's most recent attempt, as (student_id, submission)."""
        with self._lock:
            return [(student, versions[-1]) for student, versions in self._classes.get(class_id, {}).items()]

    def clear(self):
        with self._lock:
            self._classes.clear()


STORE = SubmissionStore()
