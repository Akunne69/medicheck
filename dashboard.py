
"""Statistics dashboard: pandas summaries drawn with matplotlib, embedded in Tkinter.
OWNER: Muhammad Abdullahi (branch: feature/dashboard-reports)

Contract: show_dashboard(parent) opens a Toplevel window with the charts.
Also exposes build_stats_dataframe() for reuse/testing without opening a window.
"""
import tkinter as tk
from tkinter import ttk

import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import database

AGE_BINS = [0, 12, 18, 30, 45, 60, 120]
AGE_LABELS = ["0-11", "12-17", "18-29", "30-44", "45-59", "60+"]


def build_age_group_counts(ages):
    """pandas: bucket ages into groups and count them."""
    if not ages:
        return pd.Series(dtype=int)
    series = pd.cut(pd.Series(ages), bins=AGE_BINS, labels=AGE_LABELS, right=False)
    return series.value_counts().reindex(AGE_LABELS, fill_value=0)


def show_dashboard(parent=None):
    """Open a window with four charts: common symptoms, common conditions,
    urgency breakdown, and age groups."""
    stats = database.get_stats()

    win = tk.Toplevel(parent) if parent else tk.Tk()
    win.title("MediCheck - Statistics Dashboard")
    win.geometry("900x700")

    ttk.Label(win, text=f"Total assessments recorded: {stats['total_assessments']}",
              font=("Arial", 13, "bold")).pack(pady=(10, 0))

    if stats["total_assessments"] == 0:
        ttk.Label(win, text="No assessments yet. Statistics will appear here once patients are assessed.",
                  font=("Arial", 11)).pack(pady=40)
        return win

    fig = Figure(figsize=(9, 7), dpi=100)
    ax1, ax2, ax3, ax4 = fig.subplots(2, 2).flatten()

    # 1. Common symptoms
    if stats["common_symptoms"]:
        names, counts = zip(*stats["common_symptoms"])
        ax1.barh(names, counts, color="#2E5C9A")
        ax1.invert_yaxis()
        ax1.set_title("Most common symptoms")
        ax1.tick_params(labelsize=8)

    # 2. Common conditions
    if stats["common_conditions"]:
        names, counts = zip(*stats["common_conditions"])
        ax2.barh(names, counts, color="#1F3864")
        ax2.invert_yaxis()
        ax2.set_title("Most frequently matched conditions")
        ax2.tick_params(labelsize=8)

    # 3. Urgency breakdown
    urgency_counts = stats["urgency_counts"]
    if urgency_counts:
        colors = {"GREEN": "#2e7d32", "YELLOW": "#f9a825", "RED": "#c62828"}
        labels = list(urgency_counts.keys())
        ax3.pie(urgency_counts.values(), labels=labels, autopct="%1.0f%%",
                colors=[colors.get(l, "gray") for l in labels])
        ax3.set_title("Urgency breakdown")

    # 4. Age groups (pandas bucketing)
    age_counts = build_age_group_counts(stats["ages"])
    if not age_counts.empty:
        ax4.bar(age_counts.index, age_counts.values, color="#5B8FD1")
        ax4.set_title("Assessments by age group")
        ax4.tick_params(labelsize=8)

    fig.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=win)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
    return win