from conditions import CONDITIONS


def analyse(symptoms):
    if not symptoms:
        return []
    results = []
    for condition, weights in CONDITIONS.items():
        matched = [s for s in symptoms if s in weights]
        if not matched:
            continue
        score = sum(weights[s] * symptoms[s][0] for s in matched)
        best_possible = sum(w * 3 for w in weights.values())
        percent = round(100 * score / best_possible)
        results.append((condition, percent, matched, len(weights)))
    results.sort(key=lambda r: r[1], reverse=True)
    return results


FOLLOW_UP_RULES = {
    "fever": "Have you travelled anywhere with malaria risk in the last month?",
    "cough": "Is the cough dry, or are you bringing up mucus?",
    "abdominal pain": "Is the pain in one spot, or spread across your stomach?",
}


def follow_up_questions(symptoms):
    questions = [FOLLOW_UP_RULES[s] for s in symptoms if s in FOLLOW_UP_RULES]
    return questions[:3]
