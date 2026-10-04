"""Regular-expression parser: turns typed text into structured symptoms.

OWNER: Elvis Jatau (branch: feature/analysis-engine)

Contract: extract_symptoms(text) -> {symptom: (severity 1-3, days)}
Used as the offline fallback when the Gemini API is unavailable, and to pre-fill
the free-text box on the symptom screen.
"""
import re

from conditions import SYMPTOMS

_DAYS_PATTERN = re.compile(r"(\d+)\s*(?:day|days)\b")
_WEEKS_PATTERN = re.compile(r"(\d+)\s*(?:week|weeks)\b")
_SEVERE_PATTERN = re.compile(r"\b(severe|terrible|very bad|intense|unbearable|excruciating)\b")
_MILD_PATTERN = re.compile(r"\b(mild|slight|little|minor)\b")
_NEGATION_PATTERN = re.compile(r"\b(no|not|without|never)\s+(\w[\w\s]{0,20}?)\b(?=[.,;]|$)")

# Common everyday phrasing mapped to the symptom names used in the condition data.
SYNONYMS = {
    "diarrhea": "diarrhoea",
    "stomach ache": "abdominal pain",
    "stomach pain": "abdominal pain",
    "tummy ache": "abdominal pain",
    "hot body": "fever",
    "high temperature": "fever",
    "temperature": "fever",
    "can't breathe": "difficulty breathing",
    "cant breathe": "difficulty breathing",
    "short of breath": "difficulty breathing",
    "tired": "fatigue",
    "exhausted": "fatigue",
    "throwing up": "vomiting",
    "runny tummy": "diarrhoea",
    "blocked nose": "nasal congestion",
    "stuffy nose": "nasal congestion",
}


def _normalise(text):
    text = text.lower()
    for phrase, symptom in SYNONYMS.items():
        text = text.replace(phrase, symptom)
    return text


def _find_duration_days(text):
    weeks = _WEEKS_PATTERN.search(text)
    if weeks:
        return int(weeks.group(1)) * 7
    days = _DAYS_PATTERN.search(text)
    if days:
        return int(days.group(1))
    return 1  # default: today


def _find_severity(text):
    if _SEVERE_PATTERN.search(text):
        return 3
    if _MILD_PATTERN.search(text):
        return 1
    return 2


def extract_symptoms(text):
    """Return every known symptom mentioned in free text, skipping negated ones
    ('no fever' should not count as fever)."""
    if not text or not text.strip():
        return {}
    normalised = _normalise(text)
    negated_phrases = {m.group(2).strip() for m in _NEGATION_PATTERN.finditer(normalised)}
    duration = _find_duration_days(normalised)
    severity = _find_severity(normalised)
    found = {}
    for symptom in SYMPTOMS:
        pattern = rf"\b{re.escape(symptom)}\b"
        if not re.search(pattern, normalised):
            continue
        if any(symptom in phrase for phrase in negated_phrases):
            continue
        found[symptom] = (severity, duration)
    return found
