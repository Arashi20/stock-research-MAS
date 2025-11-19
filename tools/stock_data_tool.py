# Tool that fetches and processes stock data.
import yfinance as yf
from typing import Dict, Any

def fetch_stock_data(ticker: str) -> Dict[str, Any]:
    """
    Fetch comprehensive stock data for a given ticker.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'TSLA')
    
    Returns:
        Dictionary containing stock metrics and historical data
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1y")
        
        # Extract key metrics
        data = {
            'ticker': ticker,
            'company_name': info.get('longName', ticker),
            'current_price': info.get('currentPrice', info.get('regularMarketPrice', 'N/A')),
            'market_cap': info.get('marketCap', 'N/A'),
            'pe_ratio': info.get('trailingPE', 'N/A'),
            'eps': info.get('trailingEps', 'N/A'),
            'revenue': info.get('totalRevenue', 'N/A'),
            'profit_margin': info.get('profitMargins', 'N/A'),
            'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 'N/A'),
            'fifty_two_week_low': info.get('fiftyTwoWeekLow', 'N/A'),
            'analyst_recommendation': info.get('recommendationKey', 'N/A'),
            'historical_data': hist.to_dict() if not hist.empty else {},
            'success': True
        }
        
        return data
        
    except Exception as e:
        return {
            'ticker': ticker,
            'success': False,
            'error': str(e)
        }

# Test function
if __name__ == "__main__":
    result = fetch_stock_data("AAPL")
    print(result)