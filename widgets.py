"""
widgets.py - Reusable widget factories for the dark-theme UI.
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from theme import *


def make_frame(parent, **kw):
    return ctk.CTkFrame(parent, fg_color=CLR_SURFACE,
                        corner_radius=10, **kw)


def section_label(parent, text, **kw):
    return ctk.CTkLabel(parent, text=text,
                        font=FONT_HEAD, text_color=CLR_TEXT, **kw)


def dim_label(parent, text, **kw):
    return ctk.CTkLabel(parent, text=text,
                        font=FONT_SMALL, text_color=CLR_TEXT_DIM, **kw)


def accent_btn(parent, text, command, width=120, **kw):
    return ctk.CTkButton(
        parent, text=text, command=command,
        fg_color=CLR_ACCENT, hover_color=CLR_ACCENT_DARK,
        text_color=CLR_WHITE, font=FONT_SUBH,
        height=BTN_H, width=width,
        corner_radius=6, **kw
    )


def danger_btn(parent, text, command, width=120, **kw):
    return ctk.CTkButton(
        parent, text=text, command=command,
        fg_color=CLR_DANGER, hover_color="#B91C1C",
        text_color=CLR_WHITE, font=FONT_SUBH,
        height=BTN_H, width=width,
        corner_radius=6, **kw
    )


def neutral_btn(parent, text, command, width=120, **kw):
    return ctk.CTkButton(
        parent, text=text, command=command,
        fg_color=CLR_SURFACE2, hover_color=CLR_BORDER,
        text_color=CLR_TEXT, font=FONT_SUBH,
        height=BTN_H, width=width,
        corner_radius=6, **kw
    )


def blue_btn(parent, text, command, width=120, **kw):
    return ctk.CTkButton(
        parent, text=text, command=command,
        fg_color="#0369A1", hover_color="#075985",
        text_color=CLR_WHITE, font=FONT_SUBH,
        height=BTN_H, width=width,
        corner_radius=6, **kw
    )


def make_entry(parent, placeholder="", width=200, **kw):
    return ctk.CTkEntry(
        parent, placeholder_text=placeholder,
        fg_color=CLR_SURFACE2, border_color=CLR_BORDER,
        text_color=CLR_TEXT, placeholder_text_color=CLR_TEXT_DIM,
        font=FONT_BODY, height=ENTRY_H, width=width,
        corner_radius=6, **kw
    )


def make_optionmenu(parent, variable, values, width=160, **kw):
    return ctk.CTkOptionMenu(
        parent, variable=variable, values=values,
        fg_color=CLR_SURFACE2, button_color=CLR_BORDER,
        button_hover_color=CLR_ACCENT,
        text_color=CLR_TEXT, font=FONT_BODY,
        dropdown_fg_color=CLR_SURFACE2,
        dropdown_text_color=CLR_TEXT,
        dropdown_hover_color=CLR_ACCENT_DARK,
        width=width, **kw
    )


def make_tree(parent, columns, show="headings", height=18):
    """Create a styled Treeview with scrollbar, return (frame, tree)."""
    frame = ctk.CTkFrame(parent, fg_color=CLR_BG, corner_radius=8)

    tree = ttk.Treeview(frame, columns=columns,
                        show=show, height=height,
                        style="Custom.Treeview")

    vsb = ttk.Scrollbar(frame, orient="vertical",
                        command=tree.yview,
                        style="Custom.Vertical.TScrollbar")
    tree.configure(yscrollcommand=vsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    # Alternate row colors
    tree.tag_configure("odd",  background=CLR_ROW_ODD)
    tree.tag_configure("even", background=CLR_ROW_EVEN)
    tree.tag_configure("low",  background="#3B1A1A", foreground="#FCA5A5")

    return frame, tree


def populate_tree(tree, rows, columns):
    """Clear and refill a Treeview. rows = list of dicts or sqlite3.Row."""
    tree.delete(*tree.get_children())
    for i, row in enumerate(rows):
        tag  = "odd" if i % 2 == 0 else "even"
        vals = [row[c] for c in columns]
        tree.insert("", "end", values=vals, tags=(tag,))


def stat_card(parent, label, value, color=CLR_ACCENT, width=160):
    """Small KPI card."""
    card = ctk.CTkFrame(parent, fg_color=CLR_SURFACE2,
                        corner_radius=10, width=width)
    card.pack_propagate(False)
    ctk.CTkLabel(card, text=label, font=FONT_SMALL,
                 text_color=CLR_TEXT_DIM).pack(pady=(14, 2))
    lbl = ctk.CTkLabel(card, text=str(value), font=("Segoe UI", 20, "bold"),
                       text_color=color)
    lbl.pack(pady=(0, 14))
    return card, lbl


def show_toast(parent, msg, color=CLR_ACCENT, duration=2500):
    """Floating status toast at the bottom of parent."""
    toast = ctk.CTkFrame(parent, fg_color=color, corner_radius=8)
    ctk.CTkLabel(toast, text=msg, font=FONT_BODY,
                 text_color=CLR_WHITE).pack(padx=16, pady=8)
    toast.place(relx=0.5, rely=0.96, anchor="center")
    parent.after(duration, toast.destroy)
