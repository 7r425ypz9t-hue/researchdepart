"""سلم الإصدارات المبسط والمطابق لـ SemVer."""
LADDER = {"v0.1": "Draft", "v0.5": "Reviewed", "v0.8": "Edited", "v0.9": "Approved", "v1.0": "Published"}
SEMVER = {"v0.1": "0.1.0", "v0.5": "0.5.0", "v0.8": "0.8.0", "v0.9": "0.9.0", "v1.0": "1.0.0"}
HUMAN_ONLY = {"v0.9", "v1.0"}


def next_version(current: str) -> str:
    keys = list(LADDER)
    i = keys.index(current)
    if i == len(keys) - 1:
        raise ValueError("already published; next edition starts a new project (re_edition)")
    return keys[i + 1]


def can_bump(current: str, actor: str) -> bool:
    return next_version(current) not in HUMAN_ONLY or actor == "HUMAN-AUTHOR"
