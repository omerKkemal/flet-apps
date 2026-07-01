# Flet Apps

A collection of cross-platform applications built with **Flet** and Python.

This repository serves as a central workspace for my Flet projects, including language tools, mobile applications, reusable components, and experimental cross-platform software.

## Repository Structure

```text
flet-apps/
├── orm_lite.py
├── en-to-am/
├── app/
├── PhantomGate/
├── mobile-am-to-en/
└── README.md
```

## Projects

| Project           | Description                                                                   | Status             |
| ----------------- | ----------------------------------------------------------------------------- | ------------------ |
| `en-to-am`        | English → Amharic translation application.                                    | Active             |
| `mobile-am-to-en` | Mobile application for Amharic to Latin transliteration.                      | Active             |
| `app`             | General-purpose Flet application for experimentation and feature development. | In Development     |
| `PhantomGate`     | Cross-platform Flet application under active development.                     | Active Development |

## Shared Components

| Component     | Description                                                         |
| ------------- | ------------------------------------------------------------------- |
| `orm_lite.py` | Lightweight ORM/database utilities shared across multiple projects. |

## Getting Started

Clone the repository:

```bash
git clone https://github.com/omerKkemal/flet-apps.git
cd flet-apps
```

Navigate to the project you want to run:

```bash
cd en-to-am
```

or

```bash
cd mobile-am-to-en
```

or

```bash
cd PhantomGate
```

or

```bash
cd app
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

## Technologies

* Python
* Flet
* SQLite
* SQLAlchemy (where applicable)

## Requirements

* Python 3.11+
* Flet

## License

This repository is licensed under the MIT License.