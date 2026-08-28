import tempfile
import flet as ft
import requests
from utility.api import API
from utility.setting import Setting

# Initialize configuration
config = Setting()
config.setting_var()

# Initialize API instance
api = API(
    base_url=(
        config.BASE_URL
        if hasattr(config, "BASE_URL")
        else "http://127.0.0.1:8000"
    )
)

# Offline Fallback Mock Data
MOCK_COURSES = {
    "Matematik (Demo)": {
        "ders_time": "2:00 pm",
        "day_of_week": "Mon-Wed",
        "ders_book(pdf)": "pdf/math_sample.pdf",
        "ders_teacher_name": "Ahmet Yılmaz",
    },
    "Fizik (Demo)": {
        "ders_time": "4:00 pm",
        "day_of_week": "Tue-Thu",
        "ders_book(pdf)": "pdf/physics_sample.pdf",
        "ders_teacher_name": "Ayşe Kaya",
    },
    "Kimya (Demo)": {
        "ders_time": "10:00 am",
        "day_of_week": "Friday",
        "ders_book(pdf)": "pdf/chemistry_sample.pdf",
        "ders_teacher_name": "Mehmet Demir",
    },
}


def main(page: ft.Page) -> None:
    page.title = "DERS"
    page.padding = 0

    main_lessons_list = ft.ListView(expand=True, spacing=10, padding=10)

    # 1. Header list for TabBar
    tab_headers = [
        ft.Tab(label="Main"),
        ft.Tab(label="Bookmarks"),
    ]

    # 2. Body view list for TabBarView
    tab_views = [
        ft.Column(controls=[main_lessons_list], expand=True),
        ft.Column(controls=[ft.Text("Bookmarks Content Area")], expand=True),
    ]

    tab_bar = ft.TabBar(tabs=tab_headers)
    tab_bar_view = ft.TabBarView(controls=tab_views, expand=True)

    tabs_container = ft.Tabs(
        length=len(tab_headers),
        selected_index=0,
        expand=True,
        content=ft.Column(
            expand=True,
            controls=[
                tab_bar,
                tab_bar_view,
            ],
        ),
    )

    def close_pdf_tab(header_tab: ft.Tab, view_column: ft.Column):
        """Closes an open PDF tab and safely adjusts the active tab index."""
        if header_tab in tab_headers:
            index_to_remove = tab_headers.index(header_tab)
            tab_headers.remove(header_tab)
            tab_views.remove(view_column)

            tabs_container.length = len(tab_headers)
            tabs_container.selected_index = max(0, index_to_remove - 1)
            page.update()

    def show_offline_state(container: ft.Control, retry_callback, use_demo_callback=None):
        """Displays offline banner with Retry and optional 'Use Offline Data' buttons."""
        action_buttons = [
            ft.FilledButton(
                content=ft.Text("Retry Connection"),
                icon=ft.Icons.REFRESH,
                on_click=lambda e: retry_callback(),
            )
        ]

        if use_demo_callback:
            action_buttons.append(
                ft.OutlinedButton(
                    content=ft.Text("Load Demo Data"),
                    icon=ft.Icons.OFFLINE_PIN,
                    on_click=lambda e: use_demo_callback(),
                )
            )

        offline_ui = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.WIFI_OFF_ROUNDED,
                        size=64,
                        color="grey400",
                    ),
                    ft.Text("You are offline", size=22, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        "Cannot connect to server. Would you like to retry or view offline data?",
                        color="grey600",
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Row(
                        controls=action_buttons,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=12,
            ),
            alignment=ft.Alignment(0, 0),
            expand=True,
        )

        if isinstance(container, (ft.ListView, ft.Column)):
            container.controls = [offline_ui]

        page.update()

    def open_pdf_in_new_tab(pdf_endpoint: str, ders_title: str):
        """Creates a dynamic tab, switches to it, and loads the course PDF."""
        new_header_tab = ft.Tab(label=f"📖 {ders_title}")

        pdf_body_container = ft.Column(
            expand=True,
            controls=[
                ft.Container(
                    content=ft.ProgressRing(),
                    alignment=ft.Alignment(0, 0),
                    expand=True,
                )
            ],
        )

        # Fixed: bgcolor instead of color
        top_header_bar = ft.Container(
            padding=ft.Padding(left=15, top=5, right=15, bottom=5),
            bgcolor="surfaceVariant",
            content=ft.Row(
                controls=[
                    ft.Text(f"Book: {ders_title}", weight=ft.FontWeight.BOLD, size=16),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_size=20,
                        tooltip="Close PDF Tab",
                        on_click=lambda e: close_pdf_tab(new_header_tab, pdf_view_column),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
        )

        pdf_view_column = ft.Column(
            expand=True,
            spacing=0,
            controls=[
                top_header_bar,
                pdf_body_container,
            ],
        )

        # Register header and body view in their respective lists
        tab_headers.append(new_header_tab)
        tab_views.append(pdf_view_column)

        # Sync container length and switch to newly added tab
        tabs_container.length = len(tab_headers)
        tabs_container.selected_index = len(tab_headers) - 1
        page.update()

        try:
            pdf_bytes = api.get_bytes(pdf_endpoint)

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            temp_file.write(pdf_bytes)
            temp_file.close()

            pdf_body_container.controls.clear()
            pdf_body_container.controls.append(
                ft.WebView(
                    url=f"file://{temp_file.name}",
                    expand=True,
                )
            )
        except Exception:
            show_offline_state(
                pdf_body_container,
                retry_callback=lambda: open_pdf_in_new_tab(pdf_endpoint, ders_title),
            )

        page.update()

    def populate_courses(data: dict):
        """Parses course JSON data and builds main cards."""
        main_lessons_list.controls.clear()

        for ders_name, ders_info in data.items():
            time_val = ders_info.get("ders_time", "N/A")
            day_val = ders_info.get("day_of_week", "N/A")
            pdf_endpoint = ders_info.get("ders_book(pdf)", "")
            teacher_val = ders_info.get("ders_teacher_name", "Unknown")

            card = ft.Card(
                content=ft.Container(
                    padding=15,
                    content=ft.Column(
                        controls=[
                            ft.Text(ders_name, size=18, weight=ft.FontWeight.BOLD),
                            ft.Text(f"👨‍🏫 Teacher: {teacher_val}", size=14),
                            ft.Text(f"⏰ Time: {time_val} ({day_val})", size=14),
                            ft.FilledButton(
                                content=ft.Text("View PDF (New Tab)"),
                                icon=ft.Icons.PICTURE_IN_PICTURE_ALT,
                                on_click=lambda e, url=pdf_endpoint, title=ders_name: open_pdf_in_new_tab(
                                    url, title
                                ),
                            ),
                        ]
                    ),
                )
            )
            main_lessons_list.controls.append(card)

        page.update()

    def fetch_data():
        """Fetches initial course list from API with working retry and offline fallback."""
        main_lessons_list.controls.clear()
        main_lessons_list.controls.append(
            ft.Container(
                content=ft.ProgressRing(),
                alignment=ft.Alignment(0, 0),
                expand=True,
            )
        )
        page.update()

        try:
            data = api.get("courses")
            populate_courses(data)
        except Exception:
            show_offline_state(
                main_lessons_list,
                retry_callback=fetch_data,
                use_demo_callback=lambda: populate_courses(MOCK_COURSES),
            )

    page.add(tabs_container)
    fetch_data()


if __name__ == "__main__":
    ft.app(target=main)