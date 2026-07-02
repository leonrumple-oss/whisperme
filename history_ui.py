"""Verlaufs-Fenster: die letzten Diktate ansehen und erneut kopieren."""
import tkinter as tk

import customtkinter as ctk
import pyperclip

import history
from ui_theme import (BLUE, BORDER, CARD, FIELD, FIELD_HOVER, GREEN, PRIMARY,
                      PRIMARY_HOVER, PRIMARY_TXT, SUB, TXT, VIOLET, WINBG)

MODE_COLORS = {"KI": VIOLET, "EN": BLUE, "Diktat": GREEN}


class HistoryWindow:
    def __init__(self, root: tk.Tk, app):
        self.app = app
        ctk.set_appearance_mode(
            "dark" if app.cfg.get("theme") == "dark" else "light")

        self.win = ctk.CTkToplevel(root)
        self.win.title("WisperMe – Verlauf")
        self.win.geometry("560x640")
        self.win.minsize(420, 320)
        self.win.configure(fg_color=WINBG)
        self.win.attributes("-topmost", True)

        self.f_title = ctk.CTkFont("Segoe UI", 20, "bold")
        self.f_label = ctk.CTkFont("Segoe UI", 12)
        self.f_small = ctk.CTkFont("Segoe UI", 10)

        head = ctk.CTkFrame(self.win, fg_color="transparent")
        head.pack(fill="x", padx=18, pady=(14, 6))
        ctk.CTkLabel(head, text="Verlauf", font=self.f_title,
                     text_color=TXT).pack(side="left")
        ctk.CTkLabel(head, text="die letzten 50 Diktate · nur lokal gespeichert",
                     font=self.f_small, text_color=SUB
                     ).pack(side="left", padx=(10, 0), pady=(6, 0))

        self.list_frame = ctk.CTkScrollableFrame(self.win, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=18)
        self._fill()

        footer = ctk.CTkFrame(self.win, fg_color="transparent")
        footer.pack(fill="x", padx=18, pady=12)
        ctk.CTkButton(footer, text="Schließen", width=110, height=32,
                      corner_radius=16, font=self.f_label, fg_color=PRIMARY,
                      hover_color=PRIMARY_HOVER, text_color=PRIMARY_TXT,
                      command=self.win.destroy).pack(side="right")
        ctk.CTkButton(footer, text="Verlauf leeren", width=120, height=32,
                      corner_radius=16, font=self.f_label, fg_color="transparent",
                      hover_color=FIELD_HOVER, text_color=TXT, border_width=1,
                      border_color=BORDER, command=self._clear).pack(side="left")

        self.win.lift()
        self.win.focus_force()

    def _fill(self):
        for child in self.list_frame.winfo_children():
            child.destroy()
        items = history.load()
        if not items:
            ctk.CTkLabel(self.list_frame, text="Noch keine Diktate.",
                         font=self.f_label, text_color=SUB).pack(pady=30)
            return
        for item in items:
            card = ctk.CTkFrame(self.list_frame, fg_color=CARD, corner_radius=12)
            card.pack(fill="x", pady=(0, 8))
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=12, pady=(8, 0))
            mode = item.get("modus", "Diktat")
            ctk.CTkLabel(top, text=mode, font=self.f_small,
                         text_color="#ffffff",
                         fg_color=MODE_COLORS.get(mode, "#3ad36b"),
                         corner_radius=6, padx=8, pady=1).pack(side="left")
            ctk.CTkLabel(top, text=item.get("zeit", ""), font=self.f_small,
                         text_color=SUB).pack(side="left", padx=8)
            ctk.CTkButton(top, text="Kopieren", width=76, height=24,
                          corner_radius=12, font=self.f_small, fg_color=FIELD,
                          hover_color=FIELD_HOVER, text_color=TXT,
                          command=(lambda t=item.get("text", ""):
                                   pyperclip.copy(t))).pack(side="right")
            ctk.CTkLabel(card, text=item.get("text", ""), font=self.f_label,
                         text_color=TXT, wraplength=460, justify="left",
                         anchor="w").pack(fill="x", padx=12, pady=(4, 10))

    def _clear(self):
        history.clear()
        self._fill()
