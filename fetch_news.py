# Author: Vishal L
# Purpose: Fetch sustainability-related news and retain the past 14 days of results
# Date: 2025-11-04

import requests
import json
from datetime import datetime, timedelta
import os

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

print("--- 1. Fetching fresh articles ---")

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
articles = data.get("articles", [])
print(f"Fetched {len(articles)} from API.")

# Save raw data
with open(RAW_FILE, "w", encoding="utf-8") as f:
    json.dump({"timestamp": datetime.utcnow().isoformat(), "data": articles}, f, indent=2)

# --- Load existing cache (previous news.json) ---
existing = []
if os.path.exists(OUTPUT_FILE):
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f).get("articles", [])
        print(f"Loaded {len(existing)} cached articles.")
    except Exception as e:
        print(f"Warning: could not read existing cache ({e})")

# --- Filter new articles ---
filtered = []
today = datetime.utcnow().date()
yesterday = today - timedelta(days=1)

for art in articles:
    pub_str = art.get("publishedAt", "")
    try:
        pub_dt = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
        art_date = pub_dt.date()
    except Exception:
        continue

    if art_date in [today, yesterday]:
        title = art.get("title", "").lower()
        desc = (art.get("description") or "").lower()
        if any(kw in title or kw in desc for kw in KEYWORDS):
            filtered.append({
                "title": art.get("title"),
                "source": art.get("source", {}).get("name"),
                "url": art.get("url"),
                "date": art_date.strftime("%d-%m-%Y"),
                "description": art.get("description"),
                "image": art.get("urlToImage"),
            })

print(f"Filtered {len(filtered)} new relevant articles.")

# --- Merge + deduplicate by URL ---
combined = filtered + existing
unique = []
seen_urls = set()

for a in combined:
    if not a.get("url") or a["url"] in seen_urls:
        continue
    seen_urls.add(a["url"])
    unique.append(a)

# --- Keep only the past 14 days ---
cutoff = today - timedelta(days=14)
final_articles = [
    a for a in unique
    if datetime.strptime(a["date"], "%d-%m-%Y").date() >= cutoff
]

print(f"{len(final_articles)} articles kept after 14-day filter.")

# --- Save final output ---
final_data = {
    "lastUpdated": datetime.utcnow().isoformat(),
    "count": len(final_articles),
    "articles": final_articles
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(final_data, f, indent=2, ensure_ascii=False)

print("--- ✅ News fetch and merge complete ---")
