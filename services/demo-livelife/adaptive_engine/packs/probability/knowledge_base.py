"""Probability intervention knowledge base and competency map.

Sequences and durations are from the concept document, section 12; exit checks and INT-A, INT-U and INT-S are from the strategy
doc, section 7. Everything is `draft` until a subject expert approves it. No document states an objective for any entry, so
those stay None rather than being invented.
"""
VERSION = "probability-pilot-0.1"

COMPETENCIES = {
    "PROB-01": {"name": "Identify a random experiment and list its outcomes", "prerequisites": []},
    "PROB-02": {"name": "Distinguish equally likely outcomes from those that are not", "prerequisites": ["PROB-01"]},
    "PROB-03": {"name": "Identify the sample space and represent outcomes systematically", "prerequisites": ["PROB-01"]},
    "PROB-04": {"name": "Identify and count favourable outcomes", "prerequisites": ["PROB-01", "PROB-03"]},
    "PROB-05": {"name": "Apply P(E) = favourable / total", "prerequisites": ["PROB-02", "PROB-04"]},
    "PROB-06": {"name": "Elementary events; their probabilities sum to 1", "prerequisites": ["PROB-03", "PROB-04", "PROB-05"]},
    "PROB-07": {"name": "Calculate the complement: P(not E) = 1 - P(E)", "prerequisites": ["PROB-05"]},
    "PROB-08": {"name": "Identify impossible and certain events", "prerequisites": ["PROB-01", "PROB-05"]},
    "PROB-09": {"name": "Apply probability in contextual counting problems", "prerequisites": ["PROB-04", "PROB-05"]},
    "PROB-10": {"name": "Enumerate compound outcomes", "prerequisites": ["PROB-03", "PROB-04", "PROB-05"]},
    "PROB-11": {"name": "Reason about unequal likelihood of event categories", "prerequisites": ["PROB-02", "PROB-03", "PROB-10"]},
    "PROB-12": {"name": "Use the range 0 to 1 and identify invalid values", "prerequisites": ["PROB-05", "PROB-07", "PROB-08"]},
}

# Our proposal, for expert review. Slips point at the skill the slip touches.
MISCONCEPTION_COMPETENCIES = {
    "MC-R": ["PROB-12"], "MC-L": ["PROB-02"], "MC-O": ["PROB-03"], "MC-N": ["PROB-07"], "MC-A": ["PROB-10"], "MC-U": ["PROB-09"],
    "DECK": ["PROB-09"], "SLIP-E": ["PROB-10"], "SLIP-F": ["PROB-05"],
}


def _entry(title, steps, minutes, assets, item_types, exit_check=None):
    return {"title": title, "objective": None, "steps": steps, "duration_minutes": minutes, "assets": assets,
            "item_types": item_types, "exit_check": exit_check, "review_status": "draft", "version": VERSION}


INTERVENTIONS = {
    "INT-PROB-01": _entry(
        "Count individuals, not category labels",
        ["Use a bag model with individually counted objects.", "Show the event as a subset of outcomes.",
         "Ask the learner to count total elementary outcomes and favourable outcomes.",
         "Compare 4 red / 1 blue and 3 colours / 9 marbles."],
        (10, 15), ["Physical or demo image", "Labelled set", "Mini worksheet"], ["bag_not", "labelled_faces"],
        "Faces 1, 1, 2, 3, 3, 3: P(3)? (3/6)"),
    "INT-PROB-02": _entry(
        "Equally likely outcomes",
        ["Compare a fair die or coin with a 4-red / 1-blue bag.", "Ask whether each elementary outcome is equally likely.",
         "Ask whether the colour events are equally likely.", "Clarify the assumptions."],
        (10, 15), ["Comparison cards", "Teacher prompts"], ["argument"]),
    "INT-PROB-03": _entry(
        "Sample space for two coins",
        ["Label coin A and coin B.", "Construct a 2 x 2 table or tree.", "Enumerate HH, HT, TH, TT.",
         "Highlight why HT and TH are distinct when the coins are distinguishable."],
        (10, 15), ["Table or tree template", "Guided questions"], ["coins_exactly", "coins_at_least_one"],
        "Two dice, sum 9 (4/36)"),
    "INT-PROB-04": _entry(
        "Compound enumeration for two dice",
        ["Demonstrate distinguishable blue and grey dice.", "Use the NCERT 6 x 6 outcome table.",
         "Mark a target sum.", "Count favourable pairs and divide by 36."],
        (15, 20), ["Printed 6 x 6 grid", "Coloured marks", "Worked example"], ["dice_sum", "die_twice_at_least"],
        "Two dice, sum 9 (4/36)"),
    "INT-PROB-05": _entry(
        "Favourable and total: which goes where",
        ["Use a 'whole set' representation.", "Students circle favourable outcomes and count all outcomes.",
         "Fill numerator and denominator separately before calculating."],
        (10, 10), ["Set diagram", "Structured worksheet"], []),
    "INT-PROB-06": _entry(
        "The complement relation",
        ["Draw a probability bar for the whole of 1.", "Split it into E and not E.",
         "Use P(ace) = 1/13 and P(not ace) = 12/13.", "Calculate the complement by 1 - P(E)."],
        (10, 12), ["Probability bar", "Guided practice"], ["bag_not", "complement"],
        "2 red, 3 blue, 5 yellow; P(not yellow) (5/10)"),
    "INT-PROB-07": _entry(
        "Impossible and certain events; the range",
        ["Use standard die outcomes.", "Ask about 7, less than 7, and the range of a probability.",
         "Map impossible to 0 and certain to 1.", "Practise validating probability values."],
        (8, 12), ["Number line", "Event cards"], ["complement"],
        "Which cannot be a probability: 1.2, 0, 45%, 3/5? (1.2)"),
    "INT-PROB-08": _entry(
        "Fraction simplification after a correct set-up",
        ["Brief prerequisite mini-practice reducing fractions.", "Keep the probability concept apart from arithmetic fluency."],
        (5, 10), ["Fraction practice cards"], [], "Simplify 4/36 (1/9)"),
    "INT-PROB-09": _entry(
        "Two-dice sums are not equally likely",
        ["Count frequency across the 36 ordered pairs.", "Build the distribution of sums 2 to 12.",
         "Compare the counts for 2, 7 and 12.", "Explain why the 11 sums are not equally likely."],
        (15, 20), ["6 x 6 table", "Tally chart"], ["dice_sum"]),
    "INT-A": _entry(
        "'At least once' without adding",
        ["Shade row 5 and column 5 of the 6 x 6 table.", "Show they meet at (5, 5), so 6 + 6 counts it twice.",
         "Or use 1 - P(no 5) = 1 - 25/36."],
        (10, 15), ["Printed 6 x 6 grid"], ["die_twice_at_least", "coins_at_least_one"],
        "Two dice, at least one even number? (27/36)"),
    "INT-U": _entry(
        "Recount after an item is removed",
        ["Write what is in the box now.", "Count again before dividing."],
        (10, 10), [], ["removal"], "10 pens, 3 defective; a good one removed; P(good) next (6/9)"),
    "INT-S": _entry(
        "Systematic listing",
        ["List outcomes row by row so none is skipped."],
        (5, 10), ["Printed 6 x 6 grid"], ["dice_sum"], "Two dice, sum 6, every pair listed (5/36)"),
}

# Which interventions can answer which misconception. Our proposal, for expert review.
INTERVENTION_MAP = {
    "MC-R": ["INT-PROB-07"],
    "MC-L": ["INT-PROB-01", "INT-PROB-02", "INT-PROB-09"],
    "MC-O": ["INT-PROB-03", "INT-PROB-04"],
    "MC-N": ["INT-PROB-06"],
    "MC-A": ["INT-A"],
    "MC-U": ["INT-U"],
    "SLIP-E": ["INT-S"],
    "SLIP-F": ["INT-PROB-08"],
}
