import pandas as pd
import numpy as np
from data_loader import download_data_1234, download_data_5230
from indicators import compute_cd_indicator
import yfinance as yf

def calculate_returns(data, cd_signals, periods=[3, 5, 10, 15, 20, 25, 30, 40, 50, 60, 80, 100]):
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
            result = {
                'ticker': ticker,
                'interval': interval,
                'signal_count': 0,
                'latest_signal': None,
                'latest_signal_price': None,
                'max_return': 0,
                'min_return': 0
            }
            # Add zero values for all periods
            periods = [3, 5, 10, 15, 20, 25, 30, 40, 50, 60, 80, 100]
            for period in periods:
                result[f'test_count_{period}'] = 0
                result[f'success_rate_{period}'] = 0
                result[f'avg_return_{period}'] = 0
            return result
            
        # Calculate returns for each signal
        returns_df = calculate_returns(data_frame, cd_signals)
        
        if returns_df.empty:
            result = {
                'ticker': ticker,
                'interval': interval,
                'signal_count': signal_count,
                'latest_signal': latest_signal_str,
                'latest_signal_price': latest_signal_price,
                'max_return': 0,
                'min_return': 0
            }
            # Add zero values for all periods
            periods = [3, 5, 10, 15, 20, 25, 30, 40, 50, 60, 80, 100]
            for period in periods:
                result[f'test_count_{period}'] = 0
                result[f'success_rate_{period}'] = 0
                result[f'avg_return_{period}'] = 0
            return result
        
        # Define all periods
        periods = [3, 5, 10, 15, 20, 25, 30, 40, 50, 60, 80, 100]
        
        # Initialize result dictionary with basic info
        result = {
            'ticker': ticker,
            'interval': interval,
            'signal_count': signal_count,
            'latest_signal': latest_signal_str,
            'latest_signal_price': latest_signal_price
        }
        
        # Calculate metrics for each period dynamically
        for period in periods:
            return_col = f'return_{period}'
            test_count = returns_df[return_col].count() if return_col in returns_df else 0
            success_rate = (returns_df[return_col] > 0).mean() * 100 if return_col in returns_df and test_count > 0 else 0
            avg_return = returns_df[return_col].mean() if return_col in returns_df and test_count > 0 else 0
            
            result[f'test_count_{period}'] = test_count
            result[f'success_rate_{period}'] = success_rate
            result[f'avg_return_{period}'] = avg_return
        
        # Calculate max and min returns across all periods
        all_returns = []
        for col in returns_df.columns:
            if col.startswith('return_'):
                all_returns.extend(returns_df[col].dropna().tolist())
                
        result['max_return'] = max(all_returns) if all_returns else 0
        result['min_return'] = min(all_returns) if all_returns else 0
        
        return result
        
    except Exception as e:
        print(f"Error evaluating {ticker} at {interval} interval: {e}")
        return None
