# Flet Apps

A collection of cross-platform applications built with **Flet** and Python.

This repository serves as a central workspace for my Flet projects, ranging from utilities and experiments to complete desktop and mobile applications.

## Repository Structure

```text
flet-apps/
├── orm_lite.py
├── en-to-am/
├── app/
└── README.md
```

### Directories

| Folder | Description |
|---------|-------------|
| `orm_lite.py` | Shared ORM/database utilities used across applications. |
| `en-to-am/` | English to Amharic translation application. |
| `app/` | General Flet application. |

## Getting Started

Clone the repository:

```bash
git clone https://github.com/omerKkemal/flet-apps.git
cd flet-apps
```

Navigate to the application you want to run:

```bash
cd en-to-am
```

or

```bash
cd app
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
python main.py
```

or if the project uses the Flet CLI:

```bash
flet run
```

## Applications

### en-to-am

A simple and fast English → Amharic translation application built with Flet.

**Status:** Active

---

### app

A Flet application for experimentation and feature development.

**Status:** In Development

## Shared Components

The `orm/` directory contains reusable database models and utilities shared between applications.

## Technologies

- Python
- Flet
- SQLite
- SQLAlchemy (where applicable)

## Requirements

- Python 3.11+
- Flet

## License

This repository is licensed under the MIT License.
