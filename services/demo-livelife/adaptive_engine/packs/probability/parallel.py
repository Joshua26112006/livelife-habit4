"""Parallel items: new numbers, same template, so each item computes its own answer and predicted errors.

Deterministic for a given item and attempt, so a re-test can be regenerated. An item is rejected if it matches the original or
if a misconception's predicted value equals the correct answer (the two could not be told apart).
"""
import random
from fractions import Fraction as F

from . import templates as t

COLOURS = ["red", "blue", "green", "yellow", "white", "black", "pink"]
NUMBER_WORDS = {3: "three", 4: "four", 5: "five", 6: "six"}
MAX_TRIES = 200
# "At least once in two throws" is 11/36 for every face, so only the face can change.
SAME_ANSWER_TEMPLATES = ("die_twice_at_least",)


def _bag_not(qid, rng):
    names = rng.sample(COLOURS, 3)
    counts = dict(zip(names, rng.sample(range(2, 9), 3)))
    a, b, c = names
    return t.bag_not(qid, f"A bag has {counts[a]} {a}, {counts[b]} {b} and {counts[c]} {c} marbles. One marble is drawn at random. "
                          f"Find P(not {a}).", counts, a)


def _faces(qid, rng):
    labels = rng.sample(range(1, 7), 3)
    faces = [str(x) for label, n in zip(labels, rng.sample((1, 2, 3), 3)) for x in [label] * n]
    target = max(set(faces), key=faces.count) if rng.random() < 0.5 else min(set(faces), key=faces.count)
    return t.labelled_faces(qid, f"A die has faces {', '.join(faces)}. It is thrown once. Find P({target}).", faces, target)


def _coins_exactly(qid, rng):
    n, k = rng.choice([(2, 2), (2, 0), (3, 1), (3, 2)])
    head = "head" if k == 1 else "heads"
    coins = {2: "Two", 3: "Three"}[n]
    return t.coins_exactly(qid, f"{coins} coins are tossed together. Write all the outcomes. Find P(exactly {k} {head}).", n, k)


def _coins_at_least(qid, rng):
    n, face = rng.choice([(2, "T"), (3, "H"), (3, "T")])
    word = {"H": "head", "T": "tail"}[face]
    coins = {2: "Two", 3: "Three"}[n]
    return t.coins_at_least_one(qid, f"{coins} coins are tossed. Find P(at least one {word}).", n, face)


def _dice_sum(qid, rng):
    s = rng.randint(3, 11)
    return t.dice_sum(qid, f"Two dice are thrown. List the outcomes with sum {s}. Find P(sum is {s}).", s)


def _die_twice(qid, rng):
    k = rng.randint(1, 5)
    return t.die_twice_at_least(qid, f"A die is thrown twice. Find P({k} comes up at least once).", k)


def _removal(qid, rng):
    total, bad = rng.randint(10, 20), rng.randint(2, 5)
    good = total - bad
    return t.removal(qid, f"A box has {total} bulbs, {bad} of them defective. One good bulb is sold. Find P(the next bulb drawn is good).",
                     good, total, good - 1)


def _complement(qid, rng):
    p = F(rng.randrange(5, 100, 5), 100)
    return t.complement(qid, f"P(rain tomorrow) = {float(p)}. Find P(no rain tomorrow).", p)


def _argument(qid, rng):
    parts, red = rng.choice([(5, 3), (5, 2), (6, 3), (6, 4)])
    others = rng.sample([c for c in COLOURS if c != "red"], 2)
    rest = [others[0]] * (parts - red - 1) + [others[1]]
    listing = ", ".join(["red"] * red + rest)
    return t.argument(qid, f"A spinner has {parts} equal parts: {listing}. Riya says P(red) = 1/3 because there are three colours. "
                           "Is she right? Explain.", False, r"three colours|3 colours|three outcomes|3 outcomes",
                      rf"\b{parts}\b|{NUMBER_WORDS[parts]}|{red}/{parts}|{NUMBER_WORDS[red]} red")


_BUILDERS = {"bag_not": _bag_not, "labelled_faces": _faces, "coins_exactly": _coins_exactly, "coins_at_least_one": _coins_at_least,
             "dice_sum": _dice_sum, "die_twice_at_least": _die_twice, "removal": _removal, "complement": _complement, "argument": _argument}


def _acceptable(item, original):
    if item["text"] == original["text"]:
        return False
    if item["type"] == "argue":
        return True
    predicted = [s["value"] for s in item["signatures"] if "value" in s]
    new_answer = item["correct"] != original["correct"] or original["template"] in SAME_ANSWER_TEMPLATES
    return 0 < item["correct"] < 1 and new_answer and item["correct"] not in predicted


def parallel_item(original, attempt):
    """A new item for the same template and competencies."""
    rng = random.Random(f"{original['id']}:{attempt}")
    qid = f"{original['id']}-P{attempt}"
    for _ in range(MAX_TRIES):
        item = _BUILDERS[original["template"]](qid, rng)
        if _acceptable(item, original):
            return {**item, "template": original["template"], "competency_ids": original["competency_ids"], "parallel_of": original["id"]}
    raise ValueError(f"no acceptable parallel item for {original['id']}")
