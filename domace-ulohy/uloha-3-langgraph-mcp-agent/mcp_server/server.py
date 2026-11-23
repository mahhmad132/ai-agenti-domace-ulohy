"""
Môj MCP server s nástrojmi pre agenta (úloha 3).

Agent ho spúšťa sám cez stdio. Samostatne:
    uv run mcp_server/server.py
"""

import sqlite3

import httpx
from fastmcp import FastMCP

from eshop_db import DB_PATH, build_db

mcp = FastMCP("eshop")


@mcp.tool
def calculator(operation: str, a: float, b: float) -> float:
    """Kalkulačka. operation je jedno z: add, subtract, multiply, divide, power."""
    if operation == "add":
        return a + b
    if operation == "subtract":
        return a - b
    if operation == "multiply":
        return a * b
    if operation == "divide":
        return a / b
    if operation == "power":
        return a**b
    raise ValueError(f"Neznáma operácia: {operation}")


@mcp.tool
def list_tables() -> dict:
    """Vráti tabuľky v databáze e-shopu a ich stĺpce."""
    con = sqlite3.connect(DB_PATH)
    tables = [row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    result = {}
    for table in tables:
        result[table] = [col[1] for col in con.execute(f"PRAGMA table_info({table})")]
    con.close()
    return result


@mcp.tool
def run_sql(query: str) -> list[dict]:
    """Spustí SQL SELECT nad databázou e-shopu (SQLite). Vráti max 50 riadkov."""
    if not query.strip().lower().startswith("select"):
        raise ValueError("Povolený je iba SELECT.")
    # databázu otvoríme iba na čítanie
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    rows = con.execute(query).fetchmany(50)
    con.close()
    return [dict(row) for row in rows]


@mcp.tool
def search_reviews(text: str, max_rating: int = 5) -> list[dict]:
    """Hľadá text v recenziách produktov (title, comment). Text píš po anglicky."""
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT product_name, rating, title, comment FROM reviews "
        "WHERE (title LIKE ? OR comment LIKE ?) AND rating <= ? LIMIT 10",
        (f"%{text}%", f"%{text}%", max_rating),
    ).fetchall()
    con.close()
    return [dict(row) for row in rows]


@mcp.tool
def wikipedia_search(query: str, lang: str = "en") -> dict:
    """Vyhľadá článok na Wikipédii a vráti jeho krátke zhrnutie."""
    headers = {"User-Agent": "ai-agenti-uloha3/0.1"}
    search = httpx.get(
        f"https://{lang}.wikipedia.org/w/api.php",
        params={"action": "query", "list": "search", "srsearch": query, "format": "json"},
        headers=headers,
    ).json()
    results = search["query"]["search"]
    if not results:
        return {"result": "Nič som nenašiel."}

    title = results[0]["title"]
    summary = httpx.get(
        f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}",
        headers=headers,
        follow_redirects=True,
    ).json()
    return {"title": title, "summary": summary.get("extract", "")}


if __name__ == "__main__":
    if not DB_PATH.exists():
        build_db()
    mcp.run(show_banner=False)
