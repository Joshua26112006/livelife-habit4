"""Bulk answer sheets. The main input is the handwriting reader's JSON: one entry per student, each with the transcribed
segments of their sheet. A CSV (one row per student, one column per question) is still read for older sample files.

JSON, per student:  {"studentId": "...", "segments": [{"questionNumber": 2, "status": "active", "transcription": "...", ...}]}
  status            "active" is the answer; "rough" is working kept beside it; "struck" (crossed out) is ignored
  transcription     the student's full working, as written; this is what the engine reads, not "studentAnswer"
  questionNumber    matched to a paper item's "number" (or its position when items have none)
  parts             a question with parts, such as Q2 (i) and (ii), is split at its "(i)", "(ii)" markers. Each item names
                    its part ("part": "ii"); the working before the first marker (the total, say) goes with every part
  structureConfidence "low" and twoAttempts true are passed on as warnings for the teacher

Nothing is silently dropped: a bad entry is reported with its reason, and a doubtful answer is reported as a warning.
"""
import csv
import io
import json
import re

ID_COLUMN = "student_id"
STUDENT_ID = re.compile(r"^[A-Za-z0-9_-]{1,40}$")
MAX_BYTES = 2_000_000
MAX_STUDENTS = 200
MAX_CELL_CHARS = 2000
_PART = re.compile(r"\(\s*(vi{0,3}|iv|i{1,3})\s*\)", re.I)


class UploadError(ValueError):
    """The file as a whole cannot be used."""


def _items(questions):
    """Accepts item dicts or bare ids, so callers holding only ids still work."""
    return [q if isinstance(q, dict) else {"id": q} for q in questions]


def _cut(text, warn):
    if len(text) > MAX_CELL_CHARS:
        warn("Answer was too long and was cut.")
        return text[:MAX_CELL_CHARS]
    return text


def _split_parts(text):
    """'pre (i) a (ii) b' -> ('pre', {'i': 'a', 'ii': 'b'}). A part written twice keeps the later one."""
    marks = list(_PART.finditer(text))
    if not marks:
        return text.strip(), {}
    parts = {}
    for mark, following in zip(marks, marks[1:] + [None]):
        parts[mark[1].lower()] = text[mark.end():following.start() if following else len(text)].strip()
    return text[:marks[0].start()].strip(), parts


def _question_keys(items):
    """item id -> (question number, part or None)."""
    return {item["id"]: (int(item.get("number", position + 1)), (item.get("part") or None)) for position, item in enumerate(items)}


def _read_json(data, items):
    try:
        body = json.loads(data.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as err:
        raise UploadError("The file is not valid JSON.") from err
    students = body.get("students") if isinstance(body, dict) else body
    if not isinstance(students, list):
        raise UploadError("The JSON needs a 'students' list.")
    if len(students) > MAX_STUDENTS:
        raise UploadError(f"The file has more than {MAX_STUDENTS} students.")
    keys = _question_keys(items)
    numbers = {number for number, _ in keys.values()}
    first_part = {}
    for item_id, (number, part) in keys.items():
        first_part.setdefault(number, item_id)

    sheets, rejected, warnings, seen = [], [], [], set()
    for position, entry in enumerate(students, start=1):
        student = str(entry.get("studentId", "")).strip() if isinstance(entry, dict) else ""
        if not STUDENT_ID.match(student):
            rejected.append({"row": position, "reason": "studentId is missing or has characters other than letters, digits, - or _."})
            continue
        if student in seen:
            rejected.append({"row": position, "student": student, "reason": "This studentId appears more than once."})
            continue
        seen.add(student)
        segments = entry.get("segments") if isinstance(entry.get("segments"), list) else []
        written, rough = {}, {}
        for segment in segments:
            if not isinstance(segment, dict):
                continue
            try:
                number = int(segment.get("questionNumber"))
            except (TypeError, ValueError):
                continue
            text = str(segment.get("transcription") or "").strip()
            status = segment.get("status", "active")
            if number not in numbers:
                if status == "active" and text:
                    warnings.append({"row": position, "student": student, "question": f"Q{number}", "message": "This question is not on the paper, so it was not read."})
                continue
            if status == "active" and text:
                written.setdefault(number, []).append(text)
                if segment.get("structureConfidence") == "low":
                    warnings.append({"row": position, "student": student, "question": f"Q{number}", "message": "The handwriting was hard to read here. Check the sheet."})
                if segment.get("twoAttempts"):
                    warnings.append({"row": position, "student": student, "question": f"Q{number}", "message": "Two attempts on the sheet; the last one was read."})
            elif status == "rough" and text:
                rough.setdefault(number, []).append(text)

        answers = {}
        for item_id, (number, part) in keys.items():
            warn = lambda message, q=item_id: warnings.append({"row": position, "student": student, "question": q, "message": message})
            text = "\n".join(written.get(number, []))
            working = "\n".join(rough.get(number, []))
            if part:
                pre, parts = _split_parts(text)
                if not parts and text and first_part[number] == item_id:
                    warn("No (i), (ii) markers were found, so the whole answer was read as this part.")
                    body_text = text
                else:
                    body_text = "\n".join(x for x in (pre, parts.get(part.lower(), "")) if x) if parts.get(part.lower()) else ""
            else:
                body_text = text
            answers[item_id] = _cut("\n".join(x for x in (working, body_text) if x) if body_text else "", warn)
        sheets.append({"id": student, "answers": answers})
    if not sheets:
        raise UploadError("No student could be used.")
    return {"sheets": sheets, "rejected": rejected, "warnings": warnings}


def _read_csv(data, items):
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as err:
        raise UploadError("The file is not UTF-8 text.") from err
    rows = [row for row in csv.reader(io.StringIO(text)) if any(str(c).strip() for c in row)]
    if not rows:
        raise UploadError("The file has no rows.")
    question_ids = [i["id"] for i in items]
    header = [str(c).strip() for c in rows[0]]
    if ID_COLUMN not in header:
        raise UploadError(f"The first row must include a '{ID_COLUMN}' column.")
    missing = [q for q in question_ids if q not in header]
    unknown = [c for c in header if c and c != ID_COLUMN and c not in question_ids]
    if missing or unknown:
        raise UploadError(f"Columns do not match this paper. Missing: {', '.join(missing) or 'none'}. Unexpected: {', '.join(unknown) or 'none'}.")
    if len(rows) - 1 > MAX_STUDENTS:
        raise UploadError(f"The file has more than {MAX_STUDENTS} students.")

    position = {name: i for i, name in enumerate(header)}
    sheets, rejected, warnings, seen = [], [], [], set()
    for number, row in enumerate(rows[1:], start=2):
        student = str(row[position[ID_COLUMN]]).strip() if position[ID_COLUMN] < len(row) else ""
        if not STUDENT_ID.match(student):
            rejected.append({"row": number, "reason": "Student ID is missing or has characters other than letters, digits, - or _."})
            continue
        if student in seen:
            rejected.append({"row": number, "student": student, "reason": "This student ID appears more than once."})
            continue
        seen.add(student)
        answers = {}
        for question in question_ids:
            cell = str(row[position[question]]).strip() if position[question] < len(row) else ""
            answers[question] = _cut(cell, lambda message, q=question: warnings.append({"row": number, "student": student, "question": q, "message": message}))
        sheets.append({"id": student, "answers": answers})
    if not sheets:
        raise UploadError("No row could be used.")
    return {"sheets": sheets, "rejected": rejected, "warnings": warnings}


def parse_upload(data, filename, questions):
    """Bytes -> {sheets, rejected, warnings}. JSON is recognised by its content, so the file name does not matter.
    Raises UploadError when the file itself is unusable."""
    if not data:
        raise UploadError("The file is empty.")
    if len(data) > MAX_BYTES:
        raise UploadError("The file is larger than 2 MB.")
    if filename.lower().endswith((".xlsx", ".xlsm", ".xls")):
        raise UploadError("Excel files are not read. Upload the handwriting reader's JSON.")
    items = _items(questions)
    looks_like_json = data.lstrip(b"\xef\xbb\xbf \t\r\n")[:1] in (b"{", b"[")
    return _read_json(data, items) if looks_like_json or filename.lower().endswith(".json") else _read_csv(data, items)


def json_template(items):
    """An empty answer file in the JSON format, one segment per question number."""
    numbers = sorted({number for number, _ in _question_keys(_items(items)).values()})
    segments = [{"questionNumber": n, "status": "active", "transcription": ""} for n in numbers]
    return json.dumps({"students": [{"studentId": "student1", "segments": segments}]}, indent=2) + "\n"


def to_csv(columns, rows):
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(columns)
    writer.writerows(rows)
    return out.getvalue()
