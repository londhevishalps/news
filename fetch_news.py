# Author: Vishal L
# Purpose: Fetch Google News RSS for sustainability keywords and store last 7 days in news.json
# Date format: DD-MM-YYYY
# Uses only standard libraries + feedparser

import feedparser
import json
from datetime import datetime, timedelta
import os

# --- Keywords ---
keywords = [
    "sustainability business", "corporate sustainability", "ESG strategy", "green business",
    "circular economy", "reuse materials", "recycling fashion", "closed-loop textiles",
    "sustainable textiles", "eco-friendly fabrics", "ethical apparel", "fashion sustainability",
    "textile wastewater", "water stewardship", "water pollution textile", "clean water in fashion",
    "green chemistry", "sustainable chemicals", "ZDHC", "chemical management textiles",
    "supply chain transparency", "supplier audits", "CSR compliance", "ethical sourcing",
    "carbon footprint fashion", "climate action textile", "net zero supply chain",
    "sustainable innovation", "eco-fashion technology", "sustainable material innovation",
    "GRI reporting", "Higg Index", "sustainability standards", "corporate ESG report"
]

rss_urls = [f"https://news.google.com/rss/search?q={keyword.replace(' ', '+')}" for keyword in keywords]

# --- Load existing news ---
if os.path.exists("news.json"):
    with open("news.json", "r", encoding="utf-8") as f:
        all_articles = json.load(f)
else:
    all_articles = []

existing_urls = {article["url"] for article in all_articles}

# --- Fetch new news ---
new_articles = []
seven_days_ago = datetime.now() - timedelta(days=7)

for url in rss_urls:
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            link = entry.link
            if link in existing_urls:
                continue

            # Parse date
            if 'published' in entry:
                try:
                    dt = datetime.strptime(entry.published[:10], "%Y-%m-%d")
                except:
                    dt = datetime.now()
            else:
                dt = datetime.now()

            if dt < seven_days_ago:
                continue  # Skip older than 7 days

            date_str = dt.strftime("%d-%m-%Y")
            article = {
                "title": entry.title,
                "url": link,
                "source": entry.source.title if 'source' in entry else 'Unknown',
                "date": date_str
            }
            new_articles.append(article)
            existing_urls.add(link)
    except Exception as e:
        print(f"Error fetching feed {url}: {e}")

# --- Merge, keep only last 7 days ---
all_articles.extend(new_articles)
all_articles = [a for a in all_articles if datetime.strptime(a["date"], "%d-%m-%Y") >= seven_days_ago]

# --- Sort descending ---
all_articles.sort(key=lambda x: datetime.strptime(x["date"], "%d-%m-%Y"), reverse=True)

# --- Save JSON ---
with open("news.json", "w", encoding="utf-8") as f:
    json.dump(all_articles, f, ensure_ascii=False, indent=2)

print(f"Fetched {len(new_articles)} new articles. Total stored (last 7 days): {len(all_articles)}")
