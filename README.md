# Flet Apps

A collection of cross-platform applications built with **Flet**.

This repository serves as a central place for my Flet projects, experiments, templates, and production-ready applications. Each application is contained in its own directory with its own source code and, when necessary, additional documentation.

## About

Flet enables developers to build desktop, web, and mobile applications using only Python, without writing frontend code in JavaScript or Dart. It uses Flutter for rendering and supports Windows, Linux, macOS, Android, iOS, and the Web from a single codebase. :contentReference[oaicite:0]{index=0}

## Repository Structure

```
flet-apps/
├── app-1/
│   ├── main.py
│   ├── README.md
│   └── ...
├── app-2/
│   ├── main.py
│   ├── README.md
│   └── ...
├── templates/
└── README.md
```

Each application is self-contained and may have its own dependencies and documentation.

## Getting Started

Clone the repository:

```bash
git clone https://github.com/<your-username>/flet-apps.git
cd flet-apps
```

Navigate to the application you want to run:

```bash
cd app-name
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
python main.py
```

or, if the project uses the Flet CLI:

```bash
flet run
```

The Flet CLI also supports running, debugging, packaging, and building applications for desktop, web, Android, and iOS. :contentReference[oaicite:1]{index=1}

## Apps

| Application | Description | Status |
|------------|-------------|--------|
| App Name | Short description | ✅ Active |
| App Name | Short description | 🚧 In Progress |
| App Name | Short description | 🧪 Experimental |

## Features

- Cross-platform Flet applications
- Modern Flutter-based UI
- Python-only development
- Reusable components and utilities
- Personal experiments and production projects

## Requirements

- Python 3.11+
- Flet
- Additional dependencies listed per project

## Contributing

Suggestions, bug reports, and pull requests are welcome.

## License

This repository is licensed under the MIT License unless otherwise specified by an individual project.
