"""Urgency rules and self-care guidance.
OWNER: Raihanatu Idris (branch: feature/urgency-guidance)

Contract: assess(symptoms, matches) -> (level, message)
    level = "GREEN" | "YELLOW" | "RED"

guidance_for(condition) -> general self-care text for the top matched condition.

Never prescribes medication or dosages.
"""

from conditions import GUIDANCE, RED_FLAGS


STRONG_MATCH_THRESHOLD = 60   # percent
LONG_DURATION_DAYS = 3
MAX_SEVERITY = 3


MESSAGES = {
    "RED": "Urgent: seek medical attention promptly.",
    "YELLOW": "Moderate: consider seeing a healthcare professional.",
    "GREEN": "Mild: monitor and seek routine care if needed.",
}


def assess(symptoms, matches):
    """Decide the urgency level.

    Red-flag symptoms always win, regardless of the match score.
    """

    if not symptoms:
        return "GREEN", MESSAGES["GREEN"]

    if RED_FLAGS & set(symptoms):
        return "RED", MESSAGES["RED"]

    worst_severity = max(
        severity for severity, _days in symptoms.values()
    )

    longest_duration = max(
        days for _severity, days in symptoms.values()
    )

    strong_match = (
        bool(matches)
        and matches[0][1] >= STRONG_MATCH_THRESHOLD
    )

    if (
        worst_severity >= MAX_SEVERITY
        or longest_duration > LONG_DURATION_DAYS
        or strong_match
    ):
        return "YELLOW", MESSAGES["YELLOW"]

    return "GREEN", MESSAGES["GREEN"]


def guidance_for(condition):
    """General self-care / when-to-seek-care text.

    condition may be None.
    """

    if condition is None:
        return (
            "No strong condition match was found. "
            "Monitor your symptoms and see a doctor "
            "if they continue or worsen."
        )

    return GUIDANCE.get(
        condition,
        "See a healthcare professional if symptoms continue or worsen."
    )