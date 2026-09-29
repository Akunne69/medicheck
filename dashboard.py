
import matplotlib.pyplot as plt
from database import get_connection


def _cursor():
    """Return a database cursor that closes with its connection."""
    connection = get_connection()
    try:
        return connection.cursor()
    finally:
        connection.close()


def create_dashboard(data):
    figure, axes = plt.subplots(
        2,
        2,
        figsize=(14, 9)
    )

    figure.suptitle(
        f"MediCheck Dashboard\n"
        f"Total Assessments: {data['total_assessments']}",
        fontsize=18,
        fontweight="bold"
    )

    if data["total_assessments"] == 0:
        for axis in axes.flat:
            axis.axis("off")

        figure.text(
            0.5,
            0.5,
            "Statistics will appear once patients are assessed.",
            ha="center",
            va="center",
            fontsize=16
        )

        figure.tight_layout(rect=[0, 0, 1, 0.93])
        return figure

    # Symptoms chart
    symptom_rows = data["common_symptoms"]

    axes[0, 0].barh(
        [row["symptom"] for row in symptom_rows][::-1],
        [row["total"] for row in symptom_rows][::-1],
        color="#4C78A8"
    )

    axes[0, 0].set_title("Most Common Symptoms")
    axes[0, 0].set_xlabel("Number of reports")

    # Conditions chart
    condition_rows = data["common_conditions"]

    axes[0, 1].barh(
        [row["condition"] for row in condition_rows][::-1],
        [row["total"] for row in condition_rows][::-1],
        color="#59A14F"
    )

    axes[0, 1].set_title("Most Frequently Matched Conditions")
    axes[0, 1].set_xlabel("Number of assessments")

    # Urgency chart
    urgency_counts = {
        "GREEN": 0,
        "YELLOW": 0,
        "RED": 0,
    }

    for row in data["urgency_breakdown"]:
        urgency = row["urgency"].upper()

        if urgency in urgency_counts:
            urgency_counts[urgency] = row["total"]

    axes[1, 0].pie(
        urgency_counts.values(),
        labels=urgency_counts.keys(),
        colors=["#59A14F", "#F28E2B", "#E15759"],
        autopct="%1.1f%%",
        startangle=90
    )

    axes[1, 0].set_title("Urgency Breakdown")

    # Age-group chart
    age_labels = [
        "0-11",
        "12-17",
        "18-29",
        "30-44",
        "45-59",
        "60+",
    ]

    age_counts = [
        data["age_groups"].get(age_group, 0)
        for age_group in age_labels
    ]

    axes[1, 1].bar(
        age_labels,
        age_counts,
        color="#B279A2"
    )

    axes[1, 1].set_title("Assessments by Age Group")
    axes[1, 1].set_xlabel("Age group")
    axes[1, 1].set_ylabel("Number of assessments")

    figure.tight_layout(rect=[0, 0, 1, 0.93])

    return figure


def show_dashboard(data):
    figure = create_dashboard(data)
    figure.show()

def get_dashboard_data():
    with _cursor() as cur:
        # Total saved assessments
        cur.execute("""
            SELECT COUNT(*) AS total
            FROM assessments
        """)
        total_assessments = cur.fetchone()["total"]

        # Most common symptoms
        cur.execute("""
            SELECT symptom, COUNT(*) AS total
            FROM assessment_symptoms
            GROUP BY symptom
            ORDER BY total DESC
            LIMIT 10
        """)
        common_symptoms = [
            dict(row) for row in cur.fetchall()
        ]

        # Most frequently matched conditions
        cur.execute("""
            SELECT top_match AS condition, COUNT(*) AS total
            FROM assessments
            WHERE top_match IS NOT NULL
              AND top_match != ''
            GROUP BY top_match
            ORDER BY total DESC
            LIMIT 10
        """)
        common_conditions = [
            dict(row) for row in cur.fetchall()
        ]

        # Urgency breakdown
        cur.execute("""
            SELECT urgency, COUNT(*) AS total
            FROM assessments
            WHERE urgency IN ('GREEN', 'YELLOW', 'RED')
            GROUP BY urgency
        """)
        urgency_breakdown = [
            dict(row) for row in cur.fetchall()
        ]

        # Assessments grouped by age range
        cur.execute("""
            SELECT
                CASE
                    WHEN patients.age BETWEEN 0 AND 11 THEN '0-11'
                    WHEN patients.age BETWEEN 12 AND 17 THEN '12-17'
                    WHEN patients.age BETWEEN 18 AND 29 THEN '18-29'
                    WHEN patients.age BETWEEN 30 AND 44 THEN '30-44'
                    WHEN patients.age BETWEEN 45 AND 59 THEN '45-59'
                    WHEN patients.age >= 60 THEN '60+'
                END AS age_group,
                COUNT(*) AS total
            FROM assessments
            INNER JOIN patients
                ON assessments.patient_id = patients.id
            GROUP BY age_group
        """)
        age_rows = cur.fetchall()

    age_order = ["0-11", "12-17", "18-29", "30-44", "45-59", "60+"]

    age_groups = {
        age_group: 0
        for age_group in age_order
    }

    for row in age_rows:
        if row["age_group"] in age_groups:
            age_groups[row["age_group"]] = row["total"]

    return {
        "total_assessments": total_assessments,
        "common_symptoms": common_symptoms,
        "common_conditions": common_conditions,
        "urgency_breakdown": urgency_breakdown,
        "age_groups": age_groups,
    }

