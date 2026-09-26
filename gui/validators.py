"""Input validation with regular expressions.
OWNER: Nodunachukwu Akunne (branch: feature/gui-registration)
Each function returns the cleaned value or raises a custom exception (exception handling).
"""
import re
from datetime import date, datetime

from exceptions import InvalidAgeError, InvalidDateError, InvalidNameError, InvalidPhoneError

NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z\s'\-]{1,49}$")
# Nigerian numbers: 08031234567 or +2348031234567
PHONE_PATTERN = re.compile(r"^(\+234|0)[789][01]\d{8}$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_name(raw):
    name = " ".join(raw.split())
    if not NAME_PATTERN.match(name):
        raise InvalidNameError("Name must be 2 to 50 letters (spaces, hyphens and apostrophes allowed).")
    return name


def validate_age(raw):
    try:
        age = int(raw.strip())
    except ValueError:
        raise InvalidAgeError("Age must be a whole number.") from None
    if not 0 <= age <= 120:
        raise InvalidAgeError("Age must be between 0 and 120.")
    return age


def validate_phone(raw):
    phone = re.sub(r"[\s\-]", "", raw)
    if not PHONE_PATTERN.match(phone):
        raise InvalidPhoneError("Enter a valid number, e.g. 08031234567 or +2348031234567.")
    return phone


def validate_optional_date(raw):
    """Used for the last-period date. Empty is fine (feature is optional). Returns a date or None."""
    raw = raw.strip()
    if not raw:
        return None
    if not DATE_PATTERN.match(raw):
        raise InvalidDateError("Use the format YYYY-MM-DD, e.g. 2026-09-01.")
    try:
        parsed = datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        raise InvalidDateError("That date does not exist. Use the format YYYY-MM-DD.") from None
    if parsed > date.today():
        raise InvalidDateError("The date cannot be in the future.")
    return parsed


def validate_cycle_length(raw):
    """Optional; defaults to 28 if left blank."""
    raw = raw.strip()
    if not raw:
        return 28
    try:
        length = int(raw)
    except ValueError:
        raise InvalidAgeError("Cycle length must be a whole number of days.") from None
    if not 15 <= length <= 45:
        raise InvalidAgeError("Cycle length should be between 15 and 45 days.")
    return length