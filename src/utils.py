import pandas as pd
import os

def save_results(results, output_file):
    df = pd.DataFrame(results)
    if df.empty:
        print("No results to save")
        return
    df = df.sort_values(by=['signal_date', 'breakthrough_date', 'score', 'interval'], ascending=[False, False, False, False])
    
    # Include signal_price in the saved columns if it exists
    columns_to_save = ['ticker', 'interval', 'score', 'signal_date']
    if 'signal_price' in df.columns:
        columns_to_save.append('signal_price')
    columns_to_save.append('breakthrough_date')
    
    df.to_csv(output_file, sep='\t', index=False, columns=columns_to_save)

def save_breakout_candidates_1234(df, file_path):
    # Extract base name and directory from the input file path
    directory = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)
    output_path = os.path.join(directory, base_name).replace("details", "summary")
    
    # Handle case where df might be a list (convert to empty DataFrame)
    if isinstance(df, list):
        df = pd.DataFrame()
    
    # Handle empty DataFrame
    if df.empty:
        print("No 1234 breakout candidates to save")
        # Create empty file with headers
        empty_df = pd.DataFrame(columns=['ticker', 'date', 'intervals', 'signal_price', 'current_price', 'current_time', 'nx_1d', 'nx_30m', 'nx_1d_current', 'nx_30m_current', 'nx_1h_current'])
        empty_df.to_csv(output_path, sep='\t', index=False)
        return
    
    # Check which columns exist and save accordingly
    available_columns = ['ticker', 'date', 'intervals']
    if 'signal_price' in df.columns:
        available_columns.append('signal_price')
    if 'current_price' in df.columns:
        available_columns.append('current_price')
    if 'current_time' in df.columns:
        available_columns.append('current_time')
    if 'nx_1d' in df.columns:
        available_columns.append('nx_1d')
    if 'nx_30m' in df.columns:
        available_columns.append('nx_30m')
    if 'nx_1d_current' in df.columns:
        available_columns.append('nx_1d_current')
    if 'nx_30m_current' in df.columns:
        available_columns.append('nx_30m_current')
    if 'nx_1h_current' in df.columns:
        available_columns.append('nx_1h_current')
    
    df.to_csv(output_path, sep='\t', index=False, columns=available_columns)

def save_breakout_candidates_5230(df, file_path):
    # Extract base name and directory from the input file path
    directory = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)
    output_path = os.path.join(directory, base_name).replace("details", "summary")
    
    # Handle case where df might be a list (convert to empty DataFrame)
    if isinstance(df, list):
        df = pd.DataFrame()
    
    # Handle empty DataFrame
    if df.empty:
        print("No 5230 breakout candidates to save")
        # Create empty file with headers
        empty_df = pd.DataFrame(columns=['ticker', 'date', 'intervals', 'signal_price', 'current_price', 'current_time', 'nx_1h', 'nx_1d_current', 'nx_30m_current', 'nx_1h_current'])
        empty_df.to_csv(output_path, sep='\t', index=False)
        return
    
    # Check which columns exist and save accordingly
    available_columns = ['ticker', 'date', 'intervals']
    if 'signal_price' in df.columns:
        available_columns.append('signal_price')
    if 'current_price' in df.columns:
        available_columns.append('current_price')
    if 'current_time' in df.columns:
        available_columns.append('current_time')
    if 'nx_1h' in df.columns:
        available_columns.append('nx_1h')
    if 'nx_1d_current' in df.columns:
        available_columns.append('nx_1d_current')
    if 'nx_30m_current' in df.columns:
        available_columns.append('nx_30m_current')
    if 'nx_1h_current' in df.columns:
        available_columns.append('nx_1h_current')
    
    df.to_csv(output_path, sep='\t', index=False, columns=available_columns)

def save_mc_breakout_candidates_1234(df, file_path):
    """Save MC 1234 breakout candidates summary"""
    # Extract base name and directory from the input file path
    directory = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)
    output_path = os.path.join(directory, base_name).replace("details", "summary")
    
    # Handle case where df might be a list (convert to empty DataFrame)
    if isinstance(df, list):
        df = pd.DataFrame()
    
    # Handle empty DataFrame
    if df.empty:
        print("No MC 1234 breakout candidates to save")
        # Create empty file with headers
        empty_df = pd.DataFrame(columns=['ticker', 'date', 'intervals', 'signal_price', 'current_price', 'current_time', 'nx_1d', 'nx_1d_current', 'nx_30m_current', 'nx_1h_current'])
        empty_df.to_csv(output_path, sep='\t', index=False)
        return
    
    # Check which columns exist and save accordingly
    available_columns = ['ticker', 'date', 'intervals']
    if 'signal_price' in df.columns:
        available_columns.append('signal_price')
    if 'current_price' in df.columns:
        available_columns.append('current_price')
    if 'current_time' in df.columns:
        available_columns.append('current_time')
    if 'nx_1d' in df.columns:
        available_columns.append('nx_1d')
    if 'nx_1d_current' in df.columns:
        available_columns.append('nx_1d_current')
    if 'nx_30m_current' in df.columns:
        available_columns.append('nx_30m_current')
    if 'nx_1h_current' in df.columns:
        available_columns.append('nx_1h_current')
    
    df.to_csv(output_path, sep='\t', index=False, columns=available_columns)

def save_mc_breakout_candidates_5230(df, file_path):
    """Save MC 5230 breakout candidates summary"""
    # Extract base name and directory from the input file path
    directory = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)
    output_path = os.path.join(directory, base_name).replace("details", "summary")
    
    # Handle case where df might be a list (convert to empty DataFrame)
    if isinstance(df, list):
        df = pd.DataFrame()
    
    # Handle empty DataFrame
    if df.empty:
        print("No MC 5230 breakout candidates to save")
        # Create empty file with headers
        empty_df = pd.DataFrame(columns=['ticker', 'date', 'intervals', 'signal_price', 'current_price', 'current_time', 'nx_1h', 'nx_1d_current', 'nx_30m_current', 'nx_1h_current'])
        empty_df.to_csv(output_path, sep='\t', index=False)
        return
    
    # Check which columns exist and save accordingly
    available_columns = ['ticker', 'date', 'intervals']
    if 'signal_price' in df.columns:
        available_columns.append('signal_price')
    if 'current_price' in df.columns:
        available_columns.append('current_price')
    if 'current_time' in df.columns:
        available_columns.append('current_time')
    if 'nx_1h' in df.columns:
        available_columns.append('nx_1h')
    if 'nx_1d_current' in df.columns:
        available_columns.append('nx_1d_current')
    if 'nx_30m_current' in df.columns:
        available_columns.append('nx_30m_current')
    if 'nx_1h_current' in df.columns:
        available_columns.append('nx_1h_current')
    
    df.to_csv(output_path, sep='\t', index=False, columns=available_columns)

def calculate_current_nx_values(ticker, all_ticker_data, precomputed_series=None):
    """
    Calculate current NX values for nx_1d, nx_30m, and nx_1h at the current time.

    This function prefers previously computed NX booleans when provided, avoiding
    any new data fetches or redundant computations. If a precomputed series is
    not provided for a timeframe, it computes the value from the pre-downloaded
    data in all_ticker_data.

    Parameters:
        ticker (str): The stock ticker symbol
        all_ticker_data (dict): Dictionary with pre-downloaded ticker data
        precomputed_series (dict | None): Optional mapping per timeframe containing
            the historical NX boolean series for this ticker. Expected keys are
            '1d', '30m', '1h'. Each value can be a dict of {date -> bool} or a
            pandas Series/DataFrame convertible to the same.

    Returns:
        dict: Dictionary with keys 'nx_1d_current', 'nx_30m_current', 'nx_1h_current'
    """
    current_nx = {
        'nx_1d_current': None,
        'nx_30m_current': None,
        'nx_1h_current': None,
    }

    def latest_bool_from_series(series_like):
        if series_like is None:
            return None
        try:
            # Normalize to dict
            if hasattr(series_like, 'to_dict'):
                series_dict = series_like.to_dict()
            elif isinstance(series_like, dict):
                series_dict = series_like
            else:
                return None
            if not series_dict:
                return None
            last_key = max(series_dict.keys())
            val = series_dict.get(last_key, None)
            if val is None:
                return None
            # Some series may store numpy.bool_ or object; coerce to bool
            return bool(val)
        except Exception:
            return None

    pre = precomputed_series or {}

    # Prefer precomputed latest values when available; otherwise compute from data
    # 1d
    nx_1d_pre = latest_bool_from_series(pre.get('1d'))
    if nx_1d_pre is not None:
        current_nx['nx_1d_current'] = nx_1d_pre
    elif ticker in all_ticker_data and '1d' in all_ticker_data[ticker] and not all_ticker_data[ticker]['1d'].empty:
        df_stock = all_ticker_data[ticker]['1d']
        close = df_stock['Close']
        short_close = close.ewm(span=24, adjust=False).mean()
        long_close = close.ewm(span=89, adjust=False).mean()
        current_nx['nx_1d_current'] = short_close.iloc[-1] > long_close.iloc[-1]

    # 30m
    nx_30m_pre = latest_bool_from_series(pre.get('30m'))
    if nx_30m_pre is not None:
        current_nx['nx_30m_current'] = nx_30m_pre
    elif ticker in all_ticker_data and '30m' in all_ticker_data[ticker] and not all_ticker_data[ticker]['30m'].empty:
        df_stock_30m = all_ticker_data[ticker]['30m']
        close_30m = df_stock_30m['Close']
        short_close_30m = close_30m.ewm(span=24, adjust=False).mean()
        long_close_30m = close_30m.ewm(span=89, adjust=False).mean()
        current_nx['nx_30m_current'] = short_close_30m.iloc[-1] > long_close_30m.iloc[-1]

    # 1h
    nx_1h_pre = latest_bool_from_series(pre.get('1h'))
    if nx_1h_pre is not None:
        current_nx['nx_1h_current'] = nx_1h_pre
    elif ticker in all_ticker_data and '1h' in all_ticker_data[ticker] and not all_ticker_data[ticker]['1h'].empty:
        df_stock_1h = all_ticker_data[ticker]['1h']
        close_1h = df_stock_1h['Close']
        short_close_1h = close_1h.ewm(span=24, adjust=False).mean()
        long_close_1h = close_1h.ewm(span=89, adjust=False).mean()
        current_nx['nx_1h_current'] = short_close_1h.iloc[-1] > long_close_1h.iloc[-1]

    return current_nx
