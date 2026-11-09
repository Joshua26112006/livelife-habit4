"""What each module asks the AI, and how each reply is checked before it can touch anything.

The model never decides a status, a group or mastery: those stay in the rules. Each module has one job for it, limited to the
material given here. Every reply is validated, and anything invalid is ignored so the rules' result stands.
Student IDs are never sent, except M8's opaque codes so notes can be matched to students.
"""
from .pack import UNMAPPED

GUARD = ("You support a school teacher. Use only the material given. Describe answers and needs, never label a child's ability or "
         "character. Do not claim that any teaching method is proven to work. Reply with one JSON object only.")
MAX_TEXT = 400
BANNED = ("weak", "slow learner", "lazy", "low ability", "stupid", "bad student", "learning style")


def clean(value, limit=MAX_TEXT):
    return " ".join(value.split())[:limit] if isinstance(value, str) else ""


def safe_text(value, limit=MAX_TEXT):
    text = clean(value, limit)
    return "" if any(word in text.lower() for word in BANNED) else text


def _task(pack, task_id, instruction, material, max_tokens=700):
    return {"id": str(task_id), "kind": "json", "system": f"{GUARD} Subject and scope: {pack.brief} {instruction}", "user": material, "max_tokens": max_tokens}


def _catalogue(pack):
    return "\n".join(f"{code}: {e['name']}. {e['belief']}" for code, e in pack.misconceptions.items() if e["kind"] == "belief")


# ---- Modules 3 and 7: reading answers the rules cannot judge alone
def marking_tasks(pack, sheets, items):
    """Rubric marking for written answers; catalogue-limited reading for answers the rules could not place."""
    tasks = []
    written = [i for i in items if i["type"] == pack.written_type]
    for sheet in sheets:
        answers = {i["id"]: sheet["answers"].get(i["id"], "") for i in written}
        pending = {qid: text for qid, text in answers.items() if isinstance(text, str) and text.strip()}
        if pending:
            tasks.append({"id": sheet["id"], "kind": "rubric", "answers": {
                qid: {"text": text, "key": pack.rubric_key(item), "question": item["text"]}
                for qid, text in pending.items() for item in written if item["id"] == qid}})
    for sheet in sheets:
        unplaced = []
        for item in items:
            if item["type"] == pack.written_type:
                continue
            trace = pack.read_answer(item, sheet["answers"].get(item["id"], ""))
            if trace["result"] == "argument_unclear" or any(f["belief"] == UNMAPPED for f in trace["findings"]):
                unplaced.append(f'{item["id"]}. Question: {item["text"]}\nAnswer: """{trace["working"]}"""')
        if unplaced:
            tasks.append(_task(pack, f'read:{sheet["id"]}', 'For each answer choose the single catalogue code that best explains it, or "unmapped" if none clearly does. '
                                                     'Never invent a code. Reply as {"answers": {"<question id>": {"code": "...", "why": "one short sentence quoting the answer"}}}.',
                               f"Catalogue:\n{_catalogue(pack)}\n\nAnswers:\n" + "\n\n".join(unplaced)))
    return tasks


def apply_marking(pack, sheets, items, results):
    """Validated marks and readings merged into the sheets. Returns (sheets, how many students the AI failed for)."""
    written = {i["id"] for i in items if i["type"] == pack.written_type}
    known = {i["id"] for i in items}
    updated, failed = [], 0
    for sheet in sheets:
        answers, hints = dict(sheet["answers"]), {}
        marks = results.get(sheet["id"])
        for qid in written:
            text = answers.get(qid, "")
            mark = (marks or {}).get(qid) if isinstance(marks, dict) else None
            score = mark.get("score") if isinstance(mark, dict) else None
            valid = isinstance(score, int) and not isinstance(score, bool) and 0 <= score <= 4
            answers[qid] = {"text": text, "score": score if valid else None, "flag": bool(mark.get("flag")) if valid else False,
                            "evidence": clean(mark.get("evidence")) if valid else ""}
        if written and marks is None and any(answers[q]["text"].strip() for q in written):
            failed += 1
        reading = results.get(f'read:{sheet["id"]}')
        for qid, hint in (reading.get("answers", {}) if isinstance(reading, dict) else {}).items():
            code = hint.get("code") if isinstance(hint, dict) else None
            if qid in known and pack.misconceptions.get(code, {}).get("kind") == "belief":
                hints[qid] = {"code": code, "why": clean(hint.get("why"))}
        updated.append({**sheet, "answers": answers, "ai_hints": hints})
    return updated, failed


# ---- Module 4
def intervention_tasks(pack, cycle):
    needs = {}
    for mapping in cycle.mappings:
        primary = mapping["primary"]
        if primary and primary["candidates"]:
            entry = needs.setdefault(primary["misconception_id"], {"candidates": primary["candidates"], "students": 0})
            entry["students"] += 1
    tasks = []
    for code, need in needs.items():
        options = "\n".join(f'{i}: {pack.interventions[i]["title"]}. Steps: {" ".join(pack.interventions[i]["steps"])}' for i in need["candidates"])
        lines = [f["evidence"] for d in cycle.diagnoses.values() for t in d["traces"] for f in t["findings"] if f["belief"] == code][:4]
        tasks.append(_task(pack, code, 'Choose the one curated intervention that best fits this class evidence. You may only pick from the list. '
                                 'Reply as {"choice": "<id>", "why": "two short sentences for the teacher"}.',
                           f"Need: {pack.misconceptions[code]['name']}\nStudents: {need['students']}\nEvidence seen:\n- " + "\n- ".join(map(str, lines)) +
                           f"\n\nCurated interventions:\n{options}", 300))
    return tasks


def apply_interventions(cycle, results):
    preferred, why = {}, {}
    for mapping in cycle.mappings:
        primary = mapping["primary"]
        if not primary:
            continue
        code = primary["misconception_id"]
        reply = results.get(code)
        if isinstance(reply, dict) and reply.get("choice") in primary["candidates"]:
            preferred[code] = reply["choice"]
            why[code] = safe_text(reply.get("why"))
    return preferred, why


# ---- Module 5
def cluster_tasks(cycle):
    if not cycle.groups:
        return []
    material = "\n".join(f'{g["group_id"]}: need "{g["need"]}", {len(g["student_ids"])} students' for g in cycle.groups)
    return [_task(cycle.pack, "groups", 'For each temporary group, write one short sentence the teacher can read, on what this group needs next. Describe the need, not the students. '
                            'Reply as {"groups": {"<group id>": "sentence"}}.', material)]


def apply_clusters(cycle, results):
    replies = results.get("groups", {}).get("groups", {}) if isinstance(results.get("groups"), dict) else {}
    known = {g["group_id"] for g in cycle.groups}
    return {gid: safe_text(text) for gid, text in replies.items() if gid in known and safe_text(text)} if isinstance(replies, dict) else {}


# ---- Module 6
def material_tasks(pack, plan):
    tasks = []
    for group_id, card in plan["cards"].items():
        tasks.append(_task(pack, group_id, "Draft teaching material strictly within this approved intervention. Add no new concepts and keep to the steps given. "
                                     'Reply as {"teacher_script": ["short lines"], "worksheet": ["short student tasks"], "exit_ticket": "one question"}.',
                           f'Intervention: {card["title"]}\nSteps: {" ".join(card["steps"])}\nTeacher guidance: {" ".join(card["teacher_guidance"])}\n'
                           f'Student task: {" ".join(card["student_task"])}\nMinutes: {card["duration_minutes"][1]}', 900))
    return tasks


def apply_materials(plan, results):
    materials = {}
    for group_id in plan["cards"]:
        reply = results.get(group_id)
        if not isinstance(reply, dict):
            continue
        script = [safe_text(x) for x in reply.get("teacher_script", []) if safe_text(x)][:10] if isinstance(reply.get("teacher_script"), list) else []
        sheet = [safe_text(x) for x in reply.get("worksheet", []) if safe_text(x)][:8] if isinstance(reply.get("worksheet"), list) else []
        if script and sheet:
            materials[group_id] = {"teacher_script": script, "worksheet": sheet, "exit_ticket": safe_text(reply.get("exit_ticket")), "label": "AI draft: review before use"}
    return materials


# ---- Module 7, the paper
def paper_tasks(pack, paper):
    material = "\n".join(f'{i["id"]}: {i["text"]}' for i in paper)
    return [_task(pack, "paper", 'Review each question for a school student: is it clear and unambiguous? Do not rewrite it. '
                           'Reply as {"items": {"<id>": {"clear": true, "note": "only if not clear"}}}.', material, 900)]


def apply_paper(paper, results):
    replies = results.get("paper", {}).get("items", {}) if isinstance(results.get("paper"), dict) else {}
    known = {i["id"] for i in paper}
    if not isinstance(replies, dict):
        return {}
    return {qid: clean(r.get("note")) or "Flagged as unclear" for qid, r in replies.items() if qid in known and isinstance(r, dict) and r.get("clear") is False}


# ---- Module 8
def profile_tasks(pack, comparison):
    rows = "\n".join(f'{s["student"]}: V1 {s["v1_percent"]}%, V2 {s["v2_percent"]}%; no longer seen {s["no_longer_seen"]}; still seen {s["still_seen"]}; new {s["newly_seen"]}; next {s["next"]["action"]}'
                     for s in comparison["students"])
    counts = "\n".join(f'{m["name"]}: {m["v1_students"]} to {m["v2_students"]} students' for m in comparison["misconceptions"])
    return [_task(pack, "summary", "Summarise these results for the teacher in plain words. Every statement must match a row below: a need whose V2 count is 0 is no longer seen, and only a need listed under still seen remains. Report what changed; do not say the teaching caused it. Do not change any status or next step. "
                             'Reply as {"class_summary": "three sentences at most", "students": {"<code>": "one sentence on what to do next"}}.',
                  f"By misconception:\n{counts}\n\nBy student:\n{rows}", 1200)]


def apply_profile(comparison, results):
    reply = results.get("summary") if isinstance(results.get("summary"), dict) else {}
    notes = reply.get("students", {}) if isinstance(reply.get("students"), dict) else {}
    known = {s["student"] for s in comparison["students"]}
    return {"class_summary": safe_text(reply.get("class_summary"), 700),
            "students": {sid: safe_text(text) for sid, text in notes.items() if sid in known and safe_text(text)}}
