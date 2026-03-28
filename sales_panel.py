"""
sales_panel.py - POS / checkout panel. Accessible by Admin & Cashier.
Fixed: Receipt window is scrollable and resizable; size slider added.
"""

import customtkinter as ctk
from tkinter import messagebox, ttk
import tkinter as tk
from datetime import datetime
import database as db
from theme import *
from widgets import (make_frame, section_label, make_entry, make_tree,
                     accent_btn, danger_btn, neutral_btn, blue_btn,
                     show_toast, dim_label)


class SalesPanel(ctk.CTkFrame):
    def __init__(self, master, user, **kw):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0, **kw)
        self.user = user
        self.cart = []
        self._build()
        self._load_products()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=PAD, pady=(PAD, 0))
        section_label(hdr, "🛒  Point of Sale").pack(side="left")
        dim_label(hdr, f"Cashier: {self.user['username']}").pack(
            side="right", padx=8)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=PAD, pady=PAD)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        self._build_left(body)
        self._build_right(body)

    def _build_left(self, parent):
        left = ctk.CTkFrame(parent, fg_color=CLR_SURFACE, corner_radius=10)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ctk.CTkLabel(left, text="Products", font=FONT_HEAD,
                     text_color=CLR_TEXT).pack(anchor="w", padx=14, pady=(14, 4))

        self.prod_search = ctk.StringVar()
        self.prod_search.trace_add("write", lambda *a: self._load_products())
        srch = make_entry(left, placeholder="🔍  Filter…", width=260)
        srch.configure(textvariable=self.prod_search)
        srch.pack(padx=14, pady=(0, 8), anchor="w")

        pf = ctk.CTkFrame(left, fg_color=CLR_BG, corner_radius=8)
        pf.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        self.prod_tree = ttk.Treeview(
            pf,
            columns=("id", "name", "price", "stock"),
            show="headings", height=18,
            style="Custom.Treeview"
        )
        for col, head, w in [("id","ID",50),("name","Product",200),
                               ("price","Price",90),("stock","Stock",70)]:
            self.prod_tree.heading(col, text=head)
            self.prod_tree.column(col, width=w, minwidth=40)

        vsb = ttk.Scrollbar(pf, orient="vertical",
                            command=self.prod_tree.yview,
                            style="Custom.Vertical.TScrollbar")
        self.prod_tree.configure(yscrollcommand=vsb.set)
        self.prod_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        pf.rowconfigure(0, weight=1)
        pf.columnconfigure(0, weight=1)

        self.prod_tree.tag_configure("odd",  background=CLR_ROW_ODD)
        self.prod_tree.tag_configure("even", background=CLR_ROW_EVEN)
        self.prod_tree.tag_configure("zero", background="#3B1A1A",
                                     foreground="#FCA5A5")

        qrow = ctk.CTkFrame(left, fg_color="transparent")
        qrow.pack(padx=14, pady=(0, 14), fill="x")
        ctk.CTkLabel(qrow, text="Qty:", font=FONT_SUBH,
                     text_color=CLR_TEXT_DIM).pack(side="left")
        self.qty_var = ctk.StringVar(value="1")
        self.qty_entry = make_entry(qrow, width=70)
        self.qty_entry.configure(textvariable=self.qty_var)
        self.qty_entry.pack(side="left", padx=8)
        accent_btn(qrow, "+ Add to Cart",
                   self._add_to_cart, width=150).pack(side="left")
        self.prod_tree.bind("<Double-1>", lambda e: self._add_to_cart())

    def _build_right(self, parent):
        right = ctk.CTkFrame(parent, fg_color=CLR_SURFACE, corner_radius=10)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        ctk.CTkLabel(right, text="Cart", font=FONT_HEAD,
                     text_color=CLR_TEXT).grid(row=0, column=0,
                     sticky="w", padx=14, pady=(14, 4))

        cf = ctk.CTkFrame(right, fg_color=CLR_BG, corner_radius=8)
        cf.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 8))

        self.cart_tree = ttk.Treeview(
            cf,
            columns=("name", "qty", "price", "subtotal"),
            show="headings", height=12,
            style="Custom.Treeview"
        )
        for col, head, w in [("name","Item",160),("qty","Qty",50),
                               ("price","Price",80),("subtotal","Total",90)]:
            self.cart_tree.heading(col, text=head)
            self.cart_tree.column(col, width=w, minwidth=40)

        self.cart_tree.tag_configure("odd",  background=CLR_ROW_ODD)
        self.cart_tree.tag_configure("even", background=CLR_ROW_EVEN)
        cf.pack_propagate(False)
        self.cart_tree.pack(fill="both", expand=True)

        ca = ctk.CTkFrame(right, fg_color="transparent")
        ca.grid(row=2, column=0, padx=14, pady=(0, 8), sticky="ew")
        neutral_btn(ca, "✕ Remove",    self._remove_item, width=100).pack(
            side="left", padx=4)
        danger_btn(ca,  "🗑 Clear Cart", self._clear_cart,  width=110).pack(
            side="left", padx=4)

        tot = ctk.CTkFrame(right, fg_color=CLR_SURFACE2, corner_radius=8)
        tot.grid(row=3, column=0, padx=14, pady=(0, 14), sticky="ew")

        def tot_row(label, var, big=False):
            r = ctk.CTkFrame(tot, fg_color="transparent")
            r.pack(fill="x", padx=14, pady=3)
            font = ("Segoe UI", 14, "bold") if big else FONT_BODY
            ctk.CTkLabel(r, text=label, font=font,
                         text_color=CLR_TEXT_DIM).pack(side="left")
            lbl = ctk.CTkLabel(r, text="SAR 0.00", font=font,
                               text_color=CLR_ACCENT if big else CLR_TEXT)
            lbl.configure(textvariable=var)
            lbl.pack(side="right")

        self.sub_var   = tk.StringVar(value="SAR  0.00")
        self.vat_var   = tk.StringVar(value="SAR  0.00")
        self.total_var = tk.StringVar(value="SAR  0.00")

        ctk.CTkFrame(tot, fg_color="transparent", height=8).pack()
        tot_row("Subtotal",   self.sub_var)
        tot_row("VAT (15%)",  self.vat_var)
        ctk.CTkFrame(tot, fg_color=CLR_BORDER, height=1).pack(
            fill="x", padx=14, pady=4)
        tot_row("TOTAL",      self.total_var, big=True)
        ctk.CTkFrame(tot, fg_color="transparent", height=8).pack()

        accent_btn(right, "💳  Process & Print Receipt",
                   self._checkout, width=280).grid(
            row=4, column=0, padx=14, pady=(0, 16))

    def _load_products(self):
        q = self.prod_search.get().lower() if hasattr(self, "prod_search") else ""
        rows = db.get_all_products()
        if q:
            rows = [r for r in rows if q in r["name"].lower()]
        self.prod_tree.delete(*self.prod_tree.get_children())
        for i, row in enumerate(rows):
            tag = "zero" if row["quantity"] == 0 else (
                "odd" if i % 2 == 0 else "even")
            self.prod_tree.insert(
                "", "end",
                values=(row["id"], row["name"],
                        f"SAR {row['price']:.2f}", row["quantity"]),
                iid=str(row["id"]),
                tags=(tag,)
            )

    def _add_to_cart(self):
        sel = self.prod_tree.selection()
        if not sel:
            show_toast(self, "⚠  Select a product first", color=CLR_WARNING)
            return
        pid = int(sel[0])
        row = db.get_product(pid)
        if not row:
            return
        try:
            qty = int(self.qty_var.get())
            if qty <= 0:
                raise ValueError()
        except ValueError:
            show_toast(self, "⚠  Enter a valid quantity", color=CLR_WARNING)
            return

        already = sum(i["quantity"] for i in self.cart if i["product_id"] == pid)
        if already + qty > row["quantity"]:
            show_toast(self,
                       f"⚠  Only {row['quantity'] - already} left in stock",
                       color=CLR_WARNING)
            return

        for item in self.cart:
            if item["product_id"] == pid:
                item["quantity"] += qty
                item["subtotal"] = round(item["quantity"] * item["price"], 2)
                self._refresh_cart()
                return

        self.cart.append({
            "product_id": pid,
            "name":       row["name"],
            "price":      row["price"],
            "quantity":   qty,
            "subtotal":   round(row["price"] * qty, 2),
        })
        self._refresh_cart()
        show_toast(self, f"✓  {row['name']} × {qty} added")

    def _refresh_cart(self):
        self.cart_tree.delete(*self.cart_tree.get_children())
        for i, item in enumerate(self.cart):
            tag = "odd" if i % 2 == 0 else "even"
            self.cart_tree.insert("", "end", values=(
                item["name"], item["quantity"],
                f"SAR {item['price']:.2f}",
                f"SAR {item['subtotal']:.2f}"
            ), tags=(tag,))
        self._update_totals()

    def _update_totals(self):
        sub = sum(i["subtotal"] for i in self.cart)
        vat = round(sub * 0.15, 2)
        tot = round(sub + vat, 2)
        self.sub_var.set(f"SAR  {sub:.2f}")
        self.vat_var.set(f"SAR  {vat:.2f}")
        self.total_var.set(f"SAR  {tot:.2f}")

    def _remove_item(self):
        sel = self.cart_tree.selection()
        if not sel:
            return
        idx = self.cart_tree.index(sel[0])
        del self.cart[idx]
        self._refresh_cart()

    def _clear_cart(self):
        if self.cart and messagebox.askyesno("Clear Cart",
                                             "Remove all items from cart?"):
            self.cart.clear()
            self._refresh_cart()

    def _checkout(self):
        if not self.cart:
            show_toast(self, "⚠  Cart is empty", color=CLR_WARNING)
            return
        sub   = sum(i["subtotal"] for i in self.cart)
        vat   = round(sub * 0.15, 2)
        total = round(sub + vat, 2)

        sale_id = db.create_sale(self.cart, total, self.user["id"])
        self._load_products()
        receipt = self.cart.copy()
        self.cart.clear()
        self._refresh_cart()
        ReceiptWindow(self, sale_id, receipt, sub, vat, total, self.user)


# ── Receipt window ────────────────────────────────────────────────────────────
class ReceiptWindow(ctk.CTkToplevel):
    """
    Fully scrollable receipt window.
    - Resizable by dragging any edge
    - Font-size slider at the top to zoom in/out
    - Copy-to-clipboard button always visible in the pinned footer
    """

    MIN_W, MIN_H = 420, 480

    def __init__(self, parent, sale_id, items, sub, vat, total, user):
        super().__init__(parent)
        self.title(f"Receipt — SALE-{sale_id:05d}")
        self.resizable(True, True)
        self.minsize(self.MIN_W, self.MIN_H)
        self.configure(fg_color=CLR_BG)
        self.grab_set()

        self.sale_id = sale_id
        self.items   = items
        self.sub     = sub
        self.vat     = vat
        self.total   = total
        self.user    = user
        self._font_size = tk.IntVar(value=10)

        self._build()
        self._center()

    def _center(self):
        self.update_idletasks()
        w, h = 480, 620
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ── Layout: toolbar / scrollable body / pinned footer ─────────
    def _build(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Top toolbar ───────────────────────────────────────
        toolbar = ctk.CTkFrame(self, fg_color=CLR_SURFACE2,
                               corner_radius=0, height=46)
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.grid_propagate(False)

        ctk.CTkLabel(toolbar, text="Font size:",
                     font=FONT_SMALL, text_color=CLR_TEXT_DIM).pack(
            side="left", padx=(14, 4), pady=10)

        self._size_lbl = ctk.CTkLabel(toolbar, text="10 pt",
                                      font=FONT_SMALL, text_color=CLR_TEXT,
                                      width=38)
        self._size_lbl.pack(side="left", pady=10)

        slider = ctk.CTkSlider(
            toolbar,
            from_=8, to=18, number_of_steps=10,
            variable=self._font_size,
            command=self._on_font_change,
            fg_color=CLR_BORDER,
            progress_color=CLR_ACCENT,
            button_color=CLR_ACCENT,
            button_hover_color=CLR_ACCENT_DARK,
            width=160,
        )
        slider.pack(side="left", padx=6, pady=10)

        ctk.CTkLabel(toolbar, text="  ↔ drag edges to resize",
                     font=FONT_SMALL, text_color=CLR_TEXT_DIM).pack(
            side="left", pady=10)

        # ── Scrollable body ───────────────────────────────────
        self._scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=CLR_SURFACE,
            corner_radius=0,
            scrollbar_button_color=CLR_BORDER,
            scrollbar_button_hover_color=CLR_ACCENT,
        )
        self._scroll.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self._scroll.columnconfigure(0, weight=1)

        self._build_receipt_body()

        # ── Pinned footer ─────────────────────────────────────
        footer = ctk.CTkFrame(self, fg_color=CLR_SURFACE2,
                              corner_radius=0, height=60)
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_propagate(False)
        footer.columnconfigure((0, 1), weight=1)

        blue_btn(footer, "📋  Copy Receipt",
                 self._copy_receipt, width=160).grid(
            row=0, column=0, padx=(20, 8), pady=12, sticky="e")
        accent_btn(footer, "✓  Done",
                   self.destroy, width=120).grid(
            row=0, column=1, padx=(8, 20), pady=12, sticky="w")

    def _build_receipt_body(self):
        """Render all receipt content inside the scrollable area."""
        # Clear previous render (needed when font size changes)
        for w in self._scroll.winfo_children():
            w.destroy()

        fs   = self._font_size.get()
        mono = ("Consolas", fs)
        bold = ("Segoe UI", fs + 4, "bold")
        sub  = ("Segoe UI", fs - 1)
        now  = datetime.now().strftime("%d %b %Y  %H:%M")

        pad = {"padx": 28}

        # ── Store header ──────────────────────────────────────
        ctk.CTkLabel(self._scroll, text="🥦  FreshMart POS",
                     font=bold, text_color=CLR_ACCENT).pack(pady=(24, 2), **pad)
        ctk.CTkLabel(self._scroll, text="Fruit & Vegetable Sales",
                     font=sub, text_color=CLR_TEXT_DIM).pack(**pad)
        self._divider()

        # ── Meta ──────────────────────────────────────────────
        meta = [
            ("Receipt #",  f"SALE-{self.sale_id:05d}"),
            ("Date",       now),
            ("Cashier",    self.user["username"]),
        ]
        for k, v in meta:
            r = ctk.CTkFrame(self._scroll, fg_color="transparent")
            r.pack(fill="x", **pad, pady=1)
            ctk.CTkLabel(r, text=k, font=sub,
                         text_color=CLR_TEXT_DIM).pack(side="left")
            ctk.CTkLabel(r, text=v, font=sub,
                         text_color=CLR_TEXT).pack(side="right")

        self._divider()

        # ── Column header ─────────────────────────────────────
        ctk.CTkLabel(self._scroll,
                     text=f"{'ITEM':<20} {'QTY':>4}  {'PRICE':>8}  {'TOTAL':>9}",
                     font=mono, text_color=CLR_TEXT_DIM).pack(anchor="w", **pad)
        ctk.CTkLabel(self._scroll, text="─" * 48,
                     font=mono, text_color=CLR_BORDER).pack(anchor="w", **pad)

        # ── Line items ────────────────────────────────────────
        for item in self.items:
            name = item["name"][:20]
            line = (f"{name:<20} {item['quantity']:>4}  "
                    f"SAR{item['price']:>5.2f}  "
                    f"SAR{item['subtotal']:>6.2f}")
            ctk.CTkLabel(self._scroll, text=line,
                         font=mono, text_color=CLR_TEXT).pack(anchor="w", **pad)

        self._divider()

        # ── Totals ────────────────────────────────────────────
        def tot_row(k, v, accent=False):
            r = ctk.CTkFrame(self._scroll, fg_color="transparent")
            r.pack(fill="x", **pad, pady=2)
            f = ("Segoe UI", fs + 2, "bold") if accent else sub
            c = CLR_ACCENT if accent else CLR_TEXT
            ctk.CTkLabel(r, text=k, font=f,
                         text_color=CLR_TEXT_DIM).pack(side="left")
            ctk.CTkLabel(r, text=v, font=f,
                         text_color=c).pack(side="right")

        tot_row("Subtotal",  f"SAR {self.sub:.2f}")
        tot_row("VAT (15%)", f"SAR {self.vat:.2f}")
        ctk.CTkFrame(self._scroll, fg_color=CLR_BORDER, height=1).pack(
            fill="x", padx=28, pady=6)
        tot_row("TOTAL",     f"SAR {self.total:.2f}", accent=True)

        self._divider()

        ctk.CTkLabel(self._scroll,
                     text="Thank you for shopping with us! 🌿",
                     font=sub, text_color=CLR_TEXT_DIM).pack(pady=(0, 24), **pad)

    def _divider(self):
        ctk.CTkFrame(self._scroll, fg_color=CLR_BORDER, height=1).pack(
            fill="x", padx=28, pady=10)

    def _on_font_change(self, val):
        size = int(float(val))
        self._size_lbl.configure(text=f"{size} pt")
        self._build_receipt_body()

    def _copy_receipt(self):
        now  = datetime.now().strftime("%d %b %Y  %H:%M")
        txt  = f"{'FreshMart POS':^48}\n"
        txt += f"{'Fruit & Vegetable Sales':^48}\n"
        txt += "─" * 48 + "\n"
        txt += f"Receipt #: SALE-{self.sale_id:05d}\n"
        txt += f"Date     : {now}\n"
        txt += f"Cashier  : {self.user['username']}\n"
        txt += "─" * 48 + "\n"
        txt += f"{'ITEM':<20} {'QTY':>4}  {'PRICE':>8}  {'TOTAL':>9}\n"
        txt += "─" * 48 + "\n"
        for item in self.items:
            txt += (f"{item['name'][:20]:<20} {item['quantity']:>4}  "
                    f"SAR{item['price']:>5.2f}  "
                    f"SAR{item['subtotal']:>6.2f}\n")
        txt += "─" * 48 + "\n"
        txt += f"{'Subtotal':<38} SAR {self.sub:>7.2f}\n"
        txt += f"{'VAT (15%)':<38} SAR {self.vat:>7.2f}\n"
        txt += f"{'TOTAL':<38} SAR {self.total:>7.2f}\n"
        txt += "─" * 48 + "\n"
        txt += "Thank you for shopping with us!\n"

        self.clipboard_clear()
        self.clipboard_append(txt)
        show_toast(self, "✓ Receipt copied to clipboard")
