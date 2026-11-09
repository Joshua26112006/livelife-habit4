"""Module 4: intervention mapping.

Retrieves curated interventions for each supported hypothesis and ranks them by rules: most matching evidence first, then
the shortest. The model never invents pedagogy here. Only an expert-approved intervention may be recommended; the pilot can
pass allow_draft=True to preview unreviewed entries, and each one stays labelled with its review status.
"""
CARD_FIELDS = ("objective", "steps", "exit_check")


def _rank(pack, code, questions):
    templates = [pack.item(q)["template"] for q in questions]

    def key(intervention_id):
        entry = pack.interventions[intervention_id]
        matches = sum(t in entry["item_types"] for t in templates)
        return (-matches, entry["duration_minutes"][1], intervention_id)

    return sorted(pack.intervention_map.get(code, ()), key=key)


def _mapping(pack, diagnosis, code, allow_draft, preferred):
    ranked = _rank(pack, code, diagnosis["summary"][code]["questions"])
    if preferred.get(code) in ranked:
        ranked.remove(preferred[code])
        ranked.insert(0, preferred[code])
    usable = [i for i in ranked if allow_draft or pack.interventions[i]["review_status"] == "approved"]
    return {
        "misconception_id": code,
        "competency_ids": pack.misconceptions[code]["competency_ids"],
        "candidates": ranked,
        "recommended": usable[0] if usable else None,
        "review_status": pack.interventions[usable[0]]["review_status"] if usable else None,
        "why": diagnosis["summary"][code]["questions"],
    }


def map_student(pack, diagnosis, allow_draft=False, preferred=None):
    """One student's primary intervention for this session and the needs stored for later ones."""
    preferred = preferred or {}
    step = diagnosis["next"]
    if step["action"] == "group":
        primary, later = step["target"], step["held_for_later"]
    elif step["action"] == "practice":
        primary, later = step["target"][0], step["target"][1:]
    else:
        return {"student": diagnosis["student"], "primary": None, "secondary": []}
    return {
        "student": diagnosis["student"],
        "primary": _mapping(pack, diagnosis, primary, allow_draft, preferred),
        "secondary": [_mapping(pack, diagnosis, code, allow_draft, preferred) for code in later],
    }


def teaching_card(pack, intervention_id, practice_items=()):
    """The printable card. Anything the experts have not written is listed, never filled in."""
    entry = pack.interventions[intervention_id]
    misconceptions = [c for c, ids in pack.intervention_map.items() if intervention_id in ids]
    guidance = [pack.misconceptions[c]["teacher"] for c in misconceptions if pack.misconceptions[c]["teacher"]]
    tasks = [pack.misconceptions[c]["student"] for c in misconceptions if pack.misconceptions[c]["student"]]
    return {
        "intervention_id": intervention_id,
        "title": entry["title"],
        "objective": entry["objective"],
        "steps": entry["steps"],
        "teacher_guidance": guidance,
        "student_task": tasks,
        "practice": [{"id": p["id"], "text": p["text"]} for p in practice_items],
        "answer_key": {p["id"]: str(p["correct"]) for p in practice_items if "correct" in p},
        "exit_check": entry["exit_check"],
        "duration_minutes": entry["duration_minutes"],
        "assets": entry["assets"],
        "review_status": entry["review_status"],
        "version": entry["version"],
        "awaiting_expert_draft": [f for f in CARD_FIELDS if not entry[f]],
    }
