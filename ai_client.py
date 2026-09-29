"""Gemini API client: symptom extraction, plain-language explanation, follow-up questions.
OWNER: Abdullahi Ibrahim (branch: feature/ai-integration)

Design rules (see the project proposal, section 6.4):
  - The AI is a helper only. It never decides urgency and never replaces the rule-based engine.
  - Only symptoms are sent to the API. Names, phone numbers and other personal details never are.
  - Every call has a timeout and is wrapped in try/except. On any failure this module raises
    APIConnectionError, and the GUI falls back to the offline parser / plain guidance text.
  - The prompt explicitly forbids diagnosis, medication names and dosages.
  - The API key lives in config.json (git-ignored). config.example.json shows the format.
"""
import json
import os
import re

import requests

from exceptions import APIConnectionError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

# Google retires Gemini models regularly (gemini-2.0-flash was shut down on 1 June 2026).
# If the AI ever starts returning "not found" errors, add a "model" line to config.json
# with a current model name from https://ai.google.dev/gemini-api/docs/models - no code change needed.
DEFAULT_MODEL = "gemini-3.1-flash-lite"
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
TIMEOUT_SECONDS = 8

SAFETY_INSTRUCTION = (
    "You are a helpful assistant inside a student health-education project called MediCheck. "
    "You must NEVER diagnose a condition, NEVER name a medication, and NEVER give a dosage. "
    "Only describe symptoms in structured form or explain results in plain, general language."
)


def _get_api_key():
    if not os.path.exists(CONFIG_PATH):
        raise APIConnectionError(
            "No config.json found. Copy config.example.json to config.json and add your Gemini API key."
        )
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            config = json.load(f)
    except (OSError, json.JSONDecodeError) as err:
        raise APIConnectionError(f"config.json could not be read: {err}") from err
    key = config.get("gemini_api_key", "")
    if not key or key == "PASTE_YOUR_KEY_HERE":
        raise APIConnectionError("No Gemini API key set in config.json.")
    return key


def _get_model():
    """Model name from config.json ("model" key), or the default if it is not set."""
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f).get("model") or DEFAULT_MODEL
    except (OSError, json.JSONDecodeError):
        return DEFAULT_MODEL


def _call_gemini(prompt):
    """Send one prompt to Gemini and return the raw text reply. Raises APIConnectionError."""
    key = _get_api_key()
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 400},
    }
    try:
        response = requests.post(
            f"{API_BASE}/{_get_model()}:generateContent",
            params={"key": key},
            json=payload,
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except requests.exceptions.Timeout as err:
        raise APIConnectionError("The AI service took too long to respond.") from err
    except requests.exceptions.RequestException as err:
        raise APIConnectionError(f"Could not reach the AI service: {err}") from err
    except (KeyError, IndexError, ValueError) as err:
        raise APIConnectionError(f"The AI service returned an unexpected response: {err}") from err


def _strip_code_fence(text):
    """Gemini sometimes wraps JSON in ```json ... ``` — remove that if present."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else text


def extract_symptoms(text):
    """Ask Gemini to turn free text into {symptom: (severity, days)}.
    Returns None (not an exception) if the API is not configured, so callers can
    silently fall back to the regex parser. Raises APIConnectionError on a real failure.
    """
    if not os.path.exists(CONFIG_PATH):
        return None # AI not configured on this machine; fall back quietly

    from conditions import SYMPTOMS # local import avoids a circular import at module load
    prompt = (
        f"{SAFETY_INSTRUCTION}\n\n"
        f"Known symptom list: {', '.join(SYMPTOMS)}.\n"
        f"From the patient's message below, pick only symptoms from that list. "
        f"Reply with ONLY a JSON object mapping each found symptom to "
        f'[severity, days], severity from 1 (mild) to 3 (severe). '
        f"If no days are mentioned, use 1. If no severity is implied, use 2.\n\n"
        f'Patient message: "{text}"\n\nJSON:'
    )
    raw = _call_gemini(prompt)
    try:
        parsed = json.loads(_strip_code_fence(raw))
    except json.JSONDecodeError as err:
        raise APIConnectionError(f"Could not understand the AI's reply: {err}") from err
    result = {}
    for symptom, value in parsed.items():
        if symptom in SYMPTOMS and isinstance(value, (list, tuple)) and len(value) == 2:
            result[symptom] = (int(value[0]), int(value[1]))
    return result


def explain(result):
    """Ask Gemini to explain the rule-based result in plain language.
    Returns a safe fallback string instead of raising, so the results screen always has text.
    """
    if not os.path.exists(CONFIG_PATH):
        return "(AI explanation unavailable: no API key configured.)"
    matches = result.get("matches", [])
    level, message = result.get("urgency", ("GREEN", ""))
    summary = "; ".join(f"{c} ({p}% match)" for c, p, _m, _t in matches) or "no strong matches"
    prompt = (
        f"{SAFETY_INSTRUCTION}\n\n"
        f"A rule-based system found these possible conditions for a patient: {summary}. "
        f"The urgency level is {level} ({message}). "
        f"In 3 to 4 short, plain-language sentences, explain what this means for the patient "
        f"and why these conditions were suggested, without diagnosing or naming medication."
    )
    try:
        return _call_gemini(prompt).strip()
    except APIConnectionError as err:
        return f"(AI explanation unavailable: {err})"


def suggest_follow_up_questions(symptoms):
    """Ask Gemini for up to 3 extra follow-up questions. Returns [] on any failure."""
    if not os.path.exists(CONFIG_PATH) or not symptoms:
        return []
    prompt = (
        f"{SAFETY_INSTRUCTION}\n\n"
        f"A patient reports these symptoms: {', '.join(symptoms)}. "
        f"Suggest up to 3 short, general follow-up questions a health-assessment app could ask "
        f"to better understand the situation. Reply with ONLY a JSON list of strings."
    )
    try:
        raw = _call_gemini(prompt)
        parsed = json.loads(_strip_code_fence(raw))
        return [str(q) for q in parsed][:3] if isinstance(parsed, list) else []
    except (APIConnectionError, json.JSONDecodeError):
        return []