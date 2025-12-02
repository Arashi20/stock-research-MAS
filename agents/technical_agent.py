# This agent will perform technical analysis on stock data using various indicators.

import logging
from agents.state import AgentState
from tools.technical_analysis_tool import fetch_technical_indicators

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def technical_analysis_agent(state: AgentState) -> AgentState:
    """
    Agent that performs technical analysis.
    Runs in parallel with financial and sentiment agents.
    """
    ticker = state['ticker']
    logger.info(f"📈 Technical Analysis Agent: Analyzing trends for {ticker}")
    
    # Fetch indicators
    tech_data = fetch_technical_indicators(ticker)
    
    if tech_data['success']:
        logger.info(f"✅ Technical Analysis Agent: Indicators calculated")
        logger.info(f"   Trend: {tech_data.get('trend')}")
        logger.info(f"   RSI: {tech_data.get('rsi'):.2f}")
        logger.info(f"   Stoch %K: {tech_data.get('stoch_k'):.2f}")
        state['technical_data'] = tech_data
    else:
        logger.error(f"❌ Technical Analysis Agent: Failed - {tech_data.get('error')}")
        state['errors'].append(f"Technical analysis error: {tech_data.get('error')}")
        state['technical_data'] = {}
        
    return state