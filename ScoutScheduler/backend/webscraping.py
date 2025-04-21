from bs4 import BeautifulSoup

# Holiday scraper constants
HOLIDAY_CACHE = "data/holiday_data.json"
BADGE_CACHE = "data/badge_data.json"
URL = "https://www.scouts.org.uk/cubs/activity-badges/"

scraper = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "windows", "mobile": False}
)

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
