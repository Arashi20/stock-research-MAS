import streamlit as st
import sys
import os

# Add the current directory to sys.path to ensure imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import run_stock_analysis

# Page Config must be the first Streamlit command
st.set_page_config(
    page_title="Stock Research Agent",
    page_icon="📈",
    layout="wide"
)

# --- Authentication Logic ---
def check_password():
    """
    Returns `True` if the user had the correct password.
    """
    correct_password = os.environ.get("APP_PASSWORD")
    
    if not correct_password:
        st.warning("⚠️ No APP_PASSWORD set in environment variables.")
        return False

    def password_entered():
        if st.session_state["password"] == correct_password:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "Please enter the access password:", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(
            "Please enter the access password:", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        return True

# --- Main App Execution ---
if check_password():
    st.title("Stock Research Multi-Agent System")
    st.markdown("---")

    with st.sidebar:
        st.header("About")
        st.markdown("""
        This AI Agent team researches stocks using:
        - **Financial Data Analysis**
        - **News Sentiment Analysis**
        - **Technical Analysis**
        """)
        st.markdown("---")
        
        if st.button("Logout"):
            st.session_state["password_correct"] = False
            st.rerun()
            
        st.markdown("---")
        st.info("Built by Arash Mirshahi")

    default_query = st.query_params.get("ticker", "")

    query = st.text_input(
        "Enter a company name or ticker symbol to analyze:",
        value=default_query,
        placeholder="Should I invest in Nvidia?",
        help="Ask about any public company and the agents will research it for you. WARNING: ETFs are (not yet) supported!",
    )

    if st.button("Run Analysis", type="primary"):
        if not query:
            st.warning("Please enter a query first.")
        else:
            with st.spinner("Agents are researching... this may take a minute..."):
                try:
                    result = run_stock_analysis(query)
                    
                    # Handle case where ticker wasn't found
                    if result.get('errors') and result['ticker'] == 'UNKNOWN':
                        st.error("Analysis failed. Please try a specific company name or ticker.")
                        with st.expander("See error details"):
                            st.write(result['errors'])
                    
                    # Handle case where ticker was found but analysis failed (e.g., Delisted)
                    elif not result.get('report'):
                         st.error(f"Could not generate report for {result.get('ticker')}.")
                         st.warning("This usually happens if the stock is delisted or data is unavailable.")
                         if result.get('errors'):
                             with st.expander("See error details"):
                                 # This will show the "ERROR:yfinance..." message you wanted
                                 st.write(result['errors'])

                    else:
                        # Success Display
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Company", f"{result['company_name']} ({result['ticker']})")
                        
                        with col2:
                            st.metric("Recommendation", result.get('recommendation', 'N/A'))
                            
                        with col3:
                            # --- FIXED CRASH HERE ---
                            # Check if sentiment is a number before formatting
                            sentiment = result.get('sentiment_score')
                            
                            if isinstance(sentiment, (int, float)):
                                emoji = "😊" if sentiment > 0.3 else "😐" if sentiment > -0.3 else "😟"
                                st.metric("Sentiment Score", f"{sentiment:.2f} {emoji}")
                            else:
                                st.metric("Sentiment Score", "N/A")

                        st.markdown(result['report'])
                        
                        st.download_button(
                            label="💾 Download Report",
                            data=result['report'],
                            file_name=f"{result['ticker']}_analysis.md",
                            mime="text/markdown"
                        )
                        
                except Exception as e:
                    st.error(f"An unexpected error occurred: {str(e)}")