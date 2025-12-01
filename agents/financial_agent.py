# Agent that retrieves financial data.

import logging
from typing import Dict, Any
from agents.state import AgentState
from tools.stock_data_tool import fetch_stock_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def financial_data_agent(state: AgentState) -> AgentState:
    """
    Agent that fetches financial data for a stock.
    Runs in parallel with sentiment agent.
    """
    ticker = state['ticker']
    
    logger.info(f"💰 Financial Data Agent: Fetching data for {ticker}")
    
    # Use our tool to fetch data
    financial_data = fetch_stock_data(ticker)
    
    if financial_data['success']:
        logger.info(f"✅ Financial Data Agent: Successfully retrieved data for {ticker}")
        logger.info(f"   Current Price: ${financial_data.get('current_price', 'N/A')}")
        logger.info(f"   P/E Ratio: {financial_data.get('pe_ratio', 'N/A')}")
        logger.info(f"   PEG Ratio: {financial_data.get('peg_ratio', 'N/A')}")
        logger.info(f"   ROE: {financial_data.get('return_on_equity', 'N/A')}")
    else:
        logger.error(f"❌ Financial Data Agent: Failed to fetch data - {financial_data.get('error')}")
        state['errors'].append(f"Financial data error: {financial_data.get('error')}")
    
    # Update state with financial data
    state['financial_data'] = financial_data
    state['company_name'] = financial_data.get('company_name', ticker)
    
    return state

