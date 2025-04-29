#!/usr/bin/env bash
# ------------------------------------------------------------
# One-shot refactor script for ymarikkar/scout-disso
# ------------------------------------------------------------
set -euo pipefail

echo "==> Creating refactor branch"
git checkout -b refactor/clean-2025-04

echo "==> Setting up src/ package skeleton"
mkdir -p src/scout_disso/{scheduler,badges,ui/pages,utils}
touch src/scout_disso/__init__.py

# -- helper: safe mv if file exists --------------------------
mvmaybe () { [ -e "$1" ] && git mv "$1" "$2" || echo "skip $1"; }

echo "==> Moving core logic into new package"
mvmaybe scheduler_logic.py          src/scout_disso/scheduler/logic.py
mvmaybe webscraper_holidays.py      src/scout_disso/scheduler/holidays.py
mvmaybe badge_tracker.py            src/scout_disso/badges/logic.py
mvmaybe webscraper_badges.py        src/scout_disso/badges/scraper.py
mvmaybe writer_client.py            src/scout_disso/utils/writer_api.py
mvmaybe data_store.py               src/scout_disso/utils/data_store.py
mvmaybe streamlit_app.py            src/scout_disso/ui/app.py
mvmaybe streamlit_dashboard.py      src/scout_disso/ui/pages/dashboard.py
mvmaybe streamlit_badges.py         src/scout_disso/ui/pages/badges.py
mvmaybe streamlit_calendar.py       src/scout_disso/ui/pages/calendar.py
mvmaybe streamlit_settings.py       src/scout_disso/ui/pages/settings.py
mvmaybe main.py                     src/scout_disso/main.py

echo "==> Quarantining legacy / unused modules"
mkdir -p legacy/gui
for f in tk_*.py tkinter_*.py gui_*.*; do
    [ -e "$f" ] && git mv "$f" legacy/gui/ || true
done
mvmaybe badge_api_fastapi.py        legacy/badge_api_fastapi.py
mvmaybe writerintergration.py       legacy/writerintergration.py
mvmaybe old_tests/                  legacy/old_tests

echo "==> Removing obvious generated / cache artefacts"
git rm -rf __pycache__ 2>/dev/null || true
git rm -rf .pytest_cache 2>/dev/null || true

echo "==> Writing .gitignore"
cat > .gitignore <<'EOF'
# Python
__pycache__/
*.py[cod]
*.pyo
# Env / tooling
.venv/
.env
# Build / misc
dist/
build/
.eggs/
.DS_Store
EOF
git add .gitignore

echo "==> Pruning requirements.txt"
# minimal example – adjust manually if needed
cat > requirements.txt <<'EOF'
streamlit==1.33.0
pandas
requests
beautifulsoup4
orjson
or-tools
black
isort
EOF
git add requirements.txt

echo "==> Adding pre-commit config"
cat > .pre-commit-config.yaml <<'EOF'
repos:
  - repo: https://github.com/psf/black
    rev: 24.3.0
    hooks: [ {id: black} ]
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks: [ {id: isort} ]
EOF
git add .pre-commit-config.yaml

echo "==> Adding GitHub Actions CI workflow"
mkdir -p .github/workflows
cat > .github/workflows/ci.yml <<'YAML'
name: CI
on: [push, pull_request]
jobs:
  lint-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - run: pip install -r requirements.txt
      - run: black --check src
      - run: isort --check-only src
YAML
git add .github/workflows/ci.yml

echo "==> Rewriting README placeholder"
cat > README.md <<'EOF'
# Scout-Disso (refactored)

AI-driven scheduler and badge-manager for UK Scout leaders.

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export WRITER_API_KEY="your_key_here"
streamlit run src/scout_disso/ui/app.py
