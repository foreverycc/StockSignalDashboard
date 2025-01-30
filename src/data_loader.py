import pandas as pd
import yfinance as yf

def load_stock_list(file_path):
    return pd.read_csv(file_path, sep='\t', header=None, names=['ticker'])['ticker'].tolist()

def download_data(ticker, interval, period):
    interval_map = {
        # '1m': '1m',
        # '2m': '2m',
        '5m': '5m',
        '15m': '15m',
        '30m': '30m',
        '1h': '60m',
        '1d': '1d'
    }
    yf_interval = interval_map.get(interval, interval)
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(interval=interval, period=period)
        return data
    except Exception as e:
        print(f"Error downloading {ticker} {interval}: {e}")
        return pd.DataFrame()