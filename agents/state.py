# The state is a central repository for shared information among agents.
# It allows agents to read and update shared data.

from typing import TypedDict, Dict, List, Any, Optional

class AgentState(TypedDict):
    """
    Shared state that gets passed between all agents.
    Each agent reads from and writes to this state.
    """
    # Input
    user_query: str
    ticker: str
    company_name: str
    
    # Financial Data Agent output
    financial_data: Optional[Dict[str, Any]]
    
    # Sentiment Analysis Agent output
    sentiment_data: Optional[Dict[str, Any]]
    sentiment_score: Optional[float]
    
    # Report Generator Agent output
    final_report: Optional[str]
    recommendation: Optional[str]
    
    # Metadata
    errors: List[str]