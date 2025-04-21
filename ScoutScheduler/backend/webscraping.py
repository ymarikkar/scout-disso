import os, json, re, cloudscraper
from bs4 import BeautifulSoup

BADGE_CACHE = "data/badge_data.json"
URL = "https://www.scouts.org.uk/cubs/activity-badges/"

scraper = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "windows", "mobile": False}
)

def fetch_badge_data():
    print("Downloading with Cloudscraper…")
    html = scraper.get(URL, timeout=30).text
    soup = BeautifulSoup(html, "html.parser")

    badges = {}
    for a in soup.select("a[href*='/activity-badges/']"):
        href = a["href"]
        name = a.get_text(strip=True)
        if not name or not re.search(r"/activity-badges/[a-z0-9-]+/?$", href):
            continue
        if href.startswith("/"):
            href = "https://www.scouts.org.uk" + href
        badges[name] = href

    os.makedirs("data", exist_ok=True)
    with open(BADGE_CACHE, "w", encoding="utf‑8") as f:
        json.dump(badges, f, indent=2)
    print(f"Saved {len(badges)} badges")
    return badges

if __name__ == "__main__":
    fetch_badge_data()
