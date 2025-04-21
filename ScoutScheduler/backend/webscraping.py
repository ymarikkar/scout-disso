import os
import json
from bs4 import BeautifulSoup
import requests

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# Use webdriver-manager to automatically manage the ChromeDriver.
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

BADGE_CACHE = "data/badge_data.json"
HOLIDAY_CACHE = "data/holiday_data.json"

def fetch_badge_data():
    os.makedirs("data", exist_ok=True)
    url = "https://www.scouts.org.uk/cubs/activity-badges/"
    print("Fetching badge data from:", url)
    
    # Set up Chrome options for Selenium.
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    
    # Setup ChromeDriver via webdriver-manager.
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Load the page.
    driver.get(url)
    
    # ---------- wait ----------
    print("Waiting for badge cards (div.badge-card) to load…")
    try:
        cards_present = EC.presence_of_element_located((By.CSS_SELECTOR, "div.badge-card"))
        WebDriverWait(driver, 25).until(cards_present)
        print("Badge cards detected.")
    except Exception as e:
        print("Still no badge cards after wait:", e)
        # keep going – we'll scroll & try again
    # ---------- scroll and second wait ----------
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.badge-card"))
    )

    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "html.parser")
    badges = {}
    for card in soup.select("div.badge-card"):
        title_tag = card.select_one("h3.badge-card__title")
        link_tag  = card.select_one("a")
        if title_tag and link_tag:
            title = title_tag.get_text(strip=True)
            badges[title] = "https://www.scouts.org.uk" + link_tag["href"]

    print("Found", len(badges), "badge cards in the parsed HTML.")

    # NEW selector
    for card in soup.select("div.badge-card"):
        title_tag = card.select_one("h3.badge-card__title")
        link_tag  = card.select_one("a")
        if title_tag and link_tag:
            title = title_tag.get_text(strip=True)
            link  = link_tag["href"]
            badges[title] = "https://www.scouts.org.uk" + link

    with open(BADGE_CACHE, "w", encoding="utf-8") as f:
        json.dump(badges, f, indent=4)
    
    print("Badge data has been written to", BADGE_CACHE)
    return badges

def fetch_school_holidays():
    os.makedirs("data", exist_ok=True)
    url = "https://www.harrow.gov.uk/schools-learning/school-term-dates"
    print("Fetching school holiday data from:", url)
    response = requests.get(url)
    print("Status Code for school holiday data:", response.status_code)
    soup = BeautifulSoup(response.content, "html.parser")
    
    holiday_data = {}
    info_box = soup.find("div", class_="harrow-info-box harrow-info-box--key-info")
    if info_box:
        heading = info_box.find("h3", class_="harrow-info-box__title")
        key = heading.get_text(strip=True) if heading else "School Term Dates"
        holiday_data[key] = {}
        
        content = info_box.find("div", class_="harrow-info-box__content")
        if content:
            paragraphs = content.find_all("p")
            print("Found", len(paragraphs), "paragraphs in the holiday info content.")
            for p in paragraphs:
                strong = p.find("strong")
                if strong:
                    term_title = strong.get_text(strip=True)
                    ul = p.find_next_sibling("ul")
                    if ul:
                        dates = [li.get_text(strip=True) for li in ul.find_all("li")]
                        holiday_data[key][term_title] = dates
    
    with open(HOLIDAY_CACHE, "w", encoding="utf-8") as f:
        json.dump(holiday_data, f, indent=4)
    
    print("Holiday data has been written to", HOLIDAY_CACHE)
    return holiday_data

if __name__ == "__main__":
    print("Script started.")
    
    print("==== Fetching Badge Data with Selenium ====")
    badges = fetch_badge_data()
    print("Total badges found:", len(badges))
    print("Badge preview:", list(badges.items())[:5])
    
    print("\n==== Fetching School Holiday Data ====")
    holidays = fetch_school_holidays()
    print("Total holiday entries found:", len(holidays))
    print("Holiday data:", holidays)
