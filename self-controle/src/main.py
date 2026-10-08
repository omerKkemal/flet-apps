"""
Behavior Tracker - built with Python Flet
Run:  pip install flet
      python behavior_tracker.py
Data is saved in data.json next to this file.
"""
import json
import os
import uuid
from datetime import date, datetime, timedelta

import flet as ft
import flet_charts as fc

try:  # only installed/working in the Android build
    from flet_android_notifications import FletAndroidNotifications
except ImportError:
    FletAndroidNotifications = None

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

    # ---------- notifications ----------
    notifier = FletAndroidNotifications() if FletAndroidNotifications else None
    state["mode"] = "inexact_allow_while_idle"

    async def reschedule():
        """Cancel everything and schedule the next 7 days of blueprint alarms.
        Alarms are handled by Android's AlarmManager, so they fire even if the
        app is closed. Reopening the app refreshes the next 7 days."""
        if not notifier:
            return
        try:
            await notifier.cancel_all()
            now = datetime.now()
            n = 1
            for offset in range(7):
                base = (now + timedelta(days=offset)).date()
                for s in data["schedule"]:
                    try:
                        h, m = map(int, s["time"].split(":"))
                        when = datetime(base.year, base.month, base.day, h, m)
                    except ValueError:
                        continue
                    if when <= now:
                        continue
                    await notifier.schedule_notification(
                        notification_id=n,
                        title="Time for your next task",
                        body=f'{s["time"]} - {s["title"]}',
                        scheduled_time=when,
                        payload=s["id"],
                        schedule_mode=state["mode"],
                    )
                    n += 1
        except Exception as ex:
            print("Notification scheduling failed:", ex)

    async def setup_notifications():
        if not notifier:
            return
        try:
            await notifier.request_permissions()
            if await notifier.request_exact_alarm_permission():
                state["mode"] = "exact_allow_while_idle"
        except Exception as ex:
            print("Notification permission error:", ex)
        await reschedule()

    def commit(resched=False):
        save(data)
        if resched:
            page.run_task(reschedule)
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
                                        ft.Button(
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
                                        ft.Button(
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

    # ---------- HISTORY (dashboard) ----------
    def day_stats(k):
        d = data["days"].get(k)
        valid = {s["id"] for s in data["schedule"]}
        done = {x for x in d["done"] if x in valid} if d else set()
        pct = len(done) / len(valid) if valid else 0
        return {
            "pct": pct,
            "done": done,
            "c": sum(d["control"].values()) if d else 0,
            "s": sum(d["slip"].values()) if d else 0,
            "cd": d["control"] if d else {},
            "sd": d["slip"] if d else {},
        }

    def streak():
        """Consecutive days with >=80% of the routine done (today doesn't break it)."""
        n = 0
        for i in range(400):
            k = (date.today() - timedelta(days=i)).isoformat()
            if day_stats(k)["pct"] >= 0.8:
                n += 1
            elif i > 0:
                break
        return n

    def set_range(n):
        state["range"] = n
        render()

    def stat_card(title, value, sub, color):
        return ft.Container(
            expand=True, padding=12, border_radius=12, bgcolor=color,
            content=ft.Column(
                [
                    ft.Text(title, size=12),
                    ft.Text(value, size=26, weight=ft.FontWeight.BOLD),
                    ft.Text(sub, size=11),
                ],
                spacing=2,
            ),
        )

    def panel(title, *controls):
        return ft.Container(
            padding=12, border_radius=12, bgcolor=ft.Colors.GREY_100,
            content=ft.Column(
                [ft.Text(title, size=16, weight=ft.FontWeight.BOLD), *controls], spacing=8
            ),
        )

    def x_labels(labels, step):
        return [
            fc.ChartAxisLabel(value=i, label=ft.Text(l, size=9))
            for i, l in enumerate(labels)
            if i % step == 0
        ]

    def history_view():
        n = state.get("range", 7)
        T = len(data["schedule"])  # tasks per day in the blueprint
        keys = [(date.today() - timedelta(days=i)).isoformat() for i in range(n - 1, -1, -1)]
        st = [day_stats(k) for k in keys]
        labels = [
            date.fromisoformat(k).strftime("%a")[:2] if n <= 7 else str(date.fromisoformat(k).day)
            for k in keys
        ]
        step = 1 if n <= 7 else 5
        D = sum(len(x["done"]) for x in st)
        avg = sum(x["pct"] for x in st) / n
        C = sum(x["c"] for x in st)
        S = sum(x["s"] for x in st)
        ctrl = f"{int(C / (C + S) * 100)}%" if C + S else "-"
        bar_w = 14 if n <= 7 else 5

        range_btns = ft.Row(
            [
                (ft.Button if n == r else ft.TextButton)(
                    f"{r} days", on_click=lambda e, r=r: set_range(r)
                )
                for r in (7, 30)
            ]
        )

        rows = [
            ft.Text("Dashboard", size=22, weight=ft.FontWeight.BOLD),
            range_btns,
            ft.Row(
                [
                    stat_card("Tasks done", f"{D}/{T * n}", f"last {n} days", ft.Colors.BLUE_100),
                    stat_card("Avg completion", f"{int(avg * 100)}%", f"today {len(st[-1]['done'])}/{T}", ft.Colors.GREEN_100),
                ]
            ),
            ft.Row(
                [
                    stat_card("Self-control", ctrl, f"{C} won / {S} lost", ft.Colors.ORANGE_100),
                    stat_card("Streak", f"{streak()}", "days at 80%+", ft.Colors.PURPLE_100),
                ]
            ),
        ]

        # 1) tasks done per day (bar chart, tap a bar for "done/total")
        rows.append(
            panel(
                "Tasks done per day",
                fc.BarChart(
                    height=170,
                    max_y=max(T, 1),
                    groups=[
                        fc.BarChartGroup(
                            x=i,
                            rods=[
                                fc.BarChartRod(
                                    from_y=0,
                                    to_y=len(x["done"]),
                                    width=bar_w,
                                    color=ft.Colors.BLUE_400,
                                    tooltip=f"{labels[i]}: {len(x['done'])}/{T}",
                                )
                            ],
                        )
                        for i, x in enumerate(st)
                    ],
                    bottom_axis=fc.ChartAxis(labels=x_labels(labels, step)),
                ),
            )
        )

        # 2) trend line: routine % and self-control %
        series = [
            fc.LineChartData(
                points=[fc.LineChartDataPoint(i, x["pct"] * 100) for i, x in enumerate(st)],
                color=ft.Colors.BLUE_400, stroke_width=3, curved=True,
            )
        ]
        ctrl_pts = [
            fc.LineChartDataPoint(i, x["c"] / (x["c"] + x["s"]) * 100)
            for i, x in enumerate(st) if x["c"] + x["s"]
        ]
        if ctrl_pts:
            series.append(
                fc.LineChartData(points=ctrl_pts, color=ft.Colors.GREEN_400, stroke_width=3, curved=True)
            )
        rows.append(
            panel(
                "Trend (%)",
                fc.LineChart(
                    height=170, min_y=0, max_y=100, min_x=0, max_x=max(n - 1, 1),
                    data_series=series,
                    bottom_axis=fc.ChartAxis(labels=x_labels(labels, step)),
                ),
                ft.Text("Blue = routine completion   Green = self-control", size=11),
            )
        )

        # 3) self-control per day (stacked bars)
        mx = max([x["c"] + x["s"] for x in st] + [1])
        rows.append(
            panel(
                "Self-control per day",
                fc.BarChart(
                    height=170,
                    max_y=mx + 1,
                    groups=[
                        fc.BarChartGroup(
                            x=i,
                            rods=[
                                fc.BarChartRod(
                                    from_y=0,
                                    to_y=x["c"] + x["s"],
                                    width=bar_w,
                                    color=ft.Colors.GREEN_400,
                                    tooltip=f"{labels[i]}: {x['c']} won / {x['s']} lost",
                                    stack_items=[
                                        fc.BarChartRodStackItem(0, x["c"], ft.Colors.GREEN_400),
                                        fc.BarChartRodStackItem(x["c"], x["c"] + x["s"], ft.Colors.RED_400),
                                    ],
                                )
                            ],
                        )
                        for i, x in enumerate(st)
                    ],
                    bottom_axis=fc.ChartAxis(labels=x_labels(labels, step)),
                ),
                ft.Text("Green = I controlled myself   Red = behavior took control", size=11),
            )
        )

        # 4) donut: done vs missed tasks
        if T:
            secs = [
                fc.PieChartSection(v, color=col, title=f"{name} {v}", radius=38,
                                   title_style=ft.TextStyle(size=11, color=ft.Colors.WHITE))
                for v, col, name in ((D, ft.Colors.GREEN_500, "Done"), (T * n - D, ft.Colors.GREY_500, "Missed"))
                if v > 0
            ]
            rows.append(panel(f"Done vs missed ({n} days)", fc.PieChart(sections=secs, center_space_radius=36, height=150)))

        # 5) per-task and per-behavior numbers
        if data["schedule"]:
            items = []
            for s in sorted(data["schedule"], key=lambda x: x["time"]):
                cnt = sum(1 for x in st if s["id"] in x["done"])
                items.append(
                    ft.Column(
                        [
                            ft.Row([ft.Text(f'{s["time"]}  {s["title"]}', expand=True), ft.Text(f"{cnt}/{n} days")]),
                            ft.ProgressBar(value=cnt / n, color=ft.Colors.BLUE_400),
                        ],
                        spacing=2,
                    )
                )
            rows.append(panel("Routine consistency", *items))

        if data["behaviors"]:
            items = []
            for b in data["behaviors"]:
                c = sum(x["cd"].get(b["id"], 0) for x in st)
                s = sum(x["sd"].get(b["id"], 0) for x in st)
                pct = c / (c + s) if c + s else 0
                items.append(
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(b["name"], expand=True),
                                    ft.Text(f"{c} won / {s} lost  ({int(pct * 100)}%)" if c + s else "no data"),
                                ]
                            ),
                            ft.ProgressBar(value=pct, color=ft.Colors.GREEN_400),
                        ],
                        spacing=2,
                    )
                )
            rows.append(panel("Behavior control", *items))

        # 6) last 7 days in numbers
        recent = [ft.Text(f"{k}   {len(x['done'])}/{T} tasks   {x['c']} won / {x['s']} lost", size=13)
                  for k, x in reversed(list(zip(keys, st))[-7:])]
        rows.append(panel("Recent days", *recent))
        return rows

    # ---------- PLAN (blueprint) ----------
    def add_schedule(e):
        title = new_title.value.strip()
        try:
            h, m = map(int, new_time.value.strip().split(":"))
            assert 0 <= h < 24 and 0 <= m < 60
        except Exception:
            new_time.error_text = "Use HH:MM"
            page.update()
            return
        new_time.error_text = None
        if not title:
            return
        data["schedule"].append({"id": uuid.uuid4().hex[:8], "time": f"{h:02d}:{m:02d}", "title": title})
        new_title.value = ""
        commit(resched=True)

    def del_schedule(sid):
        data["schedule"] = [s for s in data["schedule"] if s["id"] != sid]
        commit(resched=True)

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
    page.run_task(setup_notifications)


if __name__ == "__main__":
    # ft.run in newer Flet versions, ft.app in older ones
    (getattr(ft, "run", None) or ft.app)(main)