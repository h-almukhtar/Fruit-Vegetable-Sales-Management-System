"""
theme.py - Centralized color palette, fonts, and style helpers.
"""

# ── Palette ────────────────────────────────────
CLR_BG          = "#0F1923"   # deep navy – main background
CLR_SURFACE     = "#162433"   # card surface
CLR_SURFACE2    = "#1E3145"   # slightly lighter surface
CLR_BORDER      = "#2A4560"   # subtle border
CLR_ACCENT      = "#22C55E"   # fresh green – primary accent
CLR_ACCENT_DARK = "#16A34A"   # darker green hover
CLR_ACCENT2     = "#38BDF8"   # sky blue – secondary accent
CLR_WARNING     = "#F59E0B"   # amber – warnings
CLR_DANGER      = "#EF4444"   # red – destructive actions
CLR_TEXT        = "#E2EAF0"   # primary text
CLR_TEXT_DIM    = "#7A9BB5"   # muted text
CLR_WHITE       = "#FFFFFF"
CLR_ROW_ODD     = "#162433"
CLR_ROW_EVEN    = "#1A2D40"
CLR_ROW_SEL     = "#1E4D2B"   # selected row bg

# ── Fonts ──────────────────────────────────────
FONT_TITLE  = ("Segoe UI", 22, "bold")
FONT_HEAD   = ("Segoe UI", 14, "bold")
FONT_SUBH   = ("Segoe UI", 11, "bold")
FONT_BODY   = ("Segoe UI", 10)
FONT_SMALL  = ("Segoe UI",  9)
FONT_MONO   = ("Consolas",  10)

# ── Padding / sizes ────────────────────────────
PAD         = 12
PAD_SM      = 6
BTN_H       = 34
ENTRY_H     = 32

# ── ttk Treeview style dict ────────────────────
def apply_treeview_style(style):
    """
    Apply dark theme to ttk.Style for Treeview.
    Call once after creating a Tk/CTk root.
    """
    style.theme_use("clam")

    style.configure("Custom.Treeview",
        background=CLR_ROW_ODD,
        foreground=CLR_TEXT,
        fieldbackground=CLR_ROW_ODD,
        rowheight=28,
        font=FONT_BODY,
        borderwidth=0,
        relief="flat",
    )
    style.configure("Custom.Treeview.Heading",
        background=CLR_SURFACE2,
        foreground=CLR_ACCENT2,
        font=FONT_SUBH,
        borderwidth=0,
        relief="flat",
    )
    style.map("Custom.Treeview",
        background=[("selected", CLR_ROW_SEL)],
        foreground=[("selected", CLR_WHITE)],
    )
    style.map("Custom.Treeview.Heading",
        background=[("active", CLR_BORDER)],
    )

    # Scrollbar
    style.configure("Custom.Vertical.TScrollbar",
        background=CLR_SURFACE2,
        troughcolor=CLR_BG,
        arrowcolor=CLR_TEXT_DIM,
        borderwidth=0,
    )
