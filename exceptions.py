"""Custom exceptions and logging setup.
OWNER: Raihanatu Idris (branch: feature/urgency-guidance)
"""
import logging
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")


class MediCheckError(Exception):
    """Base class for all MediCheck errors (safe to show to the user)."""


class InvalidInputError(MediCheckError):
    """A form field contains invalid data."""


class InvalidNameError(InvalidInputError):
    pass


class InvalidAgeError(InvalidInputError):
    pass


class InvalidPhoneError(InvalidInputError):
    pass


class InvalidDateError(InvalidInputError):
    pass


class APIConnectionError(MediCheckError):
    """The Gemini API could not be reached or returned an error."""


class DataFileError(MediCheckError):
    """A data file (JSON/CSV/config) is missing or corrupt."""


class DatabaseError(MediCheckError):
    """A database operation failed."""


def setup_logging():
    """Send errors to data/medicheck.log (file handling)."""
    os.makedirs(DATA_DIR, exist_ok=True)
    logging.basicConfig(
        filename=os.path.join(DATA_DIR, "medicheck.log"),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )