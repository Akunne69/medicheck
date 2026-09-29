"""Menstrual cycle helper (optional, informational only).

OWNER: Raihanatu Idris
BRANCH: feature/urgency-guidance

This helper does not diagnose reproductive conditions.
It estimates cycle day and phase from a last-period date and
can provide a short informational note about reported symptoms.

Contract:
    estimate(last_period_date, cycle_length=28, today=None) -> dict or None
    note_for(symptoms, cycle_info) -> str
"""

from datetime import date, timedelta


_PHASE_FRACTIONS = [
    (0.00, 0.18, "menstrual"),
    (0.18, 0.46, "follicular"),
    (0.46, 0.57, "ovulation"),
    (0.57, 1.00, "luteal"),
]


PMS_SYMPTOMS = {
    "cramps",
    "bloating",
    "mood swings",
    "breast tenderness",
    "fatigue",
}


def _phase_for_day(day_in_cycle, cycle_length):
    """Return the estimated phase for a given cycle day."""

    # Cycle Day 1 corresponds to position 0.0 in the cycle.
    fraction = (day_in_cycle - 1) / cycle_length

    for start, end, name in _PHASE_FRACTIONS:
        if start <= fraction < end:
            return name

    return "luteal"


def estimate(last_period_date, cycle_length=28, today=None):
    """
    Return estimated cycle information.

    The first day of the period is Cycle Day 1.

    Returns None if:
    - no period date is supplied
    - the supplied period date is in the future
    """

    if last_period_date is None:
        return None

    cycle_length = cycle_length or 28
    today = today or date.today()

    days_since = (today - last_period_date).days

    # Future dates are treated as invalid/not provided.
    if days_since < 0:
        return None

    is_late = days_since > cycle_length + 3

    if is_late:
        day_in_cycle = cycle_length
        phase = "late / cycle overdue"
    else:
        # Period start = Cycle Day 1
        day_in_cycle = (days_since % cycle_length) + 1
        phase = _phase_for_day(day_in_cycle, cycle_length)

    return {
        "days_since_last_period": days_since,
        "day_of_cycle": day_in_cycle,
        "phase": phase,
        "next_predicted": last_period_date + timedelta(days=cycle_length),
        "is_late": is_late,
    }


def note_for(symptoms, cycle_info):
    """
    Return a short informational note when relevant.

    Returns an empty string when there is nothing relevant to mention.
    """

    if not cycle_info:
        return ""

    symptoms = set(symptoms or [])

    if cycle_info["is_late"] and "missed period" not in symptoms:
        return (
            "Your period appears later than expected based on your usual "
            "cycle length. If it is significantly delayed, consider seeing a doctor."
        )

    if (
        cycle_info["phase"] in ("luteal", "menstrual")
        and PMS_SYMPTOMS & symptoms
    ):
        return "These symptoms are common in the days around a period."

    return ""
