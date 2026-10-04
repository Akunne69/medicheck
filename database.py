
_RECORDS = []

"""SQLite database: patients, assessments and statistics.
OWNER: Ahmad Gali (branch: feature/database)

Tables
------
patients            one row per registered patient
assessments         one row per completed assessment (linked to a patient)
assessment_symptoms one row per symptom reported in an assessment (used for stats)

Contracts used by the rest of the app
--------------------------------------
save_assessment(patient, symptoms, result, cycle_info=None) -> assessment_id
find_patient(name_or_phone)                                 -> list[dict]
get_all_assessments()                                        -> list[dict]
get_stats()                                                   -> dict
"""
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import date

from exceptions import DatabaseError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "medicheck.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS patients (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    age         INTEGER NOT NULL,
    sex         TEXT NOT NULL,
    phone       TEXT NOT NULL,
    history     TEXT DEFAULT '',
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assessments (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id   INTEGER NOT NULL REFERENCES patients(id),
    date         TEXT NOT NULL,
    top_match    TEXT,
    top_percent  INTEGER,
    urgency      TEXT NOT NULL,
    explanation  TEXT,
    cycle_note   TEXT,
    matches_json TEXT
);

CREATE TABLE IF NOT EXISTS assessment_symptoms (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id  INTEGER NOT NULL REFERENCES assessments(id),
    symptom        TEXT NOT NULL,
    severity       INTEGER NOT NULL,
    duration_days  INTEGER NOT NULL
);
"""


def _connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def _cursor():
    """Give calling code a cursor and commit/rollback automatically."""
    conn = _connect()
    try:
        cur = conn.cursor()
        yield cur
        conn.commit()
    except sqlite3.Error as err:
        conn.rollback()
        raise DatabaseError(f"Database error: {err}") from err
    finally:
        conn.close()


def init_db():
    with _cursor() as cur:
        cur.executescript(SCHEMA)


def _find_or_create_patient(cur, patient):
    cur.execute(
        "SELECT id FROM patients WHERE phone = ? ORDER BY id DESC LIMIT 1",
        (patient["phone"],),
    )
    row = cur.fetchone()
    if row:
        return row["id"]
    cur.execute(
        "INSERT INTO patients (name, age, sex, phone, history, created_at) VALUES (?,?,?,?,?,?)",
        (patient["name"], patient["age"], patient["sex"], patient["phone"],
         patient.get("history", ""), str(date.today())),
    )
    return cur.lastrowid


def save_assessment(patient, symptoms, result, cycle_info=None):
    """Store the patient (reusing an existing record by phone) and the assessment.
    symptoms = {name: (severity, days)}
    result   = {"matches": [...], "urgency": (level, message), "explanation": str}
    Returns the new assessment id.
    """
    matches = result.get("matches", [])
    level, _message = result.get("urgency", ("GREEN", ""))
    top_match, top_percent = (matches[0][0], matches[0][1]) if matches else (None, None)
    cycle_note = (cycle_info or {}).get("note", "") if isinstance(cycle_info, dict) else (cycle_info or "")

    with _cursor() as cur:
        patient_id = _find_or_create_patient(cur, patient)
        cur.execute(
            "INSERT INTO assessments "
            "(patient_id, date, top_match, top_percent, urgency, explanation, cycle_note, matches_json) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (patient_id, str(date.today()), top_match, top_percent, level,
             result.get("explanation", ""), cycle_note, json.dumps(matches)),
        )
        assessment_id = cur.lastrowid
        for symptom, (severity, days) in symptoms.items():
            cur.execute(
                "INSERT INTO assessment_symptoms (assessment_id, symptom, severity, duration_days) "
                "VALUES (?,?,?,?)",
                (assessment_id, symptom, severity, days),
            )
    return assessment_id


def find_patient(name_or_phone):
    """Return a list of patients (with their past assessments) matching a name or phone."""
    key = f"%{name_or_phone.strip().lower()}%"
    with _cursor() as cur:
        cur.execute(
            "SELECT * FROM patients WHERE lower(name) LIKE ? OR phone LIKE ? ORDER BY id DESC",
            (key, f"%{name_or_phone.strip()}%"),
        )
        patients = [dict(row) for row in cur.fetchall()]
        for p in patients:
            cur.execute(
                "SELECT * FROM assessments WHERE patient_id = ? ORDER BY id DESC", (p["id"],)
            )
            p["assessments"] = [dict(row) for row in cur.fetchall()]
    return patients


def get_all_assessments():
    """Every assessment joined with its patient's name and age, newest first."""
    with _cursor() as cur:
        cur.execute(
            "SELECT a.*, p.name AS patient_name, p.age AS patient_age, p.sex AS patient_sex "
            "FROM assessments a JOIN patients p ON p.id = a.patient_id "
            "ORDER BY a.id DESC"
        )
        return [dict(row) for row in cur.fetchall()]


def get_stats():
    """Aggregate numbers for the dashboard."""
    with _cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM assessments")
        total = cur.fetchone()["n"]

        cur.execute(
            "SELECT symptom, COUNT(*) AS n FROM assessment_symptoms "
            "GROUP BY symptom ORDER BY n DESC LIMIT 10"
        )
        common_symptoms = [(row["symptom"], row["n"]) for row in cur.fetchall()]

        cur.execute(
            "SELECT top_match, COUNT(*) AS n FROM assessments "
            "WHERE top_match IS NOT NULL GROUP BY top_match ORDER BY n DESC LIMIT 10"
        )
        common_conditions = [(row["top_match"], row["n"]) for row in cur.fetchall()]

        cur.execute(
            "SELECT p.age FROM assessments a JOIN patients p ON p.id = a.patient_id"
        )
        ages = [row["age"] for row in cur.fetchall()]

        cur.execute("SELECT urgency, COUNT(*) AS n FROM assessments GROUP BY urgency")
        urgency_counts = {row["urgency"]: row["n"] for row in cur.fetchall()}

    return {
        "total_assessments": total,
        "common_symptoms": common_symptoms,
        "common_conditions": common_conditions,
        "ages": ages,
        "urgency_counts": urgency_counts,
    }


def backup_database(dest_path=None):
    """Copy the live database file to a backup file (file handling)."""
    import shutil
    if not os.path.exists(DB_PATH):
        raise DatabaseError("No database file exists yet.")
    dest_path = dest_path or os.path.join(BASE_DIR, "data", f"medicheck_backup_{date.today()}.db")
    shutil.copyfile(DB_PATH, dest_path)
    return dest_path
