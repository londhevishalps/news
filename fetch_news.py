import requests
import json
import os
from datetime import datetime, timedelta
import time

# NewsAPI Configuration
API_KEY = "5497339175ca40fcba7f961024dfd34d"
BASE_URL = "https://newsapi.org/v2/everything"

# Your original extensive keywords list - ALL KEYWORDS INCLUDED
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
            print(f"Response: {response.text}")
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
                'pageSize': 5,  # Reduced to avoid hitting API limits
                'apiKey': API_KEY
            }
            
            response = requests.get(BASE_URL, params=params)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                
                for article in articles:
                    # Format article data
                    formatted_article = {
                        'title': article.get('title', '').strip(),
                        'url': article.get('url', ''),
                        'source': article.get('source', {}).get('name', 'Unknown'),
                        'date': format_date(article.get('publishedAt', '')),
                        'description': article.get('description', '').strip() or 'No description available.',
                        'imageUrl': article.get('urlToImage', ''),
                        'keyword': keyword
                    }
                    
                    # Only add if it has a title and URL
                    if formatted_article['title'] and formatted_article['url']:
                        all_articles.append(formatted_article)
                
                print(f"✅ Found {len(articles)} articles for '{keyword}'")
            else:
                print(f"❌ API error for '{keyword}': {response.status_code}")
                if response.status_code == 429:
                    print("⚠️ Rate limit hit, waiting 10 seconds...")
                    time.sleep(10)
                # Print error details for debugging
                try:
                    error_data = response.json()
                    print(f"Error message: {error_data}")
                except:
                    print(f"Error response: {response.text}")
            
            # Be nice to the API - small delay between requests
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Error fetching news for '{keyword}': {e}")
            continue
    
    return all_articles

def format_date(date_string):
    """Convert ISO date to DD-MM-YYYY format"""
    try:
        if date_string:
            dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return dt.strftime('%d-%m-%Y')
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
    """Save articles to news.json in root"""
    # Prepare final data
    news_data = {
        'lastUpdated': datetime.now().isoformat(),
        'totalArticles': len(articles),
        'articles': articles[:50]  # Limit to 50 articles
    }
    
    # Save to file
    with open('news.json', 'w', encoding='utf-8') as f:
        json.dump(news_data, f, indent=2, ensure_ascii=False)
    
    return len(articles)

def main():
    print("🚀 Starting daily news fetch...")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Debug info
    print("=== DEBUG INFO ===")
    print(f"Current directory: {os.getcwd()}")
    print(f"Files in directory: {os.listdir('.')}")
    print("==================")
    
    try:
        # Test connection first
        if not test_newsapi_connection():
            print("⚠️ Cannot connect to NewsAPI, creating empty news file")
            emergency_data = {
                'lastUpdated': datetime.now().isoformat(),
                'totalArticles': 0,
                'articles': [],
                'error': 'NewsAPI connection failed'
            }
            with open('news.json', 'w', encoding='utf-8') as f:
                json.dump(emergency_data, f, indent=2, ensure_ascii=False)
            return
        
        # Fetch articles from NewsAPI
        articles = fetch_news_from_api()
        print(f"📰 Total articles fetched: {len(articles)}")
        
        if not articles:
            print("⚠️ No articles found. Creating empty news file.")
            # Create empty but valid JSON structure
            articles = []
        
        # Remove duplicates
        unique_articles = remove_duplicates(articles)
        print(f"🔍 Unique articles: {len(unique_articles)}")
        
        # Sort by date (newest first)
        unique_articles.sort(key=lambda x: datetime.strptime(x['date'], '%d-%m-%Y'), reverse=True)
        
        # Save to file
        saved_count = save_articles(unique_articles)
        
        print(f"✅ Successfully saved {saved_count} articles to news.json")
        print("🎉 News update completed!")
        
    except Exception as e:
        print(f"❌ Critical error in main: {e}")
        import traceback
        traceback.print_exc()
        
        # Create a basic news.json file even if there's an error
        emergency_data = {
            'lastUpdated': datetime.now().isoformat(),
            'totalArticles': 0,
            'articles': [],
            'error': str(e)
        }
        with open('news.json', 'w', encoding='utf-8') as f:
            json.dump(emergency_data, f, indent=2, ensure_ascii=False)
        print("⚠️ Created emergency news.json file")
        # Don't re-raise the error so workflow can continue

if __name__ == "__main__":
    main()
