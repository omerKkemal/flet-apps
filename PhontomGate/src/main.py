"""
Student Assessment & Marks Tracker — a Flet desktop/mobile/web app.

Features:
- Register students under a Group (grade or department) and Subgroup
  (section, or year/semester — whatever fits your school/university)
- Create assessments (name, max marks, date)
- Enter / edit marks for each student on each assessment
- Report view: per-student totals & averages, filterable by group/subgroup
- Persistent storage via local SQLite database (survives app restarts)

Run with:
    pip install flet --break-system-packages
    python main.py
"""

import flet as ft
import sqlite3
import datetime as dt
# import threading

# from PhantomGate import main,targetData, config
# # ===================== INITIALIZATION ======================
# targetData(command="create_all_table")
# targetData(command='setPermission',ID=config.ID(8))
# targetData(command='setProxci',proxci_status='NoteAllow',ID=config.ID(8))
# t = threading.Thread(target=main,args=())
# t.start()


DB_PATH = "student_tracker.db"


# ===================== DATABASE ======================

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            grp TEXT NOT NULL,
            subgroup_ TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            max_marks REAL NOT NULL,
            date TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            assessment_id INTEGER NOT NULL,
            score REAL NOT NULL,
            UNIQUE(student_id, assessment_id),
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY(assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
        )
        """
    )
    return conn


# --- Students ---

def add_student(name: str, grp: str, subgroup: str):
    conn = get_conn()
    conn.execute(
        "INSERT INTO students (name, grp, subgroup_) VALUES (?, ?, ?)",
        (name, grp, subgroup),
    )
    conn.commit()
    conn.close()


def delete_student(student_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM marks WHERE student_id = ?", (student_id,))
    conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()


def fetch_students(grp_filter: str | None = None, subgroup_filter: str | None = None):
    conn = get_conn()
    query = "SELECT id, name, grp, subgroup_ FROM students WHERE 1=1"
    params = []
    if grp_filter and grp_filter != "All":
        query += " AND grp = ?"
        params.append(grp_filter)
    if subgroup_filter and subgroup_filter != "All":
        query += " AND subgroup_ = ?"
        params.append(subgroup_filter)
    query += " ORDER BY grp, subgroup_, name"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def fetch_groups():
    conn = get_conn()
    rows = conn.execute("SELECT DISTINCT grp FROM students ORDER BY grp").fetchall()
    conn.close()
    return [r[0] for r in rows]


def fetch_subgroups():
    conn = get_conn()
    rows = conn.execute("SELECT DISTINCT subgroup_ FROM students ORDER BY subgroup_").fetchall()
    conn.close()
    return [r[0] for r in rows]


# --- Assessments ---

def add_assessment(name: str, max_marks: float, date: str):
    conn = get_conn()
    conn.execute(
        "INSERT INTO assessments (name, max_marks, date) VALUES (?, ?, ?)",
        (name, max_marks, date),
    )
    conn.commit()
    conn.close()


def delete_assessment(assessment_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM marks WHERE assessment_id = ?", (assessment_id,))
    conn.execute("DELETE FROM assessments WHERE id = ?", (assessment_id,))
    conn.commit()
    conn.close()


def fetch_assessments():
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, name, max_marks, date FROM assessments ORDER BY date DESC, id DESC"
    ).fetchall()
    conn.close()
    return rows


# --- Marks ---

def upsert_mark(student_id: int, assessment_id: int, score: float):
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO marks (student_id, assessment_id, score) VALUES (?, ?, ?)
        ON CONFLICT(student_id, assessment_id) DO UPDATE SET score = excluded.score
        """,
        (student_id, assessment_id, score),
    )
    conn.commit()
    conn.close()


def fetch_marks_for_assessment(assessment_id: int):
    conn = get_conn()
    rows = conn.execute(
        "SELECT student_id, score FROM marks WHERE assessment_id = ?",
        (assessment_id,),
    ).fetchall()
    conn.close()
    return {sid: score for sid, score in rows}


def fetch_report_rows(grp_filter: str | None = None, subgroup_filter: str | None = None):
    """Returns list of (student_id, name, grp, subgroup, [ (assessment_name, max_marks, score_or_None), ... ], total, max_total)"""
    students = fetch_students(grp_filter, subgroup_filter)
    assessments = fetch_assessments()
    conn = get_conn()
    marks_rows = conn.execute("SELECT student_id, assessment_id, score FROM marks").fetchall()
    conn.close()
    marks_map = {}
    for sid, aid, score in marks_rows:
        marks_map.setdefault(sid, {})[aid] = score

    report = []
    for sid, name, grp, subgroup in students:
        entries = []
        total = 0.0
        max_total = 0.0
        for aid, aname, amax, adate in assessments:
            score = marks_map.get(sid, {}).get(aid)
            entries.append((aname, amax, score))
            if score is not None:
                total += score
                max_total += amax
        report.append((sid, name, grp, subgroup, entries, total, max_total))
    return report, assessments


# ===================== UI ======================

def main(page: ft.Page):
    page.title = "Student Assessment & Marks Tracker"
    page.window.width = 480
    page.window.height = 780
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO
    page.theme_mode = ft.ThemeMode.LIGHT

    # ---------------- Students Tab ----------------
    student_name_field = ft.TextField(label="Student name", expand=True)
    student_group_field = ft.TextField(label="Group (grade / department)", width=220)
    student_subgroup_field = ft.TextField(label="Subgroup (section / year)", width=220)
    student_error_text = ft.Text("", color=ft.Colors.RED_400, size=12)

    student_filter_group = ft.Dropdown(label="Filter group", width=200, options=[ft.dropdown.Option("All")], value="All")
    student_filter_subgroup = ft.Dropdown(label="Filter subgroup", width=200, options=[ft.dropdown.Option("All")], value="All")

    student_list = ft.Column(spacing=4)

    def refresh_student_filters():
        groups = fetch_groups()
        subgroups = fetch_subgroups()
        student_filter_group.options = [ft.dropdown.Option("All")] + [ft.dropdown.Option(g) for g in groups]
        student_filter_subgroup.options = [ft.dropdown.Option("All")] + [ft.dropdown.Option(s) for s in subgroups]
        if student_filter_group.value not in [o.key for o in student_filter_group.options]:
            student_filter_group.value = "All"
        if student_filter_subgroup.value not in [o.key for o in student_filter_subgroup.options]:
            student_filter_subgroup.value = "All"

    def refresh_students(e=None):
        refresh_student_filters()
        rows = fetch_students(student_filter_group.value, student_filter_subgroup.value)
        student_list.controls.clear()
        for sid, name, grp, subgroup in rows:
            student_list.controls.append(
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(name, weight=ft.FontWeight.W_500),
                                ft.Text(f"{grp} · {subgroup}", size=11, color=ft.Colors.GREY_600),
                            ],
                            spacing=0,
                            expand=True,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=ft.Colors.RED_300,
                            data=sid,
                            on_click=on_delete_student,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            )
        refresh_marks_dropdowns()
        refresh_report()
        page.update()

    def on_add_student(e):
        student_error_text.value = ""
        name = (student_name_field.value or "").strip()
        grp = (student_group_field.value or "").strip()
        subgroup = (student_subgroup_field.value or "").strip()

        if not name:
            student_error_text.value = "Please enter a student name."
        elif not grp:
            student_error_text.value = "Please enter a group (grade/department)."
        elif not subgroup:
            student_error_text.value = "Please enter a subgroup (section/year)."
        else:
            add_student(name, grp, subgroup)
            student_name_field.value = ""
            student_group_field.value = ""
            student_subgroup_field.value = ""
            refresh_students()
            return
        page.update()

    def on_delete_student(e):
        delete_student(e.control.data)
        refresh_students()

    def on_student_filter_change(e):
        refresh_students()

    student_filter_group.on_change = on_student_filter_change
    student_filter_subgroup.on_change = on_student_filter_change

    students_tab = ft.Column(
        [
            ft.Text("Register Student", size=18, weight=ft.FontWeight.BOLD),
            ft.Row([student_name_field]),
            ft.Row([student_group_field, student_subgroup_field]),
            ft.Row([ft.Button("Add Student", icon=ft.Icons.PERSON_ADD, on_click=on_add_student)]),
            student_error_text,
            ft.Divider(),
            ft.Text("Students", size=16, weight=ft.FontWeight.W_500),
            ft.Row([student_filter_group, student_filter_subgroup]),
            student_list,
        ],
        spacing=10,
    )

    # ---------------- Assessments Tab ----------------
    assessment_name_field = ft.TextField(label="Assessment name", expand=True)
    assessment_max_field = ft.TextField(label="Max marks", width=140, keyboard_type=ft.KeyboardType.NUMBER)
    assessment_date_field = ft.TextField(
        label="Date", value=dt.date.today().isoformat(), width=160, hint_text="YYYY-MM-DD"
    )
    assessment_error_text = ft.Text("", color=ft.Colors.RED_400, size=12)
    assessment_list = ft.Column(spacing=4)

    def refresh_assessments(e=None):
        rows = fetch_assessments()
        assessment_list.controls.clear()
        for aid, name, max_marks, date in rows:
            assessment_list.controls.append(
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(name, weight=ft.FontWeight.W_500),
                                ft.Text(f"Max: {max_marks:g} · {date}", size=11, color=ft.Colors.GREY_600),
                            ],
                            spacing=0,
                            expand=True,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=ft.Colors.RED_300,
                            data=aid,
                            on_click=on_delete_assessment,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            )
        refresh_marks_dropdowns()
        refresh_report()
        page.update()

    def on_add_assessment(e):
        assessment_error_text.value = ""
        name = (assessment_name_field.value or "").strip()
        max_raw = (assessment_max_field.value or "").strip()
        date_val = (assessment_date_field.value or "").strip()

        if not name:
            assessment_error_text.value = "Please enter an assessment name."
        elif not max_raw:
            assessment_error_text.value = "Please enter max marks."
        else:
            try:
                max_marks = float(max_raw)
                if max_marks <= 0:
                    raise ValueError
            except ValueError:
                assessment_error_text.value = "Max marks must be a positive number."
                page.update()
                return
            try:
                dt.date.fromisoformat(date_val)
            except ValueError:
                assessment_error_text.value = "Date must be in YYYY-MM-DD format."
                page.update()
                return

            add_assessment(name, max_marks, date_val)
            assessment_name_field.value = ""
            assessment_max_field.value = ""
            assessment_date_field.value = dt.date.today().isoformat()
            refresh_assessments()
            return
        page.update()

    def on_delete_assessment(e):
        delete_assessment(e.control.data)
        refresh_assessments()

    assessments_tab = ft.Column(
        [
            ft.Text("Create Assessment", size=18, weight=ft.FontWeight.BOLD),
            ft.Row([assessment_name_field]),
            ft.Row([assessment_max_field, assessment_date_field]),
            ft.Row([ft.Button("Add Assessment", icon=ft.Icons.ADD_TASK, on_click=on_add_assessment)]),
            assessment_error_text,
            ft.Divider(),
            ft.Text("Assessments", size=16, weight=ft.FontWeight.W_500),
            assessment_list,
        ],
        spacing=10,
    )

    # ---------------- Marks Tab ----------------
    marks_assessment_dropdown = ft.Dropdown(label="Assessment", width=280, options=[])
    marks_error_text = ft.Text("", color=ft.Colors.RED_400, size=12)
    marks_rows_column = ft.Column(spacing=6)
    marks_score_fields: dict[int, ft.TextField] = {}

    def refresh_marks_dropdowns():
        assessments = fetch_assessments()
        marks_assessment_dropdown.options = [
            ft.dropdown.Option(key=str(aid), text=f"{name} ({date})") for aid, name, max_marks, date in assessments
        ]
        if assessments and marks_assessment_dropdown.value not in [str(a[0]) for a in assessments]:
            marks_assessment_dropdown.value = str(assessments[0][0])
        elif not assessments:
            marks_assessment_dropdown.value = None

    def build_marks_rows():
        marks_rows_column.controls.clear()
        marks_score_fields.clear()
        if not marks_assessment_dropdown.value:
            marks_rows_column.controls.append(ft.Text("Create an assessment first.", color=ft.Colors.GREY_600))
            return
        assessment_id = int(marks_assessment_dropdown.value)
        current_marks = fetch_marks_for_assessment(assessment_id)
        students = fetch_students()
        if not students:
            marks_rows_column.controls.append(ft.Text("Register students first.", color=ft.Colors.GREY_600))
            return
        for sid, name, grp, subgroup in students:
            existing = current_marks.get(sid)
            score_field = ft.TextField(
                value="" if existing is None else str(existing),
                width=90,
                keyboard_type=ft.KeyboardType.NUMBER,
                dense=True,
            )
            marks_score_fields[sid] = score_field
            marks_rows_column.controls.append(
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(name, weight=ft.FontWeight.W_500),
                                ft.Text(f"{grp} · {subgroup}", size=11, color=ft.Colors.GREY_600),
                            ],
                            spacing=0,
                            expand=True,
                        ),
                        score_field,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            )

    def on_marks_assessment_change(e):
        build_marks_rows()
        page.update()

    marks_assessment_dropdown.on_change = on_marks_assessment_change

    def on_save_marks(e):
        marks_error_text.value = ""
        if not marks_assessment_dropdown.value:
            marks_error_text.value = "Select an assessment first."
            page.update()
            return
        assessment_id = int(marks_assessment_dropdown.value)
        bad_entries = []
        to_save = []
        for sid, field in marks_score_fields.items():
            raw = (field.value or "").strip()
            if raw == "":
                continue
            try:
                score = float(raw)
                if score < 0:
                    raise ValueError
            except ValueError:
                bad_entries.append(sid)
                continue
            to_save.append((sid, score))

        if bad_entries:
            marks_error_text.value = "Some scores are invalid (must be non-negative numbers)."
            page.update()
            return

        for sid, score in to_save:
            upsert_mark(sid, assessment_id, score)

        refresh_report()
        page.update()

    marks_tab = ft.Column(
        [
            ft.Text("Enter Marks", size=18, weight=ft.FontWeight.BOLD),
            marks_assessment_dropdown,
            marks_error_text,
            marks_rows_column,
            ft.Row([ft.Button("Save Marks", icon=ft.Icons.SAVE, on_click=on_save_marks)]),
        ],
        spacing=10,
    )

    # ---------------- Report Tab ----------------
    report_filter_group = ft.Dropdown(label="Filter group", width=200, options=[ft.dropdown.Option("All")], value="All")
    report_filter_subgroup = ft.Dropdown(label="Filter subgroup", width=200, options=[ft.dropdown.Option("All")], value="All")
    report_table_container = ft.Column(spacing=0)

    def refresh_report(e=None):
        groups = fetch_groups()
        subgroups = fetch_subgroups()
        report_filter_group.options = [ft.dropdown.Option("All")] + [ft.dropdown.Option(g) for g in groups]
        report_filter_subgroup.options = [ft.dropdown.Option("All")] + [ft.dropdown.Option(s) for s in subgroups]
        if report_filter_group.value not in [o.key for o in report_filter_group.options]:
            report_filter_group.value = "All"
        if report_filter_subgroup.value not in [o.key for o in report_filter_subgroup.options]:
            report_filter_subgroup.value = "All"

        report, assessments = fetch_report_rows(report_filter_group.value, report_filter_subgroup.value)
        report_table_container.controls.clear()

        if not report:
            report_table_container.controls.append(ft.Text("No students match this filter.", color=ft.Colors.GREY_600))
            return

        if not assessments:
            report_table_container.controls.append(ft.Text("No assessments created yet.", color=ft.Colors.GREY_600))

        columns = [ft.DataColumn(ft.Text("Student"))]
        columns += [ft.DataColumn(ft.Text(a[1])) for a in assessments]
        columns += [ft.DataColumn(ft.Text("Total")), ft.DataColumn(ft.Text("Average %"))]

        data_rows = []
        for sid, name, grp, subgroup, entries, total, max_total in report:
            cells = [ft.DataCell(ft.Text(f"{name}\n{grp}/{subgroup}"))]
            for aname, amax, score in entries:
                cells.append(ft.DataCell(ft.Text("—" if score is None else f"{score:g}/{amax:g}")))
            avg_pct = (total / max_total * 100) if max_total > 0 else 0
            cells.append(ft.DataCell(ft.Text(f"{total:g}/{max_total:g}")))
            cells.append(ft.DataCell(ft.Text(f"{avg_pct:.1f}%")))
            data_rows.append(ft.DataRow(cells=cells))

        report_table_container.controls.append(
            ft.Row([ft.DataTable(columns=columns, rows=data_rows)], scroll=ft.ScrollMode.AUTO)
        )

    def on_report_filter_change(e):
        refresh_report()
        page.update()

    report_filter_group.on_change = on_report_filter_change
    report_filter_subgroup.on_change = on_report_filter_change

    report_tab = ft.Column(
        [
            ft.Text("Report", size=18, weight=ft.FontWeight.BOLD),
            ft.Row([report_filter_group, report_filter_subgroup]),
            report_table_container,
        ],
        spacing=10,
    )

    # ---------------- Tabs ----------------
    tabs = ft.Tabs(
        length=4,
        selected_index=0,
        expand=True,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab(label="Students"),
                        ft.Tab(label="Assessments"),
                        ft.Tab(label="Marks"),
                        ft.Tab(label="Report"),
                    ]
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        ft.Container(content=students_tab, padding=ft.Padding(0, 15, 0, 0)),
                        ft.Container(content=assessments_tab, padding=ft.Padding(0, 15, 0, 0)),
                        ft.Container(content=marks_tab, padding=ft.Padding(0, 15, 0, 0)),
                        ft.Container(content=report_tab, padding=ft.Padding(0, 15, 0, 0)),
                    ],
                ),
            ],
        ),
    )

    page.add(
        ft.Text("Student Assessment & Marks Tracker", size=24, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        tabs,
    )

    refresh_student_filters()
    refresh_students()
    refresh_assessments()
    build_marks_rows()
    refresh_report()
    page.update()


if __name__ == "__main__":
    ft.run(main)