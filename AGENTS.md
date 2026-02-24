# Repository Guidelines

## Project Structure & Module Organization

This repository is a Python-based job recruitment data analysis and visualization system. Core modules live at the repo root:

- `crawler/`: data collection adapters and platform-specific crawlers.
- `storage/`: SQLAlchemy models and database operations.
- `pipeline/`: data cleaning and transformation pipeline.
- `analytics/`: statistics, trends, and recommendation logic.
- `viz/`: Pyecharts/Matplotlib visualizations.
- `webapp/`: Flask web UI and templates.
- `utils/`: shared utilities (logging, HTTP, parsing).
- `tests/`: automated tests.
- `data/`, `analytics/`, `viz/`: runtime artifacts and outputs.

Key entry scripts are in the repo root: `run.py`, `run_web.py`, `run_crawl.py`, and `init_database.py`.

## Build, Test, and Development Commands

- `pip install -r requirements.txt`: install runtime dependencies.
- `python init_database.py`: create MySQL database and tables (reads `config.yaml`).
- `python run.py --crawl-first`: one-click startup with environment checks and optional initial crawl.
- `python run_web.py`: start the Flask web app only.
- `python run_crawl.py --keyword python --city Remote`: run a manual crawl.
- `playwright install`: required only for the 51job crawler.

## Coding Style & Naming Conventions

- Python code follows PEP 8 with 4-space indentation.
- Modules, functions: `snake_case`. Classes: `PascalCase`. Constants: `UPPER_SNAKE_CASE`.
- No enforced formatter or linter is configured; keep changes clean and consistent with nearby files.

## Testing Guidelines

- Tests live in `tests/` and follow `test_*.py` naming.
- Recommended runner: `pytest` (not pinned in `requirements.txt`; install as needed).
- Prefer unit tests for analytics and pipeline logic; add integration tests for crawlers when feasible.

## Commit & Pull Request Guidelines

- Commit messages in history are short and sometimes use Conventional Commit prefixes like `feat:`. Use concise, imperative summaries; add a prefix if it helps clarity.
- PRs should include a clear description, testing notes, and any relevant config changes (e.g., `config.yaml`).
- If you touch the web UI, include before/after screenshots.

## Security & Configuration Tips

- Configure MySQL and proxies in `config.yaml`. Avoid committing real credentials.
- Crawlers must respect platform terms and rate limits; adjust `crawler.polite_sleep_*` settings as needed.
