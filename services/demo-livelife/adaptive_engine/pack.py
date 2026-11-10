"""The contract between Modules 1-2 (curriculum map, diagnostic) and Modules 3-8.

Everything chapter-specific arrives in a ChapterPack, so Modules 3-8 hold no subject knowledge and a new chapter needs no
engine change. Field meanings follow the data model in section 7 of the concept document.

  competencies     {id: {name, prerequisites[]}}                                Module 1
  items            [{id, text, type, template, competency_ids[], correct}]      Module 2
  misconceptions   {code: {name, belief, kind (belief|slip|fact), competency_ids[], student, teacher, content, exit_check}}
  teaching_order   belief codes, earliest fixed first
  probes           {code: follow-up question}; separating_probes {frozenset(codes): question}
  interventions    {id: Intervention}; intervention_map {code: [intervention ids]}
  read_answer      optional plugin: (item, raw text) -> trace, for items with no "format"; otherwise the engine reads them (reading.py)
  parallel_item    optional plugin: (item, attempt) -> a parallel item; otherwise items carry a variant bank
  subject          {subject, board, grade, chapter, source}: shown to teachers
  brief            the subject and curriculum context given to every AI call for this pack
  upload_hint      how answers should be written in the bulk file
  sample           (pack, round) -> a synthetic CSV for trying the flow
"""
from dataclasses import dataclass, field
from typing import Callable, Dict, FrozenSet, List, Optional, Tuple

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
    read_answer: Optional[Callable[[dict, str], dict]] = None
    parallel_item: Optional[Callable[[dict, int], dict]] = None
    extension_task: str = ""
    subject: Dict[str, str] = field(default_factory=dict)
    brief: str = ""
    upload_hint: str = ""
    sample: Optional[Callable[["ChapterPack", str], str]] = None

    @property
    def slips(self):
        return tuple(code for code, entry in self.misconceptions.items() if entry["kind"] == "slip")

    @property
    def retest_items(self):
        """Items a V2 paper parallels: those with a variant bank, or computed by the plugin."""
        return [i for i in self.items if i.get("variants") or (self.parallel_item and not i.get("format"))]

    def read(self, item, raw):
        from . import reading
        return reading.read(item, raw) if item.get("format") else self.read_answer(item, raw)

    def parallel(self, item, attempt):
        from . import reading
        return self.parallel_item(item, attempt) if self.parallel_item and not item.get("format") else reading.parallel(self, item, attempt)

    def describe(self):
        """The subject map a teacher can inspect: what this pack knows and how much of it is expert-reviewed."""
        statuses = [e["review_status"] for e in self.interventions.values()]
        return {
            "chapter_id": self.chapter_id, "version": self.version, "subject": self.subject, "upload_hint": self.upload_hint,
            "competencies": self.competencies,
            "misconceptions": {c: {k: e[k] for k in ("name", "belief", "kind", "competency_ids")} for c, e in self.misconceptions.items()},
            "questions": [{"id": i["id"], "text": i["text"], "competency_ids": i["competency_ids"], "level": i.get("level"), "icon": i.get("icon"),
                           "answer": str(i.get("correct") or i.get("answer") or i.get("key") or "Reasoned answer")} for i in self.items],
            "interventions": {"total": len(statuses), "approved": statuses.count("approved")},
        }

    def item(self, item_id):
        return next(item for item in self.items if item["id"] == item_id)
