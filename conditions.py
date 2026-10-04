import json
import os
from exceptions import DataFileError
 
_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "conditions.json")
 
def _load():
    try:
        with open(_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as err:
        raise DataFileError(f"Could not read condition data: {err}") from err
 
_data = _load()
SYMPTOMS = _data["symptoms"]
RED_FLAGS = set(_data["red_flags"])
CONDITIONS = _data["conditions"]
GUIDANCE = _data["guidance"]