import base64
import hashlib
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

# Local storage paths
BOOKMARKS_FILE = Path("bookmarks.json")
CACHE_DIR = Path(".pdf_cache")
CACHE_DIR.mkdir(exist_ok=True)

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

    # Page transition animations across platforms
    page.theme = ft.Theme(
        page_transitions=ft.PageTransitionsTheme(
            android=ft.PageTransitionTheme.ZOOM,
            ios=ft.PageTransitionTheme.CUPERTINO,
            windows=ft.PageTransitionTheme.ZOOM,
            macos=ft.PageTransitionTheme.CUPERTINO,
        )
    )

    # In-memory Bookmark Store
    bookmarked_courses = {}

    def load_bookmarks_from_disk():
        """Loads bookmarked courses from local JSON."""
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
        """Saves current bookmarked courses to local JSON."""
        try:
            with open(BOOKMARKS_FILE, "w", encoding="utf-8") as f:
                json.dump(bookmarked_courses, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[Bookmark Save Error] {e}")

    load_bookmarks_from_disk()

    def reset_button(btn: ft.FilledButton):
        """Restores the button to its default state with icon and text."""
        if btn:
            btn.content = ft.Row(
                controls=[
                    ft.Text("Read Book", size=14),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, size=18),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=4,
            )
            btn.disabled = False
            page.update()

    def build_single_page_viewer(pdf_bytes: bytes) -> ft.Control:
        """Renders one page at a time using PyMuPDF for smooth memory usage."""
        if not fitz:
            raise RuntimeError("PyMuPDF (fitz) is not installed.")

        pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(pdf_doc)
        current_page = [0]

        def render_page_b64(page_num: int) -> str:
            pdf_page = pdf_doc.load_page(page_num)
            pixmap = pdf_page.get_pixmap(dpi=110)
            return f"data:image/png;base64,{base64.b64encode(pixmap.tobytes('png')).decode('utf-8')}"

        img_display = ft.Image(
            src=render_page_b64(0),
            fit="contain",
            expand=True,
        )

        page_indicator = ft.Text(
            f"Page 1 of {total_pages}",
            size=14,
            weight=ft.FontWeight.BOLD,
            color="grey800",
        )

        prev_button = ft.IconButton(
            icon=ft.Icons.NAVIGATE_BEFORE,
            icon_size=28,
            disabled=True,
            tooltip="Previous Page",
        )

        next_button = ft.IconButton(
            icon=ft.Icons.NAVIGATE_NEXT,
            icon_size=28,
            disabled=(total_pages <= 1),
            tooltip="Next Page",
        )

        def change_page(delta: int):
            new_idx = current_page[0] + delta
            if 0 <= new_idx < total_pages:
                current_page[0] = new_idx
                img_display.src = render_page_b64(new_idx)
                page_indicator.value = f"Page {new_idx + 1} of {total_pages}"
                prev_button.disabled = new_idx == 0
                next_button.disabled = new_idx == total_pages - 1
                page.update()

        prev_button.on_click = lambda e: change_page(-1)
        next_button.on_click = lambda e: change_page(1)

        pagination_bar = ft.Container(
            padding=ft.Padding(12, 6, 12, 6),
            bgcolor="surfaceVariant",
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    prev_button,
                    page_indicator,
                    next_button,
                ],
            ),
        )

        return ft.Column(
            expand=True,
            spacing=0,
            controls=[
                ft.Container(
                    content=img_display,
                    expand=True,
                    alignment=ft.Alignment(0, 0),
                    padding=8,
                ),
                pagination_bar,
            ],
        )

    def open_pdf_view(pdf_endpoint: str, ders_title: str, clicked_btn=None):
        clean_endpoint = pdf_endpoint.strip() if pdf_endpoint else ""
        if not clean_endpoint:
            reset_button(clicked_btn)
            return

        progress_bar = ft.ProgressBar(width=260, value=0.0, color="indigo400", bgcolor="grey200")
        percentage_text = ft.Text("0%", size=13, weight=ft.FontWeight.BOLD, color="indigo700")
        status_text = ft.Text("Connecting...", size=14, color="grey700", weight=ft.FontWeight.W_500)

        loading_card = ft.Card(
            elevation=4,
            opacity=0,
            scale=0.85,
            animate_opacity=ft.Animation(350, ft.AnimationCurve.EASE_OUT),
            animate_scale=ft.Animation(350, ft.AnimationCurve.EASE_OUT_BACK),
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

        loading_card.opacity = 1.0
        loading_card.scale = 1.0
        page.update()

        try:
            # Generate local filename hash
            cache_key = hashlib.md5(clean_endpoint.encode("utf-8")).hexdigest() + ".pdf"
            cached_file_path = CACHE_DIR / cache_key

            # 1. READ FROM LOCAL DISK CACHE IF AVAILABLE
            if cached_file_path.exists():
                status_text.value = "Opening cached file..."
                progress_bar.value = 1.0
                percentage_text.value = "100%"
                page.update()

                with open(cached_file_path, "rb") as f:
                    pdf_bytes = f.read()

            # 2. DOWNLOAD FROM NETWORK IF NOT CACHED
            else:
                if clean_endpoint.startswith(("http://", "https://")):
                    full_download_url = clean_endpoint
                else:
                    base_pdf = PDF_BASE_URL if PDF_BASE_URL.endswith("/") else PDF_BASE_URL + "/"
                    full_download_url = urljoin(base_pdf, clean_endpoint.lstrip("/"))

                headers = {
                    "User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Mobile Safari/537.36",
                    "Accept": "*/*",
                }

                resp = requests.get(full_download_url, headers=headers, stream=True, timeout=90)
                resp.raise_for_status()

                total_length = resp.headers.get("content-length")
                pdf_bytes = bytearray()

                status_text.value = "Downloading PDF..."
                page.update()

                if total_length is None:
                    progress_bar.value = None
                    percentage_text.value = "Downloading..."
                    page.update()
                    pdf_bytes = resp.content
                else:
                    total_size = int(total_length)
                    downloaded = 0
                    chunk_size = 64 * 1024  # 64 KB chunks
                    last_percent = -1

                    for chunk in resp.iter_content(chunk_size=chunk_size):
                        if chunk:
                            pdf_bytes.extend(chunk)
                            downloaded += len(chunk)
                            progress = min(downloaded / total_size, 1.0)
                            current_percent = int(progress * 100)

                            # Throttle UI renders to whole percentage changes
                            if current_percent != last_percent:
                                last_percent = current_percent
                                progress_bar.value = progress
                                percentage_text.value = f"{current_percent}%"
                                page.update()

                # Save file to cache for future requests
                with open(cached_file_path, "wb") as f:
                    f.write(pdf_bytes)

            status_text.value = "Rendering page..."
            page.update()

            # Render viewer
            viewer = build_single_page_viewer(bytes(pdf_bytes))
            viewer_container = ft.Container(
                content=viewer,
                opacity=0,
                animate_opacity=ft.Animation(400, ft.AnimationCurve.EASE_IN_OUT),
                expand=True,
            )

            body_container.controls.clear()
            body_container.controls.append(viewer_container)
            page.update()

            viewer_container.opacity = 1.0
            page.update()

            reset_button(clicked_btn)

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
                                on_click=lambda e: handle_read_click(e, clean_endpoint, ders_title),
                            ),
                        ],
                        spacing=12,
                    ),
                )
            )
            reset_button(clicked_btn)

        page.update()

    def handle_read_click(e, url, title):
        btn = e.control
        btn.disabled = True

        # In-button spinning indicator
        btn.content = ft.Row(
            controls=[
                ft.ProgressRing(width=16, height=16, stroke_width=2.5, color="white"),
                ft.Text("Loading...", size=14),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        )
        page.update()

        # Execute PDF fetching and rendering in the background.
        # Using page.run_thread (instead of a raw threading.Thread)
        # keeps page.update() calls from this background work properly
        # synced with Flet's own event loop, so the UI updates right
        # away instead of only flushing on the next unrelated click.
        page.run_thread(open_pdf_view, url, title, btn)

    courses_list = ft.ListView(expand=True, spacing=12, padding=12)
    bookmarks_list = ft.ListView(expand=True, spacing=12, padding=12)
    content_switcher = ft.Container(content=courses_list, expand=True)

    def update_bookmarks_ui():
        """Renders list of bookmarked courses."""
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
                                            content=ft.Row(
                                                controls=[
                                                    ft.Text("Read Book", size=14),
                                                    ft.Icon(ft.Icons.CHEVRON_RIGHT, size=18),
                                                ],
                                                alignment=ft.MainAxisAlignment.CENTER,
                                                spacing=4,
                                            ),
                                            expand=True,
                                            on_click=lambda e, url=pdf_endpoint, title=ders_name: handle_read_click(
                                                e, url, title
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
                                        content=ft.Row(
                                            controls=[
                                                ft.Text("Read Book", size=14),
                                                ft.Icon(ft.Icons.CHEVRON_RIGHT, size=18),
                                            ],
                                            alignment=ft.MainAxisAlignment.CENTER,
                                            spacing=4,
                                        ),
                                        expand=True,
                                        on_click=lambda e, url=pdf_endpoint, title=ders_name: handle_read_click(
                                            e, url, title
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