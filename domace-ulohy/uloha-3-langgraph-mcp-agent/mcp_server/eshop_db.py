"""Vytvorí SQLite databázu e-shopu z JSON súborov z kurzu (03_N8N/databases/data)."""

import json
import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "eshop.db"


def load(name):
    with open(DATA_DIR / f"{name}.json", encoding="utf-8") as f:
        return json.load(f)


def build_db():
    con = sqlite3.connect(DB_PATH)
    con.executescript("""
        DROP TABLE IF EXISTS users;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS order_items;
        DROP TABLE IF EXISTS reviews;

        CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, first_name TEXT, last_name TEXT,
            city TEXT, country TEXT, is_premium INTEGER, total_orders INTEGER, total_spent REAL);
        CREATE TABLE products (id INTEGER PRIMARY KEY, sku TEXT, name TEXT, description TEXT,
            category TEXT, brand TEXT, price REAL, stock_quantity INTEGER, rating REAL, review_count INTEGER);
        CREATE TABLE orders (id INTEGER PRIMARY KEY, order_number TEXT, user_id INTEGER, order_date TEXT,
            status TEXT, total_amount REAL, payment_method TEXT, shipping_country TEXT);
        CREATE TABLE order_items (order_id INTEGER, product_id INTEGER, product_name TEXT,
            quantity INTEGER, unit_price REAL, total_price REAL);
        CREATE TABLE reviews (id INTEGER PRIMARY KEY, product_id INTEGER, product_name TEXT,
            user_name TEXT, rating INTEGER, title TEXT, comment TEXT);
    """)

    for u in load("users"):
        con.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?)", (
            u["id"], u["email"], u["first_name"], u["last_name"],
            u["shipping_address"]["city"], u["shipping_address"]["country"],
            u["is_premium"], u["stats"]["orders_count"], u["stats"]["total_spent"]))

    for p in load("products"):
        con.execute("INSERT INTO products VALUES (?,?,?,?,?,?,?,?,?,?)", (
            p["id"], p["sku"], p["name"], p["description"], p["category"], p["brand"],
            p["price"], p["stock_quantity"], p["rating"], p["review_count"]))

    for o in load("orders"):
        con.execute("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?)", (
            o["id"], o["order_number"], o["user_id"], o["order_date"], o["status"],
            o["totals"]["total"], o["payment_info"]["method"], o["shipping_address"]["country"]))
        for i in o["items"]:
            con.execute("INSERT INTO order_items VALUES (?,?,?,?,?,?)", (
                o["id"], i["product_id"], i["product_name"], i["quantity"], i["unit_price"], i["total_price"]))

    for r in load("reviews"):
        con.execute("INSERT INTO reviews VALUES (?,?,?,?,?,?,?)", (
            r["id"], r["product_id"], r["product_name"], r["user_name"], r["rating"], r["title"], r["comment"]))

    con.commit()
    con.close()


if __name__ == "__main__":
    build_db()
    print("Databáza vytvorená:", DB_PATH)
