# Tool that fetches and processes stock data.
import yfinance as yf
from typing import Dict, Any
import pandas as pd # For free cashflow + shares outstanding calculations

def fetch_stock_data(ticker: str) -> Dict[str, Any]:
    # ... existing setup ...
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1y")

        # --- NEW: Calculate Historical Metrics (3 Years) ---
        fcf_metrics = {'avg_fcf_3y': 'N/A', 'fcf_trend': 'N/A'}
        share_metrics = {'share_dilution_3y': 'N/A', 'shares_outstanding_trend': 'N/A'}


        try:
            # 1. Free Cash Flow Analysis
            cf = stock.cash_flow
            if not cf.empty and 'Free Cash Flow' in cf.index:
                # Get last 3 years (columns are usually dates descending)
                last_3_years = cf.loc['Free Cash Flow'].head(3)
                if len(last_3_years) > 0:
                    fcf_metrics['avg_fcf_3y'] = last_3_years.mean()
                    # Check if improving or worsening (compare most recent to oldest in range)
                    if len(last_3_years) > 1:
                        recent = last_3_years.iloc[0]
                        older = last_3_years.iloc[-1]
                        fcf_metrics['fcf_trend'] = "Improving" if recent > older else "Worsening"

            # 2. Share Dilution Analysis (Shares Outstanding)
            bs = stock.balance_sheet
            # yfinance often uses 'Ordinary Shares Number' or 'Share Issued'
            share_key = 'Ordinary Shares Number' if 'Ordinary Shares Number' in bs.index else 'Share Issued'
            
            if not bs.empty and share_key in bs.index:
                shares = bs.loc[share_key].head(3)
                if len(shares) >= 2:
                    current_shares = shares.iloc[0]
                    old_shares = shares.iloc[-1]
                    
                    # Calculate total dilution percentage over the period
                    dilution = ((current_shares - old_shares) / old_shares) * 100
                    share_metrics['share_dilution_3y'] = dilution
                    share_metrics['shares_outstanding_trend'] = f"{dilution:.2f}% {'Increase (Dilution)' if dilution > 0 else 'Decrease (Buyback)'}"
                    
        except Exception as e:
            print(f"Warning: Could not calculate historical metrics: {e}")
        
        # Extract key metrics
        data = {
            'ticker': ticker,
            'company_name': info.get('longName', ticker),
            'currency': info.get('currency', 'USD'), 
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

            # --- Fundamental Trends ---
            'avg_fcf_3y': fcf_metrics['avg_fcf_3y'],
            'share_dilution_3y': share_metrics['shares_outstanding_trend'],
            
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