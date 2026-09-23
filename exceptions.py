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