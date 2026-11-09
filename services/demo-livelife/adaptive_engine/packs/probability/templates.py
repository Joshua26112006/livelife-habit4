"""Layer 1: question templates ("buggy solvers").

Each template computes the correct answer and every misconception's predicted trace from the question's own numbers, so a
new question of the same type needs no new rules. A signature predicts a denominator (`total`), a final value (`value`),
or that chances were added (`adds`).
"""
from fractions import Fraction as F
from itertools import product


def bag_not(qid, text, counts, target):
    """Bag with category counts; ask P(not target)."""
    total = sum(counts.values())
    others = [c for c in counts if c != target]
    signatures = [
        dict(belief="MC-L", step="Total", total=len(counts),
             why=f"denominator {len(counts)} = number of colours, not number of items"),
        dict(belief="MC-L", step="Total", value=F(len(others), len(counts)), why="counted colours instead of items"),
        dict(belief="MC-N", step="Method", value=F(counts[target], total),
             why=f"gave P({target}) instead of P(not {target})"),
    ]
    signatures += [dict(belief="MC-N", step="Method", value=F(counts[c], total), why=f"used only '{c}' as 'not {target}'")
                   for c in others]
    return dict(id=qid, text=text, type="bag_not", correct=F(total - counts[target], total), total=total,
                signatures=signatures)


def labelled_faces(qid, text, faces, target):
    distinct = len(set(faces))
    return dict(id=qid, text=text, type="faces", correct=F(faces.count(target), len(faces)), total=len(faces),
                signatures=[dict(belief="MC-L", step="Total", total=distinct,
                                 why=f"denominator {distinct} = number of different labels, not {len(faces)} faces")])


def coins_exactly(qid, text, n, k):
    space = list(product("HT", repeat=n))
    fav = [s for s in space if s.count("H") == k]
    return dict(id=qid, text=text, type="coins", correct=F(len(fav), len(space)), total=len(space),
                space=["".join(s) for s in space],
                signatures=[dict(belief="MC-L", step="Total", total=n + 1,
                                 why=f"{n + 1} outcomes = number of heads 0..{n}, not {len(space)} ordered results")])


def coins_at_least_one(qid, text, n, face="H"):
    space = list(product("HT", repeat=n))
    fav = [s for s in space if face in s]
    return dict(id=qid, text=text, type="coins", correct=F(len(fav), len(space)), total=len(space),
                space=["".join(s) for s in space],
                signatures=[dict(belief="MC-A", step="Method", adds=True, value=F(n, 2), why="added 1/2 for each coin"),
                            dict(belief="MC-L", step="Total", total=n + 1,
                                 why=f"{n + 1} outcomes = number of heads, not ordered results")])


def dice_sum(qid, text, s):
    fav = [(a, b) for a in range(1, 7) for b in range(1, 7) if a + b == s]
    unordered = {tuple(sorted(p)) for p in fav}
    return dict(id=qid, text=text, type="dice", correct=F(len(fav), 36), total=36, fav=fav,
                signatures=[dict(belief="MC-L", step="Total", total=11, why="11 outcomes = the sums 2..12"),
                            dict(belief="MC-O", step="Total", total=21, why="21 = pairs with order ignored"),
                            dict(belief="MC-O", step="Favourable", value=F(len(unordered), 36),
                                 why="counted each pair once, ignoring order")])


def die_twice_at_least(qid, text, k):
    fav = [(a, b) for a in range(1, 7) for b in range(1, 7) if k in (a, b)]
    return dict(id=qid, text=text, type="dice", correct=F(len(fav), 36), total=36, fav=fav,
                signatures=[dict(belief="MC-A", step="Method", adds=True, value=F(2, 6),
                                 why=f"added 1/6 + 1/6: ({k}, {k}) counted twice"),
                            dict(belief="MC-L", step="Sample space", value=F(1, 2),
                                 why=f"'{k} comes or it doesn't' taken as two equal outcomes"),
                            dict(belief="MC-O", step="Total", total=21, why="21 = pairs with order ignored")])


def removal(qid, text, favourable_before, total_before, favourable_after):
    """One item is taken out, then P(next). `favourable_after` depends on what was removed."""
    return dict(id=qid, text=text, type="removal", correct=F(favourable_after, total_before - 1), total=total_before - 1,
                signatures=[dict(belief="MC-U", step="Total", total=total_before,
                                 why=f"kept the old total {total_before}; one item had been removed"),
                            dict(belief="MC-U", step="Total", value=F(favourable_before, total_before),
                                 why="answered as if no item had been removed")])


def complement(qid, text, p):
    return dict(id=qid, text=text, type="complement", correct=1 - p, total=None,
                signatures=[dict(belief="MC-N", step="Method", value=p, why="gave P(E) instead of P(not E)"),
                            dict(belief="MC-R", step="Method", value=1 + p,
                                 why="added instead of subtracting; result above 1")])


def argument(qid, text, claim_is_correct, label_words, reason_words):
    """A stated claim to judge. `label_words` is the faulty reason; `reason_words` shows the sound one."""
    return dict(id=qid, text=text, type="argue", claim_is_correct=claim_is_correct, label_words=label_words,
                reason_words=reason_words, signatures=[])


TEST = [
    bag_not("T1", "A bag has 6 green, 3 yellow and 1 white bead. One bead is drawn at random. Find P(not green).",
            {"green": 6, "yellow": 3, "white": 1}, "green"),
    labelled_faces("T2", "A die has faces 2, 2, 3, 5, 5, 5. It is thrown once. Find P(5).",
                   ["2", "2", "3", "5", "5", "5"], "5"),
    coins_exactly("T3", "Two coins are tossed together. Write all the outcomes. Find P(exactly one head).", 2, 1),
    dice_sum("T4", "Two dice are thrown. List the outcomes with sum 9. Find P(sum is 9).", 9),
    die_twice_at_least("T5", "A die is thrown twice. Find P(6 comes up at least once).", 6),
    removal("T6", "A box has 12 pens, 3 of them defective. One good pen is sold. Find P(the next pen drawn is good).",
            9, 12, 8),
    argument("T7", "A spinner has 4 equal parts: red, red, blue, green. Riya says P(red) = 1/3 because there are three "
                   "colours. Is she right? Explain.",
             False, r"three colours|3 colours|three outcomes|3 outcomes", r"\b4\b|four|2/4|two red"),
    complement("T8", "P(rain tomorrow) = 0.35. Find P(no rain tomorrow).", F(35, 100)),
    coins_at_least_one("T9", "Two coins are tossed. Find P(at least one head).", 2),
    removal("T10", "Cards numbered 1 to 10. Card 10 is drawn and kept aside. Find P(the next card is even).", 5, 10, 4),
]

# Which template built each item, and the competencies it samples. The competency tags are our proposal from the concept
# document (section 9); Module 1's approved map replaces them.
ITEM_TAGS = {
    "T1": ("bag_not", ["PROB-04", "PROB-07"]),
    "T2": ("labelled_faces", ["PROB-02", "PROB-05"]),
    "T3": ("coins_exactly", ["PROB-03", "PROB-10"]),
    "T4": ("dice_sum", ["PROB-03", "PROB-04", "PROB-10"]),
    "T5": ("die_twice_at_least", ["PROB-10"]),
    "T6": ("removal", ["PROB-09"]),
    "T7": ("argument", ["PROB-02", "PROB-11"]),
    "T8": ("complement", ["PROB-07", "PROB-12"]),
    "T9": ("coins_at_least_one", ["PROB-10"]),
    "T10": ("removal", ["PROB-09"]),
}
for item in TEST:
    item["template"], item["competency_ids"] = ITEM_TAGS[item["id"]]
