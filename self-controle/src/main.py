"""
Behavior Tracker - built with Python Flet
Run:  pip install flet
      python behavior_tracker.py
Data is saved in data.json next to this file.
"""
import json
import os
import uuid
from datetime import date, timedelta

import flet as ft

# On Android/iOS the app folder is read-only, so Flet provides a persistent,
# writable folder through FLET_APP_STORAGE_DATA. On desktop we fall back to
# the folder next to this script.
STORAGE_DIR = os.getenv("FLET_APP_STORAGE_DATA") or os.path.dirname(os.path.abspath(__file__))
os.makedirs(STORAGE_DIR, exist_ok=True)
DATA_FILE = os.path.join(STORAGE_DIR, "data.json")


# ---------- storage ----------
def load():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "schedule": [
            {"id": "s1", "time": "07:00", "title": "Exercise"},
            {"id": "s2", "time": "13:00", "title": "Eat properly"},
        ],
        "behaviors": [{"id": "b1", "name": "Scrolling social media"}],
        "days": {},
    }


def save(data):
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, DATA_FILE)  # atomic: no half-written file if Android kills the app


def day_of(data, key):
    return data["days"].setdefault(key, {"done": [], "control": {}, "slip": {}})


def main(page: ft.Page):
    page.title = "Behavior Tracker"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

    data = load()
    state = {"tab": 0}
    today = date.today().isoformat()

    # persistent input fields (so typing isn't lost on re-render)
    new_time = ft.TextField(label="Time (HH:MM)", value="08:00", width=130)
    new_title = ft.TextField(label="Routine item", expand=True)
    new_behavior = ft.TextField(label="Behavior to control", expand=True)

    body = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=10)

    def commit():
        save(data)
        render()

    # ---------- TODAY ----------
    def toggle(sid, checked):
        d = day_of(data, today)
        if checked and sid not in d["done"]:
            d["done"].append(sid)
        if not checked and sid in d["done"]:
            d["done"].remove(sid)
        commit()

    def today_view():
        d = day_of(data, today)
        items = sorted(data["schedule"], key=lambda s: s["time"])
        done = sum(1 for s in items if s["id"] in d["done"])
        pct = done / len(items) if items else 0
        rows = [
            ft.Text(f"Today - {today}", size=22, weight=ft.FontWeight.BOLD),
            ft.ProgressBar(value=pct),
            ft.Text(f"{done}/{len(items)} done ({int(pct * 100)}%)"),
        ]
        if not items:
            rows.append(ft.Text("Your blueprint is empty. Add routine items in the Plan tab."))
        for s in items:
            rows.append(
                ft.Checkbox(
                    label=f'{s["time"]}   {s["title"]}',
                    value=s["id"] in d["done"],
                    on_change=lambda e, sid=s["id"]: toggle(sid, e.control.value),
                )
            )
        return rows

    # ---------- BEHAVIOR ----------
    def bump(kind, bid):
        d = day_of(data, today)
        d[kind][bid] = d[kind].get(bid, 0) + 1
        commit()

    def undo(kind, bid):
        d = day_of(data, today)
        d[kind][bid] = max(0, d[kind].get(bid, 0) - 1)
        commit()

    def behavior_view():
        d = day_of(data, today)
        rows = [
            ft.Text("Self-control today", size=22, weight=ft.FontWeight.BOLD),
            ft.Text("Tap when you resisted, or when the behavior took control."),
        ]
        if not data["behaviors"]:
            rows.append(ft.Text("No behaviors yet. Add some in the Plan tab."))
        for b in data["behaviors"]:
            c = d["control"].get(b["id"], 0)
            s = d["slip"].get(b["id"], 0)
            score = f"{int(c / (c + s) * 100)}% control" if c + s else "no data yet"
            rows.append(
                ft.Card(
                    content=ft.Container(
                        padding=12,
                        content=ft.Column(
                            [
                                ft.Text(b["name"], size=17, weight=ft.FontWeight.BOLD),
                                ft.Text(f"Controlled: {c}   |   Took control: {s}   |   {score}"),
                                ft.Row(
                                    [
                                        ft.ElevatedButton(
                                            "I controlled myself +1",
                                            icon=ft.Icons.CHECK_CIRCLE,
                                            on_click=lambda e, i=b["id"]: bump("control", i),
                                        ),
                                        ft.IconButton(
                                            ft.Icons.UNDO,
                                            tooltip="Undo",
                                            on_click=lambda e, i=b["id"]: undo("control", i),
                                        ),
                                    ],
                                    wrap=True,
                                ),
                                ft.Row(
                                    [
                                        ft.ElevatedButton(
                                            "Behavior took control +1",
                                            icon=ft.Icons.WARNING,
                                            on_click=lambda e, i=b["id"]: bump("slip", i),
                                        ),
                                        ft.IconButton(
                                            ft.Icons.UNDO,
                                            tooltip="Undo",
                                            on_click=lambda e, i=b["id"]: undo("slip", i),
                                        ),
                                    ],
                                    wrap=True,
                                ),
                            ]
                        ),
                    )
                )
            )
        return rows

    # ---------- HISTORY ----------
    def history_view():
        rows = [ft.Text("Last 14 days", size=22, weight=ft.FontWeight.BOLD)]
        total = len(data["schedule"])
        valid = {s["id"] for s in data["schedule"]}
        for i in range(14):
            k = (date.today() - timedelta(days=i)).isoformat()
            d = data["days"].get(k)
            done = len([x for x in d["done"] if x in valid]) if d else 0
            pct = done / total if total else 0
            c = sum(d["control"].values()) if d else 0
            s = sum(d["slip"].values()) if d else 0
            ctrl = f"{int(c / (c + s) * 100)}%" if c + s else "-"
            rows.append(
                ft.Column(
                    [
                        ft.Text(f"{k}   routine {int(pct * 100)}%   control {ctrl}  ({c} won / {s} lost)"),
                        ft.ProgressBar(value=pct),
                    ],
                    spacing=4,
                )
            )
        return rows

    # ---------- PLAN (blueprint) ----------
    def add_schedule(e):
        t, title = new_time.value.strip(), new_title.value.strip()
        if not title:
            return
        data["schedule"].append({"id": uuid.uuid4().hex[:8], "time": t or "00:00", "title": title})
        new_title.value = ""
        commit()

    def del_schedule(sid):
        data["schedule"] = [s for s in data["schedule"] if s["id"] != sid]
        commit()

    def add_behavior(e):
        name = new_behavior.value.strip()
        if not name:
            return
        data["behaviors"].append({"id": uuid.uuid4().hex[:8], "name": name})
        new_behavior.value = ""
        commit()

    def del_behavior(bid):
        data["behaviors"] = [b for b in data["behaviors"] if b["id"] != bid]
        commit()

    def plan_view():
        rows = [
            ft.Text("Daily blueprint", size=22, weight=ft.FontWeight.BOLD),
            ft.Text("This repeats every day until you change it."),
            ft.Row([new_time, new_title, ft.IconButton(ft.Icons.ADD_CIRCLE, on_click=add_schedule)]),
        ]
        for s in sorted(data["schedule"], key=lambda x: x["time"]):
            rows.append(
                ft.Row(
                    [
                        ft.Text(f'{s["time"]}   {s["title"]}', expand=True),
                        ft.IconButton(ft.Icons.DELETE, on_click=lambda e, i=s["id"]: del_schedule(i)),
                    ]
                )
            )
        rows += [
            ft.Divider(),
            ft.Text("Behaviors to control", size=22, weight=ft.FontWeight.BOLD),
            ft.Row([new_behavior, ft.IconButton(ft.Icons.ADD_CIRCLE, on_click=add_behavior)]),
        ]
        for b in data["behaviors"]:
            rows.append(
                ft.Row(
                    [
                        ft.Text(b["name"], expand=True),
                        ft.IconButton(ft.Icons.DELETE, on_click=lambda e, i=b["id"]: del_behavior(i)),
                    ]
                )
            )
        return rows

    views = [today_view, behavior_view, history_view, plan_view]

    def render():
        body.controls = views[state["tab"]]()
        page.update()

    def on_nav(e):
        state["tab"] = e.control.selected_index
        render()

    page.navigation_bar = ft.NavigationBar(
        selected_index=0,
        on_change=on_nav,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.CHECKLIST, label="Today"),
            ft.NavigationBarDestination(icon=ft.Icons.PSYCHOLOGY, label="Behavior"),
            ft.NavigationBarDestination(icon=ft.Icons.INSERT_CHART, label="History"),
            ft.NavigationBarDestination(icon=ft.Icons.EDIT_CALENDAR, label="Plan"),
        ],
    )
    page.add(ft.Container(content=body, padding=16, expand=True))
    render()


if __name__ == "__main__":
    # ft.run in newer Flet versions, ft.app in older ones
    (getattr(ft, "run", None) or ft.app)(main)