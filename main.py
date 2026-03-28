"""
main.py - Entry point for FreshMart POS.

How to run:
    python main.py

Requirements:
    pip install customtkinter openpyxl

Default credentials:
    Admin   → username: admin    | password: admin123
    Cashier → username: cashier  | password: cashier123
"""

import sys
import os

# Ensure imports resolve from this directory
sys.path.insert(0, os.path.dirname(__file__))

from app import App


if __name__ == "__main__":
    app = App()
    app.mainloop()
