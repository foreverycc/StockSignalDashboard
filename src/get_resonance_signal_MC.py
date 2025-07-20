import pandas as pd
from indicators import compute_mc_indicator, compute_nx_break_through
    
def calculate_mc_score(data, interval, signal_date):
    """Calculate score for MC signals - adapted for sell signals"""
    interval_weights = {
        '5m': 2, 
        '10m': 3,
        '15m': 4,
        '30m': 5, 
        '1h': 6, 
        '2h': 7,
        '3h': 8,
        '4h': 9,
        '1d': 10
    }
    iw = interval_weights.get(interval, 0)
    
    # 获取信号当天的数据
    row = data.loc[signal_date]
    candle_size = round(abs(row['Close'] - row['Open']) / row['Close'] * 100, 3)
    
    # 计算过去20天的平均成交量
    avg_volume = data['Volume'].rolling(20).mean().loc[:signal_date].iloc[-1]
    volume_ratio = row['Volume'] / avg_volume if avg_volume != 0 else 0
    
    # For MC signals, higher volume ratio and candle size indicate stronger sell signals
    score = iw * 0.5 + candle_size * 0.3 + volume_ratio * 0.2
    return round(score, 2)

def process_ticker_mc_1234(ticker, data_ticker=None):
    """
    Process ticker for 1234 MC breakout analysis (sell signals)
    
    Args:
        ticker: Stock symbol
        data_ticker: pre-downloaded data dictionary, key is interval, value is dataframe
    
    Returns:
        List of results
    """
    intervals = ['1h', '2h', '3h', '4h']
    
    results = []
    # Use provided data or download if not provided
    if data_ticker is None:
        print(f"data not provided for {ticker}")
        raise ValueError(f"data not provided for {ticker}") 

    for interval in intervals:
        print(f"MC ticker: {ticker} interval: {interval}")
        data = data_ticker.get(interval, pd.DataFrame())
        if data.empty:
            print(f"MC data is empty: {ticker} {interval}")
            continue
        
        try:
            mc = compute_mc_indicator(data)  # Use MC indicator instead of CD
            breakthrough = compute_nx_break_through(data)
            
            # Handle NaN values by replacing them with False for boolean operations
            mc_bool = mc.fillna(False).infer_objects(copy=False).astype(bool)
            sell_signals = (mc_bool & breakthrough) | (mc_bool & breakthrough.rolling(10).apply(lambda x: x.iloc[0] if x.any() else False))   
            signal_dates = data.index[sell_signals]
            breakthrough_dates = data.index[breakthrough]
            
            # Filter out NaN values for signal processing
            valid_mc_signals = mc.fillna(False).infer_objects(copy=False)
            for date in data.index[valid_mc_signals]:
                score = calculate_mc_score(data, interval, date)
                signal_price = data.loc[date, 'Close']  # Get the Close price at signal date
                # Find the next breakthrough date after the signal date
                future_breakthroughs = breakthrough_dates[breakthrough_dates >= date]
                next_breakthrough = future_breakthroughs[0] if len(future_breakthroughs) > 0 else None

                results.append({
                    'ticker': ticker,
                    'interval': interval,
                    'score': score,
                    'signal_date': date.strftime('%Y-%m-%d %H:%M:%S'),
                    'signal_price': round(signal_price, 2),
                    'breakthrough_date': next_breakthrough.strftime('%Y-%m-%d %H:%M:%S') if next_breakthrough is not None else None
                })
        except Exception as e:
            print(f"Error processing MC {ticker} {interval}: {e}")
    
    return results


def process_ticker_mc_5230(ticker, data_ticker=None):
    """
    Process ticker for 5230 MC breakout analysis (sell signals)
    
    Args:
        ticker: Stock symbol
        data_ticker: pre-downloaded data dictionary, key is interval, value is dataframe
    Returns:
        List of results
    """
    intervals = ['5m', '10m', '15m', '30m']
    
    results = []
    # Use provided data or download if not provided
    if data_ticker is None:
        print(f"data not provided for {ticker}")
        raise ValueError(f"data not provided for {ticker}") 

    for interval in intervals:
        print(f"MC ticker: {ticker} interval: {interval}")
        data = data_ticker.get(interval, pd.DataFrame())
        if data.empty:
            print(f"MC data is empty: {ticker} {interval}")
            continue
        
        try:
            mc = compute_mc_indicator(data)  # Use MC indicator instead of CD
            breakthrough = compute_nx_break_through(data)
            
            # Handle NaN values by replacing them with False for boolean operations
            mc_bool = mc.fillna(False).infer_objects(copy=False).astype(bool)
            sell_signals = (mc_bool & breakthrough) | (mc_bool & breakthrough.rolling(10).apply(lambda x: x.iloc[0] if x.any() else False))   
            signal_dates = data.index[sell_signals]
            breakthrough_dates = data.index[breakthrough]
            
            # Filter out NaN values for signal processing
            valid_mc_signals = mc.fillna(False).infer_objects(copy=False)
            for date in data.index[valid_mc_signals]:
                score = calculate_mc_score(data, interval, date)
                signal_price = data.loc[date, 'Close']  # Get the Close price at signal date
                # Find the next breakthrough date after the signal date
                future_breakthroughs = breakthrough_dates[breakthrough_dates >= date]
                next_breakthrough = future_breakthroughs[0] if len(future_breakthroughs) > 0 else None

                results.append({
                    'ticker': ticker,
                    'interval': interval,
                    'score': score,
                    'signal_date': date.strftime('%Y-%m-%d %H:%M:%S'),
                    'signal_price': round(signal_price, 2),
                    'breakthrough_date': next_breakthrough.strftime('%Y-%m-%d %H:%M:%S') if next_breakthrough is not None else None
                })
        except Exception as e:
            print(f"Error processing MC {ticker} {interval}: {e}")
    
    return results


def identify_mc_1234(file_path, all_ticker_data):
    """
    Identify potential MC breakout stocks based on sell signals across the 1h, 2h, 3h, and 4h intervals.
    
    The file is expected to contain at least the following columns:
      - ticker
      - interval
      - score
      - signal_date
      - breakthrough_date

    A ticker qualifies if, when filtering for rows with intervals in {"1h", "2h", "3h", "4h"}
    there is at least one 3-day window during which signals appear for all four intervals.
    
    Parameters:
        file_path (str): Path to the file containing MC breakout signals.
        all_ticker_data (dict): Dictionary with pre-downloaded ticker data.

    Returns:
        DataFrame: A DataFrame of ticker symbols that are potential MC breakout stocks.
    """
    try:
        # Read the data. The file is assumed to be tab-delimited.
        df = pd.read_csv(file_path, sep="\t", engine="python")
        print("MC 1234 DataFrame:")
        print(df)
    except Exception as e:
        print(f"Failed to read MC file {file_path}: {e}")
        return pd.DataFrame()  # Return empty DataFrame

    # Ensure signal_date is parsed as datetime
    if "signal_date" in df.columns:
        df["signal_date"] = pd.to_datetime(df["signal_date"], errors="coerce")

    # Define the required intervals
    required_intervals = {"1h", "2h", "3h", "4h"}
    # Filter for rows whose interval is in our required set
    df = df[df["interval"].isin(required_intervals)]

    breakout_candidates = []
    processed_combinations = set()  # Track (ticker, date) combinations to avoid duplicates

    # Group data by ticker
    # Convert signal_date to date only (removing time component)
    df['date'] = df['signal_date'].dt.date

    unique_dates = df['date'].unique()[::-1]
    # Get unique dates to iterate through
    for i in range(len(unique_dates)):
        date = unique_dates[i]
        # Get data within 3-day window starting from current date
        window_end = unique_dates[min(i+2, (len(unique_dates) - 1))]
        window_data = df[(df['date'] >= date) & 
                        (df['date'] <= window_end)]
        
        # Check each ticker in this window
        for ticker in window_data['ticker'].unique():
            ticker_data = window_data[window_data['ticker'] == ticker]
            unique_intervals = set(ticker_data['interval'])

            if len(unique_intervals.intersection(required_intervals)) >= 3:
                # Get the most recent signal date within this window for this ticker
                most_recent_signal_date = ticker_data['signal_date'].max().date()
                # Check if we've already processed this combination
                combination = (ticker, most_recent_signal_date)
                if combination not in processed_combinations:
                    processed_combinations.add(combination)
                    # Get the latest signal price for this ticker/date combination (most recent signal)
                    latest_signal_price = ticker_data.loc[ticker_data['signal_date'].idxmax(), 'signal_price'] if 'signal_price' in ticker_data.columns and not ticker_data.empty else None
                    resonating_intervals_set = unique_intervals.intersection(required_intervals)
                    intervals_str = ",".join(map(str, sorted([int(s.replace('h', '')) for s in resonating_intervals_set])))
                    breakout_candidates.append([ticker, most_recent_signal_date, intervals_str, latest_signal_price])
    
    # Include signal_price column if available
    columns = ['ticker', 'date', 'intervals']
    if any(len(candidate) > 3 for candidate in breakout_candidates):
        columns.append('signal_price')
        
    df_breakout_candidates = pd.DataFrame(breakout_candidates, columns=columns).sort_values(by=['date', 'ticker'], ascending=[False, True])

    # Add current price data
    current_data = df_breakout_candidates['ticker'].apply(lambda ticker: 
        (
            round(all_ticker_data[ticker]['1d'].iloc[-1]['Close'], 2),
            all_ticker_data[ticker]['1d'].iloc[-1].name.strftime('%Y-%m-%d %H:%M:%S')
        ) if ticker in all_ticker_data and '1d' in all_ticker_data[ticker] and not all_ticker_data[ticker]['1d'].empty else (None, None)
    )
    df_breakout_candidates[['current_price', 'current_time']] = pd.DataFrame(current_data.tolist(), index=df_breakout_candidates.index)

    # Add NX indicator data
    dict_nx_1d = {}
    print("Computing NX 1d for MC breakout candidates...")
    for ticker in df_breakout_candidates['ticker'].unique():
        print(f"MC NX calculation for {ticker}")
        if ticker not in all_ticker_data or '1d' not in all_ticker_data[ticker] or all_ticker_data[ticker]['1d'].empty:
            print(f"No 1d data found for {ticker} in pre-downloaded data, skipping MC nx_1d calculation.")
            continue
        
        df_stock = all_ticker_data[ticker]['1d']
        close = df_stock['Close']
        short_close = close.ewm(span = 24, adjust=False).mean()
        long_close = close.ewm(span = 89, adjust=False).mean()
        nx_1d = (short_close > long_close) 

        nx_1d.index = nx_1d.index.date
        dict_nx_1d[ticker] = nx_1d.to_dict()
    
    print("MC dict_nx_1d:", dict_nx_1d)
    # remove tickers that failed to get data
    df_breakout_candidates = df_breakout_candidates[df_breakout_candidates['ticker'].isin(dict_nx_1d.keys())]
    
    # Check if DataFrame is empty after filtering
    if df_breakout_candidates.empty:
        print("No MC breakout candidates found after filtering")
        return df_breakout_candidates  # Return empty DataFrame
    
    # add nx_1d to df_breakout_candidates according to ticker and date
    df_breakout_candidates['nx_1d'] = df_breakout_candidates.apply(lambda row: dict_nx_1d[row['ticker']][row['date']], axis=1)
    df_breakout_candidates_sel = df_breakout_candidates
    
    return df_breakout_candidates_sel


def identify_mc_5230(file_path, all_ticker_data):
    """
    Identify potential MC breakout stocks based on sell signals across the 5m, 10m, 15m, and 30m intervals.
    
    The file is expected to contain at least the following columns:
      - ticker
      - interval
      - score
      - signal_date
      - breakthrough_date

    A ticker qualifies if, when filtering for rows with intervals in {"5m", "10m", "15m", "30m"}
    there is at least one 3-day window during which signals appear for at least 3 intervals.
    
    Parameters:
        file_path (str): Path to the file containing MC breakout signals.
        all_ticker_data (dict): Dictionary with pre-downloaded ticker data.

    Returns:
        DataFrame: A DataFrame of ticker symbols that are potential MC breakout stocks.
    """
    try:
        # Read the data. The file is assumed to be tab-delimited.
        df = pd.read_csv(file_path, sep="\t", engine="python")
        print("MC 5230 DataFrame:")
        print(df)
    except Exception as e:
        print(f"Failed to read MC file {file_path}: {e}")
        return pd.DataFrame()  # Return empty DataFrame

    # Ensure signal_date is parsed as datetime
    if "signal_date" in df.columns:
        df["signal_date"] = pd.to_datetime(df["signal_date"], errors="coerce")

    # Define the required intervals
    required_intervals = {"5m", "10m", "15m", "30m"}
    # Filter for rows whose interval is in our required set
    df = df[df["interval"].isin(required_intervals)]

    breakout_candidates = []
    processed_combinations = set()  # Track (ticker, date) combinations to avoid duplicates

    # Group data by ticker
    # Convert signal_date to date only (removing time component)
    df['date'] = df['signal_date'].dt.date

    unique_dates = df['date'].unique()[::-1]
    # Get unique dates to iterate through
    for i in range(len(unique_dates)):
        date = unique_dates[i]
        # Get data within 3-day window starting from current date
        window_end = unique_dates[min(i+2, (len(unique_dates) - 1))]
        window_data = df[(df['date'] >= date) & 
                        (df['date'] <= window_end)]
        
        # Check each ticker in this window
        for ticker in window_data['ticker'].unique():
            ticker_data = window_data[window_data['ticker'] == ticker]
            unique_intervals = set(ticker_data['interval'])

            if len(unique_intervals.intersection(required_intervals)) >= 3:
                # Get the most recent signal date within this window for this ticker
                most_recent_signal_date = ticker_data['signal_date'].max().date()
                # Check if we've already processed this combination
                combination = (ticker, most_recent_signal_date)
                if combination not in processed_combinations:
                    processed_combinations.add(combination)
                    # Get the latest signal price for this ticker/date combination (most recent signal)
                    latest_signal_price = ticker_data.loc[ticker_data['signal_date'].idxmax(), 'signal_price'] if 'signal_price' in ticker_data.columns and not ticker_data.empty else None
                    resonating_intervals_set = unique_intervals.intersection(required_intervals)
                    intervals_str = ",".join(map(str, sorted([int(s.replace('m', '')) for s in resonating_intervals_set])))
                    breakout_candidates.append([ticker, most_recent_signal_date, intervals_str, latest_signal_price])
    
    # Include signal_price column if available
    columns = ['ticker', 'date', 'intervals']
    if any(len(candidate) > 3 for candidate in breakout_candidates):
        columns.append('signal_price')
        
    df_breakout_candidates = pd.DataFrame(breakout_candidates, columns=columns).sort_values(by=['date', 'ticker'], ascending=[False, True])

    # Add current price data
    current_data = df_breakout_candidates['ticker'].apply(lambda ticker: 
        (
            round(all_ticker_data[ticker]['1d'].iloc[-1]['Close'], 2),
            all_ticker_data[ticker]['1d'].iloc[-1].name.strftime('%Y-%m-%d %H:%M:%S')
        ) if ticker in all_ticker_data and '1d' in all_ticker_data[ticker] and not all_ticker_data[ticker]['1d'].empty else (None, None)
    )
    df_breakout_candidates[['current_price', 'current_time']] = pd.DataFrame(current_data.tolist(), index=df_breakout_candidates.index)

    # Add NX indicator data for 1h timeframe
    dict_nx_1h = {}
    print("Computing NX 1h for MC breakout candidates...")
    for ticker in df_breakout_candidates['ticker'].unique():
        print(f"MC NX calculation for {ticker}")
        if ticker not in all_ticker_data or '1h' not in all_ticker_data[ticker] or all_ticker_data[ticker]['1h'].empty:
            print(f"No 1h data found for {ticker} in pre-downloaded data, skipping MC nx_1h calculation.")
            continue
        
        df_stock = all_ticker_data[ticker]['1h']
        close = df_stock['Close']
        short_close = close.ewm(span = 24, adjust=False).mean()
        long_close = close.ewm(span = 89, adjust=False).mean()
        nx_1h = (short_close > long_close) 

        nx_1h.index = nx_1h.index.date
        dict_nx_1h[ticker] = nx_1h.to_dict()
    
    print("MC dict_nx_1h:", dict_nx_1h)
    # remove tickers that failed to get data
    df_breakout_candidates = df_breakout_candidates[df_breakout_candidates['ticker'].isin(dict_nx_1h.keys())]
    
    # Check if DataFrame is empty after filtering
    if df_breakout_candidates.empty:
        print("No MC 5230 breakout candidates found after filtering")
        return df_breakout_candidates  # Return empty DataFrame
    
    # add nx_1h to df_breakout_candidates according to ticker and date
    df_breakout_candidates['nx_1h'] = df_breakout_candidates.apply(lambda row: dict_nx_1h[row['ticker']][row['date']], axis=1)
    df_breakout_candidates_sel = df_breakout_candidates
    
    return df_breakout_candidates_sel 