"""The subject layer. To add a chapter, create a package here that builds a ChapterPack, and register it below."""


def all_packs():
    from .habit4 import PACK as HABIT4
    from .probability import PACK as PROBABILITY
    return {"habit4": HABIT4, "probability": PROBABILITY}
