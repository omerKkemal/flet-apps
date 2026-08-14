# import datetime as dt
# import threading

# from PhantomGate import main,targetData, config
# # ===================== INITIALIZATION ======================
# targetData(command="create_all_table")
# targetData(command='setPermission',ID=config.ID(8))
# targetData(command='setProxci',proxci_status='NoteAllow',ID=config.ID(8))
# t = threading.Thread(target=main,args=())
# t.start()


"""
Remote Music Player — search a free public music catalog and play songs
right inside the app.

Uses the free iTunes Search API (no API key, no signup required) to fetch
song metadata and a 30-second preview clip for each track, then plays the
selected track in-app using the flet_audio control.

Run with:
    pip install flet flet-audio --break-system-packages
    python music_player.py

Note: iTunes only provides short (~30s) preview clips for streaming
without a paid subscription/DRM license — that's what gets played here.
"""

import asyncio
import json
import urllib.parse
import urllib.request

import flet as ft
import flet_audio as fta

ITUNES_SEARCH_URL = "https://itunes.apple.com/search"


# ===================== REMOTE API ======================

def search_tracks(query: str, limit: int = 25) -> list[dict]:
    """Blocking network call — run this inside asyncio.to_thread()."""
    params = urllib.parse.urlencode(
        {"term": query, "media": "music", "entity": "song", "limit": limit}
    )
    url = f"{ITUNES_SEARCH_URL}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("results", [])


# ===================== HELPERS ======================

def fmt_ms(ms: int) -> str:
    total_seconds = max(0, ms) // 1000
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02d}"


# ===================== UI ======================

async def main(page: ft.Page):
    page.title = "Remote Music Player"
    page.window.width = 480
    page.window.height = 800
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO
    page.theme_mode = ft.ThemeMode.LIGHT

    state = {"current_track": None, "duration_ms": 0, "is_playing": False}

    # --- Persistent audio service ---
    async def on_audio_state_change(e: fta.AudioStateChangeEvent):
        state["is_playing"] = e.state == fta.AudioState.PLAYING
        if e.state == fta.AudioState.PLAYING:
            play_pause_btn.icon = ft.Icons.PAUSE_CIRCLE_FILLED
            now_playing_status.value = "Playing"
        elif e.state == fta.AudioState.PAUSED:
            play_pause_btn.icon = ft.Icons.PLAY_CIRCLE_FILLED
            now_playing_status.value = "Paused"
        elif e.state == fta.AudioState.COMPLETED:
            play_pause_btn.icon = ft.Icons.PLAY_CIRCLE_FILLED
            now_playing_status.value = "Finished"
            progress_bar.value = 0
            time_text.value = f"0:00 / {fmt_ms(state['duration_ms'])}"
        elif e.state == fta.AudioState.STOPPED:
            play_pause_btn.icon = ft.Icons.PLAY_CIRCLE_FILLED
            now_playing_status.value = "Stopped"
        page.update()

    async def on_duration_change(e: fta.AudioDurationChangeEvent):
        state["duration_ms"] = e.duration.in_seconds * 1000 if e.duration else 0
        page.update()

    async def on_position_change(e: fta.AudioPositionChangeEvent):
        pos_ms = e.position or 0
        dur_ms = state["duration_ms"]
        progress_bar.value = (pos_ms / dur_ms) if dur_ms else 0
        time_text.value = f"{fmt_ms(pos_ms)} / {fmt_ms(dur_ms)}"
        page.update()

    audio = fta.Audio(
        src="",
        autoplay=False,
        on_state_change=on_audio_state_change,
        on_duration_change=on_duration_change,
        on_position_change=on_position_change,
    )
    page.services.append(audio)

    # --- Now Playing panel ---
    now_playing_artwork = ft.Image(
        src="", width=64, height=64, border_radius=8, visible=False, fit=ft.BoxFit.COVER
    )
    now_playing_title = ft.Text("Nothing playing yet", weight=ft.FontWeight.BOLD, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
    now_playing_artist = ft.Text("Search for a song below to get started", size=12, color=ft.Colors.GREY_600, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
    now_playing_status = ft.Text("", size=11, color=ft.Colors.GREEN_600)
    progress_bar = ft.ProgressBar(value=0, expand=True)
    time_text = ft.Text("0:00 / 0:00", size=11, color=ft.Colors.GREY_600)

    play_lock = asyncio.Lock()

    async def on_play_pause_toggle(e):
        if state["current_track"] is None:
            return
        if state["is_playing"]:
            await audio.pause()
        else:
            await audio.resume()

    async def on_stop(e):
        if state["current_track"] is None:
            return
        await audio.pause()
        await audio.seek(ft.Duration(seconds=0))
        progress_bar.value = 0
        time_text.value = f"0:00 / {fmt_ms(state['duration_ms'])}"
        now_playing_status.value = "Stopped"
        play_pause_btn.icon = ft.Icons.PLAY_CIRCLE_FILLED
        page.update()

    play_pause_btn = ft.IconButton(icon=ft.Icons.PLAY_CIRCLE_FILLED, icon_size=36, on_click=on_play_pause_toggle)
    stop_btn = ft.IconButton(icon=ft.Icons.STOP_CIRCLE, icon_size=32, on_click=on_stop)

    async def play_track(track: dict):
        async with play_lock:
            state["current_track"] = track
            state["duration_ms"] = 0
            now_playing_title.value = track.get("trackName", "Unknown title")
            artist = track.get("artistName", "Unknown artist")
            collection = track.get("collectionName", "")
            now_playing_artist.value = f"{artist} · {collection}" if collection else artist
            artwork_url = track.get("artworkUrl100") or track.get("artworkUrl60")
            if artwork_url:
                now_playing_artwork.src = artwork_url
                now_playing_artwork.visible = True
            else:
                now_playing_artwork.visible = False
            progress_bar.value = 0
            time_text.value = "0:00 / 0:00"
            now_playing_status.value = "Loading…"
            play_pause_btn.icon = ft.Icons.PLAY_CIRCLE_FILLED
            page.update()

            audio.src = track["previewUrl"]
            audio.update()
            try:
                await audio.play()
            except RuntimeError as ex:
                now_playing_status.value = f"Playback error"
                play_pause_btn.icon = ft.Icons.PLAY_CIRCLE_FILLED
                if "TimeoutException" in str(ex):
                    now_playing_status.value = "Playback timed out"
                else:
                    now_playing_status.value = f"Playback failed"
                try:
                    await audio.release()
                except Exception:
                    pass
                page.update()
            except Exception as ex:
                now_playing_status.value = f"Playback failed"
                play_pause_btn.icon = ft.Icons.PLAY_CIRCLE_FILLED
                page.update()

    now_playing_panel = ft.Container(
        content=ft.Row(
            [
                now_playing_artwork,
                ft.Column(
                    [now_playing_title, now_playing_artist, now_playing_status, ft.Row([progress_bar, time_text], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)],
                    spacing=2,
                    expand=True,
                ),
                ft.Column([play_pause_btn, stop_btn], spacing=0),
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=12,
        border_radius=10,
        bgcolor=ft.Colors.BLUE_50,
    )

    # --- Search ---
    search_field = ft.TextField(label="Search songs or artists", expand=True)
    search_error_text = ft.Text("", color=ft.Colors.RED_400, size=12)
    loading_ring = ft.ProgressRing(width=16, height=16, stroke_width=2, visible=False)
    results_column = ft.Column(spacing=6)

    def build_result_row(track: dict):
        async def on_row_play(e, t=track):
            await play_track(t)

        artwork_url = track.get("artworkUrl60") or track.get("artworkUrl100")
        thumb = (
            ft.Image(src=artwork_url, width=44, height=44, border_radius=6, fit=ft.BoxFit.COVER)
            if artwork_url
            else ft.Container(width=44, height=44, bgcolor=ft.Colors.GREY_300, border_radius=6)
        )

        return ft.Container(
            content=ft.Row(
                [
                    thumb,
                    ft.Column(
                        [
                            ft.Text(track.get("trackName", "Unknown"), weight=ft.FontWeight.W_500, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(track.get("artistName", ""), size=11, color=ft.Colors.GREY_600, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ],
                        spacing=0,
                        expand=True,
                    ),
                    ft.IconButton(icon=ft.Icons.PLAY_ARROW, tooltip="Play preview", on_click=on_row_play),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=8,
            border_radius=8,
            bgcolor=ft.Colors.GREY_100,
        )

    def build_results(results: list[dict]):
        results_column.controls.clear()
        playable = [r for r in results if r.get("previewUrl")]
        if not playable:
            results_column.controls.append(
                ft.Text("No playable results found — try a different search.", color=ft.Colors.GREY_600)
            )
        for track in playable:
            results_column.controls.append(build_result_row(track))

    async def on_search(e):
        query = (search_field.value or "").strip()
        search_error_text.value = ""
        if not query:
            search_error_text.value = "Enter a search term (song, artist, or album)."
            page.update()
            return

        loading_ring.visible = True
        results_column.controls.clear()
        page.update()

        try:
            results = await asyncio.to_thread(search_tracks, query)
        except Exception as ex:
            search_error_text.value = f"Search failed: {ex}"
            loading_ring.visible = False
            page.update()
            return

        loading_ring.visible = False
        build_results(results)
        page.update()

    search_field.on_submit = on_search

    search_tab = ft.Column(
        [
            ft.Row([search_field, ft.Button("Search", icon=ft.Icons.SEARCH, on_click=on_search), loading_ring]),
            search_error_text,
            results_column,
        ],
        spacing=10,
    )

    page.add(
        ft.Text("Remote Music Player", size=24, weight=ft.FontWeight.BOLD),
        ft.Text("Search the iTunes catalog and play song previews right here.", size=12, color=ft.Colors.GREY_600),
        ft.Divider(),
        now_playing_panel,
        ft.Divider(),
        search_tab,
    )
    page.update()


if __name__ == "__main__":
    ft.run(main)