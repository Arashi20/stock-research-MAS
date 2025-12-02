# This tool will help our technical analysis agent to perform technical analysis on stock data.
# It will fetch historical stock data and compute technical indicators.
# Think of: moving averages, RSI, MACD, etc. 
# Uses my swing trading optimized settings for weekly timeframe analysis.

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Any

def fetch_technical_indicators(ticker: str, period: str = "2y") -> Dict[str, Any]:
    """
    Fetch historical data and calculate technical indicators.
    Optimized for Swing Trading (Weekly Timeframe).
    
    Args:
        ticker: Stock ticker symbol
        period: Historical data period (default: "2y" for weekly analysis)
        
    Returns:
        Dictionary containing calculated indicators
    """
    try:
        stock = yf.Ticker(ticker)
        # Fetch daily data first, then resample to weekly
        daily_hist = stock.history(period=period)
        
        if daily_hist.empty:
            return {'success': False, 'error': 'No historical data found'}
        
        # --- RESAMPLE TO WEEKLY CANDLES (Swing Trading View) ---
        # 'W-FRI' ensures we use Friday close as the weekly close
        hist = daily_hist.resample('W-FRI').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()

        # Ensure we have enough data
        if len(hist) < 50:
            return {'success': False, 'error': 'Not enough weekly data points'}
            
        data = {}
        current_price = daily_hist['Close'].iloc[-1] # Use latest daily price for reference
        data['current_price'] = current_price
        
        # 1. Moving Averages (Weekly Trend)
        hist['SMA_20'] = hist['Close'].rolling(window=20).mean() # Approx 5 months
        hist['SMA_50'] = hist['Close'].rolling(window=50).mean() # Approx 1 year
        
        sma_20 = hist['SMA_20'].iloc[-1]
        sma_50 = hist['SMA_50'].iloc[-1]
        data['sma_20_weekly'] = sma_20
        data['sma_50_weekly'] = sma_50
        
        # Trend Detection
        if current_price > sma_20 > sma_50:
            data['trend'] = "Strong Uptrend (Weekly)"
        elif current_price < sma_20 < sma_50:
            data['trend'] = "Strong Downtrend (Weekly)"
        else:
            data['trend'] = "Consolidating / Mixed"

        # 2. RSI (14-Week)
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs)).iloc[-1]
        
        # 3. MACD (Weekly)
        exp1 = hist['Close'].ewm(span=12, adjust=False).mean()
        exp2 = hist['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        data['macd'] = macd.iloc[-1]
        data['macd_signal'] = signal.iloc[-1]
        
        # 4. STOCHASTIC OSCILLATOR (Custom Swing Settings: 14, 1, 3)
        # %K Length = 14
        # %K Smoothing = 1 (Fast Stochastic)
        # %D Smoothing = 3 (Slow Stochastic Signal)
        
        # Calculate Fast %K
        low_14 = hist['Low'].rolling(window=14).min()
        high_14 = hist['High'].rolling(window=14).max()
        hist['%K'] = 100 * ((hist['Close'] - low_14) / (high_14 - low_14))
        
        # Apply %D Smoothing (SMA 3 of %K)
        hist['%D'] = hist['%K'].rolling(window=3).mean()
        
        k_val = hist['%K'].iloc[-1]
        d_val = hist['%D'].iloc[-1]
        
        data['stoch_k'] = k_val
        data['stoch_d'] = d_val
        
        # Signal Interpretation
        if k_val > d_val and k_val < 20:
            data['stoch_signal'] = "Bullish Crossover (Oversold) - BUY SIGNAL"
        elif k_val < d_val and k_val > 80:
            data['stoch_signal'] = "Bearish Crossover (Overbought) - SELL SIGNAL"
        elif k_val > d_val:
            data['stoch_signal'] = "Bullish Momentum"
        else:
            data['stoch_signal'] = "Bearish Momentum"
        
        data['success'] = True
        return data
        
    except Exception as e:
        return {'success': False, 'error': str(e)}