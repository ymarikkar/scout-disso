import os
import json
import requests
import cloudscraper                  # <- add this
from bs4 import BeautifulSoup

BADGE_CACHE   = "data/badge_data.json"
HOLIDAY_CACHE = "data/holiday_data.json"

# Create a cloudscraper session to bypass Cloudflare
scraper = cloudscraper.create_scraper()

def fetch_badge_data():
    os.makedirs("data", exist_ok=True)
    url = "https://www.scouts.org.uk/cubs/activity-badges/"
    print("Downloading with Cloudscraper…")
    resp = scraper.get(url)
    # … your existing parsing logic …
    # write into BADGE_CACHE, return a dict of badges


def fetch_school_holidays():
    """
    Scrape Harrow Council term‑dates page and cache to data/holiday_data.json.
    Returns dict keyed by term-year containing term date lists.
    """
    url = "https://www.harrow.gov.uk/schools-learning/school-term-dates"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(resp.content, "html.parser")

    holidays = {}
    # find the Harrow‐info box
    info = soup.find("div", class_="harrow-info-box--key-info")
    if info:
        year = info.find("h3").get_text(strip=True)
        holidays[year] = {}
        content = info.find("div", class_="harrow-info-box__content")
        for paragraph in content.find_all("p"):
            strong = paragraph.find("strong")
            if not strong:
                continue
            term = strong.get_text(strip=True)
            ul = paragraph.find_next_sibling("ul")
            if not ul:
                continue
            dates = [li.get_text(strip=True) for li in ul.find_all("li")]
            holidays[year][term] = dates

    os.makedirs("data", exist_ok=True)
    with open(HOLIDAY_CACHE, "w", encoding="utf-8") as f:
        json.dump(holidays, f, indent=2)
    print(f"Saved {sum(len(v) for v in holidays.values())} holiday entries")
    return holidays

if __name__ == "__main__":
    fetch_badge_data()
