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
