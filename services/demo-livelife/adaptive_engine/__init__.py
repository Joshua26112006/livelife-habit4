"""Adaptive Teaching Engine: Modules 3 to 8 of the eight-step loop (Modules 1 and 2 hand over a ChapterPack).

  3 identification   evidence-linked misconception hypotheses, confidence, probes
  4 interventions    curated, ranked intervention retrieval; printable cards
  5 clustering       temporary groups by need; who owns each fix
  6 orchestration    a feasible, period-by-period teaching plan
  7 reassessment     parallel items and an explicit reading of the result
  8 profile          append-only evidence, competency status, next action
  cycle              one class through all of them, with teacher controls and an audit trail

Deterministic rules throughout. OCR, rubric scoring of open reasons, and generated materials are not built yet. Thresholds are
proposals to calibrate against teacher marking.
"""
from .clustering import diagnose_class
from .cycle import ClassCycle
from .identification import diagnose_student
from .pack import ChapterPack


def analyse_sheets(pack, sheets):
    """Module 3 and the class view, for callers that need no teacher workflow."""
    students = [diagnose_student(pack, sheet) for sheet in sheets]
    return {"students": students, "class": diagnose_class(pack, students)}


__all__ = ["ChapterPack", "ClassCycle", "analyse_sheets"]
