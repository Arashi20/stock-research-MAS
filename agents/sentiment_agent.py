# Agent that analyzes sentiment from news and social media.
# Runs in parallel with financial data agent.


import logging
import os
from typing import Dict, Any
from agents.state import AgentState
from tools.news_tool import fetch_recent_news
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-flash-latest",  # Use the latest Gemini Flash model
    google_api_key=os.getenv('GOOGLE_API_KEY'),  # Ensure your API key is set in environment variables
    temperature=0.3
)

def sentiment_analysis_agent(state: AgentState) -> AgentState:
    """
    Agent that analyzes news sentiment using LLM.
    Runs in parallel with financial agent.
    """
    ticker = state['ticker']
    company_name = state.get('company_name', ticker)
    
    logger.info(f"📰 Sentiment Analysis Agent: Analyzing sentiment for {company_name}")
    
    # Fetch news articles
    news_data = fetch_recent_news(ticker, company_name)
    
    if not news_data['success'] or not news_data['articles']:
        logger.warning(f"⚠️ Sentiment Analysis Agent: No news articles found for {company_name}")
        state['sentiment_data'] = {
            'sentiment_score': 0.0,
            'summary': 'No recent news available for analysis.',
            'article_count': 0
        }
        state['sentiment_score'] = 0.0
        return state
    
    # Prepare articles for LLM analysis
    articles_text = "\n\n".join([
        f"Title: {article['title']}\nDescription: {article.get('description', 'N/A')}"
        for article in news_data['articles'][:10]  # Analyze top 10 articles
    ])
    
    # Create prompt for LLM
    prompt = f"""Analyze the sentiment of the following news articles about {company_name} ({ticker}).

NEWS ARTICLES:
{articles_text}

Provide:
1. A sentiment score from -1.0 (very negative) to +1.0 (very positive)
2. A brief summary (2-3 sentences) of the overall sentiment and key themes

Format your response EXACTLY as:
SCORE: [number between -1.0 and 1.0]
SUMMARY: [your summary here]
"""
    
    try:
        # Get LLM analysis
        response = llm.invoke(prompt)
        response_text = str(response.content) 
        
        # Parse response
        score_line = [line for line in response_text.split('\n') if line.startswith('SCORE:')]
        summary_line = [line for line in response_text.split('\n') if line.startswith('SUMMARY:')]
        
        sentiment_score = 0.0
        if score_line:
            try:
                sentiment_score = float(score_line[0].replace('SCORE:', '').strip())
                # Clamp between -1 and 1
                sentiment_score = max(-1.0, min(1.0, sentiment_score))
            except:
                sentiment_score = 0.0
        
        summary = summary_line[0].replace('SUMMARY:', '').strip() if summary_line else "Analysis completed."
        
        logger.info(f"✅ Sentiment Analysis Agent: Score = {sentiment_score:.2f}")
        logger.info(f"   Analyzed {len(news_data['articles'])} articles")
        
        state['sentiment_data'] = {
            'sentiment_score': sentiment_score,
            'summary': summary,
            'article_count': len(news_data['articles']),
            'articles': news_data['articles'][:5]  # Keep top 5 for report
        }
        state['sentiment_score'] = sentiment_score
        
    except Exception as e:
        logger.error(f"❌ Sentiment Analysis Agent: LLM analysis failed - {e}")
        state['errors'].append(f"Sentiment analysis error: {str(e)}")
        state['sentiment_data'] = {
            'sentiment_score': 0.0,
            'summary': 'Sentiment analysis failed.',
            'article_count': 0
        }
        state['sentiment_score'] = 0.0
    
    return state