import base64
import json
from pathlib import Path
from urllib.parse import urljoin
import flet as ft
import requests
from utility.api import API
from utility.setting import Setting

try:
    import fitz
except ImportError:
    fitz = None

config = Setting()
config.setting_var()

API_BASE_URL = getattr(config, "BASE_URL", "http://127.0.0.1:8000")
api = API(base_url=API_BASE_URL)
PDF_BASE_URL = "https://digtvbg.com/files/"

# Local JSON storage path for bookmarks
BOOKMARKS_FILE = Path("bookmarks.json")

MOCK_COURSES = {
    "Matematik (Demo)": {
        "ders_time": "2:00 pm",
        "day_of_week": "Mon-Wed",
        "ders_book(pdf)": "books-for-hacking/Hacking%20-%20The%20Art%20of%20Exploitation%2C%202nd%20Edition%20by%20Jon%20Erickson.pdf",
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
    page.title = "DERS Mobile PDF Reader"
    page.padding = 0

    page.window.width = 412
    page.window.height = 892
    page.window.resizable = True

    # In-memory Bookmark Store
    bookmarked_courses = {}

    def load_bookmarks_from_disk():
        """Loads bookmarked courses from the local JSON file if it exists."""
        nonlocal bookmarked_courses
        if BOOKMARKS_FILE.exists():
            try:
                with open(BOOKMARKS_FILE, "r", encoding="utf-8") as f:
                    bookmarked_courses = json.load(f)
            except Exception as e:
                print(f"[Bookmark Load Error] {e}")
                bookmarked_courses = {}
        else:
            bookmarked_courses = {}

    def save_bookmarks_to_disk():
        """Saves current bookmarked courses to the local JSON file."""
        try:
            with open(BOOKMARKS_FILE, "w", encoding="utf-8") as f:
                json.dump(bookmarked_courses, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[Bookmark Save Error] {e}")

    # Initial load of bookmarks on startup
    load_bookmarks_from_disk()

    def render_pdf_in_app(pdf_bytes: bytes) -> ft.ListView:
        if not fitz:
            raise RuntimeError("PyMuPDF (fitz) is not installed.")

        pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pdf_pages_list = ft.ListView(expand=True, spacing=10, padding=8)

        for page_index in range(len(pdf_doc)):
            pdf_page = pdf_doc.load_page(page_index)
            pixmap = pdf_page.get_pixmap(dpi=130)
            img_b64 = base64.b64encode(pixmap.tobytes("png")).decode("utf-8")

            page_card = ft.Card(
                elevation=2,
                content=ft.Container(
                    padding=6,
                    content=ft.Column(
                        controls=[
                            ft.Text(
                                f"Page {page_index + 1} of {len(pdf_doc)}",
                                size=11,
                                color="grey600",
                            ),
                            ft.Image(
                                src=f"data:image/png;base64,{img_b64}",
                                fit="contain",
                                expand=True,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
            )
            pdf_pages_list.controls.append(page_card)

        pdf_doc.close()
        return pdf_pages_list

    def open_pdf_view(pdf_endpoint: str, ders_title: str):
        clean_endpoint = pdf_endpoint.strip() if pdf_endpoint else ""
        if not clean_endpoint:
            return

        # UI Progress & Animation Controls
        progress_bar = ft.ProgressBar(width=260, value=0.0, color="indigo400", bgcolor="grey200")
        percentage_text = ft.Text("0%", size=13, weight=ft.FontWeight.BOLD, color="indigo700")
        status_text = ft.Text("Connecting to server...", size=14, color="grey700", weight=ft.FontWeight.W_500)
        
        # Animated loading visual layout
        loading_card = ft.Card(
            elevation=4,
            content=ft.Container(
                padding=24,
                width=320,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.PICTURE_AS_PDF_ROUNDED, size=52, color="indigo500"),
                        ft.Container(height=8),
                        ft.ProgressRing(width=36, height=36, stroke_width=3, color="indigo400"),
                        ft.Container(height=12),
                        status_text,
                        ft.Container(height=8),
                        progress_bar,
                        percentage_text,
                    ],
                    spacing=6,
                ),
            ),
        )

        body_container = ft.Column(
            expand=True,
            controls=[
                ft.Container(
                    content=loading_card,
                    alignment=ft.Alignment(0, 0),
                    expand=True,
                )
            ],
        )

        def go_back(e):
            if len(page.views) > 1:
                page.views.pop()
                page.update()

        pdf_screen = ft.View(
            route="/pdf",
            padding=0,
            controls=[
                ft.AppBar(
                    title=ft.Text(ders_title, size=18, weight=ft.FontWeight.BOLD),
                    center_title=True,
                    bgcolor="surfaceVariant",
                    leading=ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        on_click=go_back,
                    ),
                ),
                body_container,
            ],
        )

        page.views.append(pdf_screen)
        page.update()

        try:
            if clean_endpoint.startswith(("http://", "https://")):
                full_download_url = clean_endpoint
            else:
                base_pdf = PDF_BASE_URL if PDF_BASE_URL.endswith("/") else PDF_BASE_URL + "/"
                full_download_url = urljoin(base_pdf, clean_endpoint.lstrip("/"))

            headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Mobile Safari/537.36",
                "Accept": "*/*",
            }

            # Stream response to measure progress
            resp = requests.get(full_download_url, headers=headers, stream=True, timeout=90)
            resp.raise_for_status()

            total_length = resp.headers.get("content-length")
            pdf_bytes = bytearray()

            status_text.value = "Downloading PDF..."
            page.update()

            if total_length is None:
                # Content-length header missing: show indeterminate progress
                progress_bar.value = None
                percentage_text.value = "Downloading..."
                page.update()
                pdf_bytes = resp.content
            else:
                total_size = int(total_length)
                downloaded = 0
                chunk_size = 8192

                for chunk in resp.iter_content(chunk_size=chunk_size):
                    if chunk:
                        pdf_bytes.extend(chunk)
                        downloaded += len(chunk)
                        progress = min(downloaded / total_size, 1.0)
                        progress_bar.value = progress
                        percentage_text.value = f"{int(progress * 100)}%"
                        page.update()

            # Page rendering stage
            status_text.value = "Rendering PDF pages..."
            progress_bar.value = None  # Pulse indicator during rendering
            percentage_text.value = "Almost ready..."
            page.update()

            viewer = render_pdf_in_app(bytes(pdf_bytes))
            body_container.controls.clear()
            body_container.controls.append(viewer)

        except Exception as err:
            body_container.controls.clear()
            body_container.controls.append(
                ft.Container(
                    padding=20,
                    alignment=ft.Alignment(0, 0),
                    expand=True,
                    content=ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, size=56, color="red400"),
                            ft.Text("Unable to open PDF", size=18, weight=ft.FontWeight.BOLD),
                            ft.Text(
                                str(err),
                                size=12,
                                color="grey600",
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.FilledButton(
                                content=ft.Text("Retry"),
                                icon=ft.Icons.REFRESH,
                                on_click=lambda e: open_pdf_view(clean_endpoint, ders_title),
                            ),
                        ],
                        spacing=12,
                    ),
                )
            )

        page.update()

    courses_list = ft.ListView(expand=True, spacing=12, padding=12)
    bookmarks_list = ft.ListView(expand=True, spacing=12, padding=12)

    content_switcher = ft.Container(content=courses_list, expand=True)

    def update_bookmarks_ui():
        """Renders the list of bookmarked courses."""
        bookmarks_list.controls.clear()
        if not bookmarked_courses:
            bookmarks_list.controls.append(
                ft.Container(
                    alignment=ft.Alignment(0, 0),
                    padding=40,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.BOOKMARK_BORDER, size=56, color="grey400"),
                            ft.Text("No Bookmarks Saved", color="grey600", size=16),
                            ft.Text(
                                "Tap the bookmark icon on any lesson card to save it here.",
                                color="grey500",
                                size=12,
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        spacing=8,
                    ),
                )
            )
        else:
            for ders_name, ders_info in bookmarked_courses.items():
                teacher = ders_info.get("ders_teacher_name", "Unknown")
                pdf_endpoint = (
                    ders_info.get("ders_book(pdf)")
                    or ders_info.get("ders_book")
                    or ders_info.get("pdf")
                    or ""
                )

                card = ft.Card(
                    elevation=2,
                    content=ft.Container(
                        padding=14,
                        content=ft.Column(
                            controls=[
                                ft.Text(ders_name, size=17, weight=ft.FontWeight.BOLD),
                                ft.Text(f"👨‍🏫 Teacher: {teacher}", size=13, color="grey800"),
                                ft.Row(
                                    controls=[
                                        ft.FilledButton(
                                            content=ft.Text("Read Book", size=14),
                                            icon=ft.Icons.CHEVRON_RIGHT,
                                            expand=True,
                                            on_click=lambda e, url=pdf_endpoint, title=ders_name: open_pdf_view(
                                                url, title
                                            ),
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.DELETE_OUTLINE,
                                            icon_color="red400",
                                            tooltip="Remove Bookmark",
                                            on_click=lambda e, name=ders_name: remove_bookmark(name),
                                        ),
                                    ],
                                    spacing=8,
                                ),
                            ],
                            spacing=6,
                        ),
                    ),
                )
                bookmarks_list.controls.append(card)

    def remove_bookmark(ders_name: str):
        if ders_name in bookmarked_courses:
            del bookmarked_courses[ders_name]
            save_bookmarks_to_disk()
            update_bookmarks_ui()
            if current_courses_data:
                populate_courses(current_courses_data)
            page.update()

    def on_nav_change(e):
        selected_idx = e.control.selected_index if hasattr(e.control, "selected_index") else int(e.data)
        if selected_idx == 0:
            content_switcher.content = courses_list
        else:
            update_bookmarks_ui()
            content_switcher.content = bookmarks_list
        page.update()

    nav_bar = ft.NavigationBar(
        selected_index=0,
        on_change=on_nav_change,
        destinations=[
            ft.NavigationBarDestination(
                icon=ft.Icons.MENU_BOOK_OUTLINED,
                selected_icon=ft.Icons.MENU_BOOK,
                label="Lessons",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.BOOKMARK_OUTLINE,
                selected_icon=ft.Icons.BOOKMARK,
                label="Bookmarks",
            ),
        ],
    )

    main_screen = ft.View(
        route="/",
        padding=0,
        controls=[
            ft.AppBar(
                title=ft.Text("DERS Library", weight=ft.FontWeight.BOLD),
                center_title=True,
                bgcolor="surfaceVariant",
            ),
            content_switcher,
            nav_bar,
        ],
    )

    current_courses_data = {}

    def populate_courses(data: dict):
        nonlocal current_courses_data
        current_courses_data = data
        courses_list.controls.clear()

        for ders_name, ders_info in data.items():
            teacher = ders_info.get("ders_teacher_name", "Unknown")
            time_val = ders_info.get("ders_time", "N/A")
            day_val = ders_info.get("ders_day", ders_info.get("day_of_week", "N/A"))
            pdf_endpoint = (
                ders_info.get("ders_book(pdf)")
                or ders_info.get("ders_book")
                or ders_info.get("pdf")
                or ""
            )

            is_bookmarked = ders_name in bookmarked_courses

            def toggle_bookmark(e, name=ders_name, info=ders_info):
                if name in bookmarked_courses:
                    del bookmarked_courses[name]
                    e.control.icon = ft.Icons.BOOKMARK_BORDER
                    e.control.icon_color = None
                    e.control.tooltip = "Add to Bookmark"
                else:
                    bookmarked_courses[name] = info
                    e.control.icon = ft.Icons.BOOKMARK
                    e.control.icon_color = "amber700"
                    e.control.tooltip = "Remove Bookmark"
                
                save_bookmarks_to_disk()
                page.update()

            card = ft.Card(
                elevation=2,
                content=ft.Container(
                    padding=14,
                    content=ft.Column(
                        controls=[
                            ft.Text(ders_name, size=17, weight=ft.FontWeight.BOLD),
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.PERSON_OUTLINE, size=16, color="grey700"),
                                    ft.Text(f"Teacher: {teacher}", size=13, color="grey800"),
                                ],
                                spacing=6,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.ACCESS_TIME, size=16, color="grey700"),
                                    ft.Text(f"{time_val} ({day_val})", size=13, color="grey800"),
                                ],
                                spacing=6,
                            ),
                            ft.Container(height=4),
                            ft.Row(
                                controls=[
                                    ft.FilledButton(
                                        content=ft.Text("Read Book", size=14),
                                        icon=ft.Icons.CHEVRON_RIGHT,
                                        expand=True,
                                        on_click=lambda e, url=pdf_endpoint, title=ders_name: open_pdf_view(
                                            url, title
                                        ),
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.BOOKMARK if is_bookmarked else ft.Icons.BOOKMARK_BORDER,
                                        icon_color="amber700" if is_bookmarked else None,
                                        tooltip="Remove Bookmark" if is_bookmarked else "Add to Bookmark",
                                        on_click=toggle_bookmark,
                                    ),
                                ],
                                spacing=8,
                            ),
                        ],
                        spacing=6,
                    ),
                ),
            )
            courses_list.controls.append(card)
        page.update()

    def fetch_data():
        courses_list.controls.clear()
        courses_list.controls.append(
            ft.Container(
                alignment=ft.Alignment(0, 0),
                expand=True,
                content=ft.ProgressRing(),
            )
        )
        page.update()

        try:
            data = api.get("courses")
            populate_courses(data)
        except Exception as err:
            print(f"[API Offline] {err}. Auto-switching to Mock Data...")
            populate_courses(MOCK_COURSES)

    def handle_view_pop(e):
        page.views.pop()
        page.update()

    page.on_view_pop = handle_view_pop
    page.views.clear()
    page.views.append(main_screen)
    page.update()

    fetch_data()


if __name__ == "__main__":
    ft.app(target=main)