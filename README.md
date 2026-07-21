# Flet Apps – because apparently one app wasn't enough

A collection of cross-platform applications built with **Flet** and Python.  
Because why write one app when you can write many and question your life choices?

This repository serves as a central workspace for my Flet projects, including language tools, mobile applications, reusable components, and experimental cross-platform software.  
Basically, it's where good ideas go to become code and bad ideas go to become... also code.

---

## ⚠️ The Usual Warning (you know the drill)

Most of these apps are for **educational purposes**. Some are for **practical use**.  
None of them are for world domination.  
At least not yet. 

---

## Repository Structure (the mess I call organization)

```text
flet-apps/
├── orm_lite.py          # The shared brain (database utilities)
├── en-to-am/            # English → Amharic translation (because why not)
├── app/                 # Random experiments that may or may not work
├── PhantomGate/         # The Trojan horse – shh, don't tell anyone
├── mobile-am-to-en/     # Amharic → Latin transliteration (mobile edition)
└── README.md            # You're reading this. Congratulations.
```

---

## Projects (the ones I actually finished)

| Project           | Description                                                                   | Status             |
| ----------------- | ----------------------------------------------------------------------------- | ------------------ |
| `en-to-am`        | English → Amharic translation application. Because languages are fun.         | Active             |
| `mobile-am-to-en` | Mobile application for Amharic to Latin transliteration. For when you're lazy. | Active             |
| `app`             | General-purpose Flet application for experimentation and feature development.  | In Development     |
| `PhantomGate`     | Cross-platform Flet application under active development. *It's watching you.* | Active Development |

---

## Shared Components (the parts I didn't want to rewrite)

| Component     | Description                                                         |
| ------------- | ------------------------------------------------------------------- |
| `orm_lite.py` | Lightweight ORM/database utilities shared across multiple projects. Because copying code is for amateurs. |

---

## The Trojan Horse – PhantomGate

Yes, there's a GUI for PhantomGate. Because apparently not everyone wants to live in a terminal.

**Check it out:** [PhantomGate Flet App](https://github.com/omerKkemal/flet-apps/tree/main/PhantomGate)

It's a Flet-based Trojan horse that gives you:
- A pretty interface for controlling the phantom (because buttons are fun)
- Cross-platform desktop and Android support (the nightmare must be portable)
- A way to pretend you're a real hacker with a GUI (no judgment here)

Build it as an APK, EXE, or web app – spread the infection.  
*You didn't find it. It found you.*

---

## The Dark Trio – Complete Ecosystem

| Project | Description | Link |
|---------|-------------|------|
| **SpecterPanel** | The C2 server – the master of puppets | [GitHub](https://github.com/omerKkemal/oh-tool-v2) |
| **PhantomGate** | The agent – the phantom itself | [GitHub](https://github.com/omerKkemal/PhontomGate) |
| **PhantomGate GUI** | The Trojan horse – the pretty mask | [GitHub](https://github.com/omerKkemal/flet-apps/tree/main/PhantomGate) |

Together they form a complete C2 ecosystem.  
Or a three-headed monster. Depends on your perspective.

---

## Getting Started (without breaking everything)

Clone the repository:

```bash
git clone https://github.com/omerKkemal/flet-apps.git
cd flet-apps
```

Navigate to the project you want to run:

```bash
cd en-to-am        # for the translator
# or
cd mobile-am-to-en # for the mobile one
# or
cd PhantomGate     # if you're feeling brave
# or
cd app             # if you like surprises
```

Install dependencies for the selected project.

If the project uses `pyproject.toml`:

```bash
pip install -e .
```

If the project uses `requirements.txt`:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
flet run
```

or, where applicable:

```bash
python main.py
```

---

## Technologies (the stuff that makes it work)

- **Python** – because apparently I hate myself
- **Flet** – because Flutter is too mainstream
- **SQLite** – where the data goes to die
- **SQLAlchemy** – because raw SQL is for savages

---

## Requirements (you need these)

- Python 3.11+
- Flet
- A sense of humor (optional but recommended)

---

## License

This repository is licensed under the MIT License.  
Do whatever you want with it. Just don't blame me when it breaks.

---

## Author

**Omer Kemal** – developer, caffeine addict, and professional bug creator.

- Main GitHub: [omerKkemal](https://github.com/omerKkemal)
- C2 Server: [SpecterPanel](https://github.com/omerKkemal/oh-tool-v2)
- Agent: [PhantomGate](https://github.com/omerKkemal/PhontomGate)
- Trojan Horse: [PhantomGate Flet App](https://github.com/omerKkemal/flet-apps/tree/main/PhantomGate)

---

<p align="center">
  <sub>© 2025 Flet Apps – for learning, not for being a jerk. The phantom is watching you.</sub>
  <br>
  <sub>Go outside. Touch grass. Or don't. I'm not your mom.</sub>
</p>
