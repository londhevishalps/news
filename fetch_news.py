import requests
import json
import os
from datetime import datetime, timedelta
import time
import hashlib

# -----------------------------------------
# CONFIGURATION
# -----------------------------------------
API_KEY = os.environ.get('NEWS_API_KEY')
if not API_KEY:
    raise ValueError("NEWS_API_KEY environment variable is not set")

BASE_URL = "https://newsapi.org/v2/everything"
CACHE_FILE = "news_raw.json"
FINAL_FILE = "news.json"

# 5 THEMATIC QUERIES — each counts as one API call
QUERY_THEMES = {
    "sustainable_fashion": '"sustainability" AND ("fashion" OR "apparel" OR "textile")',
    "circular_economy": '"circular economy" OR "recycling" OR "reuse" OR "waste management"',
    "green_chemistry": '"green chemistry" OR "sustainable chemistry" OR "ZDHC" OR "chemical management"',
    "carbon_supply_chain": '"carbon emissions" OR "net zero" OR "supply chain decarbonisation"',
    "esg_reporting": '"ESG report" OR "sustainability report" OR "corporate responsibility"',
}

# Sustainability context words for lightweight "semantic" filtering
CONTEXT_WORDS = [
    "sustainab", "recycl", "carbon", "emission", "waste", "water", "climate",
    "renewable", "supply chain", "esg", "zdch", "circular", "green", "ethical",
    "transparency", "footprint", "decarbon", "chemistry", "textile"
]

# -----------------------------------------
# UTILITIES
# -----------------------------------------
def clean_text(text):
    if not text:
        return ""
    return (
        text.replace('"', "'")
            .replace("\n", " ")
            .replace("\r", " ")
            .replace("\t", " ")
            .strip()
    )

def format_date(date_string):
    """Format publishedAt date from API into DD-MM-YYYY; fallback to today if invalid."""
    if not date_string:
        return datetime.now().strftime("%d-%m-%Y")
    try:
        # handle ISO timestamps
        parsed_date = datetime.fromisoformat(date_string.replace("Z", "+00:00"))
        return parsed_date.strftime("%d-%m-%Y")
    except Exception:
        try:
            date_part = date_string.split("T")[0]
            year, month, day = date_part.split("-")
            return f"{day}-{month}-{year}"
        except Exception:
            return datetime.now().strftime("%d-%m-%Y")

def hash_query(query):
    return hashlib.md5(query.encode()).hexdigest()

# -----------------------------------------
# CACHE HANDLING
# -----------------------------------------
def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception:
        return {}

def save_cache(cache_data):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, indent=2, ensure_ascii=False)

# -----------------------------------------
# FETCHING
# -----------------------------------------
def fetch_news_from_api():
    all_articles = []
    cache_data = load_cache()
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    for theme, query in QUERY_THEMES.items():
        print(f"🔍 Searching for theme: {theme}")
        q_hash = hash_query(query)

        # Check cache (valid for 24 hours)
        if q_hash in cache_data and (datetime.now() - datetime.fromisoformat(cache_data[q_hash]["timestamp"])).total_seconds() < 86400:
            print(f"🗃 Using cached results for {theme}")
            all_articles.extend(cache_data[q_hash]["articles"])
            continue

        params = {
            "q": query,
            "from": seven_days_ago,
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": 20,
            "apiKey": API_KEY,
        }

        try:
            response = requests.get(BASE_URL, params=params)
            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", [])
                formatted = []
                for article in articles:
                    title = clean_text(article.get("title", ""))
                    desc = clean_text(article.get("description", ""))
                    published_at = format_date(article.get("publishedAt", ""))

                    if not title or not article.get("url"):
                        continue

                    formatted.append({
                        "title": title,
                        "url": article.get("url"),
                        "source": clean_text(article.get("source", {}).get("name", "Unknown Source")),
                        "date": published_at,
                        "description": desc or "No description available.",
                        "imageUrl": article.get("urlToImage", ""),
                        "theme": theme
                    })
                all_articles.extend(formatted)
                # Cache results
                cache_data[q_hash] = {"timestamp": datetime.now().isoformat(), "articles": formatted}
                print(f"✅ Found {len(formatted)} new articles for {theme}")
            else:
                print(f"❌ API error for {theme}: {response.status_code}")
            time.sleep(1)
        except Exception as e:
            print(f"❌ Error fetching {theme}: {e}")

    save_cache(cache_data)
    return all_articles

# -----------------------------------------
# FILTERING & DEDUPLICATION
# -----------------------------------------
def relevance_score(article):
    text = (article["title"] + " " + article["description"]).lower()
    matches = sum(word in text for word in CONTEXT_WORDS)
    return matches / len(CONTEXT_WORDS)

def filter_relevant_articles(articles, min_score=0.05):
    return [a for a in articles if relevance_score(a) >= min_score]

def remove_duplicates(articles):
    seen = set()
    unique = []
    for a in articles:
        if a["url"] not in seen:
            seen.add(a["url"])
            unique.append(a)
    return unique

# -----------------------------------------
# SAVE FINAL FILE
# -----------------------------------------
def save_articles(articles):
    news_data = {
        "lastUpdated": datetime.now().isoformat(),
        "totalArticles": len(articles),
        "articles": articles[:30],
    }
    with open(FINAL_FILE, "w", encoding="utf-8") as f:
        json.dump(news_data, f, indent=2, ensure_ascii=False)
    print(f"💾 Saved {len(articles)} articles to {FINAL_FILE}")

# -----------------------------------------
# MAIN
# -----------------------------------------
def main():
    print("🚀 Starting sustainability news fetch")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    all_articles = fetch_news_from_api()
    print(f"📰 Total fetched: {len(all_articles)}")

    relevant = filter_relevant_articles(all_articles)
    print(f"🌱 After relevance filtering: {len(relevant)}")

    unique = remove_duplicates(relevant)
    print(f"🔍 Unique articles: {len(unique)}")

    unique.sort(key=lambda x: datetime.strptime(x["date"], "%d-%m-%Y"), reverse=True)
    save_articles(unique)

    print("✅ Done")

if __name__ == "__main__":
    main()
