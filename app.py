"""
app.py - Main application shell.
Handles: root window, login routing, admin/cashier dashboards with sidebar.
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
import database as db
from theme import *
from widgets import show_toast

# Panels
from login         import LoginScreen
from products_panel import ProductsPanel
from sales_panel    import SalesPanel
from reports_panel  import ReportsPanel
from users_panel    import UsersPanel


# ────────────────────────────────────────────────────────────────
class App(ctk.CTk):
    """Root window – manages login ↔ dashboard transitions."""

    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.title("FreshMart POS – Fruit & Vegetable Sales")
        self.geometry("1280x760")
        self.minsize(1024, 680)
        self.configure(fg_color=CLR_BG)

        # ttk style (Treeview dark theme)
        self._style = ttk.Style(self)
        from theme import apply_treeview_style
        apply_treeview_style(self._style)

        db.init_db()
        self._show_login()

    # ── Transitions ──────────────────────────────────────────
    def _show_login(self):
        self._clear()
        self._login_screen = LoginScreen(self, on_success=self._on_login)
        self._login_screen.pack(fill="both", expand=True)

    def _on_login(self, user: dict):
        self._clear()
        if user["role"] == "admin":
            AdminDashboard(self, user=user,
                           on_logout=self._show_login).pack(
                fill="both", expand=True)
        else:
            CashierDashboard(self, user=user,
                             on_logout=self._show_login).pack(
                fill="both", expand=True)

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()


# ────────────────────────────────────────────────────────────────
class _BaseDashboard(ctk.CTkFrame):
    """
    Sidebar + content area base class.
    Subclasses register nav items via self._add_nav(icon, label, widget_class).
    """
    NAV_W = 220

    def __init__(self, master, user, on_logout, **kw):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0, **kw)
        self.user      = user
        self.on_logout = on_logout
        self._panels   = {}   # label -> widget
        self._nav_btns = {}
        self._build_shell()
        self._build_nav()

    def _build_shell(self):
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, fg_color=CLR_SURFACE,
                                    corner_radius=0, width=self.NAV_W)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Content area
        self.content = ctk.CTkFrame(self, fg_color=CLR_BG, corner_radius=0)
        self.content.pack(side="left", fill="both", expand=True)

        # ── Sidebar header ────────────────────────────────────
        logo_f = ctk.CTkFrame(self.sidebar, fg_color=CLR_ACCENT,
                              width=48, height=48, corner_radius=12)
        logo_f.pack(pady=(24, 0))
        logo_f.pack_propagate(False)
        ctk.CTkLabel(logo_f, text="🥦", font=("Segoe UI", 26)).pack(expand=True)

        ctk.CTkLabel(self.sidebar, text="FreshMart",
                     font=("Segoe UI", 16, "bold"),
                     text_color=CLR_WHITE).pack(pady=(8, 2))
        ctk.CTkLabel(self.sidebar, text="POS System",
                     font=FONT_SMALL, text_color=CLR_TEXT_DIM).pack()

        ctk.CTkFrame(self.sidebar, fg_color=CLR_BORDER,
                     height=1).pack(fill="x", padx=20, pady=16)

        # Nav scroll area
        self.nav_area = ctk.CTkScrollableFrame(
            self.sidebar, fg_color="transparent",
            scrollbar_button_color=CLR_BORDER)
        self.nav_area.pack(fill="both", expand=True)

        # ── Bottom: user badge + logout ───────────────────────
        ctk.CTkFrame(self.sidebar, fg_color=CLR_BORDER,
                     height=1).pack(fill="x", padx=20, pady=8)

        role_color = CLR_ACCENT if self.user["role"] == "admin" else CLR_ACCENT2
        user_card = ctk.CTkFrame(self.sidebar, fg_color=CLR_SURFACE2,
                                 corner_radius=10)
        user_card.pack(fill="x", padx=12, pady=(0, 6))
        ctk.CTkLabel(user_card,
                     text=f"  {self.user['username']}",
                     font=FONT_SUBH, text_color=CLR_WHITE,
                     anchor="w").pack(anchor="w", padx=8, pady=(8, 2))
        ctk.CTkLabel(user_card,
                     text=f"  {self.user['role'].upper()}",
                     font=FONT_SMALL, text_color=role_color,
                     anchor="w").pack(anchor="w", padx=8, pady=(0, 8))

        ctk.CTkButton(
            self.sidebar, text="⏻  Sign Out",
            command=self._logout,
            fg_color="#2A1A1A", hover_color="#4A2020",
            text_color=CLR_DANGER, font=FONT_SUBH,
            height=36, corner_radius=8,
        ).pack(fill="x", padx=12, pady=(0, 16))

    def _add_nav(self, icon: str, label: str, widget_class, **widget_kw):
        """Register a nav item and lazily create its panel."""
        btn = ctk.CTkButton(
            self.nav_area,
            text=f"  {icon}  {label}",
            anchor="w",
            fg_color="transparent",
            hover_color=CLR_SURFACE2,
            text_color=CLR_TEXT_DIM,
            font=FONT_SUBH,
            height=40,
            corner_radius=8,
            command=lambda lbl=label: self._switch(lbl),
        )
        btn.pack(fill="x", padx=8, pady=2)
        self._nav_btns[label]  = btn
        self._panels[label]    = (widget_class, widget_kw)   # lazy

    def _switch(self, label: str):
        # Deselect all
        for lbl, btn in self._nav_btns.items():
            btn.configure(fg_color="transparent", text_color=CLR_TEXT_DIM)

        # Highlight active
        self._nav_btns[label].configure(
            fg_color=CLR_SURFACE2, text_color=CLR_ACCENT)

        # Hide all panels
        for w in self.content.winfo_children():
            w.pack_forget()

        # Show / create target panel
        entry = self._panels[label]
        if isinstance(entry, tuple):                # lazy – first visit
            cls, kw = entry
            widget = cls(self.content, **kw)
            self._panels[label] = widget
        else:
            widget = entry
        widget.pack(fill="both", expand=True)

        # Call refresh if the panel has one
        if hasattr(widget, "refresh"):
            widget.refresh()

    def _build_nav(self):
        raise NotImplementedError

    def _logout(self):
        if messagebox.askyesno("Sign Out", "Sign out of FreshMart POS?"):
            self.on_logout()


# ────────────────────────────────────────────────────────────────
class AdminDashboard(_BaseDashboard):
    def _build_nav(self):
        self._add_nav("📦", "Products",  ProductsPanel,
                      readonly=False)
        self._add_nav("🛒", "Sales / POS", SalesPanel,
                      user=self.user)
        self._add_nav("📊", "Reports",   ReportsPanel)
        self._add_nav("👤", "Users",     UsersPanel,
                      current_user=self.user)
        self._add_nav("🏪", "Inventory", _InventoryPanel)

        # default page
        self._switch("Sales / POS")


class CashierDashboard(_BaseDashboard):
    def _build_nav(self):
        self._add_nav("🛒", "Sales / POS",   SalesPanel,
                      user=self.user)
        self._add_nav("📦", "View Products", ProductsPanel,
                      readonly=True)

        self._switch("Sales / POS")


# ────────────────────────────────────────────────────────────────
class _InventoryPanel(ctk.CTkFrame):
    """Quick inventory overview with low-stock alerts (Admin only)."""

    def __init__(self, master, **kw):
        super().__init__(master, fg_color=CLR_BG, corner_radius=0, **kw)
        self._build()
        self.refresh()

    def _build(self):
        from widgets import section_label, make_tree, accent_btn

        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=PAD, pady=(PAD, 0))
        section_label(hdr, "🏪  Inventory Overview").pack(side="left")
        accent_btn(hdr, "↺ Refresh", self.refresh, width=100).pack(side="right")

        # KPI row
        kpi = ctk.CTkFrame(self, fg_color="transparent")
        kpi.pack(fill="x", padx=PAD, pady=8)
        from widgets import stat_card
        _, self._lbl_total   = stat_card(kpi, "Total Products", "—",
                                          color=CLR_ACCENT2, width=170)
        self._lbl_total.master.pack(side="left", padx=6)

        _, self._lbl_low     = stat_card(kpi, "Low Stock Items", "—",
                                          color=CLR_WARNING, width=170)
        self._lbl_low.master.pack(side="left", padx=6)

        _, self._lbl_out     = stat_card(kpi, "Out of Stock", "—",
                                          color=CLR_DANGER, width=170)
        self._lbl_out.master.pack(side="left", padx=6)

        _, self._lbl_val     = stat_card(kpi, "Stock Value (SAR)", "—",
                                          color=CLR_ACCENT, width=200)
        self._lbl_val.master.pack(side="left", padx=6)

        # ── Low-stock alert table ──────────────────────────────
        ctk.CTkLabel(self, text="⚠  Low Stock Alerts",
                     font=FONT_HEAD, text_color=CLR_WARNING).pack(
            anchor="w", padx=PAD, pady=(8, 4))

        cols  = ("id", "name", "price", "quantity", "low_stock")
        heads = ("ID", "Product", "Price", "Current Stock", "Threshold")
        tf, self.alert_tree = make_tree(self, cols, height=8)
        tf.pack(fill="x", padx=PAD, pady=(0, 8))
        for col, head, w in zip(cols, heads, (50, 200, 90, 120, 110)):
            self.alert_tree.heading(col, text=head)
            self.alert_tree.column(col, width=w, minwidth=40)

        # ── All products table ────────────────────────────────
        ctk.CTkLabel(self, text="All Products",
                     font=FONT_HEAD, text_color=CLR_TEXT).pack(
            anchor="w", padx=PAD, pady=(8, 4))

        tf2, self.all_tree = make_tree(self, cols, height=10)
        tf2.pack(fill="both", expand=True, padx=PAD, pady=(0, PAD))
        for col, head, w in zip(cols, heads, (50, 200, 90, 120, 110)):
            self.all_tree.heading(col, text=head)
            self.all_tree.column(col, width=w, minwidth=40)

    def refresh(self):
        products = db.get_all_products()
        low      = db.get_low_stock_products()
        out      = [p for p in products if p["quantity"] == 0]
        value    = sum(p["price"] * p["quantity"] for p in products)

        self._lbl_total.configure(text=str(len(products)))
        self._lbl_low.configure(text=str(len(low)))
        self._lbl_out.configure(text=str(len(out)))
        self._lbl_val.configure(text=f"{value:.2f}")

        # Alert tree
        self.alert_tree.delete(*self.alert_tree.get_children())
        for i, r in enumerate(low):
            tag = "low" if r["quantity"] == 0 else (
                "odd" if i % 2 == 0 else "even")
            self.alert_tree.insert("", "end", values=(
                r["id"], r["name"], f"SAR {r['price']:.2f}",
                r["quantity"], r["low_stock"]
            ), tags=(tag,))

        # All tree
        self.all_tree.delete(*self.all_tree.get_children())
        for i, r in enumerate(products):
            tag = "low" if r["quantity"] <= r["low_stock"] else (
                "odd" if i % 2 == 0 else "even")
            self.all_tree.insert("", "end", values=(
                r["id"], r["name"], f"SAR {r['price']:.2f}",
                r["quantity"], r["low_stock"]
            ), tags=(tag,))
