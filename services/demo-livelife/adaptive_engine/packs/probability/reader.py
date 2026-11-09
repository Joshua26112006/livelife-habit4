"""Layers 2 and 3: read one answer step by step, and match it against the misconception traces.

The five steps: Sample space, Total, Favourable, Method, Arithmetic. Confidence on one question:
  high    the working shows the faulty step
  medium  only the final answer matches what the belief predicts
  none    wrong, but no known pattern: goes to the teacher as UNMAPPED

Results: correct, correct_reason_unclear, wrong, blank, unreadable, argument_unclear.
"""
import re
from fractions import Fraction as F

from ...pack import UNMAPPED

_NUM = r"\d+(?:\.\d+)?"
# A minus is a sign only when it does not follow a number or a bracket, so "1 - 1/4" and "1 -1/4" are subtractions.
_SIGN = r"(?:(?<![\d)])(?<![\d)]\s)-)?"
_VALUE = re.compile(
    rf"(?P<pct>{_NUM})\s*%|(?P<num>{_SIGN}{_NUM})\s*/\s*(?P<den>{_SIGN}{_NUM})|(?P<dec>{_SIGN}\d*\.\d+)"
)
_PAIR = re.compile(r"\(\s*(\d)\s*,\s*(\d)\s*\)")
_COIN_SEQUENCE = re.compile(r"\b([HT]{2,4})\b")
_ADDED_FRACTIONS = re.compile(rf"{_NUM}\s*/\s*{_NUM}\s*\+\s*{_NUM}\s*/\s*{_NUM}")
# A whole number counts as the final value only as the result of a calculation ("1/2 + 1/2 = 1"), not "total = 10".
_RESULT_INTEGER = re.compile(r"[\d)]\s*=\s*(-?\d+)\s*\.?\s*$")
_BARE_INTEGER = re.compile(r"\s*(?:p\s*=\s*|ans\w*\s*[:=]?\s*)?(-?\d+)\s*\.?\s*", re.I)
_ANSWER_LABELS = re.compile(r"\b(ans|answer|final|result|hence|therefore|so|the|is|equals?|prob|probability)\b", re.I)
_DISAGREES = re.compile(r"\b(no|not|wrong|disagree|incorrect)\b", re.I)
_AGREES = re.compile(r"\b(yes|right|correct|agree)\b", re.I)


def read_values(text):
    """Every fraction, decimal and percentage in the working as (numerator, denominator), in order."""
    values = []
    for m in _VALUE.finditer(text):
        if m["pct"]:
            values.append((F(m["pct"]), F(100)))
        elif m["num"]:
            if F(m["den"]) != 0:
                values.append((F(m["num"]), F(m["den"])))
        else:
            values.append((F(m["dec"]), F(1)))
    if values:
        result = _RESULT_INTEGER.search(text)
        if result and result.start() >= list(_VALUE.finditer(text))[-1].end() - 1:
            values.append((F(result[1]), F(1)))
    else:
        bare = _BARE_INTEGER.fullmatch(text)
        if bare:
            values.append((F(bare[1]), F(1)))
    return values


def classify_reason(text):
    """Keyword stand-in for the catalogue-limited language model: 'agrees', 'disagrees' or 'unclear'."""
    if _DISAGREES.search(text):
        return "disagrees"
    return "agrees" if _AGREES.search(text) else "unclear"


def _shows_working(text, values):
    """Working is more than one value, a listing, or real words; an 'Ans:' label alone is not working."""
    if len(values) > 1 or _PAIR.search(text) or _COIN_SEQUENCE.search(text):
        return True
    return bool(re.search(r"[a-z]{3,}", _ANSWER_LABELS.sub(" ", text), re.I))


def _read_argument(q, raw, trace):
    stance = classify_reason(raw)
    has_sound_reason = bool(re.search(q["reason_words"], raw, re.I))
    trace["shows_working"] = has_sound_reason
    if stance == "unclear":
        if not has_sound_reason:
            trace["result"] = "argument_unclear"
            return trace
        stance = "agrees" if q["claim_is_correct"] else "disagrees"
    if (stance == "agrees") != q["claim_is_correct"]:
        names_label = stance == "agrees" and re.search(q["label_words"], raw, re.I)
        trace["steps"]["Sample space"] = "accepts labels as equally likely outcomes"
        trace["findings"].append(dict(belief="MC-L", step="Sample space", confidence="high" if names_label else "medium",
                                      evidence=raw))
        trace["result"] = "wrong"
    elif has_sound_reason:
        trace["steps"]["Sample space"] = "counts the equal parts"
        trace["result"] = "correct"
    else:
        trace["result"] = "correct_reason_unclear"
    return trace


def _read_listing(q, raw, trace):
    """Steps 1 and 3: any outcomes the student listed."""
    pairs = {(int(a), int(b)) for a, b in _PAIR.findall(raw)}
    sequences = set(_COIN_SEQUENCE.findall(raw))
    if q["type"] == "dice" and pairs:
        correct = set(q["fav"])
        missing = correct - pairs
        unequal = [p for p in pairs if p[0] != p[1]]
        reverse_absent = [p for p in unequal if (p[1], p[0]) not in pairs]
        if missing and unequal and len(reverse_absent) == len(unequal):
            trace["steps"]["Favourable"] = f"listed {sorted(pairs)}; every reversed pair is missing"
            trace["findings"].append(dict(belief="MC-O", step="Favourable", confidence="high",
                                          evidence=f"no reversed pairs listed: missing {sorted(missing)}"))
        elif missing:
            trace["steps"]["Favourable"] = f"listed {len(pairs)} of {len(correct)}; missing {sorted(missing)}"
            trace["findings"].append(dict(belief="SLIP-E", step="Favourable", confidence="high",
                                          evidence=f"missing {sorted(missing)}"))
        else:
            trace["steps"]["Favourable"] = f"all {len(correct)} outcomes listed"
    if q["type"] == "coins" and sequences:
        full = set(q["space"])
        absent = full - sequences
        if not absent:
            trace["steps"]["Sample space"] = f"all {len(full)} outcomes listed"
        elif any(sorted(s) == sorted(x) for s in absent for x in sequences):
            trace["steps"]["Sample space"] = f"wrote {sorted(sequences)}; {sorted(absent)} missing as a separate outcome"
            trace["findings"].append(dict(belief="MC-O", step="Sample space", confidence="high",
                                          evidence=f"{sorted(absent)} not listed separately"))


def _strongest_per_belief(findings):
    best = {}
    for finding in findings:
        if finding["belief"] not in best or finding["confidence"] == "high":
            best[finding["belief"]] = finding
    return list(best.values())


def read_answer(q, raw):
    """One answer -> its step trace, findings and result."""
    trace = {"q": q["id"], "working": raw, "steps": {}, "findings": []}
    if not raw.strip():
        trace["result"] = "blank"
        return trace
    if q["type"] == "argue":
        return _read_argument(q, raw, trace)

    values = read_values(raw)
    if not values:
        trace["result"] = "unreadable"
        return trace
    final = values[-1][0] / values[-1][1]
    setup_num, setup_den = values[0]
    setup = setup_num / setup_den
    trace["final"] = str(final)
    trace["shows_working"] = _shows_working(raw, values)

    _read_listing(q, raw, trace)

    if final == q["correct"]:
        trace["steps"].setdefault("Total", f"{setup_den} ok" if q.get("total") else "ok")
        trace["result"] = "correct"
        return trace

    trace["result"] = "wrong"
    findings = trace["findings"]

    # Step 4: method
    added = _ADDED_FRACTIONS.search(raw)
    if added:
        for s in q["signatures"]:
            if s.get("adds"):
                trace["steps"]["Method"] = "added the chance for each trial"
                findings.append(dict(belief=s["belief"], step="Method", confidence="high", evidence=added[0]))
    if final < 0 or final > 1:
        findings.append(dict(belief="MC-R", step="Method", confidence="high", evidence=f"final answer {final}"))

    # Step 5: correct set-up, wrong simplification
    if setup == q["correct"]:
        trace["steps"]["Arithmetic"] = f"set-up {setup_num}/{setup_den} correct, simplified to {final}"
        findings.append(dict(belief="SLIP-F", step="Arithmetic", confidence="high", evidence=raw))
        return trace

    # Step 2: the total, then every predicted trace
    if q.get("total") is not None:
        verdict = f"{setup_den} ok" if setup_den == q["total"] else f"used {setup_den}, should be {q['total']}"
        trace["steps"].setdefault("Total", verdict)
    level = "high" if trace["shows_working"] else "medium"
    for s in q["signatures"]:
        if "total" in s and setup_den == s["total"] and setup_den != 1:
            findings.append(dict(belief=s["belief"], step=s["step"], confidence=level,
                                 evidence=f"denominator {setup_den}: {s['why']}"))
        elif "value" in s and final == s["value"] and not any(f["belief"] == s["belief"] for f in findings):
            findings.append(dict(belief=s["belief"], step=s["step"], confidence=level,
                                 evidence=f"answer {final}: {s['why']}"))

    trace["findings"] = _strongest_per_belief(findings)
    beliefs = [f["belief"] for f in trace["findings"] if f["belief"].startswith("MC")]
    if len(beliefs) > 1:
        trace["ambiguous"] = beliefs
    if not trace["findings"]:
        trace["findings"].append(dict(belief=UNMAPPED, step="-", confidence="none",
                                      evidence=f"answer {final}; no known pattern"))
    return trace
