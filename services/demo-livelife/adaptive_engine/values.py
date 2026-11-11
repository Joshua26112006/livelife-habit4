"""Reading numbers out of written working: fractions, decimals, percentages and a final whole-number result."""
import re
from fractions import Fraction as F

_NUM = r"\d+(?:\.\d+)?"
# A minus is a sign only when it does not follow a number or a bracket, so "1 - 1/4" and "1 -1/4" are subtractions.
_SIGN = r"(?:(?<![\d)])(?<![\d)]\s)-)?"
_VALUE = re.compile(
    rf"(?P<pct>{_NUM})\s*%|(?P<num>{_SIGN}{_NUM})\s*/\s*(?P<den>{_SIGN}{_NUM})|(?P<dec>{_SIGN}\d*\.\d+)"
)
# A whole number counts as the final value only as the result of a calculation ("1/2 + 1/2 = 1"), not "total = 10".
_RESULT_INTEGER = re.compile(r"[\d)]\s*=\s*(-?\d+)\s*\.?\s*$")
_BARE_INTEGER = re.compile(r"\s*(?:p\s*=\s*|ans\w*\s*[:=]?\s*)?(-?\d+)\s*\.?\s*", re.I)


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


_ANY_NUMBER = re.compile(rf"(?P<pct>{_NUM})\s*%|(?P<num>{_SIGN}{_NUM})\s*/\s*(?P<den>{_SIGN}{_NUM})|(?P<plain>{_SIGN}{_NUM})")


def all_numbers(text):
    """Every number written, in order, including whole numbers part-way through the working ("400 x 25/100 = 100")."""
    out = []
    for m in _ANY_NUMBER.finditer(text):
        if m["pct"]:
            out.append(F(m["pct"]) / 100)
        elif m["num"]:
            if F(m["den"]) != 0:
                out.append(F(m["num"]) / F(m["den"]))
        else:
            out.append(F(m["plain"]))
    return out

