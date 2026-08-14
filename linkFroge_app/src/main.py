"""
LinkFroge GUI — Enhanced Edition (Mobile-optimized)
"""

import builtins
import contextlib
import io
import json
import threading
import time
import subprocess
from pathlib import Path
from datetime import datetime

import flet as ft
import requests

import linkFroge as lf

# -------------------- Settings persistence --------------------
SETTINGS_FILE = Path.home() / ".linkfroge" / "gui_settings.json"

def load_settings():
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}

def save_settings(data):
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)
    try:
        SETTINGS_FILE.chmod(0o600)
    except OSError:
        pass

# -------------------- Log stream with timestamp --------------------
class LogStream(io.TextIOBase):
    def __init__(self, callback, color_map=None):
        self.callback = callback
        self.color_map = color_map or {
            "[+]": ft.Colors.GREEN_400,
            "[!]": ft.Colors.ORANGE_400,
            "[*]": ft.Colors.BLUE_400,
            "[VERBOSE]": ft.Colors.GREY_400,
        }
        self.buffer = ""

    def write(self, s):
        if not s:
            return 0
        self.buffer += s.replace("\r", "\n")
        if "\n" in self.buffer:
            lines = self.buffer.split("\n")
            self.buffer = lines[-1]
            for line in lines[:-1]:
                if line.strip():
                    self._emit(line)
        return len(s)

    def flush(self):
        if self.buffer:
            self._emit(self.buffer)
            self.buffer = ""

    def _emit(self, line):
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = ft.Colors.WHITE
        for prefix, col in self.color_map.items():
            if line.startswith(prefix):
                color = col
                break
        self.callback(f"[{timestamp}] {line}", color)

# -------------------- Main App --------------------
def main(page: ft.Page):
    page.title = "LinkFroge"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 16  # reduced for mobile
    page.window.width = 820
    page.window.height = 920
    page.window.min_width = 360
    page.window.min_height = 600
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.scroll = ft.ScrollMode.AUTO  # enable scrolling on small screens

    # ---------- State ----------
    state = {
        "running": False,
        "public_url": None,
        "ngrok_process": None,
        "settings": load_settings(),
    }

    # ---------- UI controls ----------
    clipboard = ft.Clipboard()
    snack = ft.SnackBar(content=ft.Text(""), open=False)
    page.overlay.append(snack)

    # Input fields – all with responsive column spans
    port_field = ft.TextField(
        label="Local port",
        value=str(state["settings"].get("port", lf.config["port"])),
        input_filter=ft.NumbersOnlyInputFilter(),
        on_change=lambda e: auto_save_settings(),
        col={"xs": 12, "sm": 4, "md": 3},
    )
    api_field = ft.TextField(
        label="LinkFroge API endpoint",
        value=state["settings"].get("api", lf.config["linkfroge_api"]),
        expand=True,
        on_change=lambda e: auto_save_settings(),
        col={"xs": 12},
    )
    service_id_field = ft.TextField(
        label="Service ID (optional)",
        value=state["settings"].get("service_id", ""),
        on_change=lambda e: auto_save_settings(),
        col={"xs": 12, "md": 6},
    )
    service_token_field = ft.TextField(
        label="Service token (optional)",
        password=True,
        can_reveal_password=True,
        value=state["settings"].get("service_token", ""),
        on_change=lambda e: auto_save_settings(),
        col={"xs": 12, "md": 6},
    )
    ngrok_token_field = ft.TextField(
        label="Ngrok auth token (only needed the first time)",
        password=True,
        can_reveal_password=True,
        value=state["settings"].get("ngrok_token", ""),
        expand=True,
        on_change=lambda e: auto_save_settings(),
        col={"xs": 12},
    )
    register_checkbox = ft.Checkbox(
        label="Register a new service ID on start",
        value=state["settings"].get("register", False),
        on_change=lambda e: auto_save_settings(),
        col={"xs": 12, "sm": 4, "md": 4},
    )
    verbose_checkbox = ft.Checkbox(
        label="Verbose logging",
        value=state["settings"].get("verbose", False),
        on_change=lambda e: auto_save_settings(),
        col={"xs": 12, "sm": 4, "md": 4},
    )

    all_inputs = [
        port_field, api_field, service_id_field, service_token_field,
        ngrok_token_field, register_checkbox, verbose_checkbox,
    ]

    # Status display
    status_dot = ft.Container(width=10, height=10, border_radius=5, bgcolor=ft.Colors.RED_400)
    status_label = ft.Text("Stopped", size=13)
    url_text = ft.Text("No active tunnel", size=16, weight=ft.FontWeight.BOLD, selectable=True)

    # Log view
    log_view = ft.ListView(expand=True, spacing=1, auto_scroll=True)
    log_lock = threading.Lock()

    def add_log(message, color=ft.Colors.WHITE):
        with log_lock:
            log_view.controls.append(
                ft.Text(message, size=12, font_family="Consolas, monospace", selectable=True, color=color)
            )
            if len(log_view.controls) > 500:
                del log_view.controls[:50]
        page.update()

    def flash(msg, is_error=False):
        snack.content = ft.Text(msg, color=ft.Colors.WHITE)
        snack.bgcolor = ft.Colors.RED_400 if is_error else ft.Colors.GREEN_700
        snack.open = True
        page.update()

    # Buttons
    async def copy_url(e):
        if state["public_url"]:
            await clipboard.set(state["public_url"])
            flash("Public URL copied to clipboard")

    def open_url(e):
        if state["public_url"]:
            page.launch_url(state["public_url"])

    async def refresh_link(e):
        if not state["public_url"]:
            flash("No tunnel running", is_error=True)
            return
        service_id = service_id_field.value.strip()
        service_token = service_token_field.value.strip()
        if not service_id or not service_token:
            flash("Service ID and token required", is_error=True)
            return
        lf.config["service-id"] = service_id
        lf.config["service-token"] = service_token
        lf.config["linkfroge_api"] = api_field.value.strip()
        success = lf.update_service_link(state["public_url"])
        if success:
            flash("Service link updated successfully")
            add_log("[+] Service link refreshed.", ft.Colors.GREEN_400)
        else:
            flash("Failed to update service link", is_error=True)
            add_log("[!] Service link update failed.", ft.Colors.RED_400)

    copy_btn = ft.IconButton(icon=ft.Icons.COPY, tooltip="Copy URL", on_click=copy_url, disabled=True)
    open_btn = ft.IconButton(icon=ft.Icons.OPEN_IN_NEW, tooltip="Open in browser", on_click=open_url, disabled=True)
    refresh_btn = ft.Button("Refresh Service Link", icon=ft.Icons.REFRESH, disabled=True, on_click=refresh_link, col={"xs": 12, "sm": 4})
    clear_log_btn = ft.Button("Clear Log", icon=ft.Icons.CLEAR, on_click=lambda e: clear_log())
    auto_scroll_check = ft.Checkbox(label="Auto-scroll", value=True, on_change=lambda e: set_auto_scroll())

    def clear_log():
        log_view.controls.clear()
        page.update()

    def set_auto_scroll():
        log_view.auto_scroll = auto_scroll_check.value
        page.update()

    # ---------- Core functions ----------
    def set_ui_running(running: bool):
        start_btn.disabled = running
        stop_btn.disabled = not running
        refresh_btn.disabled = not (running and service_id_field.value and service_token_field.value)
        for f in all_inputs:
            f.disabled = running
        status_dot.bgcolor = ft.Colors.GREEN_400 if running else ft.Colors.RED_400
        status_label.value = "Running" if running else "Stopped"
        page.update()

    def set_url(public_url: str):
        state["public_url"] = public_url
        url_text.value = public_url
        copy_btn.disabled = False
        open_btn.disabled = False
        refresh_btn.disabled = not (public_url and service_id_field.value and service_token_field.value)
        page.update()

    def clear_url():
        state["public_url"] = None
        url_text.value = "No active tunnel"
        copy_btn.disabled = True
        open_btn.disabled = True
        refresh_btn.disabled = True
        page.update()

    save_timer = {"t": None}

    def auto_save_settings():
        def _write():
            data = {
                "port": port_field.value,
                "api": api_field.value,
                "service_id": service_id_field.value,
                "service_token": service_token_field.value,
                "ngrok_token": ngrok_token_field.value,
                "register": register_checkbox.value,
                "verbose": verbose_checkbox.value,
            }
            save_settings(data)

        if save_timer["t"] is not None:
            save_timer["t"].cancel()
        t = threading.Timer(0.4, _write)
        t.daemon = True
        save_timer["t"] = t
        t.start()

    # ---------- Worker: start tunnel ----------
    def run_tunnel() -> bool:
        try:
            port = int(port_field.value or lf.config["port"])
        except ValueError:
            port = lf.config["port"]
            port_field.value = str(port)
            flash("Invalid port, using default", is_error=True)

        lf.config["port"] = port
        lf.config["verbose"] = verbose_checkbox.value
        lf.config["linkfroge_api"] = api_field.value.strip() or lf.config["linkfroge_api"]
        lf.config["service-id"] = service_id_field.value.strip() or None
        lf.config["service-token"] = service_token_field.value.strip() or None
        lf.config["ng-auth-token"] = ngrok_token_field.value.strip() or None
        lf.config["Register-service-id"] = register_checkbox.value

        auto_save_settings()

        api_url = lf.config["linkfroge_api"]
        if api_url.startswith("https://127.0.0.1") or api_url.startswith("https://localhost"):
            lf.config["linkfroge_api"] = api_url.replace("https://", "http://")
            add_log("[*] Changed LinkFroge API to HTTP for localhost.", ft.Colors.BLUE_400)

        add_log("[+] Checking for ngrok binary...")
        if not lf.does_ngrok_exist():
            lf.DownloadNgrok(lf.config["download-ngrok"], lf.config["ngpath"])

        add_log("[+] Validating ngrok auth token...")
        if not lf.is_ng_auth_token_valid():
            add_log("[!] Ngrok authentication failed. Enter a valid auth token and try again.", ft.Colors.ORANGE_400)
            return False

        add_log(f"[+] Starting ngrok on port {port}...")
        try:
            cmd = [
                str(Path(lf.config["ngpath"]) / lf.ngrok_executable),
                "http", str(port),
                "--config", str(Path(lf.config["ngpath"]) / "ngrok.yml")
            ]
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            state["ngrok_process"] = proc
        except Exception as e:
            add_log(f"[!] Failed to start ngrok: {e}", ft.Colors.RED_400)
            return False

        public_url = None
        max_retries = 12
        for attempt in range(max_retries):
            time.sleep(1.5)
            success, u = lf.get_ngrok_link()
            if success and u:
                public_url = u
                break
            add_log(f"[*] Attempt {attempt+1}/{max_retries} - ngrok not ready yet, retrying...", ft.Colors.BLUE_400)

        if not public_url:
            add_log("[!] Failed to obtain ngrok public URL after multiple attempts.", ft.Colors.RED_400)
            stop_ngrok_process()
            return False

        set_url(public_url)

        service_id = lf.config.get("service-id")
        service_token = lf.config.get("service-token")
        if service_id and service_token:
            exists, current_link = lf.check_if_service_id_exists()
            if exists:
                if current_link != public_url:
                    lf.update_service_link(public_url)
                else:
                    add_log(f"[!] No need to update. Current link matches: {current_link}", ft.Colors.ORANGE_400)
            else:
                add_log("[!] Service ID does not exist. Create it first via the LinkFroge API,", ft.Colors.ORANGE_400)
                add_log(f"    or check 'Register a new service ID on start'. Link: {public_url}", ft.Colors.ORANGE_400)
        else:
            add_log("[+] No service credentials provided; tunnel is local-only.")
            add_log(f"[+] Public URL: {public_url}")

        if lf.config.get("Register-service-id") and lf.config.get("service-token"):
            add_log("[+] Registering service ID with LinkFroge...")
            headers = {"Authorization": f"Bearer {lf.config['service-token']}"}
            body = {"link": public_url}
            try:
                response = requests.post(
                    f"{lf.config['linkfroge_api']}/register_service",
                    headers=headers,
                    json=body
                )
                if response.status_code == 200:
                    data = response.json()
                    new_id = data.get("service_link_id")
                    lf.config["service-id"] = new_id
                    if new_id:
                        service_id_field.value = new_id
                        add_log(f"[+] Service ID registered: {new_id}", ft.Colors.GREEN_400)
                        auto_save_settings()
                else:
                    add_log(f"[!] Failed to register service ID. Status: {response.status_code}", ft.Colors.RED_400)
            except Exception as exc:
                add_log(f"[!] Error registering service ID: {exc}", ft.Colors.RED_400)

        add_log("[+] Tunnel is live. Click 'Stop tunnel' to end it.", ft.Colors.GREEN_400)
        return True

    def stop_ngrok_process():
        proc = state.get("ngrok_process")
        if proc and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=5)
                add_log("[+] Ngrok process terminated.")
            except subprocess.TimeoutExpired:
                proc.kill()
                add_log("[!] Ngrok process had to be killed.", ft.Colors.ORANGE_400)
            except Exception as e:
                add_log(f"[!] Error stopping ngrok: {e}", ft.Colors.RED_400)
        state["ngrok_process"] = None

    def stop_flow():
        stop_ngrok_process()
        lf.stop_ngrok()
        clear_url()
        set_ui_running(False)

    # ---------- Button handlers ----------
    def start_click(e):
        if state["running"]:
            return
        try:
            port = int(port_field.value)
            if not (1 <= port <= 65535):
                raise ValueError
        except ValueError:
            flash("Invalid port number", is_error=True)
            return
        if not api_field.value.strip():
            flash("API endpoint cannot be empty", is_error=True)
            return

        state["running"] = True
        log_view.controls.clear()
        set_ui_running(True)
        status_label.value = "Starting..."
        page.update()
        threading.Thread(target=worker, daemon=True).start()

    def stop_click(e):
        state["running"] = False
        status_label.value = "Stopping..."
        page.update()
        threading.Thread(target=stop_flow, daemon=True).start()

    def worker():
        stream = LogStream(add_log)
        old_input = builtins.input

        def fake_input(prompt=""):
            if prompt:
                add_log(prompt)
            token = ngrok_token_field.value.strip()
            add_log(token if token else "(no ngrok auth token entered)")
            return token

        builtins.input = fake_input
        succeeded = False
        try:
            with contextlib.redirect_stdout(stream):
                succeeded = run_tunnel()
        except Exception as exc:
            add_log(f"[!] Unexpected error: {exc}", ft.Colors.RED_400)
        finally:
            stream.flush()
            builtins.input = old_input
            if not succeeded:
                clear_url()
                state["running"] = False
            set_ui_running(succeeded)
            auto_save_settings()

    # ---------- Assemble UI ----------
    start_btn = ft.Button(
        "Start tunnel", icon=ft.Icons.PLAY_ARROW,
        bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE,
        on_click=start_click,
        col={"xs": 12, "sm": 4},
    )
    stop_btn = ft.Button(
        "Stop tunnel", icon=ft.Icons.STOP,
        bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE,
        disabled=True, on_click=stop_click,
        col={"xs": 12, "sm": 4},
    )

    # Build the page using ResponsiveRow for all sections
    page.add(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.LINK, size=32, color=ft.Colors.GREEN_400),
                        ft.Text("LinkFroge", size=28, weight=ft.FontWeight.BOLD),
                        ft.Container(expand=True),
                        ft.IconButton(icon=ft.Icons.SETTINGS, tooltip="Save settings", on_click=lambda e: auto_save_settings()),
                    ],
                    spacing=10,
                ),
                ft.Text(
                    "Expose a local server through ngrok and optionally keep a LinkFroge service link pointed at it.",
                    size=13, color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.Divider(),
                # Port + checkboxes row
                ft.ResponsiveRow(
                    [port_field, register_checkbox, verbose_checkbox],
                    spacing=10,
                    run_spacing=10,
                ),
                # API endpoint (full width)
                ft.ResponsiveRow([api_field], spacing=0),
                # Service ID / Token row
                ft.ResponsiveRow(
                    [service_id_field, service_token_field],
                    spacing=12,
                    run_spacing=10,
                ),
                # Ngrok token (full width)
                ft.ResponsiveRow([ngrok_token_field], spacing=0),
                # Action buttons
                ft.ResponsiveRow(
                    [start_btn, stop_btn, refresh_btn],
                    spacing=12,
                    run_spacing=10,
                ),
                ft.Divider(),
                # Status and log controls
                ft.ResponsiveRow(
                    [
                        ft.Row([status_dot, status_label], spacing=8, col={"xs": 12, "sm": 6}),
                        ft.Row([clear_log_btn, auto_scroll_check], spacing=8, alignment=ft.MainAxisAlignment.END, col={"xs": 12, "sm": 6}),
                    ],
                    spacing=10,
                    run_spacing=10,
                ),
                ft.Row([url_text, copy_btn, open_btn], spacing=4, wrap=True),
                ft.Divider(),
                ft.Text("Log", size=13, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=log_view,
                    bgcolor=ft.Colors.BLACK,
                    border_radius=6,
                    padding=10,
                    height=300,
                ),
            ],
            spacing=14,
            expand=True,
        )
    )

    # Initial save to create settings file if missing
    auto_save_settings()

if __name__ == "__main__":
    ft.run(main, view=ft.AppView.WEB_BROWSER)