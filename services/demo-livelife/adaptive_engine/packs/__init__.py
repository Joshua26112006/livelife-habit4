"""The subject layer. A subject is a folder here with a pack.json (see adaptive_engine/loader.py); it is found automatically.
A subject whose answers can be computed exactly may also be a Python plugin, registered below.
"""
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def all_packs():
    from ..loader import load
    from .probability import PACK as PROBABILITY, SHORT_PACK
    packs = {"probability-short": SHORT_PACK, "probability": PROBABILITY}
    for path in sorted(Path(__file__).parent.glob("*/pack.json")):
        packs[path.parent.name] = load(path)
    return packs
