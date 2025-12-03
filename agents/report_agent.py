# Agent that generates reports based on analysis.
# It compiles financial data and sentiment analysis into a coherent report.


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
from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Gemini LLM with Safety Filters DISABLED
llm = ChatGoogleGenerativeAI(
    model="gemini-flash-latest",
    google_api_key=os.getenv('GOOGLE_API_KEY'),
    temperature=0.5,
    safety_settings={
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    }
)


def format_currency(value: Any, currency_code: str = "USD") -> str:
    """
    Format a value with currency code to avoid ambiguity in LLM prompts.
    """
    try:
        if isinstance(value, str) and value.replace('.', '', 1).isdigit():
             value = float(value)

        if isinstance(value, (int, float)):
            if value < 0:
                return f"-{currency_code} {abs(value):,.2f}"
            return f"{currency_code} {value:,.2f}"
        
        return str(value) if value else "N/A"
    except:
        return "N/A"


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
    technical_data = state.get('technical_data', {})
    
    # --- DEBUG LOGGING ---
    logger.info(f"   Financial Data Success: {financial_data.get('success')}")
    logger.info(f"   Sentiment Data Present: {bool(sentiment_data)}")
    logger.info(f"   Technical Data Present: {bool(technical_data)}")
    
    # Check if we have the necessary data
    if not financial_data or not financial_data.get('success'):
        logger.error(f"❌ Report Generator: Financial data failed/missing for {ticker}. Skipping report.")
        # If we are here, it means financial data is missing despite logs saying otherwise?
        state['final_report'] = None
        state['recommendation'] = "UNAVAILABLE"
        return state
    
    try:
        # Get currency code (default to USD)
        currency = financial_data.get('currency', 'USD')
        
        # Format currency fields
        current_price_str = format_currency(financial_data.get('current_price'), currency)
        avg_fcf_str = format_currency(financial_data.get('avg_fcf_3y'), currency)
        fcf_str = format_currency(financial_data.get('free_cash_flow'), currency)
        
        
        # Prepare data for LLM
        financial_summary = f"""
Valuation:
- Current Price: {current_price_str}
- Market Cap: {format_currency(financial_data.get('market_cap'), currency)}
- Forward P/E: {financial_data.get('forward_pe', 'N/A')}
- PEG Ratio: {financial_data.get('peg_ratio', 'N/A')} (Low < 1.0 suggests undervalued)
- Price-to-Book: {financial_data.get('price_to_book', 'N/A')}

Cash Flow & Dilution (CRITICAL):
- Avg Free Cash Flow (3y): {avg_fcf_str}
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
- Free Cash Flow: {fcf_str}
- Dividend Yield: {financial_data.get('dividend_yield', 'N/A')}

Market Data:
- 52-Week High: {format_currency(financial_data.get('fifty_two_week_high'), currency)}
- 52-Week Low: {format_currency(financial_data.get('fifty_two_week_low'), currency)}
- Analyst Recommendation: {financial_data.get('analyst_recommendation', 'N/A').upper()}
"""

        sentiment_summary = f"""
Sentiment Score: {sentiment_data.get('sentiment_score', 0):.2f} (-1 = very negative, +1 = very positive)
Articles Analyzed: {sentiment_data.get('article_count', 0)}
Summary: {sentiment_data.get('summary', 'No sentiment data available')}
"""

        technical_summary = f"""
Trend (Weekly): {technical_data.get('trend', 'N/A')}
RSI (14-Week): {technical_data.get('rsi', 'N/A'):.2f}
MACD (Weekly): {technical_data.get('macd', 'N/A'):.2f}

Stochastic Oscillator (Weekly 14,1,3):
- %K Line: {technical_data.get('stoch_k', 'N/A'):.2f} (Green Line)
- %D Line: {technical_data.get('stoch_d', 'N/A'):.2f} (Red Line)
- Signal: {technical_data.get('stoch_signal', 'N/A')}
"""
        

        # UPDATED PROMPT - MORE CRITICAL
        prompt = f"""You are a skeptical Fundamental Investment Analyst.
        
COMPANY: {company_name} ({ticker})

FINANCIAL DATA:
{financial_summary}

SENTIMENT ANALYSIS:
{sentiment_summary}

TECHNICAL ANALYSIS:
{technical_summary}

Generate a brutal, honest investment report.

CRITICAL INSTRUCTIONS:
1. **Cash is King**: If "Avg Free Cash Flow" is negative, the company is burning cash. This is a major risk.
2. **Watch Dilution**: If "Share Dilution" is positive (e.g., >5%), the company is funding itself by selling shares, diluting existing holders. Treat this negatively.
3. **Ignore Analysts**: If the company burns cash and dilutes shareholders, you MUST be skeptical of "BUY" ratings from external analysts.
4. **Valuation**: Is the P/E justifiable given the cash flow?
5. **Use Technicals for Timing**: Use RSI/Stochastics to recommend *when* to buy/sell (e.g., "Good company, but wait for RSI to cool off").

Report Structure:
1. **Executive Summary**: BUY/HOLD/SELL. (Be brave: assign SELL if cash burn + dilution are high, even if sentiment is good).
2. **Cash Flow & Dilution Analysis**: deeply analyze the 3-year FCF and share count trends.
3. **Valuation**: Cheap or Value Trap?
4. **Management Efficiency**: ROE/ROA.
5. **Risk Assessment**: Bankruptcy risk? Dilution risk?
6. **Technical Analysis**: Use RSI, Stochastics, and other indicators to assess timing and momentum.
7. **Conclusion**: Final verdict.

Start with: # Fundamental Analysis Report: {company_name} ({ticker})

IMPORTANT:
At the very end of your response, on a new line, you MUST print the final recommendation in this exact format:
VERDICT: [BUY/HOLD/SELL]
"""
    
        logger.info("🤖 Report Generator: Sending prompt to LLM...")
        
        # Generate report using LLM
        response = llm.invoke(prompt)
        
        logger.info("🤖 Report Generator: Received response from LLM")

        # Handle different response types (string or list)
        if isinstance(response.content, str):
            report_content = response.content
        elif isinstance(response.content, list):
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
            
        # Check for empty report
        if not report_content or report_content.strip() == "":
            logger.error("❌ Report Generator Agent: LLM returned empty report (Possible Safety Block)")
            report_content = f"""# Analysis Blocked
            
The AI model refused to generate a report for **{company_name}**. 
This often happens with Defense/Weapon companies due to safety filters.
"""

        # --- SANITIZATION STEP ---
        report_content = report_content.replace("\\$", "$")
        report_content = re.sub(r'\$(-?\$?[\d,.]+\w*)\$', r'\1', report_content)
        report_content = report_content.replace("$", "＄")
        

        # --- EXTRACTION LOGIC ---
        match = re.search(r'VERDICT:\s*(BUY|SELL|HOLD)', report_content, re.IGNORECASE)

        if match:
            recommendation = match.group(1).upper()
        else:
            logger.warning("⚠️ LLM did not output VERDICT format. Falling back to keyword search.")
            if "SELL" in report_content.upper()[-500:]:
                recommendation = "SELL"
            elif "BUY" in report_content.upper()[-500:]:
                recommendation = "BUY"
            else:
                recommendation = "HOLD"
        
        logger.info(f"✅ Report Generator Agent: Report created")
        
        state['final_report'] = report_content
        state['recommendation'] = recommendation
        
    except BaseException as e:
        logger.critical(f"❌ Report Generator Agent: CRITICAL FAILURE - {e}", exc_info=True)
        state['errors'].append(f"Report generation critical error: {str(e)}")
        state['final_report'] = f"# Error\n\nFailed to generate report: {str(e)}"
        state['recommendation'] = "ERROR"
    
    return state