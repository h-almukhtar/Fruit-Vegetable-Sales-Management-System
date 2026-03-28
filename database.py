"""
database.py - Database layer for Fruit & Vegetable Sales Management System
Handles all SQLite operations: initialization, CRUD, queries.
"""

import sqlite3
import hashlib
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "sales_system.db")


# ──────────────────────────────────────────────
# Connection helper
# ──────────────────────────────────────────────
def get_connection():
    """Return a connection with row_factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password: str) -> str:
    """SHA-256 hash a password."""
    return hashlib.sha256(password.encode()).hexdigest()


# ──────────────────────────────────────────────
# Database initialisation
# ──────────────────────────────────────────────
def init_db():
    """Create tables and seed default admin/cashier accounts."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT    NOT NULL UNIQUE,
                password TEXT    NOT NULL,
                role     TEXT    NOT NULL CHECK(role IN ('admin','cashier')),
                created  TEXT    DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS products (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                name         TEXT    NOT NULL UNIQUE,
                price        REAL    NOT NULL CHECK(price >= 0),
                quantity     INTEGER NOT NULL CHECK(quantity >= 0),
                low_stock    INTEGER NOT NULL DEFAULT 10,
                updated      TEXT    DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS sales (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                date       TEXT    NOT NULL DEFAULT (datetime('now')),
                total      REAL    NOT NULL,
                cashier_id INTEGER REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS sale_items (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id    INTEGER NOT NULL REFERENCES sales(id),
                product_id INTEGER NOT NULL REFERENCES products(id),
                name       TEXT    NOT NULL,
                price      REAL    NOT NULL,
                quantity   INTEGER NOT NULL,
                subtotal   REAL    NOT NULL
            );
        """)

        # Seed default users if they don't exist
        seeds = [
            ("admin",   "admin123",    "admin"),
            ("cashier", "cashier123",  "cashier"),
        ]
        for uname, pwd, role in seeds:
            existing = conn.execute(
                "SELECT id FROM users WHERE username=?", (uname,)
            ).fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO users (username, password, role) VALUES (?,?,?)",
                    (uname, hash_password(pwd), role)
                )

        # Seed sample products if empty
        if not conn.execute("SELECT 1 FROM products LIMIT 1").fetchone():
            sample = [
                ("Apple",      1.50, 100),
                ("Banana",     0.75, 150),
                ("Orange",     1.20, 80),
                ("Mango",      2.00, 60),
                ("Strawberry", 3.50, 40),
                ("Grapes",     2.80, 70),
                ("Watermelon", 4.00, 25),
                ("Carrot",     0.90, 120),
                ("Tomato",     1.10, 90),
                ("Potato",     0.60, 200),
                ("Onion",      0.80, 180),
                ("Spinach",    1.30, 55),
                ("Broccoli",   1.80, 45),
                ("Cucumber",   0.95, 75),
                ("Lettuce",    1.40, 50),
            ]
            conn.executemany(
                "INSERT INTO products (name, price, quantity) VALUES (?,?,?)",
                sample
            )


# ──────────────────────────────────────────────
# USER operations
# ──────────────────────────────────────────────
def authenticate(username: str, password: str):
    """Return user Row if credentials match, else None."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, hash_password(password))
        ).fetchone()


def get_all_users():
    with get_connection() as conn:
        return conn.execute(
            "SELECT id, username, role, created FROM users ORDER BY id"
        ).fetchall()


def add_user(username: str, password: str, role: str):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?,?,?)",
            (username, hash_password(password), role)
        )


def update_user_password(user_id: int, new_password: str):
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET password=? WHERE id=?",
            (hash_password(new_password), user_id)
        )


def delete_user(user_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM users WHERE id=?", (user_id,))


# ──────────────────────────────────────────────
# PRODUCT operations
# ──────────────────────────────────────────────
def get_all_products():
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM products ORDER BY name"
        ).fetchall()


def get_product(product_id: int):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM products WHERE id=?", (product_id,)
        ).fetchone()


def add_product(name: str, price: float, quantity: int, low_stock: int = 10):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO products (name, price, quantity, low_stock) VALUES (?,?,?,?)",
            (name, price, quantity, low_stock)
        )


def update_product(product_id: int, name: str, price: float, quantity: int, low_stock: int):
    with get_connection() as conn:
        conn.execute(
            """UPDATE products SET name=?, price=?, quantity=?, low_stock=?,
               updated=datetime('now') WHERE id=?""",
            (name, price, quantity, low_stock, product_id)
        )


def delete_product(product_id: int):
    """
    Delete a product. If it has sales history, we cannot delete it outright
    (foreign key constraint from sale_items). In that case we mark it as
    archived by setting quantity=-1 and prepending '[Archived] ' to the name,
    so the sales history stays intact. Callers receive a clear message.
    """
    with get_connection() as conn:
        # Check if any sale_items reference this product
        linked = conn.execute(
            "SELECT COUNT(*) FROM sale_items WHERE product_id=?",
            (product_id,)
        ).fetchone()[0]

        if linked > 0:
            # Cannot hard-delete — archive it instead so FK is preserved
            conn.execute(
                "UPDATE products SET name = CASE "
                "WHEN name NOT LIKE ? THEN ? || name ELSE name END, "
                "quantity = 0, updated = datetime('now') WHERE id = ?",
                ("[Archived]%", "[Archived] ", product_id)
            )
            conn.commit()   # commit BEFORE raising so archive is saved
            raise ValueError(
                "This product has sales history and cannot be fully deleted.\n"
                "It has been archived and hidden from the active product list."
            )
        else:
            conn.execute("DELETE FROM products WHERE id=?", (product_id,))


def get_low_stock_products():
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM products WHERE quantity <= low_stock ORDER BY quantity"
        ).fetchall()


def deduct_stock(product_id: int, qty: int):
    with get_connection() as conn:
        conn.execute(
            "UPDATE products SET quantity = quantity - ? WHERE id=?",
            (qty, product_id)
        )


# ──────────────────────────────────────────────
# SALES operations
# ──────────────────────────────────────────────
def create_sale(cart: list, total: float, cashier_id: int) -> int:
    """
    cart: list of dicts with keys: product_id, name, price, quantity, subtotal
    Returns the new sale_id.
    """
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO sales (total, cashier_id) VALUES (?,?)",
            (total, cashier_id)
        )
        sale_id = cur.lastrowid
        for item in cart:
            conn.execute(
                """INSERT INTO sale_items
                   (sale_id, product_id, name, price, quantity, subtotal)
                   VALUES (?,?,?,?,?,?)""",
                (sale_id, item["product_id"], item["name"],
                 item["price"], item["quantity"], item["subtotal"])
            )
            # Deduct stock within same connection/transaction
            conn.execute(
                "UPDATE products SET quantity = quantity - ? WHERE id=?",
                (item["quantity"], item["product_id"])
            )
        return sale_id


def get_sale(sale_id: int):
    with get_connection() as conn:
        sale  = conn.execute("SELECT * FROM sales WHERE id=?", (sale_id,)).fetchone()
        items = conn.execute(
            "SELECT * FROM sale_items WHERE sale_id=?", (sale_id,)
        ).fetchall()
        return sale, items


def get_all_sales(date_filter: str = None):
    with get_connection() as conn:
        if date_filter:
            return conn.execute(
                """SELECT s.id, s.date, s.total, u.username AS cashier
                   FROM sales s LEFT JOIN users u ON s.cashier_id=u.id
                   WHERE DATE(s.date)=? ORDER BY s.date DESC""",
                (date_filter,)
            ).fetchall()
        return conn.execute(
            """SELECT s.id, s.date, s.total, u.username AS cashier
               FROM sales s LEFT JOIN users u ON s.cashier_id=u.id
               ORDER BY s.date DESC"""
        ).fetchall()


# ──────────────────────────────────────────────
# REPORT queries
# ──────────────────────────────────────────────
def get_summary():
    """Return overall totals."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as cnt, COALESCE(SUM(total),0) as revenue FROM sales"
        ).fetchone()
        return dict(row)


def get_daily_sales():
    with get_connection() as conn:
        return conn.execute(
            """SELECT DATE(date) as day,
                      COUNT(*) as transactions,
                      SUM(total) as revenue
               FROM sales
               GROUP BY day ORDER BY day DESC LIMIT 30"""
        ).fetchall()


def get_best_sellers(limit: int = 10):
    with get_connection() as conn:
        return conn.execute(
            """SELECT name,
                      SUM(quantity) as units_sold,
                      SUM(subtotal) as revenue
               FROM sale_items
               GROUP BY name ORDER BY units_sold DESC LIMIT ?""",
            (limit,)
        ).fetchall()
