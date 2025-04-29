# Scout-Disso (refactored)

AI-driven scheduler and badge-manager for UK Scout leaders.

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export WRITER_API_KEY="your_key_here"
streamlit run src/scout_disso/ui/app.py
