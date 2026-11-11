"""The routing rules, as one block of settings. The engine has defaults, a pack may set its own in pack.json ("policy"), and a
class may override either, so a teacher can try different rules on the same answers without touching code.

  group_from      the weakest evidence that is enough to put a student in a teaching group for a thinking error:
                    "candidate"  one question shows it (default: club students by error at once, no follow-up first)
                    "likely"     two or more questions, all medium
                    "confirmed"  two or more questions, at least one high; anything weaker gets a follow-up question first
  content_share   percent of the class showing an error at which our content owns the main fix (default 25)
  teacher_share   percent at which the teacher does (default 10); below it, the student does
  max_group_size  largest teaching group before it is split (default 12)
  owners          {error code: [owners]} who fixes that error, whatever the share. Owners: content, teacher, student.
                  In a class override, "auto" for a code goes back to the share rule.
"""
from fractions import Fraction

OWNERS = ("content", "teacher", "student")
STRENGTH = ("confirmed", "likely", "candidate")  # strongest evidence first
AUTO = "auto"
DEFAULTS = {"group_from": "candidate", "content_share": 25, "teacher_share": 10, "max_group_size": 12, "owners": {}}
NUMBERS = ("content_share", "teacher_share", "max_group_size")


def problems(policy, codes=None):
    """What is wrong with a policy block (pack or class override), as plain messages. An empty list means it is usable."""
    if not isinstance(policy, dict):
        return ["policy must be an object"]
    found = [f"policy: unknown setting '{k}'" for k in policy if k not in DEFAULTS]
    if "group_from" in policy and policy["group_from"] not in STRENGTH:
        found.append(f"policy: group_from must be one of {', '.join(STRENGTH)}")
    for key in NUMBERS:
        if key in policy:
            value = policy[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= (100 if key != "max_group_size" else 500):
                found.append(f"policy: {key} must be a number in range")
            elif key == "max_group_size" and (value < 1 or value != int(value)):
                found.append("policy: max_group_size must be a whole number of 1 or more")
    owners = policy.get("owners", {})
    if not isinstance(owners, dict):
        return found + ["policy: owners must map error codes to owner lists"]
    for code, who in owners.items():
        if codes is not None and code not in codes:
            found.append(f"policy owners: unknown error code {code}")
        if who != AUTO and not (isinstance(who, list) and who and all(o in OWNERS for o in who)):
            found.append(f"policy owners: {code} needs a list from {', '.join(OWNERS)}, or '{AUTO}'")
    return found


def resolve(pack_policy=None, overrides=None):
    """Engine defaults, then the pack's settings, then the class's. Owners merge code by code."""
    pack_policy, overrides = pack_policy or {}, overrides or {}
    merged = {**DEFAULTS, **{k: v for k, v in pack_policy.items() if k != "owners"}, **{k: v for k, v in overrides.items() if k != "owners"}}
    owners = {**pack_policy.get("owners", {}), **overrides.get("owners", {})}
    merged["owners"] = {code: [o for o in OWNERS if o in who] for code, who in owners.items() if who != AUTO}
    if merged["teacher_share"] > merged["content_share"]:
        raise ValueError("teacher_share cannot be above content_share")
    merged["max_group_size"] = int(merged["max_group_size"])
    return merged


def share(policy, key):
    return Fraction(str(policy[key])) / 100


def groupable(policy):
    """Evidence statuses that are enough for a teaching group, strongest first."""
    return STRENGTH[:STRENGTH.index(policy["group_from"]) + 1]
