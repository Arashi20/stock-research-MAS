# Agent that generates reports based on analysis.
# It compiles financial data and sentiment analysis into a coherent report.

import logging
import os
import matplotlib.pyplot as plt
import pandas as pd
import re
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

Cash Flow & Dilution (CRITICAL):
- Avg Free Cash Flow (3y): ${financial_data.get('avg_fcf_3y', 'N/A')}
- Share Dilution (3y): {financial_data.get('share_dilution_3y', 'N/A')}
  (Note: Positive dilution means shareholders are owning less of the company over time)

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
    # Pylance type errors are fine here: The agents set the data.
    sentiment_summary = f"""
Sentiment Score: {sentiment_data.get('sentiment_score', 0):.2f} (-1 = very negative, +1 = very positive)
Articles Analyzed: {sentiment_data.get('article_count', 0)}
Summary: {sentiment_data.get('summary', 'No sentiment data available')}
"""
    

    # UPDATED PROMPT - MORE CRITICAL
    prompt = f"""You are a skeptical Fundamental Investment Analyst.
    
COMPANY: {company_name} ({ticker})

FINANCIAL DATA:
{financial_summary}

SENTIMENT ANALYSIS:
{sentiment_summary}

Generate a brutal, honest investment report.

CRITICAL INSTRUCTIONS:
1. **Cash is King**: If "Avg Free Cash Flow" is negative, the company is burning cash. This is a major risk.
2. **Watch Dilution**: If "Share Dilution" is positive (e.g., >5%), the company is funding itself by selling shares, diluting existing holders. Treat this negatively.
3. **Ignore Analysts**: If the company burns cash and dilutes shareholders, you MUST be skeptical of "BUY" ratings from external analysts.
4. **Valuation**: Is the P/E justifiable given the cash flow?

Report Structure:
1. **Executive Summary**: BUY/HOLD/SELL. (Be brave: assign SELL if cash burn + dilution are high, even if sentiment is good).
2. **Cash Flow & Dilution Analysis**: deeply analyze the 3-year FCF and share count trends.
3. **Valuation**: Cheap or Value Trap?
4. **Management Efficiency**: ROE/ROA.
5. **Risk Assessment**: Bankruptcy risk? Dilution risk?
6. **Conclusion**: Final verdict.

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

        # --- NEW EXTRACTION LOGIC ---
        # Look for "VERDICT: BUY" or "VERDICT: SELL" at the end
        match = re.search(r'VERDICT:\s*(BUY|SELL|HOLD)', report_content, re.IGNORECASE)

        

        if match:
            recommendation = match.group(1).upper()
        else:
            # Fallback if LLM forgets the format
            logger.warning("⚠️ LLM did not output VERDICT format. Falling back to keyword search.")
            if "SELL" in report_content.upper()[-500:]: # Only look at the end
                recommendation = "SELL"
            elif "BUY" in report_content.upper()[-500:]:
                recommendation = "BUY"
            else:
                recommendation = "HOLD"
        
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