# Scout‑Disso

## Overview
Scout‑Disso is an AI‑assisted desktop application for Scout leaders to schedule sessions and track badge progress using a minimalistic Tkinter GUI&#8203;:contentReference[oaicite:0]{index=0}. It combines badge data scraped from the Scouts website, local school holiday calendars, and leader preferences to recommend optimised session plans&#8203;:contentReference[oaicite:1]{index=1}. This prototype supports session CRUD operations, badge tracking, and an integrated AI chatbot for on‑demand planning advice&#8203;:contentReference[oaicite:2]{index=2}.

## Features
- **Session Scheduler**: Add, edit, and delete meeting sessions with date, time, and title fields&#8203;:contentReference[oaicite:3]{index=3}.  
- **Badge Tracker**: View completed and in‑progress badges for each Scout, toggle status, and filter by completion state&#8203;:contentReference[oaicite:4]{index=4}.  
- **AI Assistant**: Converse with an AI module to get session suggestions, badge insights, and feedback loops directly within the app&#8203;:contentReference[oaicite:5]{index=5}.  
- **Cloud‑backed Scraping**: Fetches all UK Cub Scout badges via Cloudscraper and term dates from local council sites, caching in JSON for offline use&#8203;:contentReference[oaicite:6]{index=6}.  
- **Minimalistic GUI**: Built with pure Tkinter for ease of future migration to PyQt or other frameworks&#8203;:contentReference[oaicite:7]{index=7}.

## Installation
1. **Clone the repository**  
   ```bash
   git clone https://github.com/ymarikkar/scout-disso.git
   cd scout-disso

   python -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate

pip install -r requirements.txt

python ScoutScheduler/backend/webscraping.py

python -m ScoutScheduler.main
``` :contentReference[oaicite:8]{index=8}

ScoutScheduler/             # Application package
├── backend/                # Data scraping & management modules
│   ├── webscraping.py      # Badge & holiday fetchers
│   └── data_management.py  # Load/save JSON sessions & badges
├── gui/                    # Tkinter GUI modules
│   ├── scheduler.py        # Session scheduling window
│   ├── badge_tracker.py    # Badge tracking window
│   └── chatbot.py          # AI chatbot window
├── main.py                 # Entry point: brings it all together
└── requirements.txt        # Exact dependency versions
``` :contentReference[oaicite:9]{index=9}

## Configuration
- **API Keys**: Set `WRITER_API_KEY` in your environment for AI suggestions.  
- **Cloudscraper Settings**: No manual install; Cloudscraper handles Cloudflare bypass automatically&#8203;:contentReference[oaicite:10]{index=10}.  
- **Holiday Source**: The default is Harrow Council; update `webscraping.py` to target other councils.

## Roadmap
1. **Finalize scheduling engine**: Automate session suggestions based on badge complexity, available slots, and holidays.  
2. **Refactor GUI imports**: Eliminate circular imports by using local imports within functions.  
3. **Enhance AI prompts**: Improve the quality and context of session‑planning suggestions.  
4. **PyQt migration**: Evaluate migrating from Tkinter to PyQt for richer widgets.  
5. **User authentication**: Add simple login/role management for multiple leaders. :contentReference[oaicite:11]{index=11}

## Contributing
1. Fork the repository.  
2. Create a feature branch.  
3. Implement and test your changes.  
4. Open a pull request describing your improvements. :contentReference[oaicite:12]{index=12}

## License
This project is licensed under the MIT License. See [LICENSE](LICENSE) for details&#8203;:contentReference[oaicite:13]{index=13}.


