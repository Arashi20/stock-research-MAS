# This tool will help our technical analysis agent to perform technical analysis on stock data.
# It will fetch historical stock data and compute technical indicators.
# Think of: moving averages, RSI, MACD, etc. 

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Any

def fetch_technical_indicators(ticker: str, period: str = "1y") -> Dict[str, Any]:
    """
    Fetch historical data and calculate technical indicators.
    
    Args:
        ticker: Stock ticker symbol
        period: Historical data period (default: "1y")
        
    Returns:
        Dictionary containing calculated indicators
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        
        if hist.empty:
            return {'success': False, 'error': 'No historical data found'}
        
        # Ensure we have enough data
        if len(hist) < 200:
            return {'success': False, 'error': 'Not enough data points for 200-day SMA'}
            
        data = {}
        
        # 1. Moving Averages (Trends)
        hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
        hist['SMA_200'] = hist['Close'].rolling(window=200).mean()
        
        current_price = hist['Close'].iloc[-1]
        sma_50 = hist['SMA_50'].iloc[-1]
        sma_200 = hist['SMA_200'].iloc[-1]
        
        data['current_price'] = current_price
        data['sma_50'] = sma_50
        data['sma_200'] = sma_200
        
        # Determine Trend
        if current_price > sma_50 > sma_200:
            data['trend'] = "Uptrend (Bullish)"
        elif current_price < sma_50 < sma_200:
            data['trend'] = "Downtrend (Bearish)"
        else:
            data['trend'] = "Sideways / Consolidation"
            
        # 2. RSI (Momentum)
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs)).iloc[-1]
        
        # 3. MACD (Trend Following Momentum)
        exp1 = hist['Close'].ewm(span=12, adjust=False).mean()
        exp2 = hist['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        
        data['macd'] = macd.iloc[-1]
        data['macd_signal'] = signal.iloc[-1]
        
        # 4. Stochastic Oscillator (Timing)
        # %K = (Current Close - Lowest Low) / (Highest High - Lowest Low) * 100
        low_14 = hist['Low'].rolling(window=14).min()
        high_14 = hist['High'].rolling(window=14).max()
        
        k_percent = 100 * ((hist['Close'] - low_14) / (high_14 - low_14))
        data['stoch_k'] = k_percent.iloc[-1]
        
        data['success'] = True
        return data
        
    except Exception as e:
        return {'success': False, 'error': str(e)}