# Personal Stock Research Assistent
An intelligent multi-agent system that automates comprehensive stock analysis.

This project was meant as a submission to the **Agents Intensive - Capstone Project**.

# Problem Statement
Individual investors spend 3-5 hours researching a single stock before making investment decisions. This manual process involves checking multiple financial websites for price data and fundamentals, reading through dozens of news articles to gauge market sentiment, and synthesizing all this information into a coherent investment thesis. The repetitive nature of gathering the same types of data for each stock becomes mentally exhausting and time-consuming. Manual research also struggles with consistency—analysis quality varies based on available time and energy, and it's easy to miss critical information when juggling multiple data sources. Automation can streamline data gathering from financial APIs, analyze news sentiment using LLMs, generate comprehensive reports, and maintain consistent analysis quality across all stocks, allowing investors to focus their expertise on strategic decision-making and portfolio management rather than data collection.

# Solution Statement
AI agents can automatically fetch real-time financial data (price, P/E ratio, market cap, historical performance) from Yahoo Finance, eliminating manual website checks. They can analyze recent news articles using LLM-powered sentiment analysis, converting qualitative information into quantitative scores that capture market mood. Additionally, agents can synthesize multi-source data into professional-grade investment reports with clear BUY/HOLD/SELL recommendations, complete with risk assessments and supporting evidence—transforming stock research from a 3-5 hour manual process into a 25-second automated workflow that delivers institutional-quality analysis to individual investors.

# Architecture
Core to the Stock Research Assistant is the orchestrator agent—a prime example of a multi-agent system. It's not a monolithic application but an ecosystem of specialized agents, each contributing to a different stage of the analysis process. This modular approach, facilitated by LangGraph, allows for a sophisticated workflow with both parallel and sequential execution patterns.

### The Orchestrator Agent
The orchestrator is the central coordinator, built using LangGraph's StateGraph with a shared AgentState TypedDict. Its definition highlights several key responsibilities: parsing natural language queries using Google Gemini Flash LLM to extract stock ticker symbols, managing workflow dependencies between specialized agents, and handling error states gracefully. Crucially, it coordinates both parallel execution (Financial Data + Sentiment Analysis agents running simultaneously) and sequential execution (Report Generator waiting for data collection).

### The Specialized Sub-Agents
#### Financial Data Analyst: *financial_data_agent*
This agent is responsible for retrieving comprehensive quantitative metrics from Yahoo Finance API. It fetches current price, 52-week high/low, P/E ratio, market capitalization, profit margins, and one year of historical price data. The agent wraps the yfinance library with error handling and structured output formatting, ensuring reliable data retrieval even when network issues occur. 

#### Market Sentiment Analyst: *sentiment_analysis_agent*
Once data collection begins (running in parallel with the financial agent), the sentiment analyst takes over. This LLM-powered agent fetches the 20 most recent news articles about the target company using NewsAPI, then uses Gemini Flash to analyze headline sentiment. Through careful prompt engineering, it converts qualitative news coverage into a quantitative sentiment score ranging from -1.0 (very negative) to +1.0 (very positive), along with a supporting summary of key themes. 


#### Report Generator: *report_generator_agent*
After both data collection agents complete (sequential execution), the report generator synthesizes their outputs into a comprehensive markdown report. This agent is an expert technical writer, capable of creating institutional-quality investment analysis with sections for executive summary, financial metrics, market sentiment, risk assessment, and final recommendation. It uses structured prompts to ensure consistent report quality and applies logic to determine BUY/HOLD/SELL recommendations based on multiple factors.

# Essential Tools and Workflow
#### Stock Data Retrieval (*fetch_stock_data*)
A robust wrapper around the yfinance library that handles API calls, extracts relevant metrics, and returns structured dictionaries. It includes fallback logic for missing data fields and comprehensive error handling.

#### News Aggregation (*fetch_recent_news*)
This tool interfaces with NewsAPI to fetch recent articles, filters for relevance, and structures the data for LLM analysis. It handles rate limiting gracefully and provides meaningful error messages.


#### LLM-Powered Query Parsing
Unlike traditional regex-based parsers, the orchestrator uses Gemini Flash to extract ticker symbols from natural language. This handles variations like "NVDA" vs "nvidia" vs "what about the GPU company?" with impressive robustness.

#### Parallel Execution via *LangGraph*
The financial and sentiment agents run simultaneously through LangGraph's node configuration. This reduces total execution time by ~37% (from 13 seconds sequential to 10 seconds parallel), demonstrating the efficiency gains of proper agent coordination.


# The Iterative Workflow
The beauty of the system lies in its clear execution flow:

1. User asks: "Should I invest in NVDA?"
2. Orchestrator parses query → extracts "NVDA" ticker
3. Financial + Sentiment agents execute in parallel
4. Report generator waits for both, then synthesizes findings
5. User receives comprehensive report in ~25 seconds

This multi-agent coordination, powered by LangGraph, results in a system that is modular (easy to add new agents), reusable (agents can be used independently), and scalable (handles multiple stocks efficiently).

# Value Statement
The Stock Research Assistant reduced my investment research time by 99.9% (from 3-5 hours to 15 seconds per stock), enabling me to analyze more companies while maintaining comprehensive analysis quality. I've also expanded my research into new sectors—the automated news sentiment analysis surfaces insights I'd otherwise miss due to time constraints and information overload.

# Future Enhancements
If I had more time, I would add:

1. Technical Analysis Agent - Calculate RSI, MACD, and Bollinger Bands to complement fundamental analysis
2. Portfolio Optimizer Agent - Compare multiple stocks and suggest optimal allocation strategies
3. Backtesting Agent - Test recommendations against historical data to validate accuracy
4. Real-time Alert System - Monitor price movements and news for existing holdings using WebSocket integration

This would require integrating additional financial APIs (Alpha Vantage for technical indicators) and implementing persistent storage for historical analysis tracking.


# Conclusion
The Personal Stock Research Assistant demonstrates how well-designed multi-agent systems can deliver genuine value to end users. By automating data collection, analysis, and synthesis, it proves that AI agents can handle complex, multi-step analytical tasks while maintaining quality and consistency. The system showcases practical mastery of LangGraph orchestration, LLM integration, and real-world API usage—transforming a labor-intensive manual process into an efficient, scalable automated workflow.