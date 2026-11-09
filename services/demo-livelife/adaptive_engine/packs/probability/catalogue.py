"""Layer 0: the misconception catalogue, teaching order, probes and intervention text.

Wording comes from the handoff, the strategy doc and the class report. A remedy that none of them drafted is None, not
invented: those are for the subject experts to write (see `needs_expert_draft`). Every rule here is a proposal to be
calibrated against teacher marking.
"""

TEACHING_ORDER = ("MC-R", "MC-L", "MC-O", "MC-N", "MC-A", "MC-U")
SLIPS = ("SLIP-E", "SLIP-F")

CATALOGUE = {
    "MC-R": {
        "name": "Accepts a probability outside 0 to 1",
        "belief": "A probability can be any number.",
        "kind": "belief",
        "student": "Place 0, 1/2 and 1 on a line; a part can't exceed the whole.",
        "teacher": "Use the note on p. 207: favourable outcomes never exceed all outcomes.",
        "content": None,
        "exit_check": "Which cannot be a probability: 1.2, 0, 45%, 3/5? (1.2)",
    },
    "MC-L": {
        "name": "Counts categories, not outcomes",
        "belief": "The categories in the question (colours, sums, 'comes or not') are the equally likely outcomes.",
        "kind": "belief",
        "student": "Before dividing, list what you could actually pick, one by one. Self-check: does my total equal the "
                   "number of real objects (10 beads, 36 dice results)?",
        "teacher": "Open with the NCERT bag of 4 red and 1 blue ball (p. 203): colours are not equally likely, each ball "
                   "is. Have students number every bead. Ask the 'Why?' at Example 8 aloud: why 9 marbles, not 3 colours?",
        "content": "Our worked examples state 'equally likely' for the student, so they never judge it. Add a contrast "
                   "pair to each lesson (labels vs. items), an 'outcome list' box before every formula, and argument "
                   "items such as 'Riya says 1/3 because there are three colours'.",
        "exit_check": "Faces 1, 1, 2, 3, 3, 3: P(3)? (3/6)",
    },
    "MC-O": {
        "name": "Treats (a, b) and (b, a) as one outcome",
        "belief": "(3, 6) and (6, 3) are the same outcome.",
        "kind": "belief",
        "student": "Give each die a colour and always write (blue, grey). Self-check: two dice must give 36 outcomes.",
        "teacher": "Use the blue and grey dice and the 6 x 6 table (Example 13, Fig. 14.3). Ask why (1, 4) is a different "
                   "cell from (4, 1).",
        "content": "Show the two-dice table with coloured dice in the lesson, not only described. Add practice that asks "
                   "for both orders of a pair.",
        "exit_check": "Two dice, sum 9 (4/36)",
    },
    "MC-N": {
        "name": "Answers P(E) for 'not E'",
        "belief": "'Not green' is answered with the green count, or one other category.",
        "kind": "belief",
        "student": "Underline 'not'. Shade E and count everything left. Self-check: P(E) + P(not E) = 1.",
        "teacher": "Short reteach with Example 4 (not an ace = 52 - 4) and a three-colour bag.",
        "content": "Our 'not' examples have only two outcomes (win or lose, girl or boy). Add one with three or more "
                   "categories.",
        "exit_check": "2 red, 3 blue, 5 yellow; P(not yellow) (5/10)",
    },
    "MC-A": {
        "name": "Adds chances for 'at least one'",
        "belief": "'At least once in two throws' is the chance for each throw added together.",
        "kind": "belief",
        "student": "For 'at least once', count the cells or use 1 - P(none). Self-check: two coins, 'at least one head' "
                   "by adding gives 1/2 + 1/2 = 1, which is impossible.",
        "teacher": "Shade row 6 and column 6 of the 6 x 6 table (Fig. 14.3); show they share (6, 6), so 6 + 6 counts it "
                   "twice. Link to the note in Example 9: 1 - P(no head).",
        "content": "Our material has no worked example of a die thrown twice. Add one solved both ways (count the 11 "
                   "cells; 1 - 25/36), plus the coins case where adding gives 1.",
        "exit_check": "Two dice, at least one even number? (27/36)",
    },
    "MC-U": {
        "name": "Keeps the old total after an item is removed",
        "belief": "The total stays the same after an item is removed.",
        "kind": "belief",
        "student": "Write what is in the box now, then count again.",
        "teacher": "Use Q15 and Q17: write what is in the box now, then count again (the chapter has no worked example).",
        "content": None,
        "exit_check": "10 pens, 3 defective; a good one removed; P(good) next (6/9)",
    },
    "DECK": {
        "name": "Doesn't know the deck",
        "belief": "Thinks there is one king. A fact gap, not a probability error: the method was right.",
        "kind": "fact",
        "student": "Learn the deck: 4 suits of 13 cards; 4 of each rank; 12 face cards.",
        "teacher": "Two-minute deck recap with a real pack before any card question.",
        "content": "Add a deck reference card to the start of the card questions.",
        "exit_check": "How many queens are in a deck of 52? Find P(queen). (4/52)",
    },
    "SLIP-E": {
        "name": "Listing slip",
        "belief": "Missed one outcome while listing; order is understood.",
        "kind": "slip",
        "student": "List row by row of the 6 x 6 table so none is skipped.",
        "teacher": None,
        "content": None,
        "exit_check": "Two dice, sum 6, every pair listed (5/36)",
    },
    "SLIP-F": {
        "name": "Arithmetic slip",
        "belief": "Correct set-up, wrong simplification.",
        "kind": "slip",
        "student": "Two short simplification drills; recheck the last line by multiplying back.",
        "teacher": None,
        "content": None,
        "exit_check": "Simplify 4/36 (1/9)",
    },
}

# One short follow-up per belief. MC-R and MC-U have no drafted probe yet: those students go to the teacher instead.
PROBES = {
    "MC-L": "A die has faces A, B, C, D, E, A. How many faces show A? Find P(A). (1/5 confirms; 2/6 rules it out.)",
    "MC-O": "Is blue 2, grey 5 the same outcome as blue 5, grey 2?",
    "MC-A": "Shade every cell of the 6 x 6 table with a 6. How many?",
    "MC-N": "2 red and 8 blue balls. Find P(not red).",
}

# Used when two beliefs fit one answer and the rest of the sheet does not settle which it is.
SEPARATING_PROBES = {
    frozenset(("MC-L", "MC-O")): "Name the coins Re 1 and Rs 2. Write every way they can land. (Three lines confirms "
                                 "MC-L or MC-O; then ask 'Is HT the same as TH?' to separate them.)",
}


def needs_expert_draft():
    """Which belief remedies, per owner, have no drafted text yet."""
    return {
        code: [owner for owner in ("student", "teacher", "content") if not entry[owner]]
        for code, entry in CATALOGUE.items()
        if entry["kind"] != "slip" and not all(entry[o] for o in ("student", "teacher", "content"))
    }
