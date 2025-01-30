import yfinance as yf
import pandas as pd
from typing import List, Dict

class DataFetcher:
    INTERVALS = ['1m', '2m', '5m', '15m', '30m', '1h', '1d']
    
    def __init__(self):
        self.period_map = {
            '1m': 'max',
            '2m': '1mo',
            '5m': '1mo',
            '15m': '3mo',
            '30m': '3mo',
            '1h': '6mo',
            '1d': '1y',
        }

    def fetch_data(self, ticker: str, interval: str) -> pd.DataFrame:
        """
        Fetch stock data for a specific ticker and interval.
        
        Args:
            ticker: Stock ticker symbol
            interval: Time interval for the data
            
        Returns:
            DataFrame containing the stock data
        """
        stock = yf.Ticker(ticker)
        period = self.period_map[interval]
        
        try:
            df = stock.history(interval=interval, period=period)
            return df
        except Exception as e:
            print(f"Error fetching data for {ticker} at interval {interval}: {str(e)}")
            return pd.DataFrame()

    def fetch_all_intervals(self, ticker: str) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for all intervals for a given ticker.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary mapping intervals to their corresponding DataFrames
        """
        return {
            interval: self.fetch_data(ticker, interval)
            for interval in self.INTERVALS
        } 