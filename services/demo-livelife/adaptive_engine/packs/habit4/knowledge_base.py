"""Habit 4 misconception patterns, interventions and parallel scenarios. ALL DRAFT, for the LiveLife subject expert to review.

Patterns come from level 1 of each scenario rubric (lib/livelifeDemo/rubrics.ts) and from the wrong options of the knowledge
check. Each describes a pattern in an answer, never a child. Nothing here is expert-approved, so the engine will not recommend
an intervention from it unless a caller explicitly previews drafts. Content-team remedies and objectives are left None.
"""
VERSION = "habit4-draft-0.1"
ALL_COMPETENCIES = ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"]


def _pattern(name, belief, competencies, student, teacher, exit_check):
    return {"name": name, "belief": belief, "kind": "belief", "competency_ids": competencies, "student": student, "teacher": teacher,
            "content": None, "exit_check": exit_check}


MISCONCEPTIONS = {
    "WW-NAMES": _pattern("Mixes up the mindset names", "Win-Win, Win-Lose and Lose-Win are interchangeable names.", ["S2"],
                         "Say who gets what they need in each one before naming it.",
                         "Sort short situations into the three mindsets, asking who gets what they need each time.",
                         "A friend always picks the film and you never say what you want. Name the mindset and say why."),
    "WW-GIVE-IN": _pattern("Treats Win-Win as one person giving in", "Win-Win means I should just agree.", ["S1"],
                           "Ask: did what matters to me get said too?",
                           "Use the lesson's point that Win-Win does not mean both get their first choice; contrast giving in with looking for a third option.",
                           "Your friend wants to leave early and you do not. What would Win-Win look like? Why is giving in not the same?"),
    "WW-INSIST": _pattern("Treats a good outcome as getting my way", "My idea matters more than the other person's.", ["S1", "S2"],
                          "Before deciding, say what the other person needs.",
                          "Use Courage and Consideration: keep the courage to speak and add consideration for the other person.",
                          "Your group must pick one topic and you love yours. What do you say first?"),
    "WW-ONE-SIDED": _pattern("Decides without asking what the other person needs", "One side's need is enough to decide.", ["S3", "S4"],
                             "Write one question that finds out what the other person needs.",
                             "Practise asking before proposing: each pair states both needs, then one option that serves both.",
                             "Two teams want the hall at the same time. What do you ask before suggesting a plan?"),
    "WW-DISMISS": _pattern("Responds without listening", "Disagreeing means correcting or ignoring.", ["S5"],
                           "Say back what you heard, then ask one respectful question.",
                           "Model acknowledging a view before sharing your own; pairs rehearse with a low-stakes disagreement.",
                           "Write one sentence that shows you heard a classmate you disagree with."),
    "WW-AVOID": _pattern("Avoids or hides a broken promise", "If I say nothing, trust is not affected.", ["S6"],
                         "Tell the person early, say what happened, agree a next step.",
                         "Use the Emotional Bank Account as a metaphor: telling early protects trust, hiding withdraws from it.",
                         "You cannot finish your part by the agreed time. What do you do, and when?"),
    "WW-VAGUE": _pattern("Makes a promise too general to check", "Meaning well is the same as a clear commitment.", ["S8"],
                         "Add when, with whom, and how you will know you did it.",
                         "Rewrite broad promises like 'be nicer' into an action, a time and a check.",
                         "Rewrite 'I will be helpful' as a promise you could check this week."),
    "WW-AGREEMENT": _pattern("Treats an agreement as a general rule", "An agreement is a rule or a promise, without clear parts.", ["S7"],
                             "Check for all five parts before you finish.",
                             "Build one agreement together using Desired Results, Guidelines, Resources, Accountability and Consequences.",
                             "You and a friend share a bicycle. Write the five parts of your agreement."),
    "H4-PARTIAL": {"name": "Partly shown", "belief": "On the right track; part of what the rubric looks for is missing.", "kind": "slip",
                   "competency_ids": ALL_COMPETENCIES, "student": "Look at the rubric's next level and add the missing part.",
                   "teacher": None, "content": None, "exit_check": None},
}

TEACHING_ORDER = ("WW-NAMES", "WW-GIVE-IN", "WW-INSIST", "WW-ONE-SIDED", "WW-DISMISS", "WW-AVOID", "WW-VAGUE", "WW-AGREEMENT")

# What choosing each wrong option suggests, per knowledge-check question.
DISTRACTORS = {
    "K1": {"A": "WW-INSIST", "B": "WW-GIVE-IN", "D": "WW-AVOID"},
    "K2": {"A": "WW-NAMES", "C": "WW-NAMES", "D": "WW-NAMES"},
    "K3": {"A": "WW-INSIST", "B": "WW-GIVE-IN", "D": "WW-ONE-SIDED"},
    "K4": {"A": "WW-INSIST", "B": "WW-AVOID", "D": "WW-INSIST"},
    "K5": {"A": "WW-DISMISS", "C": "WW-DISMISS", "D": "WW-DISMISS"},
    "K6": {"A": "WW-AVOID", "B": "WW-AVOID", "D": "WW-AVOID"},
    "K7": {"B": "WW-AGREEMENT", "C": "WW-AGREEMENT", "D": "WW-AGREEMENT"},
    "K8": {"A": "WW-VAGUE", "B": "WW-VAGUE", "D": "WW-VAGUE"},
    "K9": {"B": "WW-NAMES", "C": "WW-NAMES", "D": "WW-NAMES"},
}

# What a rubric level 1 points to. Two entries mean the rubric's own wording covers both, so a probe decides.
LEVEL_ONE_PATTERNS = {
    "S1": ["WW-GIVE-IN", "WW-INSIST"],
    "S2": ["WW-NAMES", "WW-INSIST"],
    "S3": ["WW-ONE-SIDED"],
    "S4": ["WW-ONE-SIDED"],
    "S5": ["WW-DISMISS"],
    "S6": ["WW-AVOID"],
    "S7": ["WW-AGREEMENT"],
    "S8": ["WW-VAGUE"],
}

PROBES = {
    "WW-NAMES": "A student always lets others choose. Which mindset is that, and who is not getting what they need?",
    "WW-GIVE-IN": "If you agree just to stop an argument, is that Win-Win? Why or why not?",
    "WW-INSIST": "Your idea was not chosen. What would still make the result fair?",
    "WW-ONE-SIDED": "What would you need to know from the other person before you decide?",
    "WW-DISMISS": "A classmate disagrees with you. What is the first thing you would say?",
    "WW-AVOID": "You realise you cannot keep a promise. Who do you tell, and when?",
    "WW-VAGUE": "How would someone else know that you kept this promise?",
    "WW-AGREEMENT": "What would your agreement say about what happens if someone does not do their part?",
}

SEPARATING_PROBES = {
    frozenset(("WW-GIVE-IN", "WW-INSIST")): "When two friends disagree, who should change their mind, and why?",
    frozenset(("WW-NAMES", "WW-INSIST")): "Name the mindset in 'my idea must be chosen'. Would you do it that way yourself?",
}


def _entry(title, steps):
    return {"title": title, "objective": None, "steps": steps, "duration_minutes": (10, 15), "assets": [],
            "item_types": ["mcq", "scenario"], "exit_check": None, "review_status": "draft", "version": VERSION}


INTERVENTIONS = {
    "INT-H4-NAMES": _entry("Telling the mindsets apart (lesson: h4-mindsets)", ["Recap the three ways to handle a problem.", "Sort situations into the three mindsets.", "Say who gets what they need in each."]),
    "INT-H4-GIVE-IN": _entry("Win-Win is not giving in (lesson: h4-mindsets)", ["Contrast giving in with looking for a third option.", "Replay one scenario both ways.", "Students write an option that considers both."]),
    "INT-H4-INSIST": _entry("Courage with consideration (lesson: h4-mindsets)", ["Revisit courage and consideration.", "Find what the other person needs in a scenario.", "Rewrite a demand as a shared proposal."]),
    "INT-H4-ONE-SIDED": _entry("Ask before deciding (lesson: h4-mindsets)", ["Each partner states what they need.", "Write one respectful question.", "Propose an option and check it with both."]),
    "INT-H4-DISMISS": _entry("Listening when you disagree (lesson: h4-mindsets)", ["Model acknowledging before responding.", "Pairs rehearse with a low-stakes disagreement.", "Write a sentence that shows listening."]),
    "INT-H4-AVOID": _entry("Protecting trust when a promise slips (lesson: h4-promises)", ["Use the Emotional Bank Account metaphor.", "Compare telling early with hiding it.", "Write what to say and when."]),
    "INT-H4-VAGUE": _entry("Promises you can check (lesson: h4-promises)", ["Compare a broad promise with a specific one.", "Add action, time and check.", "Rewrite a promise of your own."]),
    "INT-H4-AGREEMENT": _entry("The five parts of an agreement (lesson: h4-agreements)", ["Name the five parts.", "Build one agreement together.", "Check a sample agreement for missing parts."]),
    "INT-H4-PRACTICE": _entry("Reaching the next rubric level", ["Read the next rubric level.", "Add the missing part to your own answer."]),
}

INTERVENTION_MAP = {
    "WW-NAMES": ["INT-H4-NAMES"], "WW-GIVE-IN": ["INT-H4-GIVE-IN"], "WW-INSIST": ["INT-H4-INSIST"], "WW-ONE-SIDED": ["INT-H4-ONE-SIDED"],
    "WW-DISMISS": ["INT-H4-DISMISS"], "WW-AVOID": ["INT-H4-AVOID"], "WW-VAGUE": ["INT-H4-VAGUE"], "WW-AGREEMENT": ["INT-H4-AGREEMENT"],
    "H4-PARTIAL": ["INT-H4-PRACTICE"],
}

# New situations per competency, marked with that competency's existing rubric. The first two are re-tests, the last two practice.
PARALLEL_SCENARIOS = {
    "S1": ["Two cousins disagree about which show to watch. One says, “Win-Win means I just have to let you pick.” What would you suggest?",
           "Your group disagrees about where to sit. Someone says, “Fine, I’ll give up, that’s Win-Win.” What would you say?",
           "Two friends want different snacks to share. What would a Win-Win look like?",
           "A friend says Win-Win means nobody gets anything they want. What would you tell them?"],
    "S2": ["A team captain says, “We do it my way or not at all.” Which mindset is this? Explain and suggest a better approach.",
           "A student always stays quiet and lets others decide, even when upset. Which mindset is this? Suggest a better approach.",
           "Someone says, “If I win, you have to lose.” Which mindset is this, and why?",
           "A friend says, “Whatever you want, I don’t matter.” Which mindset is this, and what could help?"],
    "S3": ["Your friend wants to revise tonight; you want to go out. What would you ask or say before deciding?",
           "Your partner wants to present first; you are nervous about going last. What would you say before deciding?",
           "A teammate wants a bright poster and you want a simple one. What would you ask them?",
           "Your sibling wants the room quiet and you want music. What would you ask first?"],
    "S4": ["Two classmates need the same library book this week. Suggest one solution and say how you would check it is fair.",
           "Two groups want the same practice ground after school. Suggest one solution and how you would check it is fair.",
           "Two friends need the same calculator for a test and homework. What could work for both?",
           "Two students both want the window seat on a trip. What could work for both?"],
    "S5": ["A classmate says your favourite sport is boring. Write one sentence that shows listening and respect.",
           "In a debate, a classmate challenges your point. Write one sentence you could say that shows respect.",
           "A friend thinks your plan will not work. What could you say first?",
           "Someone in your group has a different answer from yours. What could you say?"],
    "S6": ["You told a friend you would return their notes today, but you left them at home. What would you do to protect trust?",
           "You agreed to help with a poster but have a family event. What would you do to protect trust?",
           "You will be late to meet a friend. What would you do?",
           "You forgot to do your part of a group task. What would you do next?"],
    "S7": ["You and a neighbour want to share a cricket bat. What would you include in your agreement so it is clear and fair?",
           "You and your sibling want to share a tablet. What would you include in your agreement so it is clear and fair?",
           "Your group is sharing art supplies. What should your agreement include?",
           "Two friends are planning to share chores for a class party. What should their agreement include?"],
    "S8": ["Choose one situation at home where you could practise Think Win-Win this week. What will you do, and how will you check?",
           "Choose one group activity at school this week. What specific action will you take, and how will you check?",
           "Write one Win-Win action for tomorrow and how you will know you did it.",
           "Write one promise for this week that someone else could check."],
}
