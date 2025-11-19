#Main entry point for the Stock Analysis Agents project

import logging
from agents.orchestrator import create_stock_research_agent
from agents.state import AgentState

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def run_stock_analysis(query: str) -> dict:
    """
    Run stock analysis for a given query.
    
    Args:
        query: User query (e.g., "Should I invest in TSLA?")
    
    Returns:
        Dictionary containing the final report and recommendation
    """
    print("\n" + "="*70)
    print(f"🚀 STARTING STOCK ANALYSIS")
    print("="*70)
    
    # Create the agent workflow
    agent = create_stock_research_agent()
    
    # Initialize state
    initial_state: AgentState = {
        'user_query': query,
        'ticker': '',
        'company_name': '',
        'financial_data': None,
        'sentiment_data': None,
        'sentiment_score': None,
        'final_report': None,
        'recommendation': None,
        'errors': []
    }
    
    # Run the workflow
    print(f"\n💬 Query: '{query}'")
    print("\n⏳ Running multi-agent analysis...\n")
    
    final_state = agent.invoke(initial_state)
    
    print("\n" + "="*70)
    print(f"✅ ANALYSIS COMPLETE")
    print("="*70)
    
    return {
        'ticker': final_state.get('ticker'),
        'company_name': final_state.get('company_name'),
        'recommendation': final_state.get('recommendation'),
        'sentiment_score': final_state.get('sentiment_score'),
        'report': final_state.get('final_report'),
        'errors': final_state.get('errors', [])
    }

def main():
    """Main function for interactive use."""
    
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║     Personal Stock Research Assistant                 ║
    ║     Powered by Multi-Agent AI System                  ║
    ╚═══════════════════════════════════════════════════════╝
    """)
    
    # Example queries
    example_queries = [
        "Should I invest in TSLA?",
        "Give me an analysis of AAPL",
        "What do you think about NVDA?",
        "analyze microsoft stock",
        "tell me about Amazon"
    ]
    
    print("\n📝 Example queries:")
    for i, query in enumerate(example_queries, 1):
        print(f"  {i}. {query}")
    
    print("\n" + "-"*70)
    
    # Get user input
    user_query = input("\n💬 Enter your query (or press Enter for TSLA example): ").strip()
    
    if not user_query:
        user_query = "Should I invest in TSLA?"
        print(f"Using example: '{user_query}'")
    
    # Run analysis
    try:
        result = run_stock_analysis(user_query)
        
        # Display results
        if result['errors'] and result['ticker'] == 'UNKNOWN':
            print("\n❌ Analysis failed:")
            for error in result['errors']:
                print(f"  - {error}")
        else:
            print(f"\n📊 Company: {result['company_name']} ({result['ticker']})")
            print(f"💡 Recommendation: {result['recommendation']}")
            
            if result['sentiment_score'] is not None:
                sentiment_emoji = "😊" if result['sentiment_score'] > 0.3 else "😐" if result['sentiment_score'] > -0.3 else "😟"
                print(f"📰 Sentiment Score: {result['sentiment_score']:.2f} {sentiment_emoji}")
            
            print("\n" + "="*70)
            print("📄 FULL REPORT:")
            print("="*70)
            print(result['report'])
            
            # Save report to file
            if result['ticker'] and result['ticker'] != 'UNKNOWN':
                filename = f"report_{result['ticker']}.md"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(result['report'])
                print(f"\n💾 Report saved to: {filename}")
            
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()