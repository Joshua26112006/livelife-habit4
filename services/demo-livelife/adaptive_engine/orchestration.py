"""Module 6: teacher-led differentiated instruction: a period-by-period plan the teacher can actually run.

One teacher cannot teach two groups at once, so groups get direct teaching in priority order and whatever does not fit moves
to the next period. Every other group has a supervised task with an answer key. The plan stays a recommendation until the
teacher approves it.
"""
from .interventions import teaching_card

DEFAULT_PERIOD_MINUTES = 45
RECAP_MINUTES = 5
EXIT_TICKET_MINUTES = 5
PRACTICE_ITEMS_PER_GROUP = 2
PRACTICE_ATTEMPT_BASE = 100


def _practice_items(pack, evidence_item_id):
    return [pack.parallel_item(pack.item(evidence_item_id), PRACTICE_ATTEMPT_BASE + i) for i in range(PRACTICE_ITEMS_PER_GROUP)]


def plan_sessions(pack, groups, evidence_item_for, period_minutes=DEFAULT_PERIOD_MINUTES, cohorts=(), card_groups=()):
    """groups in priority order -> periods of direct-teaching slots, and a card for each group."""
    teaching_time = period_minutes - RECAP_MINUTES - EXIT_TICKET_MINUTES
    if teaching_time <= 0:
        raise ValueError("period is too short for a recap and an exit ticket")
    periods, cards = [], {}
    current, used = [], 0
    for group in groups:
        minutes = pack.interventions[group["intervention_id"]]["duration_minutes"][1]
        if minutes > teaching_time:
            raise ValueError(f"{group['group_id']} needs {minutes} minutes; a period has {teaching_time} for teaching")
        if used + minutes > teaching_time:
            periods.append(current)
            current, used = [], 0
        current.append({"group_id": group["group_id"], "minutes": minutes})
        used += minutes
        cards[group["group_id"]] = teaching_card(pack, group["intervention_id"], _practice_items(pack, evidence_item_for[group["group_id"]]))
    if current:
        periods.append(current)
    for group in card_groups:
        cards[group["group_id"]] = teaching_card(pack, group["intervention_id"], _practice_items(pack, evidence_item_for[group["group_id"]]))

    all_groups = [g["group_id"] for g in groups]
    schedule = []
    for number, slots in enumerate(periods, 1):
        taught = {slot["group_id"] for slot in slots}
        clock = RECAP_MINUTES
        timed = []
        for slot in slots:
            others = [g for g in all_groups if g != slot["group_id"]]
            timed.append({"start": clock, "end": clock + slot["minutes"], "teacher_with": slot["group_id"],
                          "independent_practice": others})
            clock += slot["minutes"]
        schedule.append({
            "period": number,
            "recap": [0, RECAP_MINUTES],
            "direct_teaching": timed,
            "exit_ticket": [period_minutes - EXIT_TICKET_MINUTES, period_minutes],
            "deferred_to_later_period": [g for g in all_groups if g not in taught and not _taught_before(schedule, g)],
        })
    return {"status": "recommended", "period_minutes": period_minutes, "periods": schedule, "cards": cards, "independent_cohorts": list(cohorts),
            "practice_card_groups": [g["group_id"] for g in card_groups]}


def _taught_before(schedule, group_id):
    return any(slot["teacher_with"] == group_id for period in schedule for slot in period["direct_teaching"])
