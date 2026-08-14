# LinkFroge GUI

<p align="center">
  <img src="https://raw.githubusercontent.com/omerkkemal/linkfroge/main/screen_shot/gui.png" alt="LinkFroge GUI" width="700">
</p>

---

## Because even CLI tools need a pretty face.

A Flet desktop GUI wrapper for `linkFroge.py` – because not everyone wants to live in the terminal. Click buttons instead of typing commands. Watch logs in real-time. Pretend you're using a real application.

---

## What It Is

This is a **graphical interface** for the LinkFroge CLI agent. It imports `linkFroge.py` directly and drives its existing functions from a friendly UI instead of the command line. No changes were made to `linkFroge.py` itself – it's the same trusty CLI under the hood, just with a shiny wrapper.

---

## It is capable of

- **One-Click Tunnel** – Start and stop ngrok with a single button
- **Live Log Streaming** – Every `print()` from `linkFroge.py` appears in real-time
- **Auto-Download ngrok** – Downloads ngrok to `~/.linkfroge` on first run
- **Ngrok Auth Integration** – No terminal prompts – paste your token once
- **Service ID Registration** – Register new service IDs directly from the GUI
- **Copy & Open** – One-click copy or open your public URL in browser
- **Real-time Status** – See your tunnel status, URL, and logs at a glance
- **Persistent Settings** – Fields retain values between runs
- **Input Locking** – All fields lock while tunnel is running (no accidental changes)

---

## Quick Start (Without Breaking Things)

### 1. Install Dependencies
```bash
pip install flet requests tqdm
```

### 2. Get the Files
Place `app.py` and `linkFroge.py` in the same folder.

```
your-folder/
├── app.py           # The GUI
└── linkFroge.py     # The CLI (unchanged)
```

### 3. Run It
```bash
python app.py
```

The GUI window will open. You're welcome.

---

## How to Use It (With Pictures)

<div align="center">

### Step 1: Set Your Port
<img src="screen_shot/gui_port.png" alt="Set port" width="600">

*Default is 55555. Change it if you're feeling rebellious.*

<br><br>

### Step 2: Add Your Ngrok Auth Token
<img src="screen_shot/gui_auth.png" alt="Add auth token" width="600">

*The app feeds it to `linkFroge` automatically – no terminal prompts. Just paste and forget.*

<br><br>

### Step 3: Configure LinkFroge Service (Optional)
<img src="screen_shot/gui_service.png" alt="Service config" width="600">

*Fill in Service ID and Token to keep a hosted link pointed at your tunnel. Or check "Register a new service ID on start" to create one.*

<br><br>

### Step 4: Start Tunnel
<img src="screen_shot/gui_start.png" alt="Start tunnel" width="600">

*Click the green button. Watch the logs. Feel powerful.*

<br><br>

### Step 5: Copy or Open Your URL
<img src="screen_shot/gui_url.png" alt="URL buttons" width="600">

*The public URL appears with Copy and Open buttons. Because copy-paste is too much effort.*

<br><br>

### Step 6: Stop When Done
<img src="screen_shot/gui_stop.png" alt="Stop tunnel" width="600">

*Click Stop. Or just close the window. We're not your mom.*

</div>

---

## Step-by-Step Walkthrough

### 1. Set the port
Enter the local port you want to expose (default `55555`). This is where your local server is running.

### 2. Enter your ngrok auth token (first run only)
Paste your ngrok auth token into the field. The app feeds it to `linkFroge`'s existing `add-authtoken` flow automatically – no terminal prompts, no blocking.

### 3. Configure LinkFroge service (optional)
- **Service ID** – Your existing service ID (if you have one)
- **Service Token** – Your service token for authentication
- **Register a new service ID on start** – Check this to create a new service ID when the tunnel starts

### 4. Click "Start tunnel"
- The app imports `linkFroge.py` and calls its `main()` function with your settings
- Progress and every `print()` from `linkFroge.py` streams live into the log panel at the bottom
- You'll see ngrok downloading, starting, and connecting

### 5. Copy or open your URL
Once connected, the public URL appears with:
- **Copy button** – Copy the URL to your clipboard
- **Open button** – Open the URL in your default browser

### 6. Click "Stop tunnel"
Terminates the ngrok process and stops the tunnel. All settings remain for next time.

---

## Why a GUI?

Because not everyone wants to:
- Remember command-line arguments
- Copy-paste long commands
- Deal with terminal windows
- Pretend they're a hacker

**This GUI gives you the same power with:**

| CLI | GUI |
|-----|-----|
| `--port 5000` | Input field |
| `--ngrok-auth-token` | Input field |
| `--service-id` | Input field |
| `--service-token` | Input field |
| `--register-service-id` | Checkbox |
| `--verbose` | Built-in log panel (always verbose) |
| `python linkFroge.py` | Start button |

---

## Architecture (How It Works)

```
+------------------+
|   app.py (GUI)   |
|  (Flet Desktop)  |
+--------+---------+
         |
         | imports and drives
         v
+------------------+
| linkFroge.py     |
| (Unchanged CLI)  |
+--------+---------+
         |
         | subprocess
         v
+------------------+
| ngrok            |
| (Auto-downloaded)|
+------------------+
```

The GUI:
1. Collects your settings
2. Calls `linkFroge.main()` with those settings
3. Captures all stdout/stderr and displays it in the log panel
4. Provides buttons to copy/open URLs
5. Handles the `KeyboardInterrupt` gracefully (Stop button)

**No changes were made to `linkFroge.py`** – it remains a pure CLI tool. The GUI is just a friendly wrapper.

---

## File Structure

```
LinkFrogeGUI/
├── app.py              # The GUI application
├── linkFroge.py        # The CLI (unchanged)
├── requirements.txt    # Dependencies
└── README.md           # You're reading this
```

---

## Requirements

- Python 3.8+
- flet
- requests
- tqdm

---

## Installation

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install flet requests tqdm
```

---

## Running

```bash
python app.py
```

---

## Notes

- ngrok will be auto-downloaded to `~/.linkfroge` on first run if it isn't already installed there (same behavior as the original CLI script)
- All fields are locked while a tunnel is running; stop the tunnel to change settings
- The log panel shows every `print()` from `linkFroge.py` in real-time
- Your settings (port, auth token, service ID, token) are saved between runs

---

## Troubleshooting

### "No module named 'flet'"
```bash
pip install flet
```

### "linkFroge.py not found"
Make sure `app.py` and `linkFroge.py` are in the same folder.

### "Ngrok auth token invalid"
Get a free token from [ngrok.com](https://ngrok.com) and paste it in the auth token field.

### "Service ID not found"
Either register a new one with the checkbox or provide an existing service ID.

### GUI won't start
Make sure you're using Python 3.8+ and all dependencies are installed.

---

## Coming Soon (Maybe)

- Dark mode (for the night owls)
- Save multiple profiles
- Auto-reconnect
- Statistics dashboard

---

## Contributing

If you want to make this GUI prettier or more functional:

1. Fork the repo
2. Make your changes
3. Submit a pull request

**Rules:**
- Don't break the CLI – it stays untouched
- Add sarcasm. It's required.
- Test before submitting. I'm not your QA team.

---

## License

MIT – do whatever you want. Just don't blame us if it breaks.

---

<p align="center">
  <sub>Built with spite. Powered by sarcasm. Sustained by coffee.</sub>
  <br>
  <sub>No refunds. No regrets. No sleep.</sub>
  <br>
  <sub>Now with 100% more buttons. You're welcome.</sub>
</p>