"""
Content Ingestion Module
Automatically scrapes intelligence data from RSS feeds, news APIs, and government portals.
"""

import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import re

from config import settings, RSS_FEEDS, GOV_PORTALS, RELEVANCE_KEYWORDS
from models.schemas import ArticleCategory


class NewsArticle:
    """Data class for scraped news articles."""
    
    def __init__(
        self,
        title: str,
        content: str,
        url: str,
        source: str,
        category: ArticleCategory,
        published_date: Optional[datetime] = None,
        relevance_score: float = 0.0,
    ):
        self.title = title
        self.content = content
        self.url = url
        self.source = source
        self.category = category
        self.published_date = published_date or datetime.utcnow()
        self.relevance_score = relevance_score
    
    def __repr__(self):
        return f"<NewsArticle(title='{self.title[:50]}...', category={self.category}, score={self.relevance_score:.2f})>"


def fetch_rss_feeds(hours_lookback: int = 24) -> List[NewsArticle]:
    """
    Fetch articles from RSS feeds.
    
    Args:
        hours_lookback: Only return articles published within this timeframe
    
    Returns:
        List of NewsArticle objects
    """
    print(f"📡 Fetching RSS feeds (last {hours_lookback} hours)...")
    articles = []
    cutoff_time = datetime.utcnow() - timedelta(hours=hours_lookback)
    
    for category, feed_urls in RSS_FEEDS.items():
        for feed_url in feed_urls:
            try:
                print(f"  → {feed_url}")
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries:
                    # Parse published date
                    pub_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                    
                    # Skip old articles
                    if pub_date and pub_date < cutoff_time:
                        continue
                    
                    # Extract content
                    content = ""
                    if hasattr(entry, 'summary'):
                        content = entry.summary
                    elif hasattr(entry, 'description'):
                        content = entry.description
                    
                    # Clean HTML tags
                    content = BeautifulSoup(content, 'html.parser').get_text()
                    
                    article = NewsArticle(
                        title=entry.title,
                        content=content,
                        url=entry.link,
                        source=feed.feed.get('title', 'RSS Feed'),
                        category=ArticleCategory(category),
                        published_date=pub_date,
                    )
                    
                    articles.append(article)
                
                # Rate limiting - be polite to RSS servers
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  ⚠️  Error fetching {feed_url}: {e}")
                continue
    
    print(f"✅ Fetched {len(articles)} articles from RSS feeds")
    return articles


def fetch_news_api(query: str = None, hours_lookback: int = 24) -> List[NewsArticle]:
    """
    Fetch articles from NewsAPI.
    
    Args:
        query: Search query (if None, uses category keywords)
        hours_lookback: Time window for articles
    
    Returns:
        List of NewsArticle objects
    """
    print(f"📰 Fetching from NewsAPI...")
    
    if not settings.news_api_key or settings.news_api_key == "your_newsapi_key_here":
        print("⚠️  NewsAPI key not configured, skipping...")
        return []
    
    articles = []
    base_url = "https://newsapi.org/v2/everything"
    
    # Calculate date range
    from_date = (datetime.utcnow() - timedelta(hours=hours_lookback)).strftime('%Y-%m-%d')
    
    # Query for each category
    category_queries = {
        "geopolitics": "geopolitics OR diplomacy OR international relations OR sanctions",
        "defense": "military OR defense OR NATO OR weapons OR warfare",
        "cyber": "cybersecurity OR cyber attack OR APT OR ransomware OR breach",
        "finance": "economy OR markets OR central bank OR fiscal policy OR sovereign debt",
    }
    
    for category, search_query in category_queries.items():
        try:
            params = {
                "q": search_query,
                "from": from_date,
                "language": "en",
                "sortBy": "relevancy",
                "pageSize": 20,
                "apiKey": settings.news_api_key,
            }
            
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'ok':
                for item in data.get('articles', []):
                    article = NewsArticle(
                        title=item.get('title', 'No title'),
                        content=item.get('description', '') + '\n\n' + item.get('content', ''),
                        url=item.get('url', ''),
                        source=item.get('source', {}).get('name', 'NewsAPI'),
                        category=ArticleCategory(category),
                        published_date=datetime.fromisoformat(item['publishedAt'].replace('Z', '+00:00')) if item.get('publishedAt') else None,
                    )
                    articles.append(article)
            
            # NewsAPI rate limiting: 100 requests/day on free tier
            time.sleep(1)
            
        except Exception as e:
            print(f"  ⚠️  Error fetching NewsAPI for {category}: {e}")
            continue
    
    print(f"✅ Fetched {len(articles)} articles from NewsAPI")
    return articles


def scrape_government_portals() -> List[NewsArticle]:
    """
    Scrape government portals for official press releases.
    Note: This is a simplified scraper. Production version would need
    more robust parsing for each specific portal.
    """
    print(f"🏛️  Scraping government portals...")
    articles = []
    
    for portal in GOV_PORTALS:
        try:
            print(f"  → {portal['name']}")
            
            response = requests.get(portal['url'], timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Generic scraping - look for article/press release patterns
            # This is a placeholder - real implementation would need custom parsers per site
            links = soup.find_all('a', href=True, limit=10)
            
            for link in links:
                title = link.get_text(strip=True)
                href = link['href']
                
                # Make absolute URL
                if not href.startswith('http'):
                    from urllib.parse import urljoin
                    href = urljoin(portal['url'], href)
                
                # Skip if title is too short (likely navigation link)
                if len(title) < 20:
                    continue
                
                article = NewsArticle(
                    title=title,
                    content=title,  # Placeholder - would fetch full content in production
                    url=href,
                    source=portal['name'],
                    category=ArticleCategory(portal['category']),
                )
                articles.append(article)
            
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            print(f"  ⚠️  Error scraping {portal['name']}: {e}")
            continue
    
    print(f"✅ Scraped {len(articles)} articles from government portals")
    return articles


def calculate_relevance_score(article: NewsArticle, min_score: float = 0.0) -> float:
    """
    Calculate relevance score based on keyword matching.
    
    Args:
        article: NewsArticle object
        min_score: Minimum threshold (0.0 to 1.0)
    
    Returns:
        Relevance score (0.0 to 1.0)
    """
    category_keywords = RELEVANCE_KEYWORDS.get(article.category.value, [])
    
    # Combine title and content for analysis
    text = (article.title + ' ' + article.content).lower()
    
    # Count keyword matches
    matches = 0
    for keyword in category_keywords:
        if keyword.lower() in text:
            matches += 1
    
    # Normalize score (0 to 1)
    score = min(matches / len(category_keywords), 1.0) if category_keywords else 0.0
    
    return score


def filter_content(articles: List[NewsArticle], min_score: float = None) -> List[NewsArticle]:
    """
    Filter articles by relevance score and quality thresholds.
    
    Args:
        articles: List of NewsArticle objects
        min_score: Minimum relevance score (uses config default if None)
    
    Returns:
        Filtered list of NewsArticle objects
    """
    if min_score is None:
        min_score = settings.min_relevance_score
    
    print(f"🔍 Filtering content (min score: {min_score})...")
    
    filtered = []
    for article in articles:
        # Calculate relevance
        article.relevance_score = calculate_relevance_score(article)
        
        # Apply filters
        if article.relevance_score < min_score:
            continue
        
        # Minimum content length
        if len(article.content) < 100:
            continue
        
        filtered.append(article)
    
    # Sort by relevance score (highest first)
    filtered.sort(key=lambda x: x.relevance_score, reverse=True)
    
    print(f"✅ Filtered to {len(filtered)} high-quality articles")
    return filtered


def deduplicate(articles: List[NewsArticle]) -> List[NewsArticle]:
    """
    Remove duplicate articles based on title similarity.
    
    Args:
        articles: List of NewsArticle objects
    
    Returns:
        Deduplicated list
    """
    print(f"🔄 Deduplicating articles...")
    
    seen_titles = set()
    unique = []
    
    for article in articles:
        # Normalize title for comparison
        normalized = re.sub(r'[^\w\s]', '', article.title.lower())
        
        if normalized not in seen_titles:
            seen_titles.add(normalized)
            unique.append(article)
    
    removed = len(articles) - len(unique)
    print(f"✅ Removed {removed} duplicates, {len(unique)} unique articles remain")
    return unique


def fetch_all_sources(hours_lookback: int = 24) -> List[NewsArticle]:
    """
    Main ingestion function - fetches from all sources.
    
    Args:
        hours_lookback: Time window for articles
    
    Returns:
        Combined list of NewsArticle objects
    """
    print("\n" + "="*60)
    print("🚀 STARTING CONTENT INGESTION")
    print("="*60 + "\n")
    
    all_articles = []
    
    # Fetch from all sources
    all_articles.extend(fetch_rss_feeds(hours_lookback))
    all_articles.extend(fetch_news_api(hours_lookback=hours_lookback))
    all_articles.extend(scrape_government_portals())
    
    print(f"\n📊 Total articles fetched: {len(all_articles)}")
    
    # Deduplicate
    all_articles = deduplicate(all_articles)
    
    # Filter by relevance
    all_articles = filter_content(all_articles)
    
    print(f"\n✅ Final count: {len(all_articles)} articles ready for analysis")
    print("="*60 + "\n")
    
    return all_articles
