import pandas as pd
import numpy as np
from data_loader import download_data_1234, download_data_5230
from indicators import compute_cd_indicator
import yfinance as yf

def calculate_returns(data, cd_signals, periods=[3, 5, 10, 20, 50]):
    """
    Calculate returns after CD signals for specified periods.
    
    Args:
        data: DataFrame with price data
        cd_signals: Series with CD signals (boolean)
        periods: List of periods to calculate returns for
    
    Returns:
        DataFrame with signal dates and returns for each period
    """
    results = []
    signal_dates = data.index[cd_signals]
    
    for date in signal_dates:
        idx = data.index.get_loc(date)
        
        # Skip signals that are too close to the end of the data
        if idx + max(periods) >= len(data):
            continue
            
        entry_price = data.loc[date, 'Close']
        returns = {}
        
        for period in periods:
            if idx + period < len(data):
                exit_price = data.iloc[idx + period]['Close']
                returns[f'return_{period}'] = (exit_price - entry_price) / entry_price * 100
            else:
                returns[f'return_{period}'] = np.nan
                
        results.append({
            'date': date,
            **returns
        })
    
    return pd.DataFrame(results)

def evaluate_interval(ticker, interval, data=None):
    """
    Evaluate CD signals for a specific ticker and interval.
    
    Args:
        ticker: Stock ticker symbol
        interval: Time interval to evaluate
        data: Optional pre-downloaded data dictionary
    
    Returns:
        Dictionary with evaluation metrics
    """
    print(f"Evaluating {ticker} at {interval} interval")
    
    try:
        # If data dictionary is provided, use it
        if data and interval in data and not data[interval].empty:
            data_frame = data[interval]
        else:
            # Handle weekly interval separately
            if interval == '1w':
                # Try to use daily data from the provided dictionary
                if data and '1d' in data and not data['1d'].empty:
                    daily_data = data['1d']
                else:
                    stock = yf.Ticker(ticker)
                    daily_data = stock.history(interval='1d', period='1y')
                    
                if daily_data.empty:
                    return None
                    
                # Resample daily data to weekly
                data_frame = daily_data.resample('W').agg({
                    'Open': 'first',
                    'High': 'max',
                    'Low': 'min',
                    'Close': 'last',
                    'Volume': 'sum'
                })
            # Get data based on interval type
            elif interval in ['5m', '10m', '15m', '30m']:
                data_ticker = download_data_5230(ticker)
                data_frame = data_ticker[interval]
            elif interval in ['1h', '2h', '3h', '4h']:
                data_ticker = download_data_1234(ticker)
                data_frame = data_ticker[interval]
            elif interval == '1d':
                stock = yf.Ticker(ticker)
                data_frame = stock.history(interval='1d', period='1y')
            else:
                return None
                
        if data_frame.empty:
            return None
            
        # Compute CD signals
        cd_signals = compute_cd_indicator(data_frame)
        signal_count = cd_signals.sum()
        
        # Get the latest signal date
        latest_signal_date = data_frame.index[cd_signals].max() if signal_count > 0 else None
        latest_signal_str = latest_signal_date.strftime('%Y-%m-%d %H:%M:%S') if latest_signal_date else None
        latest_signal_price = round(data_frame.loc[latest_signal_date, 'Close'], 2) if latest_signal_date is not None else None
        
        if signal_count == 0:
            return {
                'ticker': ticker,
                'interval': interval,
                'signal_count': 0,
                'latest_signal': None,
                'latest_signal_price': None,
                'test_count_3': 0,
                'test_count_5': 0,
                'test_count_10': 0,
                'test_count_20': 0,
                'test_count_50': 0,
                'success_rate_3': 0,
                'success_rate_5': 0,
                'success_rate_10': 0,
                'success_rate_20': 0,
                'success_rate_50': 0,
                'avg_return_3': 0,
                'avg_return_5': 0,
                'avg_return_10': 0,
                'avg_return_20': 0,
                'avg_return_50': 0,
                'max_return': 0,
                'min_return': 0
            }
            
        # Calculate returns for each signal
        returns_df = calculate_returns(data_frame, cd_signals)
        
        if returns_df.empty:
            return {
                'ticker': ticker,
                'interval': interval,
                'signal_count': signal_count,
                'latest_signal': latest_signal_str,
                'latest_signal_price': latest_signal_price,
                'test_count_3': 0,
                'test_count_5': 0,
                'test_count_10': 0,
                'test_count_20': 0,
                'test_count_50': 0,
                'success_rate_3': 0,
                'success_rate_5': 0,
                'success_rate_10': 0,
                'success_rate_20': 0,
                'success_rate_50': 0,
                'avg_return_3': 0,
                'avg_return_5': 0,
                'avg_return_10': 0,
                'avg_return_20': 0,
                'avg_return_50': 0,
                'max_return': 0,
                'min_return': 0
            }
        
        # Count the number of tests for each period
        test_count_3 = returns_df['return_3'].count() if 'return_3' in returns_df else 0
        test_count_5 = returns_df['return_5'].count() if 'return_5' in returns_df else 0
        test_count_10 = returns_df['return_10'].count() if 'return_10' in returns_df else 0
        test_count_20 = returns_df['return_20'].count() if 'return_20' in returns_df else 0
        test_count_50 = returns_df['return_50'].count() if 'return_50' in returns_df else 0
        
        # Calculate success rates (percentage of positive returns)
        success_rate_3 = (returns_df['return_3'] > 0).mean() * 100 if 'return_3' in returns_df and test_count_3 > 0 else 0
        success_rate_5 = (returns_df['return_5'] > 0).mean() * 100 if 'return_5' in returns_df and test_count_5 > 0 else 0
        success_rate_10 = (returns_df['return_10'] > 0).mean() * 100 if 'return_10' in returns_df and test_count_10 > 0 else 0
        success_rate_20 = (returns_df['return_20'] > 0).mean() * 100 if 'return_20' in returns_df and test_count_20 > 0 else 0
        success_rate_50 = (returns_df['return_50'] > 0).mean() * 100 if 'return_50' in returns_df and test_count_50 > 0 else 0
        
        # Calculate average returns
        avg_return_3 = returns_df['return_3'].mean() if 'return_3' in returns_df and test_count_3 > 0 else 0
        avg_return_5 = returns_df['return_5'].mean() if 'return_5' in returns_df and test_count_5 > 0 else 0
        avg_return_10 = returns_df['return_10'].mean() if 'return_10' in returns_df and test_count_10 > 0 else 0
        avg_return_20 = returns_df['return_20'].mean() if 'return_20' in returns_df and test_count_20 > 0 else 0
        avg_return_50 = returns_df['return_50'].mean() if 'return_50' in returns_df and test_count_50 > 0 else 0
        
        # Calculate max and min returns across all periods
        all_returns = []
        for col in returns_df.columns:
            if col.startswith('return_'):
                all_returns.extend(returns_df[col].dropna().tolist())
                
        max_return = max(all_returns) if all_returns else 0
        min_return = min(all_returns) if all_returns else 0
        
        return {
            'ticker': ticker,
            'interval': interval,
            'signal_count': signal_count,
            'latest_signal': latest_signal_str,
            'latest_signal_price': latest_signal_price,
            'test_count_3': test_count_3,
            'test_count_5': test_count_5,
            'test_count_10': test_count_10,
            'test_count_20': test_count_20,
            'test_count_50': test_count_50,
            'success_rate_3': success_rate_3,
            'success_rate_5': success_rate_5,
            'success_rate_10': success_rate_10,
            'success_rate_20': success_rate_20,
            'success_rate_50': success_rate_50,
            'avg_return_3': avg_return_3,
            'avg_return_5': avg_return_5,
            'avg_return_10': avg_return_10,
            'avg_return_20': avg_return_20,
            'avg_return_50': avg_return_50,
            'max_return': max_return,
            'min_return': min_return
        }
        
    except Exception as e:
        print(f"Error evaluating {ticker} at {interval} interval: {e}")
        return None
