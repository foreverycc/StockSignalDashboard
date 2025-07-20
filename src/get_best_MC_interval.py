import pandas as pd
import numpy as np
from data_loader import download_stock_data
from indicators import compute_mc_indicator
import yfinance as yf

# Maximum number of latest signals to process (to reduce noise from older signals)
MAX_SIGNALS_THRESHOLD = 7

def calculate_returns(data, mc_signals, periods=None, max_signals=MAX_SIGNALS_THRESHOLD):
    """
    Calculate returns after MC signals for specified periods.
    
    Args:
        data: DataFrame with price data
        mc_signals: Series with MC signals (boolean)
        periods: List of periods to calculate returns for (default: 0 to 100)
        max_signals: Maximum number of latest signals to process (default: MAX_SIGNALS_THRESHOLD)
    
    Returns:
        DataFrame with signal dates, returns, and volume data for each period
    """
    if periods is None:
        periods = [0] + list(range(1, 101))  # Full range from 0 to 100
    results = []
    # Handle NaN values by replacing them with False for boolean indexing
    mc_signals_bool = mc_signals.fillna(False).infer_objects(copy=False)
    signal_dates = data.index[mc_signals_bool]
    
    # Limit to the latest N signals to reduce noise from older signals
    if len(signal_dates) > max_signals:
        signal_dates = signal_dates[-max_signals:]
    
    for date in signal_dates:
        idx = data.index.get_loc(date)
        
        # Skip signals that are too close to the end of the data
        if idx + max(periods) >= len(data):
            continue
            
        entry_price = data.loc[date, 'Close']
        entry_volume = data.loc[date, 'Volume']
        returns = {}
        volumes = {}
        
        for period in periods:
            if idx + period < len(data):
                exit_price = data.iloc[idx + period]['Close']
                exit_volume = data.iloc[idx + period]['Volume']
                # For MC signals, we're looking at returns from selling (negative returns indicate profit)
                returns[f'return_{period}'] = round(float((exit_price - entry_price) / entry_price * 100), 2)  # Convert to Python float
                volumes[f'volume_{period}'] = round(int(exit_volume), 0)  # Convert to Python int
            else:
                returns[f'return_{period}'] = np.nan
                volumes[f'volume_{period}'] = np.nan
                
        results.append({
            'date': date,
            'entry_volume': entry_volume,
            **returns,
            **volumes
        })
    
    return pd.DataFrame(results)

def evaluate_interval(ticker, interval, data=None):
    """
    Evaluate MC signals for a specific ticker and interval.
    
    Args:
        ticker: Stock ticker symbol
        interval: Time interval to evaluate
        data: Optional pre-downloaded data dictionary
    
    Returns:
        Dictionary with evaluation metrics and individual returns
    """
    print(f"Evaluating {ticker} at {interval} interval for MC signals")
    
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
            elif interval in ['5m', '10m', '15m', '30m', '1h', '2h', '3h', '4h']:
                data_ticker = download_stock_data(ticker, end_date=None)
                data_frame = data_ticker[interval]
            elif interval == '1d':
                stock = yf.Ticker(ticker)
                data_frame = stock.history(interval='1d', period='1y')
            else:
                return None
                
        if data_frame.empty:
            return None
            
        # Compute MC signals
        mc_signals = compute_mc_indicator(data_frame)
        # Handle NaN values for signal count calculation
        signal_count = mc_signals.fillna(False).infer_objects(copy=False).sum()
        
        # Get the latest signal date
        # Handle NaN values by replacing them with False for boolean indexing
        mc_signals_bool = mc_signals.fillna(False).infer_objects(copy=False)
        latest_signal_date = data_frame.index[mc_signals_bool].max() if signal_count > 0 else None
        latest_signal_str = latest_signal_date.strftime('%Y-%m-%d %H:%M:%S') if latest_signal_date else None
        latest_signal_price = round(float(data_frame.loc[latest_signal_date, 'Close']), 2) if latest_signal_date is not None else None  # Convert to Python float
        
        # Get current time and price
        current_time = data_frame.index[-1]
        current_time_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
        current_price = round(float(data_frame.iloc[-1]['Close']), 2)  # Convert to Python float
        
        if signal_count == 0:
            result = {
                'ticker': ticker,
                'interval': interval,
                'signal_count': 0,
                'latest_signal': None,
                'latest_signal_price': None,
                'current_time': current_time_str,
                'current_price': current_price,
                'current_period': 0,
                'max_return': 0,
                'min_return': 0,
                'price_history': {},
                'volume_history': {}
            }
            # Add zero values for all periods
            periods = [0] + list(range(1, 101))  # Full range from 0 to 100
            for period in periods:
                result[f'test_count_{period}'] = 0
                result[f'success_rate_{period}'] = 0
                result[f'avg_return_{period}'] = 0
                result[f'avg_volume_{period}'] = 0
                result[f'returns_{period}'] = []  # Store empty list for individual returns
                result[f'volumes_{period}'] = []  # Store empty list for individual volumes
            return result
            
        # Calculate returns for each signal (limit to latest signals to reduce noise)
        returns_df = calculate_returns(data_frame, mc_signals, max_signals=MAX_SIGNALS_THRESHOLD)
        
        if returns_df.empty:
            result = {
                'ticker': ticker,
                'interval': interval,
                'signal_count': signal_count,
                'latest_signal': latest_signal_str,
                'latest_signal_price': latest_signal_price,
                'current_time': current_time_str,
                'current_price': current_price,
                'current_period': 0,
                'max_return': 0,
                'min_return': 0,
                'price_history': {},
                'volume_history': {}
            }
            # Add zero values for all periods
            periods = [0] + list(range(1, 101))  # Full range from 0 to 100
            for period in periods:
                result[f'test_count_{period}'] = 0
                result[f'success_rate_{period}'] = 0
                result[f'avg_return_{period}'] = 0
                result[f'avg_volume_{period}'] = 0
                result[f'returns_{period}'] = []  # Store empty list for individual returns
                result[f'volumes_{period}'] = []  # Store empty list for individual volumes
            return result
        
        # Define all periods
        periods = [0] + list(range(1, 101))  # Full range from 0 to 100
        
        # Initialize result dictionary with basic info
        result = {
            'ticker': ticker,
            'interval': interval,
            'signal_count': signal_count,
            'latest_signal': latest_signal_str,
            'latest_signal_price': latest_signal_price,
            'current_time': current_time_str,
            'current_price': current_price
        }
        
        # Calculate current period if there's a latest signal
        if latest_signal_date:
            # Find the index of the latest signal and current time
            signal_idx = data_frame.index.get_loc(latest_signal_date)
            current_idx = len(data_frame) - 1
            # Calculate current period as the number of data points between signal and current time
            current_period = current_idx - signal_idx
            
            # Calculate actual price history and volume history for the latest signal
            price_history = {}
            volume_history = {}
            entry_price = data_frame.loc[latest_signal_date, 'Close']
            entry_volume = data_frame.loc[latest_signal_date, 'Volume']
            price_history[0] = round(float(entry_price), 2)  # Entry price at period 0, convert to Python float
            volume_history[0] = round(int(entry_volume), 0)  # Entry volume at period 0, convert to Python int
            
            for period in periods:
                if signal_idx + period < len(data_frame):
                    actual_price = data_frame.iloc[signal_idx + period]['Close']
                    actual_volume = data_frame.iloc[signal_idx + period]['Volume']
                    price_history[period] = round(float(actual_price), 2)  # Convert to Python float
                    volume_history[period] = round(int(actual_volume), 0)  # Convert to Python int
                else:
                    price_history[period] = None
                    volume_history[period] = None
                    
            # Add current price and volume if we're beyond the latest period
            if current_period > max(periods):
                price_history[current_period] = round(float(current_price), 2)  # Convert to Python float
                volume_history[current_period] = round(int(data_frame.iloc[-1]['Volume']), 0)  # Convert to Python int
        else:
            current_period = 0
            price_history = {}
            volume_history = {}
            
        result['current_period'] = current_period
        result['price_history'] = price_history
        result['volume_history'] = volume_history
        
        # Calculate aggregated statistics for each period
        all_returns = []
        for period in periods:
            period_returns = returns_df[f'return_{period}'].dropna()
            period_volumes = returns_df[f'volume_{period}'].dropna() if f'volume_{period}' in returns_df else pd.Series([], dtype='float64')
            
            if len(period_returns) > 0:
                # For MC signals, negative returns indicate profit (price decline after sell signal)
                # So we calculate success rate as percentage of negative returns
                success_rate = round(float((period_returns < 0).mean() * 100), 2)  # Convert to Python float
                avg_return = round(float(period_returns.mean()), 2)  # Convert to Python float
                avg_volume = round(int(period_volumes.mean()), 0) if len(period_volumes) > 0 else 0  # Convert to Python int
                
                # Store aggregated metrics
                result[f'test_count_{period}'] = len(period_returns)
                result[f'success_rate_{period}'] = success_rate
                result[f'avg_return_{period}'] = avg_return
                result[f'avg_volume_{period}'] = avg_volume
                result[f'returns_{period}'] = [round(float(x), 2) for x in period_returns.tolist()]  # Convert to Python float
                result[f'volumes_{period}'] = [round(int(x), 0) for x in period_volumes.tolist()]  # Convert to Python int
                
                all_returns.extend(period_returns.tolist())
            else:
                result[f'test_count_{period}'] = 0
                result[f'success_rate_{period}'] = 0
                result[f'avg_return_{period}'] = 0
                result[f'avg_volume_{period}'] = 0
                result[f'returns_{period}'] = []
                result[f'volumes_{period}'] = []
        
        # Calculate overall min/max returns
        if all_returns:
            result['max_return'] = round(float(max(all_returns)), 2)  # Convert to Python float
            result['min_return'] = round(float(min(all_returns)), 2)  # Convert to Python float
        else:
            result['max_return'] = 0
            result['min_return'] = 0
            
        return result
        
    except Exception as e:
        print(f"Error evaluating {ticker} at {interval}: {e}")
        return None

def analyze_mc_signals(file_path):
    """
    Analyze MC signals for all tickers in the file.
    
    Args:
        file_path: Path to the file containing stock ticker symbols
    
    Returns:
        List of evaluation results
    """
    from stock_analyzer import load_stock_list
    
    stock_list = load_stock_list(file_path)
    print(f"Analyzing MC signals for {len(stock_list)} stocks from {file_path}")
    
    results = []
    intervals = ['5m', '10m', '15m', '30m', '1h', '2h', '3h', '4h', '1d', '1w']
    
    for ticker in stock_list:
        try:
            print(f"Processing {ticker}")
            # Download data once for all intervals
            data = download_stock_data(ticker, end_date=None)
            
            # Skip if no data available
            if all(df.empty for df in data.values()):
                print(f"No data available for {ticker}")
                continue
                
            # Process each interval
            for interval in intervals:
                result = evaluate_interval(ticker, interval, data=data)
                if result:
                    results.append(result)
                    
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            
    return results 