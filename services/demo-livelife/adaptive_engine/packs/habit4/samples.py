"""Synthetic sample files for the Habit 4 pack. Not real student data."""
import json
from pathlib import Path

from ...bulk import to_csv
from ...samples import paper_columns

STUDENTS = Path(__file__).resolve().parents[3] / "demos" / "adaptive-engine" / "sample_habit4.json"

# Synthetic written answers at three rubric levels, for the sample Habit 4 class.
HABIT4_V1 = {
    "S1": {4: "Win-Win is not just agreeing. They should each say what matters and try football first and the board game after, if both are happy.", 2: "They could take turns.", 1: "One of them should just give in so there is no fight."},
    "S2": {4: "That is Win-Lose because only one person's idea counts. A better way is to hear every idea and choose together.", 2: "It is Win-Lose.", 1: "That is fine, the best idea should always win."},
    "S3": {4: "I would say I know you want more practice and I want to finish today. What part needs more time, and can we plan both?", 2: "We should talk about it.", 1: "We are finishing today, that is it."},
    "S4": {4: "One uses the computer for the first half and the other the second, and we ask both if the split feels fair.", 2: "They can share the computer.", 1: "The one who came first should keep the computer."},
    "S5": {4: "I hear your point and I see it differently. Can you tell me why you think that?", 2: "Okay, thanks for saying that.", 1: "You are wrong, stop talking."},
    "S6": {4: "I would tell them early, say sorry, explain why, and agree a new time to help that works for both of us.", 2: "I would say sorry.", 1: "I would just not go and say nothing about it."},
    "S7": {4: "Desired results are equal time. Guidelines are half an hour each. Resources are the console and a timer. We check each week, and if someone skips their turn they give up ten minutes.", 2: "We will take turns and use a timer.", 1: "We promise to be fair."},
    "S8": {4: "In group work tomorrow I will listen to each partner before I speak, and I will ask a friend afterwards if I did it.", 2: "I will be nicer this week.", 1: "My teacher will make me be good."},
}
HABIT4_V2 = {
    "S1": {4: "Win-Win is not just letting someone pick. They should each say what they want and find a show both like, or watch one each.", 1: "One cousin should let the other pick."},
    "S2": {4: "That is Win-Lose, since only the captain's way counts. Better to hear the team and choose together.", 1: "That is okay, captains decide everything."},
    "S3": {4: "I would say I know you want to revise and I want to go out. How long do you need, and could we do both?", 1: "We are going out, you can revise later."},
    "S4": {4: "One borrows it for the first half of the week and the other for the rest, and we ask both if that feels fair.", 1: "Whoever took it first keeps it."},
    "S5": {4: "I understand you find it boring. What sports do you enjoy, and can I tell you why I like it?", 2: "Okay, thanks for telling me."},
    "S6": {4: "I would tell them right away, say sorry, and agree a time tomorrow to bring the notes.", 1: "I would avoid them today and hope they forget."},
    "S7": {4: "Desired results are fair use. Guidelines are alternate days. Resources are the bat and a schedule. We check on Sundays, and if someone misses a turn they swap a day.", 1: "We promise to share."},
    "S8": {4: "At home this week I will ask my sister before I use the shared desk, and I will tick a chart each day I do it.", 1: "My parents will tell me what to do."},
}
HABIT4_V2_STILL_STRUGGLING = {"H03": ["S5"], "H04": ["S6"]}


def _students():
    return json.loads(STUDENTS.read_text())["students"]


def _v1_row(student, items):
    row = [student["id"]]
    for item in items:
        if item["type"] == "mcq":
            row.append(student.get("mcq", {}).get(item["id"], item["key"]))
        else:
            score = student.get("scores", {}).get(item["id"], 4)
            row.append("I do not know, I like pizza." if score == 0 else HABIT4_V1[item["id"]][score])
    return row


def _v2_row(student, items):
    keep = HABIT4_V2_STILL_STRUGGLING.get(student["id"], [])
    row = [student["id"]]
    for item in items:
        key = item["competency_ids"][0]
        row.append(min(HABIT4_V2[key].items())[1] if key in keep else HABIT4_V2[key][4])
    return row


def sample(pack, round_name):
    columns, items = paper_columns(pack, round_name)
    build = _v1_row if round_name == "v1" else _v2_row
    return to_csv(columns, [build(student, items) for student in _students()])
