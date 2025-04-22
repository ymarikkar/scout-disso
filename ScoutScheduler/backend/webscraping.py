import os
import json
import requests
import cloudscraper
from bs4 import BeautifulSoup

BADGE_CACHE   = "data/badge_data.json"
HOLIDAY_CACHE = "data/holiday_data.json"

# bypass Cloudflare
scraper = cloudscraper.create_scraper()

def fetch_badge_data():
    os.makedirs("data", exist_ok=True)
    url = "https://www.scouts.org.uk/cubs/activity-badges/"
    response = scraper.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    badges = {}

    # New selector for the live site
    for card in soup.find_all("div", class_="sc-cards__item"):
        title_tag = card.find("h3")
        link_tag  = card.find("a", href=True)
        if title_tag and link_tag:
            title = title_tag.get_text(strip=True)
            badges[title] = link_tag["href"]

    with open(BADGE_CACHE, "w", encoding="utf-8") as f:
        json.dump(badges, f, indent=2)

    print(f"Saved {len(badges)} badges")
    return badges

def fetch_school_holidays():
    os.makedirs("data", exist_ok=True)
    url = "https://www.harrow.gov.uk/schools-learning/school-term-dates"
    print("Fetching school holidays…")
    resp = requests.get(url, headers={"User-Agent":"Mozilla/5.0"})
    resp.raise_for_status()

    soup = BeautifulSoup(resp.content, "html.parser")
    holidays = {}

    box = soup.find("div", class_="harrow-info-box--key-info")
    if box:
        year = box.find("h3").get_text(strip=True)
        holidays[year] = {}

        content = box.find("div", class_="harrow-info-box__content")
        for p in content.find_all("p"):
            strong = p.find("strong")
            if not strong:
                continue
            term = strong.get_text(strip=True)
            ul   = p.find_next_sibling("ul")
            dates = [li.get_text(strip=True) for li in ul.find_all("li")] if ul else []
            holidays[year][term] = dates

    with open(HOLIDAY_CACHE, "w", encoding="utf-8") as f:
        json.dump(holidays, f, indent=2)
    total = sum(len(v) for year in holidays.values() for v in year.values())
    print(f"Saved {total} holiday entries")
    return holidays

if __name__ == "__main__":
    fetch_badge_data()
    fetch_school_holidays()
