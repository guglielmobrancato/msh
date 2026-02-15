#!/usr/bin/env python3
"""
Ancile AI - Daily Article Generator
Generates 4 intelligence articles daily (one per category) and updates the website.
"""

import os
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
import google.generativeai as genai

# Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
NEWS_API_KEY = os.getenv('NEWS_API_KEY')

CATEGORIES = {
    'geopolitics': {
        'keywords': 'geopolitics OR NATO OR "international relations" OR diplomacy OR sanctions',
        'label': 'GEOPOLITICS',
        'emoji': '🌍'
    },
    'defense': {
        'keywords': 'military OR defense OR "armed forces" OR weapons OR warfare',
        'label': 'DEFENSE',
        'emoji': '🛡️'
    },
    'cyber': {
        'keywords': 'cybersecurity OR hacking OR "data breach" OR ransomware OR APT',
        'label': 'CYBER',
        'emoji': '💻'
    },
    'finance': {
        'keywords': 'markets OR economy OR "central bank" OR sanctions OR trade',
        'label': 'FINANCE',
        'emoji': '💰'
    }
}

def fetch_news(category_key, category_data):
    """Fetch latest news for a category"""
    url = 'https://newsapi.org/v2/everything'
    params = {
        'q': category_data['keywords'],
        'language': 'en',
        'sortBy': 'publishedAt',
        'pageSize': 5,
        'apiKey': NEWS_API_KEY,
        'from': (datetime.now() - timedelta(days=2)).isoformat()
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        articles = response.json().get('articles', [])
        return articles[0] if articles else None
    return None

def generate_analysis(news_article, category_data):
    """Generate intelligence analysis using Gemini"""
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')  # MODELLO STABILE
    
    prompt = f"""You are an intelligence analyst for Ancile AI, a strategic intelligence platform. 
Analyze this news article and write a professional intelligence report.

NEWS ARTICLE:
Title: {news_article['title']}
Content: {news_article['description']}
Source: {news_article['source']['name']}

REQUIREMENTS:
1. Write a compelling intelligence-style title (no quotes, technical language)
2. Write a 300-word analysis with:
   - Strategic implications
   - Technical details and specific metrics
   - Regional/global impact assessment
3. Use institutional language (avoid sensationalism)
4. Include confidence level: High/Moderate/Low
5. Estimate word count and reading time

Return ONLY valid JSON:
{{
  "title": "Intelligence-style title",
  "summary": "2-sentence executive summary",
  "analysis": "Full 300-word analysis in HTML paragraphs",
  "confidence": "High|Moderate|Low",
  "word_count": 2500,
  "read_time": 12
}}"""

    response = model.generate_content(prompt)
    
    try:
        # Extract JSON from response
        text = response.text.strip()
        if text.startswith('```json'):
            text = text[7:]
        if text.endswith('```'):
            text = text[:-3]
        return json.loads(text.strip())
    except:
        # Fallback if JSON parsing fails
        return {
            "title": news_article['title'],
            "summary": news_article['description'][:200],
            "analysis": f"<p>{news_article['description']}</p>",
            "confidence": "Moderate",
            "word_count": 1500,
            "read_time": 7
        }

def create_article_html(article_data, category_key, category_data, date_str):
    """Create HTML file for article"""
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{article_data['title']} | Ancile AI</title>
    <meta name="description" content="{article_data['summary']}">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            --dark-bg: #0a0e14;
            --darker-bg: #050810;
            --card-bg: #151b26;
            --border-color: #1f2937;
            --accent-blue: #3b82f6;
            --accent-cyan: #06b6d4;
            --text-primary: #e5e7eb;
            --text-secondary: #9ca3af;
            --text-muted: #6b7280;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--dark-bg);
            color: var(--text-primary);
            line-height: 1.7;
        }}
        
        .header {{
            background: var(--darker-bg);
            border-bottom: 1px solid var(--border-color);
            padding: 1.5rem 2rem;
            position: sticky;
            top: 0;
            z-index: 1000;
        }}
        
        .header-content {{
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .logo {{
            font-size: 1.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-cyan));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-decoration: none;
        }}
        
        .back-link {{
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 0.9rem;
            transition: color 0.3s;
        }}
        
        .back-link:hover {{
            color: var(--accent-cyan);
        }}
        
        .article-container {{
            max-width: 900px;
            margin: 3rem auto;
            padding: 0 2rem;
        }}
        
        .article-meta {{
            display: flex;
            gap: 1.5rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }}
        
        .category-badge {{
            padding: 0.5rem 1rem;
            background: rgba(59, 130, 246, 0.15);
            color: var(--accent-cyan);
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-radius: 0.25rem;
            font-weight: 600;
        }}
        
        .meta-item {{
            color: var(--text-muted);
            font-size: 0.9rem;
        }}
        
        h1 {{
            font-size: 2.5rem;
            font-weight: 800;
            line-height: 1.2;
            margin-bottom: 1.5rem;
            letter-spacing: -0.02em;
        }}
        
        .summary {{
            font-size: 1.2rem;
            color: var(--text-secondary);
            line-height: 1.6;
            margin-bottom: 2rem;
            padding-bottom: 2rem;
            border-bottom: 1px solid var(--border-color);
        }}
        
        .article-content {{
            font-size: 1.1rem;
            line-height: 1.8;
        }}
        
        .article-content p {{
            margin-bottom: 1.5rem;
        }}
        
        .confidence {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 0.5rem;
            margin-top: 2rem;
        }}
        
        .footer {{
            margin-top: 4rem;
            padding: 2rem;
            text-align: center;
            border-top: 1px solid var(--border-color);
            color: var(--text-muted);
        }}
    </style>
</head>
<body>
    <header class="header">
        <div class="header-content">
            <a href="/" class="logo">🛡️ ANCILE AI</a>
            <a href="/" class="back-link">← Back to Reports</a>
        </div>
    </header>
    
    <main class="article-container">
        <div class="article-meta">
            <span class="category-badge">{category_data['emoji']} {category_data['label']}</span>
            <span class="meta-item">📅 {datetime.now().strftime('%B %d, %Y')}</span>
            <span class="meta-item">📊 {article_data['word_count']} words</span>
            <span class="meta-item">⏱ {article_data['read_time']} min read</span>
            <span class="meta-item">🎯 {article_data['confidence']} Confidence</span>
        </div>
        
        <h1>{article_data['title']}</h1>
        
        <div class="summary">
            {article_data['summary']}
        </div>
        
        <div class="article-content">
            {article_data['analysis']}
        </div>
    </main>
    
    <footer class="footer">
        <p>🛡️ ANCILE AI • Strategic Intelligence Platform</p>
        <p style="margin-top: 0.5rem; font-size: 0.8rem;">
            Powered by Gemini AI • Updated automatically daily
        </p>
    </footer>
</body>
</html>"""
    
    return html

def update_homepage(articles_data):
    """Update index.html with new articles"""
    
    # Generate article cards HTML
    cards_html = ""
    for article in articles_data:
        cards_html += f"""
            <article class="article-card" onclick="window.location.href='articles/{article['filename']}'">
                <div class="article-header">
                    <div class="article-meta">
                        <span class="article-category">{article['category_data']['label']}</span>
                        <span class="article-date">{article['time_ago']}</span>
                    </div>
                    <h2 class="article-title">{article['data']['title']}</h2>
                </div>
                <div class="article-body">
                    <p class="article-summary">{article['data']['summary']}</p>
                </div>
                <div class="article-stats">
                    <div class="stat">📊 {article['data']['word_count']} words</div>
                    <div class="stat">⏱ {article['data']['read_time']} min read</div>
                    <div class="stat">🎯 {article['data']['confidence']} Confidence</div>
                </div>
            </article>
"""
    
    # Read current index.html template
    index_path = Path('index.html')
    if index_path.exists():
        with open(index_path, 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Replace content between START_ARTICLES and END_ARTICLES markers
        start_marker = '<!-- START_ARTICLES -->'
        end_marker = '<!-- END_ARTICLES -->'
        
        start_idx = html.find(start_marker)
        end_idx = html.find(end_marker)
        
        if start_idx != -1 and end_idx != -1:
            new_html = (
                html[:start_idx + len(start_marker)] +
                '\n' + cards_html +
                '\n            ' +
                html[end_idx:]
            )
            
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(new_html)

def main():
    """Main execution"""
    print("🛡️  ANCILE AI - Daily Intelligence Generation")
    print("=" * 60)
    
    articles_dir = Path('articles')
    articles_dir.mkdir(exist_ok=True)
    
    date_str = datetime.now().strftime('%Y-%m-%d')
    articles_data = []
    
    for category_key, category_data in CATEGORIES.items():
        print(f"\n{category_data['emoji']} Generating {category_data['label']} article...")
        
        # Fetch news
        news = fetch_news(category_key, category_data)
        if not news:
            print(f"  ⚠️  No news found for {category_key}")
            continue
        
        print(f"  📰 Found: {news['title'][:60]}...")
        
        # Generate analysis
        article_data = generate_analysis(news, category_data)
        print(f"  ✅ Analysis generated: {article_data['title'][:60]}...")
        
        # Create HTML file
        filename = f"{date_str}-{category_key}.html"
        html_content = create_article_html(article_data, category_key, category_data, date_str)
        
        article_path = articles_dir / filename
        with open(article_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"  💾 Saved to: {filename}")
        
        articles_data.append({
            'filename': filename,
            'data': article_data,
            'category_data': category_data,
            'time_ago': 'Today'
        })
    
    # Update homepage
    if articles_data:
        print(f"\n🔄 Updating homepage with {len(articles_data)} new articles...")
        update_homepage(articles_data)
        print("✅ Homepage updated!")
    
    print("\n" + "=" * 60)
    print(f"✅ Generated {len(articles_data)} articles successfully!")

if __name__ == '__main__':
    main()
