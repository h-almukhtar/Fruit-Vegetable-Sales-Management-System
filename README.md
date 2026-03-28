# Fruit-Vegetable-Sales-Management-System
FreshMart POS — Fruit &amp; Vegetable Sales Management System  A complete, modern desktop POS application built with Python, CustomTkinter, and SQLite. 

## Default Credentials

| Role    | Username | Password    |
|---------|----------|-------------|
| Admin   | admin    | admin123    |
| Cashier | cashier  | cashier123  |

---

## File Structure

```
FruitVegSales/
├── main.py            ← Entry point
├── app.py             ← Root window, login routing, dashboards
├── login.py           ← Login screen
├── database.py        ← All SQLite operations
├── theme.py           ← Colors, fonts, constants
├── widgets.py         ← Reusable UI components
├── products_panel.py  ← Product CRUD (Admin full / Cashier read-only)
├── sales_panel.py     ← POS checkout + receipt
├── reports_panel.py   ← Reports + CSV/Excel export (Admin)
├── users_panel.py     ← User management (Admin)
└── sales_system.db    ← Auto-created SQLite database
```

---

## Database Schema

```sql
users       (id, username, password, role, created)
products    (id, name, price, quantity, low_stock, updated)
sales       (id, date, total, cashier_id)
sale_items  (id, sale_id, product_id, name, price, quantity, subtotal)
```

---

## Feature Summary

### Admin
- Full product CRUD (add, edit, delete)
- POS / Sales checkout with receipt
- Reports: daily summary, all sales, best sellers
- Export reports to CSV or Excel (.xlsx)
- User management (create, reset password, delete)
- Inventory overview with low-stock alerts

### Cashier
- POS checkout with cart and receipt
- View product list (read-only)

---

## Notes

- VAT is calculated at **15%** (Saudi standard)
- Receipts can be copied to clipboard
- Low stock threshold is configurable per product (default: 10)
