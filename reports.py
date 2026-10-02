
"""Report generation and history export.
OWNER: Muhammad Abdullahi (branch: feature/dashboard-reports)

Contract:
  generate_report(patient, symptoms, result, cycle_note="") -> path of the .txt report file
  export_history_csv(assessments) -> path of the .csv file
"""
import csv
import os
from datetime import datetime

from exceptions import MediCheckError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORT_DIR = os.path.join(BASE_DIR, "data", "exports")


def _safe_filename(name):
    return "".join(c if c.isalnum() else "_" for c in name).strip("_") or "patient"


def generate_report(patient, symptoms, result, cycle_note=""):
    """Write a plain-text assessment report and return its file path."""
    os.makedirs(EXPORT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report_{_safe_filename(patient['name'])}_{timestamp}.txt"
    path = os.path.join(EXPORT_DIR, filename)

    matches = result.get("matches", [])
    level, message = result.get("urgency", ("GREEN", ""))

    lines = [
        "=" * 50,
        " MEDICHECK ASSESSMENT REPORT",
        "=" * 50,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        f"Patient : {patient['name']}, {patient['age']} years, {patient['sex']}",
        f"Phone   : {patient.get('phone', '')}",
        "",
        "Reported symptoms:",
    ]
    for symptom, (severity, days) in symptoms.items():
        lines.append(f"  - {symptom} (severity {severity}/3, {days} day(s))")

    lines += ["", "Possible conditions (not a diagnosis):"]
    if matches:
        for condition, percent, matched, total in matches:
            lines.append(f"  {condition}: {percent}% match "
                          f"(matched {len(matched)} of {total} key symptoms: {', '.join(matched)})")
    else:
        lines.append("  No matching conditions found in the database.")

    lines += ["", f"Urgency: {level} - {message}"]
    if cycle_note:
        lines += ["", f"Cycle note: {cycle_note}"]
    if result.get("explanation"):
        lines += ["", "AI explanation:", result["explanation"]]
    lines += ["", "This report gives general information only and is not medical advice."]

    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    except OSError as err:
        raise MediCheckError(f"Could not save the report: {err}") from err
    return path


def export_history_csv(assessments):
    """Write a CSV of past assessments (date, patient, top match, urgency) and return its path."""
    os.makedirs(EXPORT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(EXPORT_DIR, f"history_{timestamp}.csv")
    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Patient", "Age", "Sex", "Top match", "Match %", "Urgency"])
            for a in assessments:
                writer.writerow([
                    a.get("date", ""), a.get("patient_name", ""), a.get("patient_age", ""),
                    a.get("patient_sex", ""), a.get("top_match", ""),
                    a.get("top_percent", ""), a.get("urgency", ""),
                ])
    except OSError as err:
        raise MediCheckError(f"Could not export history: {err}") from err
    return path