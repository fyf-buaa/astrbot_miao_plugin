from __future__ import annotations


def reaction_bonus(mastery: float) -> dict[str, float]:
    if mastery <= 0:
        return {"amplify": 0.0, "shatter": 0.0, "catalyze": 0.0}
    amplify = 2.78 * mastery / (mastery + 1400) * 100
    shatter = 4.44 * mastery / (mastery + 1400) * 100
    catalyze = 5.0 * mastery / (mastery + 1200) * 100
    return {"amplify": amplify, "shatter": shatter, "catalyze": catalyze}
