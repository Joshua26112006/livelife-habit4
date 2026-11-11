"""The engine's own answer reader. Any subject can use it by describing its questions as data; no code per subject.

Question formats:
  choice    options, key, and which misconception each wrong option suggests
  numeric   expected answer (fractions, decimals, percentages), optional accepted forms, the steps a sound solution writes,
            the known wrong values and the misconception each shows, and a slip code for a right set-up with a wrong last line
  written   answered in words and marked 0-4 against the item's rubric (by the AI step); each level maps to patterns:
            3 or 4 shown; 1 or 2 the patterns listed for that level; 0 blank, irrelevant or flagged, for the teacher
  judged    any question with an expected answer, already marked against it (generic.py): the answer arrives as
            {text, result, code, step, evidence, shown}; a wrong answer shows the thinking error it was grouped under
Anything a format cannot place is UNMAPPED, and the AI step may place it, choosing only from the catalogue.
A subject that can compute its answers exactly may add a plugin reader instead (see ChapterPack.read_answer).
"""
import re

from .values import all_numbers

UNMAPPED = "UNMAPPED"
PRACTICE_BASE = 100
_WORDS = re.compile(r"[a-z]{3,}", re.I)


def _value(text):
    numbers = all_numbers(str(text))
    return numbers[-1] if numbers else None


def _finding(code, step, confidence, evidence):
    return dict(belief=code, step=step, confidence=confidence, evidence=evidence)


def _choice(item, raw, trace):
    choice = (raw or "").strip().upper()[:1]
    trace.update(working=choice, shows_working=False)
    if not choice:
        trace["result"] = "blank"
    elif choice not in item["options"]:
        trace["result"] = "unreadable"
    elif choice == item["key"]:
        trace["result"] = "correct"
    else:
        trace["result"] = "wrong"
        code = item.get("distractors", {}).get(choice)
        trace["findings"].append(_finding(code, "Choice", "medium", f"chose {choice}: {item['options'][choice]}") if code
                                 else _finding(UNMAPPED, "-", "none", f"chose {choice}"))
    return trace


def _written(item, raw, trace):
    answer = raw if isinstance(raw, dict) else {"text": raw or ""}
    text, score = (answer.get("text") or "").strip(), answer.get("score")
    trace.update(working=text, shows_working=bool(text))
    if answer.get("flag"):
        trace["result"] = "flagged_for_review"
    elif not text:
        trace["result"] = "blank"
    elif score is None:
        trace["result"] = "unreadable"
    elif score == 0:
        trace["result"] = "irrelevant"
    elif score >= 3:
        trace["result"] = "correct"
    else:
        trace["result"] = "wrong"
        patterns = item.get("levels", {}).get(str(score), [])
        evidence = answer.get("evidence") or f"rubric level {score}"
        trace["findings"] = [_finding(code, "Rubric", "high", evidence) for code in patterns] or [_finding(UNMAPPED, "-", "none", evidence)]
        if len(patterns) > 1:
            trace["ambiguous"] = list(patterns)
    if score is not None:
        trace["steps"]["Rubric"] = f"level {score}"
    return trace


def _numeric(item, raw, trace):
    raw = raw or ""
    trace["working"] = raw
    if not raw.strip():
        trace["result"] = "blank"
        return trace
    written = all_numbers(raw)
    if not written:
        trace["result"] = "unreadable"
        return trace
    final = written[-1]
    accepted = {_value(a) for a in [item["answer"], *item.get("accept", [])]}
    trace["final"] = str(final)
    trace["shows_working"] = len(written) > 1 or bool(_WORDS.search(raw))
    for step in item.get("steps", []):
        trace["steps"][step["label"]] = "ok" if _value(step["value"]) in written else "not shown"
    if final in accepted:
        trace["result"] = "correct"
        return trace
    trace["result"] = "wrong"
    level = "high" if trace["shows_working"] else "medium"
    for error in item.get("errors", []):
        if _value(error["value"]) == final:
            trace["findings"].append(_finding(error["code"], "Answer", level, f"answer {final}: {error.get('why', '')}".strip(": ")))
    if not trace["findings"] and item.get("slip_code") and written[0] in accepted:
        trace["findings"].append(_finding(item["slip_code"], "Arithmetic", "high", f"set-up right, last line {final}"))
    if not trace["findings"]:
        trace["findings"].append(_finding(UNMAPPED, "-", "none", f"answer {final}; no known pattern"))
    beliefs = [f["belief"] for f in trace["findings"]]
    if len(beliefs) > 1:
        trace["ambiguous"] = beliefs
    return trace


def _judged(item, raw, trace):
    answer = raw if isinstance(raw, dict) else {"text": raw or ""}
    text, result = (answer.get("text") or "").strip(), answer.get("result")
    trace.update(working=text, shows_working=result == "correct" or bool(answer.get("shown")))
    if not text:
        trace["result"] = "blank"
    elif result in ("correct", "correct_no_working"):
        trace["result"] = "correct"
        trace["shows_working"] = result == "correct"
    elif result == "wrong":
        trace["result"] = "wrong"
        step = answer.get("step") or "-"
        trace["findings"].append(_finding(answer.get("code") or UNMAPPED, step, "high" if answer.get("shown") else "medium",
                                          answer.get("evidence") or "wrong answer"))
        trace["steps"][step] = "went wrong here"
    else:
        trace["result"] = "unreadable"
    return trace


FORMATS = {"choice": _choice, "written": _written, "numeric": _numeric, "judged": _judged}


def read(item, raw):
    trace = {"q": item["id"], "working": "", "steps": {}, "findings": []}
    return FORMATS[item["format"]](item, raw, trace)


def parallel(pack, item, attempt):
    """A new question for the same competency, from the item's variant bank, or a related item's when it has none."""
    source = item if item.get("variants") else next(
        (i for i in pack.items if i.get("variants") and set(i["competency_ids"]) & set(item["competency_ids"])), None)
    if source is None:
        raise ValueError(f"No parallel question is available for {item['id']}.")
    practice = attempt >= PRACTICE_BASE
    pool = source["variants"]["practice" if practice else "retest"]
    variant = pool[(attempt - (PRACTICE_BASE if practice else 1)) % len(pool)]
    variant = {"text": variant} if isinstance(variant, str) else variant
    base = {k: v for k, v in source.items() if k not in ("variants", "id", "text")}
    return {**base, **variant, "id": f"{source['id']}-P{attempt}", "parallel_of": item["id"]}
