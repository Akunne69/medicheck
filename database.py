_RECORDS = []

def init_db():
    pass

def save_assessment(patient, symptoms, result, cycle_info=None):
    _RECORDS.append({"patient": patient, "symptoms": symptoms, "result": result})
    return len(_RECORDS)

def find_patient(name_or_phone):
    return []

def get_stats():
    return {"total_assessments": 0, "common_symptoms": [], "common_conditions": [], "ages": [], "urgency_counts": {}}