"""
login.py - Animated login screen with role-based routing.
"""

import customtkinter as ctk
from tkinter import messagebox
import database as db
from theme import *
from widgets import make_entry, accent_btn


class LoginScreen(ctk.CTkFrame):
    """Full-window login form."""

    def __init__(self, master, on_success):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0)
        self.on_success = on_success
        self._build()

    def _build(self):
        # ── Background gradient effect (canvas) ──────────────
        self.canvas = ctk.CTkCanvas(self, bg=CLR_BG, highlightthickness=0)
        self.canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Decorative circles
        self.canvas.create_oval(-120, -120, 280, 280,
                                fill="#0E2D1F", outline="")
        self.canvas.create_oval(600, 400, 1000, 800,
                                fill="#0A1E2E", outline="")

        # ── Center card ──────────────────────────────────────
        card = ctk.CTkFrame(self, fg_color=CLR_SURFACE,
                            corner_radius=16, width=400)
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.grid_propagate(False)

        # Logo area
        logo = ctk.CTkFrame(card, fg_color=CLR_ACCENT,
                            width=64, height=64, corner_radius=16)
        logo.pack(pady=(36, 0))
        logo.pack_propagate(False)
        ctk.CTkLabel(logo, text="🥦", font=("Segoe UI", 30)).pack(
            expand=True)

        ctk.CTkLabel(card, text="FreshMart POS",
                     font=("Segoe UI", 22, "bold"),
                     text_color=CLR_WHITE).pack(pady=(14, 2))
        ctk.CTkLabel(card, text="Fruit & Vegetable Sales System",
                     font=FONT_SMALL, text_color=CLR_TEXT_DIM).pack()

        # ── Form ─────────────────────────────────────────────
        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(padx=40, pady=28, fill="x")

        ctk.CTkLabel(form, text="Username", font=FONT_SUBH,
                     text_color=CLR_TEXT_DIM, anchor="w").pack(fill="x")
        self.entry_user = make_entry(form, placeholder="Enter username",
                                    width=320)
        self.entry_user.pack(pady=(4, 14), fill="x")

        ctk.CTkLabel(form, text="Password", font=FONT_SUBH,
                     text_color=CLR_TEXT_DIM, anchor="w").pack(fill="x")
        self.entry_pass = make_entry(form, placeholder="Enter password",
                                    width=320, show="●")
        self.entry_pass.pack(pady=(4, 0), fill="x")

        # Show/hide password toggle
        self._show_pw = False
        ctk.CTkCheckBox(
            form, text="Show password",
            font=FONT_SMALL, text_color=CLR_TEXT_DIM,
            fg_color=CLR_ACCENT, hover_color=CLR_ACCENT_DARK,
            command=self._toggle_pw, checkmark_color=CLR_WHITE
        ).pack(anchor="e", pady=(6, 0))

        self.error_lbl = ctk.CTkLabel(form, text="",
                                      font=FONT_SMALL, text_color=CLR_DANGER)
        self.error_lbl.pack(pady=(8, 0))

        btn = ctk.CTkButton(
            form, text="Sign In  →", command=self._login,
            fg_color=CLR_ACCENT, hover_color=CLR_ACCENT_DARK,
            text_color=CLR_WHITE, font=("Segoe UI", 13, "bold"),
            height=40, corner_radius=8,
        )
        btn.pack(fill="x", pady=(10, 0))

        # Hint
        hint = ctk.CTkFrame(card, fg_color=CLR_SURFACE2,
                            corner_radius=8)
        hint.pack(padx=40, pady=(0, 30), fill="x")
        ctk.CTkLabel(hint,
                     text="Default  admin/admin123   cashier/cashier123",
                     font=FONT_SMALL, text_color=CLR_TEXT_DIM).pack(pady=8)

        # Bind Enter key
        self.entry_pass.bind("<Return>", lambda e: self._login())
        self.entry_user.bind("<Return>", lambda e: self.entry_pass.focus())

        # Set min card size
        card.configure(width=420, height=520)

    def _toggle_pw(self):
        self._show_pw = not self._show_pw
        self.entry_pass.configure(show="" if self._show_pw else "●")

    def _login(self):
        username = self.entry_user.get().strip()
        password = self.entry_pass.get()

        if not username or not password:
            self.error_lbl.configure(text="⚠  Please fill in all fields")
            return

        user = db.authenticate(username, password)
        if user:
            self.error_lbl.configure(text="")
            self.on_success(dict(user))
        else:
            self.error_lbl.configure(text="✗  Invalid username or password")
            self.entry_pass.delete(0, "end")
