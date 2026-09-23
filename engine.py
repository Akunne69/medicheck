from conditions import CONDITIONS

def analyse(symptoms):
    return [("Malaria", 50, list(symptoms), 3)] if symptoms else []