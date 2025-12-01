# Agent that generates reports based on analysis.
# It compiles financial data and sentiment analysis into a coherent report.

import logging
import os
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO
import base64
from typing import Dict, Any
from agents.state import AgentState
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-flash-latest",  # Use the latest Gemini Flash model
    google_api_key=os.getenv('GOOGLE_API_KEY'),
    temperature=0.5
)


def create_price_chart(historical_data: Dict, ticker: str) -> str:
    """Create a simple price chart and return as base64 string."""
    try:
        if not historical_data or 'Close' not in historical_data:
            return ""
        
        # Convert to DataFrame
        df = pd.DataFrame(historical_data)
        df.index = pd.to_datetime(df.index, unit='ms') if df.index.dtype == 'int64' else df.index
        
        # Create plot
        plt.figure(figsize=(10, 6))
        plt.plot(df.index, df['Close'], linewidth=2, color='#1f77b4')
        plt.title(f'{ticker} Stock Price - Last 12 Months', fontsize=14, fontweight='bold')
        plt.xlabel('Date')
        plt.ylabel('Price ($)')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Save to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"
    except Exception as e:
        logger.error(f"Chart creation failed: {e}")
        return ""

def report_generator_agent(state: AgentState) -> AgentState:
    """
    Agent that generates the final report.
    Runs sequentially after financial and sentiment agents.
    """
    ticker = state['ticker']
    company_name = state.get('company_name', ticker)
    
    logger.info(f"📝 Report Generator Agent: Creating report for {company_name}")
    
    financial_data = state.get('financial_data', {})
    sentiment_data = state.get('sentiment_data', {})
    
    # Check if we have the necessary data
    if not financial_data or not financial_data.get('success'):
        error_report = f"""
# ❌ Analysis Failed for {ticker}

Unable to retrieve financial data. Please check if the ticker symbol is correct.

Errors: {', '.join(state.get('errors', ['Unknown error']))}
"""
        state['final_report'] = error_report
        state['recommendation'] = "UNAVAILABLE"
        return state
    
    # Generate price chart
    chart_base64 = create_price_chart(
        financial_data.get('historical_data', {}),
        ticker
    )
    
    # Prepare data for LLM
    financial_summary = f"""
Valuation:
- Current Price: ${financial_data.get('current_price', 'N/A')}
- Market Cap: ${financial_data.get('market_cap', 'N/A'):,} if isinstance(financial_data.get('market_cap'), (int, float)) else 'N/A'
- Trailing P/E: {financial_data.get('pe_ratio', 'N/A')}
- Forward P/E: {financial_data.get('forward_pe', 'N/A')}
- PEG Ratio: {financial_data.get('peg_ratio', 'N/A')} (Low < 1.0 suggests undervalued)
- Price-to-Book: {financial_data.get('price_to_book', 'N/A')}

Management Effectiveness & Profitability:
- ROE: {financial_data.get('return_on_equity', 'N/A')}
- ROA: {financial_data.get('return_on_assets', 'N/A')}
- Profit Margin: {financial_data.get('profit_margin', 'N/A')}
- Operating Margin: {financial_data.get('operating_margins', 'N/A')}

Financial Health:
- Debt-to-Equity: {financial_data.get('debt_to_equity', 'N/A')}
- Current Ratio: {financial_data.get('current_ratio', 'N/A')}
- Free Cash Flow: ${financial_data.get('free_cash_flow', 'N/A')}
- Dividend Yield: {financial_data.get('dividend_yield', 'N/A')}

Market Data:
- 52-Week High: ${financial_data.get('fifty_two_week_high', 'N/A')}
- 52-Week Low: ${financial_data.get('fifty_two_week_low', 'N/A')}
- Analyst Recommendation: {financial_data.get('analyst_recommendation', 'N/A').upper()}
"""

    sentiment_summary = f"""
    # ... keep existing sentiment summary ...
    """
    
    # UPDATED PROMPT FOR FUNDAMENTAL FOCUS
    prompt = f"""You are a Fundamental Investment Analyst creating a deep-dive stock report.
    
COMPANY: {company_name} ({ticker})

FINANCIAL DATA:
{financial_summary}

SENTIMENT ANALYSIS:
{sentiment_summary}

Generate a comprehensive fundamental investment report with the following structure:

1. **Executive Summary**: Clear BUY/HOLD/SELL recommendation based on valuation and quality.
2. **Valuation Analysis**: Is the stock cheap or expensive? (Use P/E, PEG, P/B).
3. **Management & Profitability**: Analyze management efficiency. Look for high ROE/ROA/Margins (consistently >10% indicates strong management).
4. **Financial Health**: Is the company safe? (Check Debt/Equity and Liquidity).
5. **Market Sentiment**: Summary of recent news and mood.
6. **Risk Assessment**: What could go wrong?
7. **Conclusion**: Final verdict.

Be objective, professional, and data-driven.
Start with: # Fundamental Analysis Report: {company_name} ({ticker})
"""
    
    try:
        # Generate report using LLM
        response = llm.invoke(prompt)

            # Handle different response types (string or list)
        if isinstance(response.content, str):
            report_content = response.content
        elif isinstance(response.content, list):
            # If it's a list, extracting the text from each block is necessary
            parts = []
            for item in response.content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict) and 'text' in item:
                    parts.append(item['text'])
                else:
                    parts.append(str(item))
            report_content = "".join(parts)
        else:
            report_content = str(response.content)
        
        
        # Generate price chart
        # chart_base64 = create_price_chart(
        #     financial_data.get('historical_data', {}),
        #     ticker)
        chart_base64 = ""  # Disable charts for now


        # Extract recommendation
        recommendation = "HOLD"  # Default
        if "BUY" in report_content.upper() and "DON'T BUY" not in report_content.upper():
            recommendation = "BUY"
        elif "SELL" in report_content.upper():
            recommendation = "SELL"
        
        logger.info(f"✅ Report Generator Agent: Report created")
        logger.info(f"   Recommendation: {recommendation}")
        
        state['final_report'] = report_content
        state['recommendation'] = recommendation
        
    except Exception as e:
        logger.error(f"❌ Report Generator Agent: Failed to generate report - {e}")
        state['errors'].append(f"Report generation error: {str(e)}")
        state['final_report'] = f"# Error\n\nFailed to generate report: {str(e)}"
        state['recommendation'] = "ERROR"
    
    return state