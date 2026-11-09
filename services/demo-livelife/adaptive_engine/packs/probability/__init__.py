"""CBSE Class 10 Probability: the first chapter pack and the worked example of the ChapterPack contract."""
from ...pack import ChapterPack
from .catalogue import CATALOGUE, PROBES, SEPARATING_PROBES, TEACHING_ORDER, needs_expert_draft
from .knowledge_base import COMPETENCIES, INTERVENTION_MAP, INTERVENTIONS, MISCONCEPTION_COMPETENCIES, VERSION
from .parallel import parallel_item
from .reader import read_answer
from .templates import TEST

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
)

__all__ = ["PACK", "needs_expert_draft"]
