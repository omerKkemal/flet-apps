# LinkFroge GUI

A Flet desktop app that wraps `linkFroge.py`. It imports the module directly
and drives its existing functions from a graphical interface instead of the
command line — no changes were made to `linkFroge.py` itself.

## Setup

```bash
pip install flet requests tqdm
```

Keep `linkFroge.py` and `app.py` in the same folder.

## Run

```bash
python app.py
```

## Using it

1. Set the local **port** you want to expose (default `55555`).
2. First run only: paste your **ngrok auth token** — the app feeds it to
   `linkFroge`'s existing `add-authtoken` flow automatically instead of
   blocking on a terminal prompt.
3. Optionally fill in a LinkFroge **Service ID** / **Service token** to keep
   a hosted link pointed at your tunnel, or check **"Register a new service
   ID on start"** to create one.
4. Click **Start tunnel**. Progress and every `print()` from `linkFroge.py`
   streams live into the log panel at the bottom.
5. Once connected, the public URL appears with **copy** and **open in
   browser** buttons.
6. Click **Stop tunnel** to terminate the ngrok process.

## Notes

- ngrok will be auto-downloaded to `~/.linkfroge` on first run if it isn't
  already installed there (same behavior as the original CLI script).
- All fields are locked while a tunnel is running; stop the tunnel to change
  settings.
