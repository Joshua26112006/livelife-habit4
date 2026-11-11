"""CBSE Class 10 Probability: the first chapter pack and the worked example of the ChapterPack contract."""
from dataclasses import replace

from ...pack import ChapterPack
from .catalogue import CATALOGUE, PROBES, SEPARATING_PROBES, TEACHING_ORDER, needs_expert_draft
from .knowledge_base import COMPETENCIES, INTERVENTION_MAP, INTERVENTIONS, MISCONCEPTION_COMPETENCIES, VERSION
from .parallel import parallel_item
from .reader import read_answer
from .samples import sample, short_sample
from .templates import SHORT_TEST, TEST

PACK = ChapterPack(
    chapter_id="cbse-10-maths-probability",
    version=VERSION,
    competencies=COMPETENCIES,
    items=TEST,
    misconceptions={code: {**entry, "competency_ids": MISCONCEPTION_COMPETENCIES[code]} for code, entry in CATALOGUE.items()},
    teaching_order=TEACHING_ORDER,
    probes=PROBES,
    separating_probes=SEPARATING_PROBES,
    interventions=INTERVENTIONS,
    intervention_map=INTERVENTION_MAP,
    read_answer=read_answer,
    parallel_item=parallel_item,
    sample=sample,
    subject={"subject": "Mathematics", "board": "CBSE", "grade": "Class 10", "chapter": "Probability", "source": "NCERT Chapter 14, Reprint 2026-27"},
    brief=("CBSE Class 10 Mathematics, NCERT Chapter 14 Probability (theoretical probability only: P(E) = favourable / total for equally likely outcomes, complements, "
           "coins, dice and cards). Stay within this chapter and use its language; do not introduce permutations, conditional probability or other later topics."),
    upload_hint="T1 to T10: the student's full working as written, for example: total = 10, not green = 4, P = 4/10.",
    extension_task="NCERT reasoning items: Exercise 14.1 Q22 and Q25. Explain each answer in writing.",
)

SHORT_PACK = replace(
    PACK,
    chapter_id="cbse-10-maths-probability-short",
    items=SHORT_TEST,
    sample=short_sample,
    subject={**PACK.subject, "chapter": "Probability, 3-question check"},
    upload_hint="Q1 to Q3: the student's full working as written, for example: 4 kings out of 52 cards, P = 4/52 = 1/13.",
)

__all__ = ["PACK", "SHORT_PACK", "needs_expert_draft"]
