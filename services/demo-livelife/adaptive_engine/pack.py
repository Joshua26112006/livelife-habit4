"""The contract between Modules 1-2 (curriculum map, diagnostic) and Modules 3-8.

Everything chapter-specific arrives in a ChapterPack, so Modules 3-8 hold no subject knowledge and a new chapter needs no
engine change. Field meanings follow the data model in section 7 of the concept document.

  competencies     {id: {name, prerequisites[]}}                                Module 1
  items            [{id, text, type, template, competency_ids[], correct}]      Module 2
  misconceptions   {code: {name, belief, kind (belief|slip|fact), competency_ids[], student, teacher, content, exit_check}}
  teaching_order   belief codes, earliest fixed first
  probes           {code: follow-up question}; separating_probes {frozenset(codes): question}
  interventions    {id: Intervention}; intervention_map {code: [intervention ids]}
  read_answer      (item, raw text) -> trace {q, working, steps, findings[], result, shows_working}
  parallel_item    (item, attempt) -> a new item testing the same competency, with its own expected answer
"""
from dataclasses import dataclass
from typing import Callable, Dict, FrozenSet, List, Tuple

UNMAPPED = "UNMAPPED"

# What read_answer may report when there is nothing to judge.
NO_EVIDENCE_RESULTS = ("blank", "unreadable", "argument_unclear", "irrelevant", "flagged_for_review")


@dataclass(frozen=True)
class ChapterPack:
    chapter_id: str
    version: str
    competencies: Dict[str, dict]
    items: List[dict]
    misconceptions: Dict[str, dict]
    teaching_order: Tuple[str, ...]
    probes: Dict[str, str]
    separating_probes: Dict[FrozenSet[str], str]
    interventions: Dict[str, dict]
    intervention_map: Dict[str, List[str]]
    read_answer: Callable[[dict, str], dict]
    parallel_item: Callable[[dict, int], dict]

    @property
    def slips(self):
        return tuple(code for code, entry in self.misconceptions.items() if entry["kind"] == "slip")

    def item(self, item_id):
        return next(item for item in self.items if item["id"] == item_id)
