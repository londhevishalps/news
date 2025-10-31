# Author: Vishal L
# Purpose: Fetch Google News RSS for sustainability keywords and store in news.json
# Scope: Works with keywords list and preserves all historical news
# Date format: DD-MM-YYYY

import feedparser
import json
from datetime import datetime
import os
from dateutil import parser  # pip install python-dateutil

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

# --- Fetch and parse new news ---
new_articles = []
for url in rss_urls:
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            link = entry.link
            if link not in existing_urls:
                # Parse date and convert to DD-MM-YYYY
                if 'published' in entry:
                    try:
                        dt = parser.parse(entry.published)
                        date_str = dt.strftime("%d-%m-%Y")
                    except:
                        date_str = datetime.now().strftime("%d-%m-%Y")
                else:
                    date_str = datetime.now().strftime("%d-%m-%Y")

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

# --- Merge and sort by date descending ---
all_articles.extend(new_articles)
# Convert dates back to datetime objects for proper sorting
def parse_dd_mm_yyyy(date_str):
    try:
        return datetime.strptime(date_str, "%d-%m-%Y")
    except:
        return datetime.now()

all_articles.sort(key=lambda x: parse_dd_mm_yyyy(x["date"]), reverse=True)

# --- Save to JSON ---
with open("news.json", "w", encoding="utf-8") as f:
    json.dump(all_articles, f, ensure_ascii=False, indent=2)

print(f"Fetched {len(new_articles)} new articles. Total articles stored: {len(all_articles)}")
