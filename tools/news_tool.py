# Tool that fetches and processes news data.

import os
from newsapi import NewsApiClient
from typing import Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

def fetch_recent_news(ticker: str, company_name: str, days: int = 7) -> Dict[str, Any]:
    """
    Fetch recent news articles about a company.
    
    Args:
        ticker: Stock ticker symbol
        company_name: Full company name for better search
        days: Number of days to look back (default: 7)
    
    Returns:
        Dictionary containing news articles and metadata
    """
    try:
        api_key = os.getenv('NEWS_API_KEY')
        newsapi = NewsApiClient(api_key=api_key)
        
        # Search for news using company name
        from datetime import datetime, timedelta
        from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        articles_response = newsapi.get_everything(
            q=company_name,
            from_param=from_date,
            language='en',
            sort_by='relevancy',
            page_size=20  # Get top 20 articles
        )
        
        articles = articles_response.get('articles', [])
        
        # Simplify article data
        simplified_articles = []
        for article in articles:
            simplified_articles.append({
                'title': article.get('title', ''),
                'description': article.get('description', ''),
                'source': article.get('source', {}).get('name', 'Unknown'),
                'published_at': article.get('publishedAt', ''),
                'url': article.get('url', '')
            })
        
        return {
            'ticker': ticker,
            'company_name': company_name,
            'articles': simplified_articles,
            'total_articles': len(simplified_articles),
            'success': True
        }
        
    except Exception as e:
        return {
            'ticker': ticker,
            'company_name': company_name,
            'articles': [],
            'success': False,
            'error': str(e)
        }

# Test function
if __name__ == "__main__":
    result = fetch_recent_news("AAPL", "Apple Inc")
    print(f"Found {result['total_articles']} articles")
    if result['articles']:
        print(f"First article: {result['articles'][0]['title']}")