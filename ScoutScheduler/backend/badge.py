import os
import json
from fastapi import FastAPI, HTTPException
from bs4 import BeautifulSoup
import httpx

# Import badge logic
from ScoutScheduler.backend.badge_logic import load_badges

app = FastAPI()

# Environment variable for overriding badge info URL if needed
BADGE_FILE = os.getenv("BADGE_FILE_PATH")

async def fetch_description(url: str) -> str:
    """
    Fetch the badge page and extract its descriptive content.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    # Assuming description is in the first paragraph under .article-content
    p = soup.select_one(".article-content p")
    return p.get_text(strip=True) if p else ""

@app.get("/badge_info")
async def badge_info(name: str):
    """
    Return the URL and description for a given Cub badge by name.
    """
    # Load badges from the logic module
    badges = load_badges()
    url = badges.get(name)
    if not url:
        raise HTTPException(status_code=404, detail="Badge not found")

    # Fetch live description
    description = await fetch_description(url)
    return {"name": name, "url": url, "description": description}
