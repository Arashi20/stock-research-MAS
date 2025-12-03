import streamlit as st
import sys
import os
import datetime
import extra_streamlit_components as stx # For using cookies


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
    Uses Streamlit's session_state to remember authentication status.
    """

    # IMPORTANT: Adding a unique key prevents component remounting issues
    cookie_manager = stx.CookieManager(key="mas_auth_manager")

    # 1. Check if a valid cookie already exists (Returning user)
    if cookie_manager.get("mas_auth_token") == "valid":
        return True

    # 2. Check Session State (User just logged in this session)
    if st.session_state.get("password_correct", False):
        expires = datetime.datetime.now() + datetime.timedelta(minutes=10)
        cookie_manager.set("mas_auth_token", "valid", expires_at=expires)
        return True

    # 3. If neither, show the Login Form
    correct_password = os.environ.get("APP_PASSWORD")
    
    # Safety check: If no password is set in the environment, warn the admin
    if not correct_password:
        st.warning("⚠️ No APP_PASSWORD set in environment variables. Please configure it in Railway/Locally.")
        # You might want to return True here for development, but False is safer
        return False

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == correct_password:
            st.session_state["password_correct"] = True
            # Delete password from session state for security
            del st.session_state["password"]  
        else:
            st.session_state["password_correct"] = False

    # Display Input
    st.text_input(
        "Please enter the access password:", 
        type="password", 
        on_change=password_entered, 
        key="password"
    )

    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Password incorrect")
        
    return False

# --- Main App Execution ---
if check_password():
    # Everything below this line is protected
    
    # Header
    st.title("Stock Research Multi-Agent System")
    st.markdown("---")

    # Sidebar with info
    with st.sidebar:
        st.header("About")
        st.markdown("""
        This AI Agent team researches stocks using:
        - **Financial Data Analysis**
        - **News Sentiment Analysis**
        - **Technical Analysis**
        """)
        st.markdown("---")
        
        # Logout button simply resets the session state
        if st.button("Logout"):
            st.session_state["password_correct"] = False
            st.rerun()
            
        st.markdown("---")
        st.info("Built by Arash Mirshahi")

    # Check for 'ticker' in URL parameters
    # This allows other apps to link here with a pre-filled ticker.
    # Streamlit preserves these parameters even if the password check reruns the app.
    # Default query
    default_query = st.query_params.get("ticker", "")

    # Main Input
    query = st.text_input(
        "Enter a company name or ticker symbol to analyze:",
        value=default_query,
        placeholder="Should I invest in Nvidia?",
        help="Ask about any public company and the agents will research it for you.",
    )

    if st.button("Run Analysis", type="primary"):
        if not query:
            st.warning("Please enter a query first.")
        else:
            with st.spinner("Agents are researching... this may take a minute..."):
                try:
                    # Run the actual analysis
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