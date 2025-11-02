import requests
import json
import os
from datetime import datetime, timedelta
import time

# NewsAPI Configuration
API_KEY = "5497339175ca40fcba7f961024dfd34d"
BASE_URL = "https://newsapi.org/v2/everything"

# Your original extensive keywords list
KEYWORDS = [
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

def test_newsapi_connection():
    """Test if we can connect to NewsAPI"""
    try:
        test_url = f"https://newsapi.org/v2/top-headlines?country=us&pageSize=1&apiKey={API_KEY}"
        response = requests.get(test_url)
        if response.status_code == 200:
            print("✅ NewsAPI connection successful")
            return True
        else:
            print(f"❌ NewsAPI connection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ NewsAPI connection error: {e}")
        return False

def fetch_news_from_api():
    """Fetch news from NewsAPI for all keywords"""
    all_articles = []
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    for keyword in KEYWORDS:
        try:
            print(f"🔍 Searching for: {keyword}")
            
            params = {
                'q': keyword,
                'from': seven_days_ago,
                'sortBy': 'publishedAt',
                'language': 'en',
                'pageSize': 3,  # Reduced further to avoid limits
                'apiKey': API_KEY
            }
            
            response = requests.get(BASE_URL, params=params)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                
                for article in articles:
                    # Clean and format article data
                    title = article.get('title', '').strip()
                    url = article.get('url', '')
                    
                    # Skip if no title or URL
                    if not title or not url:
                        continue
                        
                    # Clean description
                    description = article.get('description', '').strip()
                    if not description:
                        description = 'No description available.'
                    
                    # Clean source
                    source = article.get('source', {}).get('name', 'Unknown Source')
                    if not source or source == 'null':
                        source = 'Unknown Source'
                    
                    # Format article data
                    formatted_article = {
                        'title': clean_text(title),
                        'url': url,
                        'source': clean_text(source),
                        'date': format_date(article.get('publishedAt', '')),
                        'description': clean_text(description),
                        'imageUrl': article.get('urlToImage', ''),
                        'keyword': keyword
                    }
                    
                    all_articles.append(formatted_article)
                
                print(f"✅ Found {len(articles)} articles for '{keyword}'")
            else:
                print(f"❌ API error for '{keyword}': {response.status_code}")
            
            # Be nice to the API
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ Error fetching news for '{keyword}': {e}")
            continue
    
    return all_articles

def clean_text(text):
    """Clean text for JSON compatibility"""
    if not text:
        return ""
    # Remove problematic characters and extra whitespace
    cleaned = (text
               .replace('"', "'")  # Replace double quotes with single
               .replace('\n', ' ')  # Replace newlines with spaces
               .replace('\r', ' ')  # Replace carriage returns
               .replace('\t', ' ')  # Replace tabs
               .strip())
    return cleaned

def format_date(date_string):
    """Convert ISO date to DD-MM-YYYY format"""
    try:
        if date_string:
            # Handle both 2024-12-19T00:00:00Z and 2024-12-19T00:00:00+00:00 formats
            date_part = date_string.split('T')[0]
            year, month, day = date_part.split('-')
            return f"{day}-{month}-{year}"
    except:
        pass
    return datetime.now().strftime('%d-%m-%Y')

def remove_duplicates(articles):
    """Remove duplicate articles by URL"""
    seen_urls = set()
    unique_articles = []
    
    for article in articles:
        if article['url'] not in seen_urls:
            seen_urls.add(article['url'])
            unique_articles.append(article)
    
    return unique_articles

def save_articles(articles):
    """Save articles to news.json with proper encoding and formatting"""
    # Prepare final data
    news_data = {
        'lastUpdated': datetime.now().isoformat(),
        'totalArticles': len(articles),
        'articles': articles[:30]  # Limit to 30 articles
    }
    
    # Save to file with proper encoding and error handling
    try:
        with open('news.json', 'w', encoding='utf-8') as f:
            json.dump(news_data, f, indent=2, ensure_ascii=False)
        print("✅ news.json saved successfully with UTF-8 encoding")
    except Exception as e:
        print(f"❌ Error saving news.json: {e}")
        # Try with ASCII encoding as fallback
        with open('news.json', 'w', encoding='utf-8') as f:
            json.dump(news_data, f, indent=2, ensure_ascii=True)
        print("✅ news.json saved with ASCII encoding")
    
    return len(articles)

def validate_json():
    """Validate that the created JSON is valid"""
    try:
        with open('news.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("✅ news.json validation: VALID")
        return True
    except Exception as e:
        print(f"❌ news.json validation: INVALID - {e}")
        return False

def main():
    print("🚀 Starting daily news fetch...")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test connection first
        if not test_newsapi_connection():
            print("⚠️ Cannot connect to NewsAPI, creating empty news file")
            emergency_data = {
                'lastUpdated': datetime.now().isoformat(),
                'totalArticles': 0,
                'articles': []
            }
            save_articles([])
            return
        
        # Fetch articles from NewsAPI
        articles = fetch_news_from_api()
        print(f"📰 Total articles fetched: {len(articles)}")
        
        if not articles:
            print("⚠️ No articles found. Creating empty news file.")
            save_articles([])
            return
        
        # Remove duplicates
        unique_articles = remove_duplicates(articles)
        print(f"🔍 Unique articles: {len(unique_articles)}")
        
        # Sort by date (newest first)
        unique_articles.sort(key=lambda x: datetime.strptime(x['date'], '%d-%m-%Y'), reverse=True)
        
        # Save to file
        saved_count = save_articles(unique_articles)
        
        # Validate the JSON
        validate_json()
        
        print(f"✅ Successfully saved {saved_count} articles to news.json")
        print("🎉 News update completed!")
        
    except Exception as e:
        print(f"❌ Critical error in main: {e}")
        import traceback
        traceback.print_exc()
        
        # Create a basic valid news.json file even if there's an error
        emergency_data = {
            'lastUpdated': datetime.now().isoformat(),
            'totalArticles': 0,
            'articles': []
        }
        with open('news.json', 'w', encoding='utf-8') as f:
            json.dump(emergency_data, f, indent=2, ensure_ascii=False)
        print("⚠️ Created emergency news.json file")

if __name__ == "__main__":
    main()
