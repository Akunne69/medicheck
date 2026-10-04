"""Results screen and patient history search screen.

OWNER: Elvis Jatau (branch: feature/gui-results-history)
"""
import tkinter as tk
from tkinter import messagebox, ttk

import database
import reports
from exceptions import MediCheckError

LEVEL_COLORS = {"GREEN": "#2e7d32", "YELLOW": "#f9a825", "RED": "#c62828"}
TITLE_FONT = ("Arial", 20, "bold")


class ResultsFrame(ttk.Frame):
    """Shows the ranked matches, urgency banner, guidance, follow-up questions
    and AI explanation for the assessment just completed."""

    def __init__(self, parent, app):
        super().__init__(parent, padding=25)
        self.app = app
        self._last_patient = None
        self._last_symptoms = None
        self._last_result = None

        ttk.Label(self, text="Assessment Results", font=TITLE_FONT).pack(anchor="w")
        self.level_label = tk.Label(self, text="", font=("Arial", 13, "bold"), fg="white", padx=10, pady=6)
        self.level_label.pack(fill="x", pady=(8, 10))

        self.output = tk.Text(self, wrap="word", height=16, state="disabled")
        self.output.pack(fill="both", expand=True)

        buttons = ttk.Frame(self)
        buttons.pack(fill="x", pady=(12, 0))
        ttk.Button(buttons, text="View history", command=lambda: app.show_frame("HistoryFrame")).pack(side="left")
        ttk.Button(buttons, text="Save report", command=self.save_report).pack(side="left", padx=8)
        ttk.Button(buttons, text="New assessment", command=app.new_assessment).pack(side="right")

    def show_results(self, patient, symptoms, result):
        self._last_patient, self._last_symptoms, self._last_result = patient, symptoms, result
        level, message = result["urgency"]
        self.level_label.config(text=f"{level}: {message}", bg=LEVEL_COLORS.get(level, "gray"))

        lines = [f"Patient: {patient['name']}, {patient['age']}, {patient['sex']}", "",
                 "Possible conditions (not a diagnosis):"]
        matches = result.get("matches", [])
        if matches:
            for condition, percent, matched, total in matches:
                lines.append(f"  - {condition}: {percent}% "
                             f"(matched {len(matched)} of {total} key symptoms: {', '.join(matched)})")
        else:
            lines.append("  No matching conditions were found for these symptoms.")

        if result.get("guidance"):
            lines += ["", "General guidance:", f"  {result['guidance']}"]
        if result.get("follow_up"):
            lines += ["", "Follow-up questions to consider:"]
            lines += [f"  - {q}" for q in result["follow_up"]]
        if result.get("cycle_note"):
            lines += ["", f"Cycle note: {result['cycle_note']}"]
        lines += ["", "AI explanation:", result.get("explanation", ""), "",
                  "This is general information only, not medical advice."]

        self.output.config(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", "\n".join(lines))
        self.output.config(state="disabled")

    def save_report(self):
        if not self._last_patient:
            return
        try:
            path = reports.generate_report(
                self._last_patient, self._last_symptoms, self._last_result,
                cycle_note=self._last_result.get("cycle_note", ""),
            )
        except MediCheckError as err:
            messagebox.showerror("Could not save report", str(err))
            return
        messagebox.showinfo("Report saved", f"Saved to:\n{path}")


class HistoryFrame(ttk.Frame):
    """Search for a patient by name or phone and view their past assessments."""

    def __init__(self, parent, app):
        super().__init__(parent, padding=25)
        self.app = app

        ttk.Label(self, text="Patient History", font=TITLE_FONT).pack(anchor="w")

        search_row = ttk.Frame(self)
        search_row.pack(fill="x", pady=(10, 10))
        self.search_var = tk.StringVar()
        entry = ttk.Entry(search_row, textvariable=self.search_var)
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda e: self.search())
        ttk.Button(search_row, text="Search", command=self.search).pack(side="left", padx=6)
        ttk.Button(search_row, text="Export all to CSV", command=self.export_csv).pack(side="left")

        columns = ("date", "condition", "match", "urgency")
        self.tree = ttk.Treeview(self, columns=columns, show="tree headings", height=14)
        self.tree.heading("#0", text="Patient")
        self.tree.heading("date", text="Date")
        self.tree.heading("condition", text="Top match")
        self.tree.heading("match", text="Match %")
        self.tree.heading("urgency", text="Urgency")
        self.tree.column("#0", width=180)
        self.tree.column("date", width=100)
        self.tree.column("condition", width=180)
        self.tree.column("match", width=80, anchor="center")
        self.tree.column("urgency", width=90, anchor="center")
        self.tree.pack(fill="both", expand=True)

        ttk.Button(self, text="Back", command=lambda: app.show_frame("RegistrationFrame")).pack(
            anchor="w", pady=(10, 0))

    def search(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        query = self.search_var.get().strip()
        try:
            patients = database.find_patient(query) if query else self._recent_patients()
        except MediCheckError as err:
            messagebox.showerror("Search failed", str(err))
            return
        if not patients:
            messagebox.showinfo("No results", "No matching patient was found.")
            return
        for patient in patients:
            parent_id = self.tree.insert(
                "", "end", text=f"{patient['name']} ({patient['age']}, {patient['sex']})", open=True)
            for a in patient["assessments"]:
                self.tree.insert(parent_id, "end", text="", values=(
                    a["date"], a["top_match"] or "-", a["top_percent"] or "-", a["urgency"]))

    def _recent_patients(self):
        """No query typed: show everyone who has at least one assessment."""
        seen = {}
        for a in database.get_all_assessments():
            seen.setdefault(a["patient_id"], a["patient_name"])
        return [p for name in seen.values() for p in database.find_patient(name)][:20]

    def export_csv(self):
        try:
            path = reports.export_history_csv(database.get_all_assessments())
        except MediCheckError as err:
            messagebox.showerror("Export failed", str(err))
            return
        messagebox.showinfo("Exported", f"History exported to:\n{path}")
