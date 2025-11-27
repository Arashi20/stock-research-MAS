import streamlit as st
import sys
import os

# Add the current directory to sys.path to ensure imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import run_stock_analysis

# Page Config
st.set_page_config(
    page_title="Stock Research Agent",
    page_icon="📈",
    layout="wide"
)

# Header
st.title("🤖 Stock Research Multi-Agent System")
st.markdown("---")

# Sidebar with info
with st.sidebar:
    st.header("About")
    st.markdown("""
    This AI Agent team researches stocks using:
    - **Financial Data Analysis**
    - **News Sentiment Analysis**
    - **Analyst Ratings**
    - **Web Search**
    """)
    st.markdown("---")
    st.info("Built with LangGraph & Streamlit")

# Main Input
query = st.text_input(
    "Enter your research query:",
    placeholder="Should I invest in Nvidia?",
    help="Ask about any public company"
)

if st.button("Run Analysis", type="primary"):
    if not query:
        st.warning("Please enter a query first.")
    else:
        with st.spinner("🤖 Agents are researching... this may take a minute..."):
            try:
                # Redirect stdout to capture print statements if needed, 
                # or just rely on the return value
                result = run_stock_analysis(query)
                
                if result.get('errors') and result['ticker'] == 'UNKNOWN':
                    st.error("Analysis failed. Please try a specific company name or ticker.")
                    with st.expander("See error details"):
                        st.write(result['errors'])
                else:
                    # Success Display
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Company", f"{result['company_name']} ({result['ticker']})")
                    
                    with col2:
                        st.metric("Recommendation", result['recommendation'])
                        
                    with col3:
                        sentiment = result.get('sentiment_score', 0)
                        emoji = "😊" if sentiment > 0.3 else "😐" if sentiment > -0.3 else "😟"
                        st.metric("Sentiment Score", f"{sentiment:.2f} {emoji}")

                    st.markdown("### 📄 Comprehensive Report")
                    st.markdown(result['report'])
                    
                    # Download button
                    st.download_button(
                        label="💾 Download Report",
                        data=result['report'],
                        file_name=f"{result['ticker']}_analysis.md",
                        mime="text/markdown"
                    )
                    
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")