"""
products_panel.py - Product CRUD panel (Admin only).
Fixed: dialog is now scrollable with always-visible Save button.
"""

import customtkinter as ctk
from tkinter import messagebox
import database as db
from theme import *
from widgets import (make_frame, section_label, make_entry, make_tree,
                     populate_tree, accent_btn, danger_btn, neutral_btn,
                     blue_btn, dim_label, show_toast)

COLS  = ("id", "name", "price", "quantity", "low_stock", "updated")
HEADS = ("ID", "Product Name", "Price (SAR)", "Stock", "Low Stock Alert", "Last Updated")


class ProductsPanel(ctk.CTkFrame):
    def __init__(self, master, readonly=False, **kw):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0, **kw)
        self.readonly = readonly
        self._build()
        self.refresh()

    def _build(self):
        # ── Header ───────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=PAD, pady=(PAD, 0))

        section_label(hdr, "📦  Product Inventory").pack(side="left")

        if not self.readonly:
            btn_row = ctk.CTkFrame(hdr, fg_color="transparent")
            btn_row.pack(side="right")
            accent_btn(btn_row, "+ Add Product",
                       self._open_add, width=140).pack(side="left", padx=4)
            blue_btn(btn_row, "✎ Edit",
                     self._open_edit, width=100).pack(side="left", padx=4)
            danger_btn(btn_row, "✕ Delete",
                       self._delete, width=100).pack(side="left", padx=4)

        # ── Search bar ───────────────────────────────────────
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=PAD, pady=(8, 4))
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *a: self.refresh())
        srch = make_entry(bar, placeholder="🔍  Search products…", width=280)
        srch.configure(textvariable=self.search_var)
        srch.pack(side="left")

        self.low_lbl = ctk.CTkLabel(bar, text="", font=FONT_SMALL,
                                    text_color=CLR_WARNING)
        self.low_lbl.pack(side="right", padx=8)

        # ── Table ────────────────────────────────────────────
        tf, self.tree = make_tree(self, COLS, height=20)
        tf.pack(fill="both", expand=True, padx=PAD, pady=(0, PAD))

        for col, head in zip(COLS, HEADS):
            self.tree.heading(col, text=head,
                              command=lambda c=col: self._sort(c))
            w = 60 if col == "id" else 180 if col == "name" else 110
            self.tree.column(col, width=w, minwidth=50)

        self.tree.bind("<Double-1>", lambda e: self._open_edit())

    def refresh(self):
        query = self.search_var.get().lower() if hasattr(self, "search_var") else ""
        all_rows = db.get_all_products()
        # Hide archived products from the main list
        rows = [r for r in all_rows if not r["name"].startswith("[Archived]")]
        low  = [r for r in rows if r["quantity"] <= r["low_stock"]]

        if query:
            rows = [r for r in rows if query in r["name"].lower()]

        self.tree.delete(*self.tree.get_children())
        for i, row in enumerate(rows):
            tag = "low" if row["quantity"] <= row["low_stock"] else (
                "odd" if i % 2 == 0 else "even")
            vals = (row["id"], row["name"],
                    f"{row['price']:.2f}", row["quantity"],
                    row["low_stock"], row["updated"][:16])
            self.tree.insert("", "end", values=vals, tags=(tag,))

        count = len(low)
        self.low_lbl.configure(
            text=f"⚠  {count} low-stock item{'s' if count!=1 else ''}" if count else ""
        )

    def _sort(self, col):
        items = [(self.tree.set(iid, col), iid)
                 for iid in self.tree.get_children()]
        try:
            items.sort(key=lambda x: float(x[0]))
        except ValueError:
            items.sort()
        for idx, (_, iid) in enumerate(items):
            self.tree.move(iid, "", idx)

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a product first.")
            return None
        return int(self.tree.item(sel[0])["values"][0])

    def _open_add(self):
        ProductDialog(self, title="Add New Product", on_save=self._save_add)

    def _open_edit(self):
        pid = self._selected_id()
        if pid is None:
            return
        row = db.get_product(pid)
        ProductDialog(self, title="Edit Product",
                      product=dict(row),
                      on_save=lambda d: self._save_edit(pid, d))

    def _save_add(self, data):
        try:
            db.add_product(data["name"], data["price"],
                           data["quantity"], data["low_stock"])
            self.refresh()
            show_toast(self, f"✓  '{data['name']}' added successfully")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _save_edit(self, pid, data):
        try:
            db.update_product(pid, data["name"], data["price"],
                              data["quantity"], data["low_stock"])
            self.refresh()
            show_toast(self, "✓  Product updated")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _delete(self):
        pid = self._selected_id()
        if pid is None:
            return
        row = db.get_product(pid)
        if row is None:
            messagebox.showerror("Not Found", "Product not found. Please refresh.")
            self.refresh()
            return
        name = dict(row)["name"]
        if messagebox.askyesno("Confirm Delete",
                               f"Delete '{name}'?\n\n"
                               "If this product has sales history it will be archived\n"
                               "instead of permanently deleted."):
            try:
                db.delete_product(pid)
                self.refresh()
                show_toast(self, "✓  Product deleted", color=CLR_DANGER)
            except ValueError as e:
                # Archived instead of deleted — not a crash, just inform user
                self.refresh()
                show_toast(self, "⚠  Product archived (has sales history)",
                           color=CLR_WARNING, duration=4000)
            except Exception as e:
                messagebox.showerror("Delete Error",
                                     f"Could not delete product:\n\n{e}")


# ── Add / Edit Dialog ─────────────────────────────────────────────────────────
class ProductDialog(ctk.CTkToplevel):
    """
    Resizable dialog with:
    - Scrollable body so all fields are always reachable
    - Save / Cancel buttons pinned to the bottom (never hidden)
    """

    def __init__(self, parent, title, on_save, product=None):
        super().__init__(parent)
        self.on_save = on_save
        self.product = product
        self.title(title)
        self.resizable(True, True)          # user can resize freely
        self.configure(fg_color=CLR_BG)
        self.minsize(420, 420)              # minimum so buttons never hide
        self.grab_set()
        self._build(title)
        self._center()

    def _center(self):
        self.update_idletasks()
        w, h = 460, 500
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self, title):
        # ── Outer shell: scrollable top + pinned button bar ───
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)   # button bar — never scrolls away
        self.grid_columnconfigure(0, weight=1)

        # ── Scrollable content area ───────────────────────────
        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=CLR_SURFACE,
            corner_radius=12,
            scrollbar_button_color=CLR_BORDER,
            scrollbar_button_hover_color=CLR_ACCENT,
        )
        scroll.grid(row=0, column=0, sticky="nsew", padx=16, pady=(16, 0))
        scroll.columnconfigure(0, weight=1)

        # Title inside scroll area
        ctk.CTkLabel(scroll, text=title, font=FONT_HEAD,
                     text_color=CLR_WHITE).pack(pady=(20, 4))
        ctk.CTkLabel(scroll, text="Fill in all fields, then click Save below.",
                     font=FONT_SMALL, text_color=CLR_TEXT_DIM).pack(pady=(0, 16))

        # ── Form fields ───────────────────────────────────────
        form = ctk.CTkFrame(scroll, fg_color="transparent")
        form.pack(fill="x", padx=24, pady=(0, 16))

        def labeled_entry(label, default="", placeholder=""):
            ctk.CTkLabel(form, text=label, font=FONT_SUBH,
                         text_color=CLR_TEXT_DIM, anchor="w").pack(fill="x")
            e = make_entry(form, placeholder=placeholder, width=380)
            if default != "":
                e.insert(0, str(default))
            e.pack(pady=(4, 14), fill="x")
            return e

        p = self.product or {}
        self.e_name  = labeled_entry("Product Name",
                                     p.get("name", ""),
                                     "e.g. Mango")
        self.e_price = labeled_entry("Price (SAR)",
                                     p.get("price", ""),
                                     "e.g. 2.50")
        self.e_qty   = labeled_entry("Quantity in Stock",
                                     p.get("quantity", ""),
                                     "e.g. 100")
        self.e_low   = labeled_entry("Low Stock Alert Threshold",
                                     p.get("low_stock", "10"),
                                     "e.g. 10")

        # Error label inside scroll (visible when form is short)
        self.err = ctk.CTkLabel(form, text="", font=FONT_SMALL,
                                text_color=CLR_DANGER, wraplength=360)
        self.err.pack(pady=(0, 8))

        # ── Pinned button bar at the bottom ───────────────────
        btn_bar = ctk.CTkFrame(self, fg_color=CLR_SURFACE2,
                               corner_radius=0, height=64)
        btn_bar.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        btn_bar.grid_propagate(False)
        btn_bar.columnconfigure((0, 1), weight=1)

        neutral_btn(btn_bar, "Cancel", self.destroy,
                    width=140).grid(row=0, column=0, padx=(20, 8), pady=14,
                                    sticky="e")
        accent_btn(btn_bar, "💾  Save Product", self._submit,
                   width=160).grid(row=0, column=1, padx=(8, 20), pady=14,
                                   sticky="w")

    def _submit(self):
        name  = self.e_name.get().strip()
        price = self.e_price.get().strip()
        qty   = self.e_qty.get().strip()
        low   = self.e_low.get().strip()

        if not name:
            self.err.configure(text="⚠  Product name is required"); return
        try:
            price = float(price)
            if price < 0:
                raise ValueError()
        except ValueError:
            self.err.configure(text="⚠  Price must be a positive number"); return
        try:
            qty = int(qty)
            if qty < 0:
                raise ValueError()
        except ValueError:
            self.err.configure(text="⚠  Quantity must be a non-negative integer"); return
        try:
            low = int(low)
            if low < 0:
                raise ValueError()
        except ValueError:
            self.err.configure(text="⚠  Low stock threshold must be ≥ 0"); return

        self.on_save({"name": name, "price": price,
                      "quantity": qty, "low_stock": low})
        self.destroy()
