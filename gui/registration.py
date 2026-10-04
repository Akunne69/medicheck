"""Disclaimer, patient registration and symptom selection screens.
OWNER: Nodunachukwu Akunne (Project Lead), branch: feature/gui-registration
"""
import logging
import tkinter as tk
from tkinter import messagebox, ttk

import ai_client
import cycle
import database
import engine
import parser
import urgency
from conditions import SYMPTOMS
from exceptions import APIConnectionError, InvalidInputError, MediCheckError
from gui.validators import (validate_age, validate_cycle_length, validate_name,
                             validate_optional_date, validate_phone)

TITLE_FONT = ("Arial", 20, "bold")
HEADING_FONT = ("Arial", 12, "bold")
ERROR_COLOR = "#c62828"


class DisclaimerFrame(ttk.Frame):
    """First screen: the 'not medical advice' disclaimer."""

    def __init__(self, parent, app):
        super().__init__(parent, padding=30)
        ttk.Label(self, text="MediCheck", font=("Arial", 28, "bold")).pack(pady=(40, 5))
        ttk.Label(self, text="Patient Health Assessment System", font=("Arial", 13)).pack(pady=(0, 30))
        text = (
            "IMPORTANT NOTICE\n\n"
            "MediCheck gives possible matches and general health information only.\n"
            "It is NOT a diagnosis and NOT medical advice.\n\n"
            "It never prescribes medication or dosages.\n"
            "If you feel seriously unwell, contact a healthcare professional or emergency service.\n\n"
            "Use fictional data when testing this application."
        )
        ttk.Label(self, text=text, justify="center", wraplength=560, font=("Arial", 11)).pack(pady=10)
        ttk.Button(self, text="I understand, continue",
                   command=lambda: app.show_frame("RegistrationFrame")).pack(pady=30)


class RegistrationFrame(ttk.Frame):
    """Patient registration form with regex validation and optional cycle fields."""

    def __init__(self, parent, app):
        super().__init__(parent, padding=25)
        self.app = app
        self.columnconfigure(1, weight=1)

        ttk.Label(self, text="Patient Registration", font=TITLE_FONT).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))

        self.name_var = tk.StringVar()
        self.age_var = tk.StringVar()
        self.sex_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.period_var = tk.StringVar()
        self.cycle_len_var = tk.StringVar()
        self.error_labels = {}

        self._add_row(1, "Full name", ttk.Entry(self, textvariable=self.name_var), "name")
        self._add_row(3, "Age", ttk.Entry(self, textvariable=self.age_var, width=10), "age")
        sex_box = ttk.Combobox(self, textvariable=self.sex_var, values=["Female", "Male", "Other"],
                                state="readonly", width=12)
        sex_box.bind("<<ComboboxSelected>>", self._on_sex_change)
        self._add_row(5, "Sex", sex_box, "sex")
        self._add_row(7, "Phone / contact", ttk.Entry(self, textvariable=self.phone_var), "phone")

        # --- optional cycle section, shown only when Sex = Female ---
        self.cycle_frame = ttk.LabelFrame(self, text="Menstrual cycle (optional)", padding=10)
        self.cycle_frame.columnconfigure(1, weight=1)
        ttk.Label(self.cycle_frame, text="Last period start (YYYY-MM-DD)").grid(row=0, column=0, sticky="w")
        ttk.Entry(self.cycle_frame, textvariable=self.period_var, width=14).grid(row=0, column=1, sticky="w", padx=8)
        ttk.Label(self.cycle_frame, text="Average cycle length (days)").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(self.cycle_frame, textvariable=self.cycle_len_var, width=6).grid(row=1, column=1, sticky="w", padx=8, pady=(6, 0))
        ttk.Label(self.cycle_frame, text="Leave blank if you'd rather not share this.",
                  foreground="gray").grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))
        self.cycle_error = ttk.Label(self.cycle_frame, text="", foreground=ERROR_COLOR)
        self.cycle_error.grid(row=3, column=0, columnspan=2, sticky="w")
        # not gridded into self until sex == Female (see _on_sex_change)

        ttk.Label(self, text="Previous medical history", font=HEADING_FONT).grid(
            row=9, column=0, sticky="nw", pady=(8, 0))
        self.history_box = tk.Text(self, height=4, width=40, wrap="word")
        self.history_box.grid(row=9, column=1, sticky="ew", pady=(8, 0))
        ttk.Label(self, text="(optional)", foreground="gray").grid(row=10, column=1, sticky="w")

        buttons = ttk.Frame(self)
        buttons.grid(row=12, column=0, columnspan=2, pady=25, sticky="e")
        ttk.Button(buttons, text="View history", command=lambda: app.show_frame("HistoryFrame")).pack(side="left", padx=5)
        ttk.Button(buttons, text="Dashboard", command=app.open_dashboard).pack(side="left", padx=5)
        ttk.Button(buttons, text="Next: choose symptoms", command=self.submit).pack(side="left", padx=5)

    def _add_row(self, row, label, widget, key):
        ttk.Label(self, text=label, font=HEADING_FONT).grid(row=row, column=0, sticky="w", pady=(8, 0), padx=(0, 15))
        widget.grid(row=row, column=1, sticky="w" if key in ("age", "sex") else "ew", pady=(8, 0))
        err = ttk.Label(self, text="", foreground=ERROR_COLOR)
        err.grid(row=row + 1, column=1, sticky="w")
        self.error_labels[key] = err

    def _on_sex_change(self, _event=None):
        if self.sex_var.get() == "Female":
            self.cycle_frame.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        else:
            self.cycle_frame.grid_forget()
            self.period_var.set("")
            self.cycle_len_var.set("")

    def clear(self):
        for var in (self.name_var, self.age_var, self.sex_var, self.phone_var,
                    self.period_var, self.cycle_len_var):
            var.set("")
        self.history_box.delete("1.0", "end")
        for label in self.error_labels.values():
            label.config(text="")
        self.cycle_error.config(text="")
        self.cycle_frame.grid_forget()

    def submit(self):
        for label in self.error_labels.values():
            label.config(text="")
        self.cycle_error.config(text="")
        cleaned, has_error = {}, False

        checks = [
            ("name", lambda: validate_name(self.name_var.get())),
            ("age", lambda: validate_age(self.age_var.get())),
            ("phone", lambda: validate_phone(self.phone_var.get())),
        ]
        for key, check in checks:
            try:
                cleaned[key] = check()
            except InvalidInputError as err:
                self.error_labels[key].config(text=str(err))
                has_error = True

        if not self.sex_var.get():
            self.error_labels["sex"].config(text="Please choose an option.")
            has_error = True

        last_period, cycle_length = None, 28
        if self.sex_var.get() == "Female":
            try:
                last_period = validate_optional_date(self.period_var.get())
                cycle_length = validate_cycle_length(self.cycle_len_var.get())
            except InvalidInputError as err:
                self.cycle_error.config(text=str(err))
                has_error = True

        if has_error:
            return

        cleaned["sex"] = self.sex_var.get()
        cleaned["history"] = self.history_box.get("1.0", "end").strip()
        self.app.patient = cleaned
        self.app.cycle_fields = {"last_period": last_period, "cycle_length": cycle_length}
        self.app.show_frame("SymptomFrame")


class SymptomFrame(ttk.Frame):
    """Symptom selection: checkbox + severity + days, plus a free-text box."""

    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.rows = {}

        ttk.Label(self, text="Select Symptoms", font=TITLE_FONT).pack(anchor="w")
        ttk.Label(self, text="Tick each symptom, rate how severe it is (1 mild to 3 severe) and how many days.",
                  wraplength=680).pack(anchor="w", pady=(2, 8))

        text_box_frame = ttk.LabelFrame(self, text="Or describe how you feel in your own words", padding=8)
        text_box_frame.pack(fill="x", pady=(0, 8))
        self.text_box = tk.Text(text_box_frame, height=3, wrap="word")
        self.text_box.pack(fill="x")
        row = ttk.Frame(text_box_frame)
        row.pack(fill="x", pady=(5, 0))
        ttk.Button(row, text="Fill symptoms from text", command=self.fill_from_text).pack(side="left")
        self.status = ttk.Label(row, text="", foreground="gray")
        self.status.pack(side="left", padx=10)

        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(list_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas)
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.canvas.bind("<Enter>", self._bind_wheel)
        self.canvas.bind("<Leave>", self._unbind_wheel)

        header = ttk.Frame(self.inner)
        header.grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="Symptom", width=24, font=HEADING_FONT).grid(row=0, column=0)
        ttk.Label(header, text="Severity", width=10, font=HEADING_FONT).grid(row=0, column=1)
        ttk.Label(header, text="Days", width=8, font=HEADING_FONT).grid(row=0, column=2)

        for i, symptom in enumerate(SYMPTOMS, start=1):
            checked, severity, days = tk.BooleanVar(), tk.StringVar(value="2"), tk.StringVar(value="1")
            line = ttk.Frame(self.inner)
            line.grid(row=i, column=0, sticky="w", pady=1)
            ttk.Checkbutton(line, text=symptom.capitalize(), variable=checked, width=24).grid(row=0, column=0)
            ttk.Combobox(line, textvariable=severity, values=["1", "2", "3"], state="readonly", width=5).grid(row=0, column=1, padx=8)
            ttk.Spinbox(line, textvariable=days, from_=1, to=365, width=6).grid(row=0, column=2, padx=8)
            self.rows[symptom] = (checked, severity, days)

        buttons = ttk.Frame(self)
        buttons.pack(fill="x", pady=(10, 0))
        ttk.Button(buttons, text="Back", command=lambda: app.show_frame("RegistrationFrame")).pack(side="left")
        ttk.Button(buttons, text="Analyse symptoms", command=self.run_assessment).pack(side="right")

    def _bind_wheel(self, _event):
        self.canvas.bind_all("<MouseWheel>", self._on_wheel)
        self.canvas.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))

    def _unbind_wheel(self, _event):
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.canvas.unbind_all(seq)

    def _on_wheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def reset(self):
        self.text_box.delete("1.0", "end")
        self.status.config(text="")
        for checked, severity, days in self.rows.values():
            checked.set(False)
            severity.set("2")
            days.set("1")

    def fill_from_text(self):
        """Try Gemini first (if configured); fall back to the regex parser."""
        text = self.text_box.get("1.0", "end").strip()
        if not text:
            messagebox.showinfo("Nothing to read", "Type how you feel first.")
            return
        found, source = None, "the AI assistant"
        try:
            found = ai_client.extract_symptoms(text)
        except APIConnectionError as err:
            logging.warning("AI extraction failed: %s", err)
        if not found:
            found, source = parser.extract_symptoms(text), "pattern matching"
        if not found:
            messagebox.showinfo("No symptoms found",
                                 "Could not find any known symptoms. Please tick them from the list.")
            return
        for name, (sev, days) in found.items():
            if name in self.rows:
                checked, severity, day_var = self.rows[name]
                checked.set(True)
                severity.set(str(sev))
                day_var.set(str(days))
        self.status.config(text=f"Filled {len(found)} symptom(s) using {source}. Please check them.")

    def collect_selected(self):
        selected = {}
        for symptom, (checked, severity, days) in self.rows.items():
            if not checked.get():
                continue
            try:
                day_count = int(days.get())
                if day_count < 1:
                    raise ValueError
            except ValueError:
                raise InvalidInputError(f"Days for '{symptom}' must be a whole number of 1 or more.") from None
            selected[symptom] = (int(severity.get()), day_count)
        return selected

    def run_assessment(self):
        try:
            selected = self.collect_selected()
            if not selected:
                messagebox.showwarning("No symptoms", "Please select at least one symptom.")
                return

            matches = engine.analyse(selected)
            level, message = urgency.assess(selected, matches)
            top_condition = matches[0][0] if matches else None

            cycle_fields = getattr(self.app, "cycle_fields", {})
            cycle_info = cycle.estimate(cycle_fields.get("last_period"), cycle_fields.get("cycle_length", 28))
            cycle_note = cycle.note_for(selected, cycle_info)

            result = {
                "matches": matches,
                "urgency": (level, message),
                "guidance": urgency.guidance_for(top_condition),
                "follow_up": engine.follow_up_questions(selected),
                "cycle_note": cycle_note,
            }
            result["explanation"] = ai_client.explain(result)

            database.save_assessment(self.app.patient, selected, result, cycle_info={"note": cycle_note})
        except MediCheckError as err:
            messagebox.showerror("Problem", str(err))
            return
        except Exception:
            logging.exception("Unexpected error during assessment")
            messagebox.showerror("Unexpected error",
                                  "Something went wrong. The error was saved to data/medicheck.log.")
            return

        self.app.symptoms = selected
        self.app.frames["ResultsFrame"].show_results(self.app.patient, selected, result)
        self.app.show_frame("ResultsFrame")