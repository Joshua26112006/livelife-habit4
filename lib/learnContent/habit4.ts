// Learn chapter "Habit 4: Think Win-Win" (LiveLife Education, Discovering the Leader in Me, Level 5).
//
// SOURCE: the LiveLife source document (scenarios, MCQ bank, video scripts,
// reflection exercises) and LiveLife.pdf pages 2-7 (the workbook). The brief's MCQs and scenarios are used as
// written; everything else (option feedback lines, concept cards, blog walk-throughs, retention cards, image
// prompts) is AI-drafted from them and is marked FOR SME REVIEW. Added examples are ORIGINAL, ILLUSTRATIVE
// examples, not workbook text. Confirm rights before reproducing branded workbook text or artwork.
//
// THREE SECTIONS (the brief's source map):
//   h4-mindsets    PDF p2-3  Three mindsets, courage + consideration, Venn, the three scenarios
//   h4-promises    PDF p4-5  Emotional Bank Account, what a promise is, promises to self and others
//   h4-agreements  PDF p6-7  Interdependent living, the five-part Win-Win Agreement, Luis, Sam and Joseph
//
// REVIEW NOTES (for the LiveLife SME):
// 1. Win-Win is taught as a pattern, not a label for a child. Wording avoids "bad" or "selfish" for anyone.
// 2. Win-Win does NOT mean both get their first choice (brief, video 1). Every feedback line keeps that.
// 3. The Emotional Bank Account is a metaphor, not a literal score (brief, slide 11).
// 4. Mastery answers are open-ended; the keyword check is lenient. The 0-2 rubric in the brief is for teachers.
// 5. The brief's student scenario rubric (0-4), the student growth report, the teacher competency rubric and
//    the teacher action plan are NOT part of the Learn chapter; they are separate products.

import type { SeededThinkCard } from "../learnTypes";
import type { LearnChapter } from "../learnTypes";
import type { SectionConceptCards, SectionBlogContent, IdentifyQuestion } from "../learnTypes";
import type { MasteryQuestion } from "../learnTypes";
import type { RetentionSeed } from "../learnTypes";

export const H4_SECTION_IDS = ["h4-mindsets", "h4-promises", "h4-agreements"] as const;

// ─── THINK (engagement cards) ─────────────────────────────────────────────────

export const H4_THINK: Record<string, SeededThinkCard[]> = {
  "h4-mindsets": [
    {
      question: "At break time you and a friend are playing with a ball. Some students from another class come over and try to take it. What could you do?",
      imageUrl: "",
      imagePrompt: "Two children holding a ball on a sunny school playground while a few children from another class look at it hopefully, expressive friendly faces, Pixar style, no text",
      options: [
        { text: "Shout, ignore them and keep playing", hook: "That keeps the ball, but the other children feel shut out and the problem is still there. This is a Win-Lose pattern: you may win the ball but lose the relationship." },
        { text: "Give them the ball even though you want to keep playing", hook: "That ends the argument, but you may feel like a doormat. This is a Lose-Win pattern. Your need matters too." },
        { text: "Invite them to play and make the game bigger", hook: "This considers what everyone wants: a game, and to be included. That is the idea behind Win-Win. It takes courage to offer and consideration to include." },
      ],
    },
    {
      question: "Your friend wants to go to a movie. You want to go to the park. Both of you want a fun outing together. What helps most?",
      imageUrl: "",
      imagePrompt: "Two friends on a sidewalk, one pointing toward a cinema and the other toward a green park, friendly and thoughtful, warm light, Pixar style, no text",
      eyebrow: "🤔 Now try a real choice...",
      options: [
        { text: "Ask what each of you enjoys and brainstorm", hook: "Good thinking. Asking first shows you care what they want, and brainstorming opens more options than just movie or park." },
        { text: "Pick the park today and the movie next time", hook: "That can be a fair Win-Win, because both wishes get their turn. Check that your friend really agrees, too." },
        { text: "Say yes to the movie so there is no argument", hook: "Avoiding the argument can be a Lose-Win if you feel unheard. A good plan is fair, possible and agreed by both people." },
      ],
    },
    {
      question: "You want to be popular and think your clothes are the problem. You know your family cannot afford new clothes right now. What could you do?",
      imageUrl: "",
      imagePrompt: "A thoughtful child looking at shop windows with clothes, a parent walking beside them, calm and kind mood, Pixar style, no text",
      options: [
        { text: "Talk to your parents about what you want and what the family can afford", hook: "Both sides get heard. Your family's limits are real, and so is your wish. Asking calmly is a good start." },
        { text: "Look for ways to save, swap or choose something affordable", hook: "A Win-Win does not need everything you first imagined. Saving up or swapping can meet your need without putting pressure on the family." },
        { text: "Ask your parents again and again until they give in", hook: "Pushing makes it a Win-Lose and can hurt trust. Listening to why they cannot buy it is part of thinking Win-Win." },
      ],
    },
    {
      question: "The school announces a poster contest and your class decides to enter. A new girl draws really well. What is a Win-Win way to involve everyone?",
      imageUrl: "",
      imagePrompt: "A classroom of children planning a poster together, a new girl showing her drawing and others admiring it, joyful, Pixar style, no text",
      options: [
        { text: "Ask her and the class how everyone can help", hook: "Great. When the class listens first, each person can share a strength: drawing, ideas, colours or lettering." },
        { text: "Let the best drawers do everything", hook: "That may win the contest, but others feel left out. Win-Win includes everyone and still aims for a good poster." },
        { text: "Share roles so each person has a job", hook: "Yes. Shared roles mean the poster uses everyone's strengths and the work feels fair." },
      ],
    },
  ],

  "h4-promises": [
    {
      question: "A friend asks if you will bring a book to school tomorrow. You nod. Did you make a promise?",
      imageUrl: "",
      imagePrompt: "A child nodding to a friend with a storybook in hand in a bright school corridor, friendly mood, Pixar style, no text",
      options: [
        { text: "Yes. Nodding tells them you will definitely do it", hook: "Right. A promise is a statement or an action that tells someone you will definitely do something. A nod can be a promise." },
        { text: "No. I only promise when I say the word 'promise'", hook: "Not quite. People count on your word and your actions, even without the word 'promise'." },
        { text: "It depends on whether I remember", hook: "A promise does not depend on remembering. That is why small reminders, like putting the book by the door, help." },
      ],
    },
    {
      question: "You promise a friend you will help with their whole project, finish your chores forever and call them every night. What might go wrong?",
      imageUrl: "",
      imagePrompt: "A child looking overwhelmed with a long list of promises floating around them, a friend watching kindly, Pixar style, no text",
      eyebrow: "🤔 One more thing to notice...",
      options: [
        { text: "It is too big to keep, so trust could drop", hook: "Yes. Big promises are hard to keep. A good promise is specific, realistic and has a time." },
        { text: "Nothing, big promises make friends happier", hook: "They sound kind, but when a promise cannot be kept, it can feel like a withdrawal from trust." },
        { text: "I should promise something smaller and clear", hook: "Exactly. For example: 'I will help with the poster on Saturday for one hour.'" },
      ],
    },
    {
      question: "You promised to return a friend's book today, but you cannot. What do you do?",
      imageUrl: "",
      imagePrompt: "A child honestly talking to a friend about a borrowed book, both calm and kind, Pixar style, no text",
      options: [
        { text: "Tell your friend early, say sorry and make a new plan", hook: "This protects trust. Being honest early, apologising and renegotiating is what keeps a relationship strong." },
        { text: "Say nothing and hope they forget", hook: "Silence can feel like a withdrawal. Your friend may be waiting and worrying." },
        { text: "Say 'I can't finish today. Could I return it tomorrow?'", hook: "That is a clear, respectful new promise. Both of you know what to expect." },
      ],
    },
  ],

  "h4-agreements": [
    {
      question: "Luis wants his own phone. His parents want him to read more. How can they both get something good?",
      imageUrl: "",
      imagePrompt: "A boy with books at a library table while his parents smile at him and a phone sits in the background, warm light, Pixar style, no text",
      options: [
        { text: "Luis earns his phone by reading", hook: "That links the two wishes. Luis gets a phone, and the parents see him reading more. This is a Win-Win Agreement." },
        { text: "The parents decide and Luis accepts", hook: "A one-sided decision can leave Luis feeling unheard. A Win-Win Agreement is made together." },
        { text: "Luis gets the phone and promises to read later", hook: "A promise with no plan is easy to lose. A good agreement says how and when, and how to check." },
      ],
    },
    {
      question: "Two cousins live together. Sam wants to play Joseph's video games but does not look after them, which causes fights. What would help most?",
      imageUrl: "",
      imagePrompt: "Two cousins sitting together with game controllers, writing a simple plan on paper, friendly mood, Pixar style, no text",
      eyebrow: "🤔 Use the five parts...",
      options: [
        { text: "Write down turns, rules for care and how to check", hook: "Yes. Written parts like these make the plan clear: results, guidelines, resources, accountability and consequences." },
        { text: "Sam promises to be careful", hook: "A promise is a good start, but it is stronger when the rules and checks are written down together." },
        { text: "Joseph stops sharing his games", hook: "That ends the fights but it is not a Win-Win. Sam loses out and Joseph does not feel good about sharing." },
      ],
    },
    {
      question: "An agreement says: 'We check the schedule every Friday.' Which part of a Win-Win Agreement is that?",
      imageUrl: "",
      imagePrompt: "Two children checking off a weekly schedule on a wall together, calm and proud, Pixar style, no text",
      options: [
        { text: "Accountability", hook: "Yes. Accountability says how and when we check that the plan is being followed." },
        { text: "Resources", hook: "Resources are what you need to follow the plan, like a timer or a book. Checking the schedule is a different part." },
        { text: "Desired Results", hook: "Desired Results is the outcome both people want. The Friday check is how you see whether you are getting it." },
      ],
    },
  ],
};

// ─── CONCEPT cards (Understanding phase) ──────────────────────────────────────

export const H4_CONCEPT: Record<string, SectionConceptCards> = {
  "h4-mindsets": {
    cards: [
      {
        title: "Three Ways to Handle a Problem",
        hook: "A disagreement does not have to end with one person winning and one person losing.",
        body: [
          "Lose-Win: you give in, and you may feel like a doormat. Win-Lose: you get your way, but the relationship can get hurt. Win-Win: you look for a solution that considers what matters to both people.",
          "These are patterns, not labels for a person. Anyone can use any of them on a different day.",
        ],
        visual: { type: "none" },
        tip: "Win-Win does not mean both people get their first choice. It means both needs are heard and a fair, workable plan is agreed.",
        imagePrompt: "Three short scenes of children handling a disagreement over a ball: one gives in, one insists, two talk together, Pixar style, no text",
      },
      {
        title: "Courage and Consideration",
        hook: "Win-Win needs two things at once: the courage to say what you need, and the consideration to hear what the other person needs.",
        body: [
          "Courage means standing up for what you believe in a calm way. Consideration means caring about the other person's beliefs and feelings.",
          "Drawing two circles can help: write your needs in one, their needs in the other, and look for what fits in the overlap.",
        ],
        visual: { type: "none" },
        tip: "Ask yourself: Did we both feel heard? Is the plan fair? Can we really do it? Do we both agree?",
        imagePrompt: "Two children standing like two pillars together, one speaking, one listening, soft light, Pixar style, no text",
      },
    ],
  },
  "h4-promises": {
    cards: [
      {
        title: "The Emotional Bank Account",
        hook: "Trust in a relationship grows and shrinks, a bit like a bank account.",
        body: [
          "Deposits build and repair trust: keeping promises, being kind, listening. Withdrawals break trust: broken promises, ignoring someone.",
          "This is a metaphor. It helps us think about trust; nobody is keeping a score.",
        ],
        visual: { type: "none" },
        tip: "Keeping a promise is a deposit. Making deposits feels good, and withdrawals do not.",
        imagePrompt: "A glowing piggy bank filling with hearts and stars as two children keep their promises, Pixar style, no text",
      },
      {
        title: "A Promise You Can Keep",
        hook: "A promise is a statement or action that tells someone you will definitely do something.",
        body: [
          "A good promise is specific, realistic and has a time. For example: 'I will put my bag by the door tonight.'",
          "If a plan changes, tell the person early, say sorry and agree on a new plan. Keeping promises to yourself builds self-trust too.",
        ],
        visual: { type: "none" },
        tip: "Ask: Can I do it? When? What might get in the way?",
        imagePrompt: "A child writing a small promise on a sticky note and putting it on a mirror, morning light, Pixar style, no text",
      },
    ],
  },
  "h4-agreements": {
    cards: [
      {
        title: "Interdependent Living",
        hook: "You do not have to do everything alone, and neither does the other person.",
        body: [
          "A Win-Win Agreement is when two or more people commit to work together for the benefit of both. You can make one in almost any relationship or situation.",
          "It turns 'my way or your way' into 'our plan'.",
        ],
        visual: { type: "none" },
        tip: "An agreement can be changed later if it is not working. Check it together.",
        imagePrompt: "Two children carrying a heavy box together up some steps, smiling, Pixar style, no text",
      },
      {
        title: "The Five Parts of a Win-Win Agreement",
        hook: "Five simple parts turn a good idea into a clear plan.",
        body: [
          "Desired Results: what outcome do we both want? Guidelines: what rules will we follow? Resources: what do we need? Accountability: how will we check? Consequences: what fair next step happens if the plan is not followed?",
          "Example (illustrative): Two cousins share a console. Results: fair turns without arguing. Guidelines: 30-minute turns with a timer. Resources: console, timer, written schedule. Accountability: tick off turns each evening. Consequences: pause, talk, restore the missed turn.",
        ],
        visual: { type: "none" },
        tip: "Consequences are a fair, related next step. They are never humiliating or harmful.",
        imagePrompt: "Five colourful tiles on a table, each with a simple icon, two children arranging them, Pixar style, no text",
      },
    ],
  },
};

// ─── BLOG (key facts + worked scenarios) ──────────────────────────────────────

export const H4_BLOG: Record<string, SectionBlogContent> = {
  "h4-mindsets": {
    keyFacts: {
      what: "Think Win-Win is an attitude: when there is a conflict, look for a solution that considers what matters to both people.",
      formula: "Win-Win test: Did we both feel heard? Are both needs considered? Is it fair? Can we do it? Do we both freely agree?",
      example: "Friend wants a movie, you want the park. You ask what each of you enjoys and agree on the park today and the movie next time.",
      tip: "Win-Win is not giving in and not avoiding every disagreement. It is a fair plan that both people accept.",
    },
    problems: [
      {
        title: "Movie or park?",
        problem: "Maya wants to see a movie. Arjun hoped to go to the park. Both want a fun outing together. What can they do?",
        steps: [
          { method: "Listen first", instruction: "Each person says what they want and why.", visual: { type: "equation", lines: [[{ text: "Maya: ", bold: true }, { text: "I want something indoors and relaxing." }], [{ text: "Arjun: ", bold: true }, { text: "I want to run around outside." }]] }, why: "Listening shows you care and uncovers the real needs behind the first choices." },
          { method: "Brainstorm", instruction: "Make a list of options before choosing.", visual: { type: "equation", lines: [[{ text: "Park today, movie next time" }], [{ text: "A short film, then the park" }], [{ text: "Another activity both enjoy" }]] }, why: "More options make a fair choice easier." },
          { method: "Check it", instruction: "Ask: is it fair, can we do it, do we both agree?", visual: { type: "equation", lines: [[{ text: "Fair? ", bold: true }, { text: "Yes", color: "success" }], [{ text: "Possible? ", bold: true }, { text: "Yes", color: "success" }], [{ text: "Both agree? ", bold: true }, { text: "Yes", color: "success" }]] }, why: "A plan only works if both people freely accept it." },
        ],
      },
    ],
  },
  "h4-promises": {
    keyFacts: {
      what: "A promise tells someone you will definitely do something. Keeping promises builds trust, and the Emotional Bank Account is a metaphor for that trust.",
      formula: "Promise, then plan, then follow through, then communicate if plans change.",
      example: "'I will put my bag by the door tonight' is specific, realistic and has a time.",
      tip: "If you cannot keep a promise, tell the person early, say sorry and make a new plan.",
    },
    problems: [
      {
        title: "A promise at risk",
        problem: "You promised to return a friend's book at 4 pm, but you will not be able to. What helps trust most?",
        steps: [
          { method: "Be honest early", instruction: "Tell your friend as soon as you know.", visual: { type: "equation", lines: [[{ text: "\"I can't finish today.\"", bold: true }]] }, why: "Early honesty lets them plan too." },
          { method: "Say sorry", instruction: "Acknowledge the change without making excuses.", visual: { type: "equation", lines: [[{ text: "\"I'm sorry about the change.\"", bold: true }]] }, why: "A sincere apology repairs trust." },
          { method: "Make a new plan", instruction: "Offer a specific new time.", visual: { type: "equation", lines: [[{ text: "\"Could I return it tomorrow?\"", bold: true, color: "success" }]] }, why: "A clear new promise gives both of you something to rely on." },
        ],
      },
    ],
  },
  "h4-agreements": {
    keyFacts: {
      what: "A Win-Win Agreement is when two or more people commit to work together for the benefit of both. It has five parts.",
      formula: "Desired Results, Guidelines, Resources, Accountability, Consequences.",
      example: "Luis earns a phone by reading books at his grade level; his parents take him to the library and check once a week.",
      tip: "Make each part specific, fair and freely agreed. Agreements can be revised.",
    },
    problems: [
      {
        title: "The shared game console",
        problem: "Sam wants longer play, Joseph wants fair turns and less fighting. Draft an agreement (illustrative).",
        steps: [
          { method: "Desired Results", instruction: "State what both want.", visual: { type: "equation", lines: [[{ text: "Fair turns and no arguing." }]] }, why: "A shared goal keeps the plan fair." },
          { method: "Guidelines and Resources", instruction: "Rules and things you need.", visual: { type: "equation", lines: [[{ text: "30-minute turns, use a timer." }], [{ text: "Console, controller, written schedule." }]] }, why: "Clear rules and tools remove guesswork." },
          { method: "Accountability and Consequences", instruction: "How you will check, and a fair next step.", visual: { type: "equation", lines: [[{ text: "Tick off turns each evening." }], [{ text: "If missed: pause, talk, restore the turn.", color: "success" }]] }, why: "A check-in and a fair next step keep the agreement alive." },
        ],
      },
    ],
  },
};

// ─── MASTERY (conceptual written answers) ─────────────────────────────────────

export const H4_MASTERY: Record<string, MasteryQuestion[]> = {
  "h4-mindsets": [
    { conceptTitle: "Three Ways to Handle a Problem", source: "LiveLife Habit 4 brief, short answer 9", question: "Your friend wants to stay indoors and you want to go outside. Write one Win-Win option and say what each of you needs.", kind: "conceptual", keywords: ["both", "fair"], solution: "Model answer: 'I need fresh air and my friend wants to relax. We could play a board game for half an hour and then go outside for a walk.' A strong answer names both needs and gives an option that is workable." },
    { conceptTitle: "Three Ways to Handle a Problem", source: "LiveLife Habit 4 brief", question: "In your own words, explain the difference between Lose-Win and Win-Lose.", kind: "conceptual", keywords: ["give", "way"], solution: "Lose-Win: you give up what matters to you so the other person gets everything. Win-Lose: you get your way at the other person's expense." },
    { conceptTitle: "Courage and Consideration", source: "LiveLife Habit 4 brief", question: "What two things does Think Win-Win need? Say what each one means.", kind: "conceptual", keywords: ["courage", "consideration"], solution: "Courage is standing up for what you need or believe. Consideration is caring about what the other person needs and believes." },
  ],
  "h4-promises": [
    { conceptTitle: "The Emotional Bank Account", source: "LiveLife Habit 4 brief", question: "What is the Emotional Bank Account, and why is keeping a promise a deposit?", kind: "conceptual", keywords: ["trust", "deposit"], solution: "It is a metaphor for how much trust there is in a relationship. Keeping a promise builds trust, so it is like adding to the account." },
    { conceptTitle: "A Promise You Can Keep", source: "LiveLife Habit 4 brief", question: "Write one realistic promise you could keep this week. Include the action and the time.", kind: "conceptual", keywords: ["will"], solution: "Example: 'I will put my school bag by the door every night this week.' It is specific, realistic and has a time." },
    { conceptTitle: "A Promise You Can Keep", source: "LiveLife Habit 4 brief (Application D)", question: "You cannot arrive at the time you promised. What could you say or do to protect trust?", kind: "conceptual", keywords: ["sorry", "plan"], solution: "Tell them early and honestly, say sorry, and agree on a new time or plan." },
  ],
  "h4-agreements": [
    { conceptTitle: "The Five Parts of a Win-Win Agreement", source: "LiveLife Habit 4 brief", question: "Name the five parts of a Win-Win Agreement.", kind: "conceptual", keywords: ["results", "guidelines", "resources", "accountability", "consequences"], solution: "Desired Results, Guidelines, Resources, Accountability and Consequences." },
    { conceptTitle: "The Five Parts of a Win-Win Agreement", source: "LiveLife Habit 4 brief, short answer 10", question: "Give one fair guideline and one way to check (accountability) for a shared activity.", kind: "conceptual", keywords: ["check"], solution: "Guideline example: take turns for 30 minutes with a timer. Accountability example: both of us tick off the turns each evening." },
    { conceptTitle: "Interdependent Living", source: "LiveLife Habit 4 brief (Application B)", question: "Sam and Joseph share a game console. Fill in a Win-Win Agreement with all five parts.", kind: "conceptual", keywords: ["turns", "check"], solution: "Results: fair turns, less fighting. Guidelines: 30-minute turns, timer. Resources: console, timer, written schedule. Accountability: tick off turns daily. Consequences: pause, talk and restore the missed turn." },
  ],
};

// ─── SPOT IT (multiple choice, from the brief's MCQ bank) ─────────────────────

export const H4_IDENTIFY: Record<string, IdentifyQuestion[]> = {
  "h4-mindsets": [
    { conceptTitle: "Three Ways to Handle a Problem", emoji: "🤝", scenario: "A class is learning about Habit 4.", prompt: "Which is the best description of Think Win-Win?", options: ["Getting my way", "Always giving up", "Considering what matters to both people", "Avoiding every disagreement"], correct: [2], explanation: "Win-Win considers both needs. It is not giving in and it is not avoiding conflict." },
    { conceptTitle: "Three Ways to Handle a Problem", emoji: "😔", scenario: "A learner agrees to a plan they dislike so the other person gets everything.", prompt: "Which pattern is this closest to?", options: ["Lose-Win", "Win-Lose", "Win-Win", "Synergy"], correct: [0], explanation: "Giving up your own need so the other person wins looks like Lose-Win." },
    { conceptTitle: "Three Ways to Handle a Problem", emoji: "🙅", scenario: "A child insists on their own choice and refuses to consider their friend's idea.", prompt: "Which pattern is this closest to?", options: ["Lose-Win", "Win-Lose", "Win-Win", "Accountability"], correct: [1], explanation: "A one-sided win at the other person's expense is Win-Lose." },
    { conceptTitle: "Courage and Consideration", emoji: "👂", scenario: "Two friends disagree about what to play.", prompt: "What is a useful first step?", options: ["Decide who is right", "Understand each person's needs", "Tell them to stop", "Promise anything"], correct: [1], explanation: "Listen and find out what each person needs before choosing a plan." },
  ],
  "h4-promises": [
    { conceptTitle: "A Promise You Can Keep", emoji: "🎒", scenario: "You want to make a promise to a family member.", prompt: "Which promise is the most realistic?", options: ["I will never make mistakes", "I will do all the chores forever", "I will put my bag by the door tonight", "I will make everyone happy"], correct: [2], explanation: "It is specific, controllable and has a time." },
    { conceptTitle: "The Emotional Bank Account", emoji: "🏦", scenario: "In the Emotional Bank Account metaphor, people talk about deposits and withdrawals.", prompt: "Keeping a promise is...", options: ["A deposit", "A punishment", "A competition", "A payment"], correct: [0], explanation: "Consistent actions like keeping promises can build trust, so they act like deposits." },
    { conceptTitle: "A Promise You Can Keep", emoji: "⏰", scenario: "You told a friend you would meet at 4 pm but you will be late.", prompt: "What helps trust most?", options: ["Say nothing and hope they do not notice", "Tell them early, say sorry and agree on a new time", "Blame the traffic", "Cancel without saying why"], correct: [1], explanation: "Early honesty, an apology and a new plan protect trust." },
  ],
  "h4-agreements": [
    { conceptTitle: "The Five Parts of a Win-Win Agreement", emoji: "📋", scenario: "A teacher lists parts of a Win-Win Agreement.", prompt: "Which one is NOT a part?", options: ["Desired Results", "Guidelines", "Resources", "Popularity"], correct: [3], explanation: "The five parts are Desired Results, Guidelines, Resources, Accountability and Consequences." },
    { conceptTitle: "The Five Parts of a Win-Win Agreement", emoji: "📅", scenario: "An agreement says: 'We check the schedule every Friday.'", prompt: "Which part is that?", options: ["Desired Results", "Guidelines", "Accountability", "Resources"], correct: [2], explanation: "Accountability defines how follow-through is checked." },
    { conceptTitle: "Interdependent Living", emoji: "🎮", scenario: "Sam and Joseph share a game console. They write: 'We alternate 30-minute turns with a timer.'", prompt: "Which part is that?", options: ["Guidelines", "Consequences", "Accountability", "Desired Results"], correct: [0], explanation: "It is a rule for how they will play, which makes it a guideline." },
  ],
};

// ─── RETENTION (revision cards and reflection) ────────────────────────────────

export const H4_RETENTION: Record<string, RetentionSeed> = {
  "h4-mindsets": {
    cards: [
      { question: "What is Think Win-Win?", answer: "An attitude toward life: when there is a conflict, look for a solution that considers what matters to both people.", imageConcept: "Two children shaking hands over a shared game, Pixar style", imageUrl: "" },
      { question: "What are the three patterns for handling a problem?", answer: "Lose-Win (I give up), Win-Lose (I get my way at the other person's expense) and Win-Win (we consider both needs).", imageConcept: "Three small scenes showing giving in, insisting and sharing, Pixar style", imageUrl: "" },
      { question: "What two things does Win-Win need?", answer: "Courage to say what you need, and consideration for what the other person needs.", imageConcept: "Two pillars labelled with a speech bubble and an ear, Pixar style", imageUrl: "" },
      { question: "What does the Win-Win test ask?", answer: "Did we both feel heard? Are both needs considered? Is it fair? Can we do it? Do we both freely agree?", imageConcept: "A checklist with five ticks held by two children, Pixar style", imageUrl: "" },
      { question: "Reflection: think of a low-stakes disagreement. What did you want? What might the other person want? What option considers both?", answer: "Write the situation, your need, their possible need, two options, the plan you choose and why it is fair.", imageConcept: "A child writing in a journal with a friend beside them, Pixar style", imageUrl: "" },
    ],
    summary: { imageConcept: "Study-guide infographic for Think Win-Win: three patterns, courage and consideration, the Win-Win test", imageUrl: "" },
  },
  "h4-promises": {
    cards: [
      { question: "What is a promise?", answer: "A statement or action that tells someone you will definitely do something.", imageConcept: "A child nodding and shaking hands with a friend, Pixar style", imageUrl: "" },
      { question: "What is the Emotional Bank Account?", answer: "A metaphor for the amount of trust in a relationship. Deposits build trust, withdrawals break it. It is not a literal score.", imageConcept: "A piggy bank filling with hearts, Pixar style", imageUrl: "" },
      { question: "What makes a promise easy to keep?", answer: "It is specific, realistic and has a time.", imageConcept: "A sticky note with a clock and a tick, Pixar style", imageUrl: "" },
      { question: "What should you do if you cannot keep a promise?", answer: "Be honest early, say sorry and make a new plan.", imageConcept: "Two friends talking calmly about changing plans, Pixar style", imageUrl: "" },
      { question: "Reflection: write one promise to yourself and one to someone else. When will you do it? What might get in the way?", answer: "Promise, action and time, support you need, a check-in, and a backup plan.", imageConcept: "A child with two sticky notes on a mirror, Pixar style", imageUrl: "" },
    ],
    summary: { imageConcept: "Study-guide infographic for Promises and Trust: promise, deposits and withdrawals, new plan", imageUrl: "" },
  },
  "h4-agreements": {
    cards: [
      { question: "What is a Win-Win Agreement?", answer: "When two or more people commit to work together for the benefit of both. It can be made in almost any relationship.", imageConcept: "Two people shaking hands over a written plan, Pixar style", imageUrl: "" },
      { question: "Name the five parts.", answer: "Desired Results, Guidelines, Resources, Accountability, Consequences.", imageConcept: "Five colourful tiles with icons, Pixar style", imageUrl: "" },
      { question: "What is Accountability in an agreement?", answer: "How you will check that the plan is being followed, for example a weekly check.", imageConcept: "A calendar with ticks, Pixar style", imageUrl: "" },
      { question: "What makes a good consequence?", answer: "A fair, related next step such as pausing, talking and restoring a missed turn. It is never humiliating or harmful.", imageConcept: "Two children talking calmly about a missed turn, Pixar style", imageUrl: "" },
      { question: "Reflection: after trying an agreement, was it clear? Did both agree? Did we follow it? What should change?", answer: "Result, what worked, what to adjust and the next check date.", imageConcept: "Two children reviewing their plan together, Pixar style", imageUrl: "" },
    ],
    summary: { imageConcept: "Study-guide infographic for Win-Win Agreements: the five parts and a sample", imageUrl: "" },
  },
};

// ─── PICTURES ─────────────────────────────────────────────────────────────────
// Pixar-style 3D pictures (gpt-image-2, low quality), one per card, in public/learn-seeds/.
// File names: h4-<s1|s2|s3>-<think|concept|flash>-<n>.webp, n counts from 1 in card order.
// Applied here onto the cards above so no other seed file needs to know about them.
// Each section's summary is a study-guide infographic (h4-<s>-clay-1.webp, a claydough-style quick study guide like the classroom's summary.png), so the Retention screen never shows a
// "Generate" button, which would call a paid server route that needs a login.
const H4_SHORT: Record<string, string> = { "h4-mindsets": "s1", "h4-promises": "s2", "h4-agreements": "s3" };
const h4img = (id: string, kind: "think" | "concept" | "flash" | "clay", n: number) => `/learn-seeds/h4-${H4_SHORT[id]}-${kind}-${n}.webp${kind === "clay" ? "?v=2" : ""}`;

for (const id of H4_SECTION_IDS) {
  H4_THINK[id].forEach((card, i) => { card.imageUrl = h4img(id, "think", i + 1); });
  H4_CONCEPT[id].cards.forEach((card, i) => { card.imageUrl = h4img(id, "concept", i + 1); });
  H4_RETENTION[id].cards.forEach((card, i) => { card.imageUrl = h4img(id, "flash", i + 1); });
  H4_RETENTION[id].summary.imageUrl = h4img(id, "clay", 1);
}

// ─── THE CHAPTER ──────────────────────────────────────────────────────────────
// Habit 4 has its own page at /livelife/habit-4 (app/livelife/habit-4).
export const H4_CHAPTER: LearnChapter = {
  id: "habit-4-think-win-win",
  title: "Habit 4: Think Win-Win",
  subject: "Life Skills",
  gradeLevel: "Leader in Me · Level 5",
  emoji: "🤝",
  gradient: "135deg, #D97706 0%, #DC2626 100%",
  sections: [
    {
      id: "h4-mindsets",
      title: "Think Win-Win",
      description: "Three ways to handle a problem, and how to find a solution for both",
      topic: "Habit 4 Think Win-Win in the Leader in Me Level 5 workbook: Lose-Win, Win-Lose and Win-Win, courage and consideration, finding a win-win option in everyday scenarios",
      emoji: "🤝",
      thinkCards: H4_THINK["h4-mindsets"],
    },
    {
      id: "h4-promises",
      title: "Promises and Trust",
      description: "The Emotional Bank Account and keeping promises to yourself and others",
      topic: "Habit 4 Think Win-Win in the Leader in Me Level 5 workbook: what a promise is, the Emotional Bank Account metaphor, keeping promises to yourself and others, accountability partner",
      emoji: "🏦",
      thinkCards: H4_THINK["h4-promises"],
    },
    {
      id: "h4-agreements",
      title: "Win-Win Agreements",
      description: "Interdependent living and the five parts of an agreement",
      topic: "Habit 4 Think Win-Win in the Leader in Me Level 5 workbook: interdependent living, the Win-Win Agreement with its five parts (Desired Results, Guidelines, Resources, Accountability, Consequences), Luis and Sam and Joseph examples",
      emoji: "📋",
      thinkCards: H4_THINK["h4-agreements"],
    },
  ],
};

// ─── CONCEPTUAL SCREENS (story first, like the classroom's guided explainers) ─────────────────────────────
// Used only by app/livelife/habit-4/ConceptualView.tsx. Each screen: a coloured badge, a bold headline (the word
// between *stars* is highlighted), a large picture, then a short story paragraph. Wording is ORIGINAL and
// illustrative, drawn from the brief; FOR SME REVIEW.

export interface H4StoryScreen { title: string; kicker: string; headline: string; picture: string; body: string }
export interface H4Sort { prompt: string; categories: string[]; items: { text: string; answer: string }[] }

const pic = (id: string, kind: "think" | "concept", n: number) => `/learn-seeds/h4-${H4_SHORT[id]}-${kind}-${n}.webp`;

export const H4_STORY: Record<string, H4StoryScreen[]> = {
  "h4-mindsets": [
    { title: "A problem", kicker: "A problem at break time", headline: "One ball. Two groups. *What now?*", picture: pic("h4-mindsets", "think", 1),
      body: "You and a friend are playing with a ball. Some students from another class walk over and want it too. You could shout, give in, or try something different. Each choice leaves everyone feeling a different way." },
    { title: "Three patterns", kicker: "Three ways to respond", headline: "Lose-Win, Win-Lose or *Win-Win*", picture: pic("h4-mindsets", "concept", 1),
      body: "Lose-Win: you give in, and you may feel like a doormat. Win-Lose: you get your way, but the friendship can pay for it. Win-Win: you look for a plan that considers what matters to both people. These are patterns, not labels for a person." },
    { title: "Same moment", kicker: "Same moment, three mindsets", headline: "Only the *mindset* changes", picture: pic("h4-mindsets", "concept", 3),
      body: "Picture the playground again: two kids rush for the same ball. With Lose-Win, I drop what matters to me so my friend is happy. With Win-Lose, I get my way at my friend's expense. In both, someone is ignored. With Win-Win, I stand up for what matters to me and I also consider what matters to my friend, so both stay high." },
    { title: "Courage and consideration", kicker: "What Win-Win needs", headline: "*Courage* and consideration", picture: pic("h4-mindsets", "concept", 2),
      body: "Courage is saying what you need, calmly. Consideration is listening to what the other person needs. When both are there, you can find an option that fits in the overlap, like inviting the other class into a bigger game." },
    { title: "The test", kicker: "Is it really Win-Win?", headline: "Ask five *quick questions*", picture: "/learn-seeds/h4-s1-flash-4.webp",
      body: "Did we both feel heard? Are both needs considered? Is it fair? Can we really do it? Do we both freely agree? Win-Win does not mean both get their first choice. It means a fair plan that both accept." },
    { title: "Movie or park", kicker: "Real-life challenge", headline: "Maya wants the *movie*. Arjun wants the park.", picture: pic("h4-mindsets", "think", 2),
      body: "Both are your friends, and they both want a fun day together. Help them talk: ask what each one enjoys, list a few options, and check that the plan is fair and that both agree. Park today and movie next time could work, or they could find something they both enjoy." },
  ],
  "h4-promises": [
    { title: "Trust", kicker: "Trust grows and shrinks", headline: "The *Emotional Bank Account*", picture: pic("h4-promises", "concept", 1),
      body: "Think of trust in a friendship like a bank account. Kind acts, listening and kept promises are deposits. Broken promises and ignoring someone are withdrawals. It is a way of thinking about trust, not a score anyone keeps." },
    { title: "A promise", kicker: "What is a promise?", headline: "A promise says you *will* do it", picture: pic("h4-promises", "think", 1),
      body: "A promise is a statement or an action, even a nod, that tells someone you will definitely do something. When you nod at a friend who asks you to bring a book, you have made a promise." },
    { title: "Keepable", kicker: "Make it one you can keep", headline: "*Specific*, realistic and on time", picture: pic("h4-promises", "concept", 2),
      body: "\"I will help with everything forever\" is too big. \"I will put my bag by the door tonight\" is specific, realistic and has a time. Promises to yourself work the same way, and keeping them builds self-trust." },
    { title: "When plans change", kicker: "When plans change", headline: "Be honest *early*", picture: pic("h4-promises", "think", 3),
      body: "Sometimes you cannot keep a promise. Tell the person early, say sorry, and make a new plan: \"I can't finish today. Could I return it tomorrow?\" That protects trust." },
    { title: "Leo's book", kicker: "A promise gets tough", headline: "Leo can't finish the *book* in time", picture: pic("h4-promises", "concept", 3),
      body: "Leo promised to return a book today, but he cannot finish reading it. If he hides it or waits until the deadline passes, trust suffers. The responsible move is to speak up early: say sorry, explain, and agree a new day. Speaking up before the problem grows keeps the friendship strong." },
  ],
  "h4-agreements": [
    { title: "Together", kicker: "Working together", headline: "Two people, *one plan*", picture: pic("h4-agreements", "think", 1),
      body: "A Win-Win Agreement is when two or more people commit to work together for the benefit of both. Luis wants a phone. His parents want him to read more. Their agreement links both wishes." },
    { title: "Five parts", kicker: "Five parts", headline: "A plan has *five parts*", picture: pic("h4-agreements", "concept", 2),
      body: "Desired Results: what we both want. Guidelines: the rules. Resources: what we need. Accountability: how we check. Consequences: a fair next step if the plan is not followed." },
    { title: "Try it", kicker: "Try it", headline: "Sam and Joseph share a *console*", picture: pic("h4-agreements", "think", 2),
      body: "Sam wants to play Joseph's games, but the games get damaged and the cousins keep fighting. An example plan: fair 30-minute turns, a timer, a written schedule, a tick-off each evening, and a talk if a turn is missed." },
    { title: "Mia and Leo", kicker: "Your turn to apply it", headline: "Blocks or board game? *Both* speak up", picture: pic("h4-agreements", "concept", 3),
      body: "Mia wants to build with blocks. Leo wants to play a board game. If one wins and the other loses, the friendship feels shaky. When both speak up, both listen and both explore options, they can plan something fair, such as blocks first and then the game. Win-Win is never about defeating someone, and it is not about always giving in." },
    { title: "Keep it alive", kicker: "Keep it alive", headline: "An agreement can *change*", picture: pic("h4-agreements", "concept", 1),
      body: "If the plan is not working, sit down together and adjust it. Consequences should be fair and related, never humiliating. A good agreement is clear, fair and freely accepted by everyone." },
  ],
};

export const H4_SORT: Record<string, H4Sort> = {
  "h4-mindsets": {
    prompt: "Which pattern is each situation? Tap one.",
    categories: ["Lose-Win", "Win-Lose", "Win-Win"],
    items: [
      { text: "I hand over the ball even though I want to play, so there is no fight.", answer: "Lose-Win" },
      { text: "I keep the ball and tell the others to go away.", answer: "Win-Lose" },
      { text: "We invite them to join and make two teams.", answer: "Win-Win" },
      { text: "We choose the park today and the movie next time, and both agree.", answer: "Win-Win" },
      { text: "I keep pushing until my friend gives in.", answer: "Win-Lose" },
    ],
  },
  "h4-promises": {
    prompt: "Is each one a deposit or a withdrawal? Tap one.",
    categories: ["Deposit", "Withdrawal"],
    items: [
      { text: "Returning a book on the day you said you would.", answer: "Deposit" },
      { text: "Saying \"I'll come\" and not showing up, with no message.", answer: "Withdrawal" },
      { text: "Telling a friend early that you will be late.", answer: "Deposit" },
      { text: "Ignoring a friend who is talking to you.", answer: "Withdrawal" },
      { text: "Listening without interrupting.", answer: "Deposit" },
    ],
  },
  "h4-agreements": {
    prompt: "Which part of the agreement is each line? Tap one.",
    categories: ["Desired Results", "Guidelines", "Resources", "Accountability", "Consequences"],
    items: [
      { text: "Both get fair turns and enjoy playing.", answer: "Desired Results" },
      { text: "Alternate 30-minute turns.", answer: "Guidelines" },
      { text: "A console, a controller and a timer.", answer: "Resources" },
      { text: "Tick off the turns every evening.", answer: "Accountability" },
      { text: "Pause, talk and restore the missed turn.", answer: "Consequences" },
    ],
  },
};
