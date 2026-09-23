import json, os

_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "conditions.json")
_data = json.load(open(_PATH))
SYMPTOMS = _data["symptoms"]
RED_FLAGS = set(_data["red_flags"])
CONDITIONS = _data["conditions"]
GUIDANCE = _data["guidance"]