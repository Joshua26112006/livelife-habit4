"""The blank upload template for any pack's paper. Each pack supplies its own synthetic sample."""
from .bulk import ID_COLUMN, to_csv
from .reassessment import build_paper


def paper_columns(pack, round_name):
    items = pack.items if round_name == "v1" else build_paper(pack)
    return [ID_COLUMN] + [i["id"] for i in items], items


def template(pack, round_name):
    return to_csv(paper_columns(pack, round_name)[0], [])
