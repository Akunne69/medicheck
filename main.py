"""MediCheck entry point: one window that switches between screens.
OWNER: Nodunachukwu Akunne (Project Lead), branch: feature/gui-registration
Run with:  python main.py
"""
import logging
import tkinter as tk
from tkinter import ttk

import database
from exceptions import setup_logging
from gui.registration import DisclaimerFrame, RegistrationFrame, SymptomFrame
from gui.results import HistoryFrame, ResultsFrame


class MediCheckApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MediCheck - Patient Health Assessment")
        self.geometry("780x740")
        self.minsize(700, 640)
        ttk.Style(self).theme_use("clam")

        self.patient = {}
        self.symptoms = {}
        self.cycle_fields = {}

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        self.frames = {}
        for screen in (DisclaimerFrame, RegistrationFrame, SymptomFrame, ResultsFrame, HistoryFrame):
            frame = screen(container, self)
            self.frames[screen.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame("DisclaimerFrame")

    def show_frame(self, name):
        if name == "HistoryFrame":
            self.frames[name].search()  # refresh the list each time it is opened
        self.frames[name].tkraise()

    def open_dashboard(self):
        import dashboard
        dashboard.show_dashboard(self)

    def new_assessment(self):
        self.patient, self.symptoms, self.cycle_fields = {}, {}, {}
        self.frames["RegistrationFrame"].clear()
        self.frames["SymptomFrame"].reset()
        self.show_frame("RegistrationFrame")


if __name__ == "__main__":
    setup_logging()
    try:
        database.init_db()
    except Exception:
        logging.exception("Could not initialise the database")
    MediCheckApp().mainloop()