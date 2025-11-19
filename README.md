# Personal Stock Research Assistent
An intelligent multi-agent system that automates comprehensive stock analysis.


## The Problem
Individual investors spend 3-5 hours researching a single stock before making investment decisions. This process involves:

- Manually checking multiple financial websites for price data and fundamentals
- Reading through dozens of news articles and social media posts to gauge sentiment
- Calculating technical indicators using spreadsheets or separate tools
- Synthesizing all this information into a coherent investment thesis

This manual process is time-consuming, error-prone, and often results in incomplete analysis due to information overload.

## The Solution
A Personal Stock Research Assistant - an intelligent multi-agent system that automates comprehensive stock analysis. Users simply ask questions like "Should I invest in TSLA?" or "Give me a detailed analysis of NVDA" and receive a thorough, data-driven report in minutes instead of hours.


## Agent Architecture (Multi-Agent System)

### Orchestrator Agent (Main Controller)
- Type: LLM-powered agent (GPT-4, Claude, or Gemini)
- Parse user queries and extract ticker symbols
- Determine which specialized agents to invoke
- Coordinate sequential and parallel agent execution
- Synthesize final recommendations
- Tools: Agent routing, task decomposition
- Memory: Maintains conversation context and user preferences

### Financial Data Agent (Parallel)
- Type: Tool-based agent
- Role: Fetch quantitative financial data
- Data Sources: Real-time & historical price data (Yahoo Finance API), company fundamentals (revenue, earnings, P/E ratio, market cap) & financial statements (balance sheet, income statement)
- Tools: Custom API clients (yfinance, Alpha Vantage)
- Output: Structured financial metrics

### Sentiment Analysis Agent (Parallel)
- Type: LLM-powered agent
- Role: Analyze qualitative information and market sentiment
- Data Sources: Recent news articles (NewsAPI, Google News), Social media sentiment (Twitter/X, Reddit)
Analyst ratings and price targets
- Tools: OpenAPI tools (news APIs), web search, LLM for sentiment extraction
- Output: Sentiment score (-1 to +1) with supporting evidence

### Report Generator Agent (Sequential - final step)
- Type: LLM + visualization agent
- Role: Create comprehensive, readable report
- Components: Executive summary with recommendation, Visual charts (price history), Detailed sections for each analysis type, Risk warnings and disclaimers
- Tools: Matplotlib/Plotly for charts, LLM for narrative generation
- Output: Markdown/HTML report with visualizations