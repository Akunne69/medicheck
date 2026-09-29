
from pathlib import Path


def generate_report(patient, symptoms, result, cycle_note=""):
    """
    Create the text for one patient's assessment report.

    patient:
        Dictionary containing patient information, such as:
        name, age, and sex.

    symptoms:
        List of dictionaries containing:
        symptom, severity, and duration_days.

    result:
        Dictionary containing assessment results, such as:
        urgency, matches, and explanation.

    cycle_note:
        Optional menstrual-cycle-related note.
    """

    report_lines = []

    report_lines.append("MEDICHECK ASSESSMENT REPORT")
    report_lines.append("=" * 40)
    report_lines.append("")

    report_lines.append("PATIENT INFORMATION")
    report_lines.append("-" * 40)
    report_lines.append(f"Name: {patient['name']}")
    report_lines.append(f"Age: {patient['age']}")
    report_lines.append(f"Sex: {patient['sex']}")
    report_lines.append("")

    report_lines.append("REPORTED SYMPTOMS")
    report_lines.append("-" * 40)

    if symptoms:
        for item in symptoms:
            symptom = item.get("symptom", "Unknown symptom")
            severity = item.get("severity", "Not recorded")
            duration_days = item.get(
                "duration_days",
                "Not recorded"
            )

            report_lines.append(
                f"- {symptom}\n"
                f"  Severity: {severity}\n"
                f"  Duration: {duration_days} days"
            )
    else:
        report_lines.append("No symptoms recorded.")

    report_lines.append("")

    report_lines.append("POSSIBLE CONDITIONS")
    report_lines.append("-" * 40)

    matches = (
        result.get("matches")
        or result.get("possible_conditions")
        or []
    )

    if matches:
        for match in matches:
            if isinstance(match, dict):
                condition = (
                    match.get("condition")
                    or match.get("name")
                    or match.get("top_match")
                    or "Unknown condition"
                )

                percentage = (
                    match.get("percentage")
                    or match.get("percent")
                    or match.get("top_percent")
                    or "Not recorded"
                )

                report_lines.append(
                    f"- {condition}: {percentage}%"
                )
            else:
                report_lines.append(f"- {match}")
    else:
        report_lines.append(
            "No possible conditions recorded."
        )

    report_lines.append("")

    report_lines.append("ASSESSMENT RESULT")
    report_lines.append("-" * 40)

    urgency = result.get("urgency", "Not recorded")
    report_lines.append(f"Urgency: {urgency}")

    if cycle_note:
        report_lines.append(f"Cycle note: {cycle_note}")

    explanation = result.get("explanation", "")

    if explanation:
        report_lines.append("")
        report_lines.append("AI EXPLANATION")
        report_lines.append("-" * 40)
        report_lines.append(explanation)

    report_lines.append("")
    report_lines.append("=" * 40)
    report_lines.append(
        "This report is not medical advice."
    )
    report_lines.append(
        "Please consult a qualified healthcare professional."
    )

    return "\n".join(report_lines)


def save_report(
    patient,
    symptoms,
    result,
    cycle_note="",
    file_path="assessment_report.txt"
):
    report_text = generate_report(
        patient=patient,
        symptoms=symptoms,
        result=result,
        cycle_note=cycle_note
    )

    Path(file_path).write_text(
        report_text,
        encoding="utf-8"
    )

    return file_path

import csv
from pathlib import Path

from database import _cursor


def export_history_csv(file_path="assessment_history.csv"):
    with _cursor() as cur:
        cur.execute("""
            SELECT
                assessments.date AS date,
                patients.name AS patient,
                patients.age AS age,
                patients.sex AS sex,
                assessments.top_match AS top_match,
                assessments.top_percent AS match_percent,
                assessments.urgency AS urgency
            FROM assessments
            INNER JOIN patients
                ON assessments.patient_id = patients.id
            ORDER BY assessments.date DESC
        """)

        rows = cur.fetchall()

    columns = [
        "date",
        "patient",
        "age",
        "sex",
        "top_match",
        "match_percent",
        "urgency",
    ]

    with Path(file_path).open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=columns
        )

        writer.writeheader()

        for row in rows:
            writer.writerow({
                "date": row["date"],
                "patient": row["patient"],
                "age": row["age"],
                "sex": row["sex"],
                "top_match": row["top_match"] or "",
                "match_percent": (
                    row["match_percent"]
                    if row["match_percent"] is not None
                    else ""
                ),
                "urgency": row["urgency"],
            })

    return file_path
