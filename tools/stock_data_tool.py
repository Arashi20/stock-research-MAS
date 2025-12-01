# Tool that fetches and processes stock data.
import yfinance as yf
from typing import Dict, Any

def fetch_stock_data(ticker: str) -> Dict[str, Any]:
    # ... existing setup ...
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
            
            # --- VALUATION METRICS ---
            'pe_ratio': info.get('trailingPE', 'N/A'),
            'forward_pe': info.get('forwardPE', 'N/A'),
            'peg_ratio': info.get('pegRatio', 'N/A'),
            'price_to_book': info.get('priceToBook', 'N/A'),
            
            # --- PROFITABILITY & MANAGEMENT (ROIC proxies) ---
            'return_on_equity': info.get('returnOnEquity', 'N/A'),
            'return_on_assets': info.get('returnOnAssets', 'N/A'),
            'profit_margin': info.get('profitMargins', 'N/A'),
            'operating_margins': info.get('operatingMargins', 'N/A'),
            
            # --- FINANCIAL HEALTH ---
            'debt_to_equity': info.get('debtToEquity', 'N/A'),
            'current_ratio': info.get('currentRatio', 'N/A'), # Liquidity
            'free_cash_flow': info.get('freeCashflow', 'N/A'),
            
            # --- INCOME ---
            'dividend_yield': info.get('dividendYield', 'N/A'),
            
            'eps': info.get('trailingEps', 'N/A'),
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