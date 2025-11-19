# Orchestrator agent that coordinates other agents.
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

import logging
import re
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.financial_agent import financial_data_agent
from agents.sentiment_agent import sentiment_analysis_agent
from agents.report_agent import report_generator_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Approach 1: Use LLM to extract ticker from user query
load_dotenv()

# Initialize LLM for query parsing (at top of file with other imports)
query_parser_llm = ChatGoogleGenerativeAI(
    model="gemini-flash-latest",  # Points to the latest Gemini Flash model (Lightweight and fast)
    google_api_key=os.getenv('GOOGLE_API_KEY'),
    temperature=0.0  # Low temperature for consistent extraction
)

def extract_ticker_with_llm(user_query: str) -> str:
    """
    Use LLM to extract stock ticker from user query.
    Much more robust than regex!
    
    Examples:
        "Should I invest in TSLA?" -> "TSLA"
        "analyze tsla" -> "TSLA"
        "tell me about apple stock" -> "AAPL"
        "what do you think about tesla?" -> "TSLA"
    """
    
    prompt = f"""Extract the stock ticker symbol from the following user query.

User Query: "{user_query}"

Rules:
1. Return ONLY the ticker symbol (e.g., AAPL, TSLA, MSFT)
2. Return it in UPPERCASE
3. If multiple tickers mentioned, return the first/main one
4. If no ticker can be identified, return "UNKNOWN"
5. Do NOT include any explanation, just the ticker

Examples:
- "Should I invest in TSLA?" → TSLA
- "analyze apple stock" → AAPL
- "what about tesla" → TSLA
- "compare AAPL and MSFT" → AAPL
- "tell me about the stock market" → UNKNOWN

Ticker:"""

    try:
        response = query_parser_llm.invoke(prompt)
        ticker = str(response.content).strip().upper()
        
        # Validate it looks like a ticker (2-5 letters, all caps)
        if re.match(r'^[A-Z]{2,5}$', ticker):
            return ticker
        else:
            return "UNKNOWN"
            
    except Exception as e:
        logger.error(f"LLM ticker extraction failed: {e}")
        # Fallback to regex if LLM fails
        return extract_ticker_regex(user_query)

# Approach 2: Regex-based extraction (fallback)
def extract_ticker_regex(user_query: str) -> str:
    """
    Fallback regex-based ticker extraction.
    Used if LLM fails.
    """
    # Try to find ticker pattern
    ticker_match = re.search(r'\b([A-Z]{2,5})\b', user_query)
    if ticker_match:
        potential_ticker = ticker_match.group(1)
        excluded_words = {'IN', 'AN', 'TO', 'IT', 'IS', 'OR', 'ON', 'AT', 'BY', 'OF'}
        if potential_ticker not in excluded_words:
            return potential_ticker
    
    # Try company name mapping
    company_map = {
        'apple': 'AAPL',
        'tesla': 'TSLA',
        'microsoft': 'MSFT',
        'google': 'GOOGL',
        'amazon': 'AMZN',
        'meta': 'META',
        'nvidia': 'NVDA',
        'netflix': 'NFLX',
    }
    
    query_lower = user_query.lower()
    for company, ticker in company_map.items():
        if company in query_lower:
            return ticker
    
    return "UNKNOWN"

def parse_query_node(state: AgentState) -> AgentState:
    """
    Initial node that parses the user query and extracts the ticker using LLM.
    """
    user_query = state['user_query']
    
    logger.info(f"🔍 Orchestrator: Parsing query: '{user_query}'")
    
    # Use LLM to extract ticker
    ticker = extract_ticker_with_llm(user_query)
    
    if ticker == "UNKNOWN":
        logger.error("❌ Orchestrator: Could not extract ticker from query")
        state['ticker'] = "UNKNOWN"
        state['errors'] = [f"Could not identify stock ticker in query: '{user_query}'. Please mention a specific stock ticker or company name."]
    else:
        logger.info(f"✅ Orchestrator: Extracted ticker: {ticker}")
        state['ticker'] = ticker
        state['errors'] = []
    
    return state


def parallel_agents_node(state: AgentState) -> AgentState:
    """
    Node that runs financial and sentiment agents in parallel.
    This is a workaround since true parallelism in LangGraph requires threading.
    For simplicity, we'll run them sequentially but they're logically independent.
    """
    logger.info("🔄 Orchestrator: Running data collection agents...")
    
    # Run both agents (they're independent, so order doesn't matter)
    state = financial_data_agent(state)
    state = sentiment_analysis_agent(state)
    
    logger.info("✅ Orchestrator: Data collection complete")
    
    return state

def should_continue(state: AgentState) -> str:
    """
    Decision node: Check if we should continue or end due to errors.
    """
    if state['ticker'] == "UNKNOWN":
        return "end"
    return "continue"

def create_workflow() -> StateGraph:
    """
    Create the LangGraph workflow.
    
    Workflow:
        parse_query
            │
            ▼
        [Check if valid ticker]
            │
            ├─► (if invalid) → END
            │
            ▼
        parallel_agents
        (Financial + Sentiment)
            │
            ▼
        report_agent
            │
            ▼
        END
    """
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("parse_query", parse_query_node)
    workflow.add_node("parallel_agents", parallel_agents_node)
    workflow.add_node("report_agent", report_generator_agent)
    
    # Set entry point
    workflow.set_entry_point("parse_query")
    
    # Add conditional edge after parsing
    workflow.add_conditional_edges(
        "parse_query",
        should_continue,
        {
            "continue": "parallel_agents",
            "end": END
        }
    )
    
    # From parallel agents to report
    workflow.add_edge("parallel_agents", "report_agent")
    
    # From report to end
    workflow.add_edge("report_agent", END)
    
    return workflow

def create_stock_research_agent():
    """
    Create and compile the stock research agent workflow.
    
    Returns:
        Compiled LangGraph app ready to run.
    """
    workflow = create_workflow()
    app = workflow.compile()
    
    logger.info("✅ Stock Research Agent workflow created successfully")
    
    return app

# For testing: run python -m agents.orchestrator (run it as a module) in your terminal
if __name__ == "__main__":
    # Test ticker extraction with various formats
    test_queries = [
        "Should I invest in TSLA?",
        "Give me analysis of AAPL",
        "What do you think about Tesla stock?",
        "Analyze NVDA for me",
        "analyze tsla",  # lowercase!
        "tell me about apple",  # just company name
        "what's your opinion on nvidia?",
        "I want to buy some Amazon stock",
        "compare Microsoft and Apple",  # multiple stocks: should get first
    ]
    
    print("Testing LLM-based ticker extraction:")
    print("=" * 70)
    for query in test_queries:
        ticker = extract_ticker_with_llm(query)
        print(f"Query: '{query}'")
        print(f"Extracted: {ticker}")
        print()

