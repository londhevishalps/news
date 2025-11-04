# Author: Vishal L
# Purpose: Fetch sustainability-related news articles and save filtered results
# Date: 2025-11-04

import requests
import json
from datetime import datetime, timedelta
import os

# --- Configuration ---
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
OUTPUT_FILE = "news.json"
RAW_FILE = "news_raw.json"
KEYWORDS = [
    "sustainability", "climate", "carbon", "greenhouse", "emissions", "renewable",
    "wastewater", "pollution", "circular", "biodiversity", "chemical management",
    "supply chain", "ESG", "textile", "fashion", "clean production", "ZDHC"
]

DOMAINS = [
    "bbc.com", "reuters.com", "theguardian.com", "forbes.com",
    "businessoffashion.com", "ecotextile.com", "textiletoday.com.bd",
    "sourcingjournal.com", "fashionunited.com", "yahoo.com", "wsj.com"
]

# --- Fetch news from News API ---
print("--- 1. Fetching news articles ---")

params = {
    "apiKey": NEWS_API_KEY,
    "language": "en",
    "sortBy": "publishedAt",
    "pageSize": 100,
    "domains": ",".join(DOMAINS),
    "q": " OR ".join(KEYWORDS)
}

response = requests.get("https://newsapi.org/v2/everything", params=params)
data = response.json()

if "articles" not in data:
    print("No articles found or API error.")
    exit()

articles = data["articles"]
print(f"Fetched {len(articles)} articles from API.")

# --- Save raw results ---
raw_data = {
    "timestamp": datetime.utcnow().isoformat(),
    "total_articles": len(articles),
    "data": articles
}

with open(RAW_FILE, "w", encoding="utf-8") as f:
    json.dump(raw_data, f, indent=2, ensure_ascii=False)

# --- Filter articles for the past ~36 hours ---
print("--- 2. Filtering relevant articles ---")

filtered_articles = []
today = datetime.utcnow().date()
yesterday = today - timedelta(days=1)

for art in articles:
    published_str = art.get("publishedAt", "")
    try:
        published_dt = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
        art_date = published_dt.date()
    except Exception:
        continue

    if art_date in [today, yesterday]:
        title = art.get("title", "").lower()
        desc = art.get("description", "").lower() if art.get("description") else ""

        if any(kw in title or kw in desc for kw in KEYWORDS):
            filtered_articles.append({
                "title": art.get("title"),
                "source": art.get("source", {}).get("name"),
                "url": art.get("url"),
                "date": art_date.strftime("%d-%m-%Y"),
                "description": art.get("description"),
                "image": art.get("urlToImage"),
            })

print(f"{len(filtered_articles)} articles remain after filtering.")

# --- Save final filtered data ---
final_data = {
    "lastUpdated": datetime.utcnow().isoformat(),
    "count": len(filtered_articles),
    "articles": filtered_articles
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(final_data, f, indent=2, ensure_ascii=False)

print("--- ✅ News fetch complete ---")
