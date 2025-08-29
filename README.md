# table_modifier

A toolkit for modifying tabular data with both CLI and GUI components. Core features include file interfaces (CSV/Excel), a classification engine, and a Qt-based GUI.

## Installation

- Python: 3.9+
- Recommended: Poetry

Using Poetry (dev):

```
poetry install -E file
```

Using pip (runtime only):

```
pip install .
```

Optional extras:
- `file` enables pandas-backed file interfaces.

## CLI

After install, a console script is available:

```
table-modifier --help
```

Basic usage:

```
table-modifier input.xlsx output.xlsx
```

Language can be set with `-l/--lang`.

## Development

Run tests with coverage:

```
pytest -q
```

The project enforces a coverage gate (>= 60%). Non-GUI modules target >= 75% coverage.

Type checks and linting:

```
flake8
isort --check-only .
black --check .
mypy --strict src
```

## Pre-commit hooks

Install and enable hooks:

```
pre-commit install
```

Hooks run Black, isort, Flake8, and mypy over `src/`.

## Packaging notes

QSS theme files (`src/table_modifier/gui/themes/*.qss`) are included in the wheel and sdist. Theme loading prefers package resources and falls back to the filesystem in editable installs.

## Troubleshooting

- If Excel tests fail due to engine support, ensure `pandas` and `openpyxl` are available or run tests which mock Excel I/O (default in this repo).
- If CLI isn’t discovered, ensure your environment has the project installed and `table-modifier` is on PATH.

