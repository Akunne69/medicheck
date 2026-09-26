import logging
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR,"data")

def setup_logging():
    os.makedirs(DATA_DIR, exist_ok=True)
    logging.basicConfig(
        filename=os.path.join(DATA_DIR, 'medicheck.log'),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

class MedicheckError(Exception):
    pass
class InvalidNameError(MedicheckError):
    pass
class InvalidAgeError(MedicheckError):
    pass
class InvalidPhoneError(MedicheckError):
    pass
class InvalidDateError(MedicheckError):
    pass
class APIConnectionError(MedicheckError):
    pass
class DatabaseError(MedicheckError):
    pass
class DataFileError(MedicheckError):
    pass