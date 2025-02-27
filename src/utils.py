import pandas as pd
import yfinance as yf
def save_results(results, output_file):
    df = pd.DataFrame(results)
    if df.empty:
        print("No results to save")
        return
    df = df.sort_values(by=['signal_date', 'breakthrough_date', 'score', 'interval'], ascending=[False, False, False, False])
    df.to_csv(output_file, sep='\t', index=False, columns=['ticker', 'interval', 'score', 'signal_date', 'breakthrough_date'])

def save_breakout_candidates_1234(df, file_path):
    df.to_csv(f'breakout_candidates_{file_path}', sep='\t', index=False, columns=['ticker', 'date', 'score', 'nx_1d'])

def save_breakout_candidates_5230(df, file_path):
    df.to_csv(f'breakout_candidates_{file_path}', sep='\t', index=False, columns=['ticker', 'date', 'score', 'nx_1h'])

def identify_1234(file_path):
    """
    Identify potential breakout stocks based on breakout signals across the 1h, 2h, 3h, and 4h intervals.
    
    The file is expected to contain at least the following columns:
      - ticker
      - interval
      - score
      - signal_date
      - breakthrough_date

    A ticker qualifies if, when filtering for rows with intervals in {"1h", "2h", "3h", "4h"}
    there is at least one 3-day window during which signals appear for all four intervals.
    
    Parameters:
        file_path (str): Path to the file containing breakout signals.

    Returns:
        list: A list of ticker symbols that are potential breakout stocks.
    """
    try:
        # Read the data. The file is assumed to be tab-delimited.
        df = pd.read_csv(file_path, sep="\t", engine="python")
    except Exception as e:
        print(f"Failed to read file {file_path}: {e}")
        return []

    # Ensure signal_date is parsed as datetime
    if "signal_date" in df.columns:
        df["signal_date"] = pd.to_datetime(df["signal_date"], errors="coerce")

    # Define the required intervals
    required_intervals = {"1h", "2h", "3h", "4h"}
    # Filter for rows whose interval is in our required set
    df = df[df["interval"].isin(required_intervals)]

    breakout_candidates = []

    # Group data by ticker
    # Convert signal_date to date only (removing time component)
    df['date'] = df['signal_date'].dt.date

    # print(df)
    
    unique_dates = df['date'].unique()[::-1]
    # Get unique dates to iterate through
    for i in range(len(unique_dates)):
        date = unique_dates[i]
        # print("date:", date)
        # Get data within 3-day window starting from current date
        window_end = unique_dates[min(i+2, (len(unique_dates) - 1))]
        # print("window_end:", window_end)
        window_data = df[(df['date'] >= pd.to_datetime(date)) & 
                        (df['date'] <= pd.to_datetime(window_end))]
        # print("window_data:", window_data)
        # Check each ticker in this window
        for ticker in window_data['ticker'].unique():
            ticker_data = window_data[window_data['ticker'] == ticker]
            unique_intervals = set(ticker_data['interval'])
            if len(unique_intervals.intersection(required_intervals)) >= 3:
                breakout_candidates.append([ticker, date, len(unique_intervals.intersection(required_intervals))])
    df_breakout_candidates = pd.DataFrame(breakout_candidates, columns=['ticker', 'date', 'score']).sort_values(by=['date', 'ticker'], ascending=[False, True])

    dict_nx_1d = {}
    tickers_failed = []

    print(df_breakout_candidates)
    for ticker in df_breakout_candidates['ticker'].unique():
        print(ticker)

        try:
            stock = yf.Ticker(ticker)
            df_stock = stock.history(interval='1d', period='6mo')
        except Exception as e:
            print(f"Failed to get data for {ticker}: {e}, wait 1 second and retry")
            # time.sleep(1)
            # df_stock = stock.history(interval='1d', period='6mo')
        if df_stock.empty:
            print(f"Failed to get data for {ticker} after 3 retries")
            tickers_failed.append(ticker)
            continue
        
        # low = df_stock['Low']
        # short_lower = low.ewm(span = 24, adjust=False).mean()
        # long_lower = low.ewm(span = 89, adjust=False).mean()
        # nx_1d = (short_lower > long_lower) 

        close = df_stock['Close']
        short_close = close.ewm(span = 24, adjust=False).mean()
        long_close = close.ewm(span = 89, adjust=False).mean()
        nx_1d = (short_close > long_close) 

        nx_1d.index = nx_1d.index.date
        dict_nx_1d[ticker] = nx_1d.to_dict()
    
    # print (dict_nx_1d)
    # remove tickers that failed to get data
    print ("tickers_failed:", tickers_failed)
    df_breakout_candidates =df_breakout_candidates[~df_breakout_candidates['ticker'].isin(tickers_failed)]
    # add nx_1d to df_breakout_candidates according to ticker and date
    df_breakout_candidates['nx_1d'] = df_breakout_candidates.apply(lambda row: dict_nx_1d[row['ticker']][row['date']], axis=1)
    # filter df_breakout_candidates to only include rows where nx_1d is True
    df_breakout_candidates_sel = df_breakout_candidates[df_breakout_candidates['nx_1d'] == True]
    
    return df_breakout_candidates_sel


def identify_5230(file_path):
    """
    Identify potential breakout stocks based on breakout signals across the 5m, 10m, 15m, and 30m intervals.
    
    The file is expected to contain at least the following columns:
      - ticker
      - interval
      - score
      - signal_date
      - breakthrough_date

    A ticker qualifies if, when filtering for rows with intervals in {"5m", "10m", "15m", "30m"}
    there is at least one 3-day window during which signals appear for all four intervals.
    
    Parameters:
        file_path (str): Path to the file containing breakout signals.

    Returns:
        list: A list of ticker symbols that are potential breakout stocks.
    """
    try:
        # Read the data. The file is assumed to be tab-delimited.
        df = pd.read_csv(file_path, sep="\t", engine="python")
    except Exception as e:
        print(f"Failed to read file {file_path}: {e}")
        return []

    # Ensure signal_date is parsed as datetime
    if "signal_date" in df.columns:
        df["signal_date"] = pd.to_datetime(df["signal_date"], errors="coerce")

    # Define the required intervals
    required_intervals = {"5m", "10m", "15m", "30m"}
    # Filter for rows whose interval is in our required set
    df = df[df["interval"].isin(required_intervals)]

    breakout_candidates = []

    # Group data by ticker
    # Convert signal_date to date only (removing time component)
    df['date'] = df['signal_date'].dt.date

    # print(df)
    
    unique_dates = df['date'].unique()[::-1]
    # Get unique dates to iterate through
    for i in range(len(unique_dates)):
        date = unique_dates[i]
        # print("date:", date)
        # Get data within 3-day window starting from current date
        window_end = unique_dates[min(i+2, (len(unique_dates) - 1))]
        window_data = df[(df['date'] >= pd.to_datetime(date)) & 
                        (df['date'] <= pd.to_datetime(window_end))]
        # print("window_data:", window_data)
        # Check each ticker in this window
        for ticker in window_data['ticker'].unique():
            ticker_data = window_data[window_data['ticker'] == ticker]
            unique_intervals = set(ticker_data['interval'])
            if len(unique_intervals.intersection(required_intervals)) >= 3:
                if ticker not in breakout_candidates:
                    breakout_candidates.append([ticker, date, len(unique_intervals.intersection(required_intervals))])
    df_breakout_candidates = pd.DataFrame(breakout_candidates, columns=['ticker', 'date', 'score']).sort_values(by=['date', 'ticker'], ascending=[False, True])

    dict_nx_1h = {}
    tickers_failed = []

    print(df_breakout_candidates)
    for ticker in df_breakout_candidates['ticker'].unique():
        print(ticker)

        try:
            stock = yf.Ticker(ticker)
            df_stock = stock.history(interval='1h', period='3mo')
        except Exception as e:
            print(f"Failed to get data for {ticker}: {e}, wait 1 second and retry")
            # time.sleep(1)
            # df_stock = stock.history(interval='1d', period='6mo')
        if df_stock.empty:
            print(f"Failed to get data for {ticker} after 3 retries")
            tickers_failed.append(ticker)
            continue
        
        # low = df_stock['Low']
        # short_lower = low.ewm(span = 24, adjust=False).mean()
        # long_lower = low.ewm(span = 89, adjust=False).mean()
        # nx_1d = (short_lower > long_lower) 

        close = df_stock['Close']
        short_close = close.ewm(span = 24, adjust=False).mean()
        long_close = close.ewm(span = 89, adjust=False).mean()
        nx_1h = (short_close > long_close) 

        nx_1h.index = nx_1h.index.date
        dict_nx_1h[ticker] = nx_1h.to_dict()
    
    print (dict_nx_1h)
    # remove tickers that failed to get data
    print ("tickers_failed:", tickers_failed)
    df_breakout_candidates =df_breakout_candidates[~df_breakout_candidates['ticker'].isin(tickers_failed)]
    # add nx_1d to df_breakout_candidates according to ticker and date
    df_breakout_candidates['nx_1h'] = df_breakout_candidates.apply(lambda row: dict_nx_1h[row['ticker']][row['date']], axis=1)
    # filter df_breakout_candidates to only include rows where nx_1h is True
    df_breakout_candidates_sel = df_breakout_candidates[df_breakout_candidates['nx_1h'] == True]
    
    return df_breakout_candidates_sel
