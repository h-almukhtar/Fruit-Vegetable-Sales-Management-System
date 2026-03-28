"""
users_panel.py - User account management (Admin only).
"""

import customtkinter as ctk
from tkinter import messagebox
import database as db
from theme import *
from widgets import (section_label, make_tree, accent_btn, danger_btn,
                     neutral_btn, blue_btn, make_entry, make_optionmenu,
                     show_toast)


class UsersPanel(ctk.CTkFrame):
    def __init__(self, master, current_user, **kw):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0, **kw)
        self.current_user = current_user
        self._build()
        self.refresh()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=PAD, pady=(PAD, 0))
        section_label(hdr, "👤  User Management").pack(side="left")

        btn_row = ctk.CTkFrame(hdr, fg_color="transparent")
        btn_row.pack(side="right")
        accent_btn(btn_row, "+ Add User",
                   self._open_add, width=120).pack(side="left", padx=4)
        blue_btn(btn_row,   "🔑 Reset PW",
                 self._reset_pw, width=120).pack(side="left", padx=4)
        danger_btn(btn_row, "✕ Delete",
                   self._delete,  width=100).pack(side="left", padx=4)

        cols  = ("id", "username", "role", "created")
        heads = ("ID", "Username", "Role", "Created")
        tf, self.tree = make_tree(self, cols, height=20)
        tf.pack(fill="both", expand=True, padx=PAD, pady=PAD)
        for col, head, w in zip(cols, heads, (50, 200, 100, 200)):
            self.tree.heading(col, text=head)
            self.tree.column(col, width=w, minwidth=40)
        self.tree.tag_configure("admin", foreground=CLR_ACCENT)

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(db.get_all_users()):
            tag = "admin" if r["role"] == "admin" else (
                "odd" if i % 2 == 0 else "even")
            self.tree.insert("", "end", values=(
                r["id"], r["username"], r["role"].upper(),
                r["created"][:16]
            ), tags=(tag,))

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a user first.")
            return None
        return int(self.tree.item(sel[0])["values"][0])

    def _open_add(self):
        UserDialog(self, on_save=self._save_add)

    def _save_add(self, data):
        try:
            db.add_user(data["username"], data["password"], data["role"])
            self.refresh()
            show_toast(self, f"✓  User '{data['username']}' created")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _reset_pw(self):
        uid = self._selected_id()
        if uid is None:
            return
        ResetPwDialog(self, uid, on_save=lambda p: self._do_reset(uid, p))

    def _do_reset(self, uid, pw):
        db.update_user_password(uid, pw)
        show_toast(self, "✓  Password updated")

    def _delete(self):
        uid = self._selected_id()
        if uid is None:
            return
        if uid == self.current_user["id"]:
            messagebox.showwarning("Cannot Delete",
                                   "You cannot delete your own account.")
            return
        if messagebox.askyesno("Confirm", "Delete this user?"):
            db.delete_user(uid)
            self.refresh()
            show_toast(self, "✓  User deleted", color=CLR_DANGER)


# ── Dialogs ───────────────────────────────────────────────────
class UserDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_save):
        super().__init__(parent)
        self.on_save = on_save
        self.title("Add New User")
        self.resizable(False, False)
        self.configure(fg_color=CLR_BG)
        self.grab_set()
        self._build()
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 380) // 2
        y = (self.winfo_screenheight() - 360) // 2
        self.geometry(f"380x380+{x}+{y}")

    def _build(self):
        card = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=12)
        card.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(card, text="Create User", font=FONT_HEAD,
                     text_color=CLR_WHITE).pack(pady=(20, 16))

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="x", padx=24)

        ctk.CTkLabel(form, text="Username", font=FONT_SUBH,
                     text_color=CLR_TEXT_DIM, anchor="w").pack(fill="x")
        self.e_user = make_entry(form, width=330)
        self.e_user.pack(pady=(4, 12), fill="x")

        ctk.CTkLabel(form, text="Password", font=FONT_SUBH,
                     text_color=CLR_TEXT_DIM, anchor="w").pack(fill="x")
        self.e_pass = make_entry(form, width=330, show="●")
        self.e_pass.pack(pady=(4, 12), fill="x")

        ctk.CTkLabel(form, text="Role", font=FONT_SUBH,
                     text_color=CLR_TEXT_DIM, anchor="w").pack(fill="x")
        self.role_var = ctk.StringVar(value="cashier")
        make_optionmenu(form, self.role_var,
                        ["cashier", "admin"], width=330).pack(pady=(4, 0))

        self.err = ctk.CTkLabel(form, text="", font=FONT_SMALL,
                                text_color=CLR_DANGER)
        self.err.pack(pady=(8, 0))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(pady=12)
        neutral_btn(row, "Cancel", self.destroy, width=100).pack(
            side="left", padx=6)
        accent_btn(row, "Create", self._submit, width=100).pack(
            side="left", padx=6)

    def _submit(self):
        u = self.e_user.get().strip()
        p = self.e_pass.get()
        r = self.role_var.get()
        if not u:
            self.err.configure(text="Username is required"); return
        if len(p) < 6:
            self.err.configure(text="Password must be ≥ 6 chars"); return
        self.on_save({"username": u, "password": p, "role": r})
        self.destroy()


class ResetPwDialog(ctk.CTkToplevel):
    def __init__(self, parent, uid, on_save):
        super().__init__(parent)
        self.on_save = on_save
        self.title("Reset Password")
        self.resizable(False, False)
        self.configure(fg_color=CLR_BG)
        self.grab_set()
        self._build()
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 340) // 2
        y = (self.winfo_screenheight() - 260) // 2
        self.geometry(f"340x260+{x}+{y}")

    def _build(self):
        card = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=12)
        card.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(card, text="Reset Password", font=FONT_HEAD,
                     text_color=CLR_WHITE).pack(pady=(20, 16))
        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="x", padx=24)
        ctk.CTkLabel(form, text="New Password", font=FONT_SUBH,
                     text_color=CLR_TEXT_DIM, anchor="w").pack(fill="x")
        self.e_pw = make_entry(form, width=290, show="●")
        self.e_pw.pack(pady=(4, 12), fill="x")
        self.err = ctk.CTkLabel(form, text="", font=FONT_SMALL,
                                text_color=CLR_DANGER)
        self.err.pack()
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(pady=12)
        neutral_btn(row, "Cancel", self.destroy, width=100).pack(
            side="left", padx=6)
        accent_btn(row, "Reset", self._submit, width=100).pack(
            side="left", padx=6)

    def _submit(self):
        pw = self.e_pw.get()
        if len(pw) < 6:
            self.err.configure(text="Password must be ≥ 6 chars"); return
        self.on_save(pw)
        self.destroy()
