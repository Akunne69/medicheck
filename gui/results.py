import tkinter as tk
from tkinter import ttk

class ResultsFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        tk.Label(self, text="Results go here").pack()
    def show_results(self, patient, symptoms, result):
        pass

class HistoryFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        tk.Label(self, text="History goes here").pack()
    def search(self):
        pass