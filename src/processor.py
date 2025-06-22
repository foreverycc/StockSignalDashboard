import pandas as pd
from data_loader import download_stock_data
from indicators import compute_cd_indicator, compute_nx_break_through
    
def calculate_score(data, interval, signal_date):
    interval_weights = {
        # '1m': 1, 
        # '2m': 2, 
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
    candle_size = abs(row['Close'] - row['Open']) / row['Close'] * 100
    
    # 计算过去20天的平均成交量
    avg_volume = data['Volume'].rolling(20).mean().loc[:signal_date].iloc[-1]
    volume_ratio = row['Volume'] / avg_volume if avg_volume != 0 else 0
    
    score = iw * 0.5 + candle_size * 0.3 + volume_ratio * 0.2
    return round(score, 2)

def process_ticker_1234(ticker, data_ticker=None):
    """
    Process ticker for 1234 breakout analysis
    
    Args:
        ticker: Stock symbol
        data_ticker: Optional pre-downloaded data dictionary
    
    Returns:
        List of results
    """
    intervals = ['1h', '2h', '3h', '4h']
    
    results = []
    # Use provided data or download if not provided
    if data_ticker is None:
        print (f"data not provided for {ticker}")
        # throw an error
        raise ValueError(f"data not provided for {ticker}") 

    for interval in intervals:
        print(f"ticker: {ticker} interval: {interval}")
        data = data_ticker.get(interval, pd.DataFrame())
        if data.empty:
            print(f"data is empty: {ticker} {interval}")
            continue
        
        try:
            cd = compute_cd_indicator(data)
            breakthrough = compute_nx_break_through(data)
            buy_signals = (cd.astype(bool) & breakthrough) | (cd.astype(bool) & breakthrough.rolling(10).apply(lambda x: x.iloc[0] if x.any() else False))   
            signal_dates = data.index[buy_signals]
            breakthrough_dates = data.index[breakthrough]
            
            for date in data.index[cd]:
                score = calculate_score(data, interval, date)
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
            print(f"Error processing {ticker} {interval}: {e}")
    
    return results


def process_ticker_5230(ticker, data_ticker=None):
    """
    Process ticker for 5230 breakout analysis
    
    Args:
        ticker: Stock symbol
        data_ticker: Optional pre-downloaded data dictionary
    
    Returns:
        List of results
    """
    intervals = ['5m', '10m', '15m', '30m']
    
    results = []
    # Use provided data or download if not provided
    if data_ticker is None:
        print (f"data not provided for {ticker}")
        # throw an error
        raise ValueError(f"data not provided for {ticker}") 

    for interval in intervals:
        print(f"ticker: {ticker} interval: {interval}")
        data = data_ticker.get(interval, pd.DataFrame())
        if data.empty:
            print(f"data is empty: {ticker} {interval}")
            continue
        
        try:
            cd = compute_cd_indicator(data)
            breakthrough = compute_nx_break_through(data)
            buy_signals = (cd.astype(bool) & breakthrough) | (cd.astype(bool) & breakthrough.rolling(10).apply(lambda x: x.iloc[0] if x.any() else False))   
            signal_dates = data.index[buy_signals]
            breakthrough_dates = data.index[breakthrough]
            
            for date in data.index[cd]:
                score = calculate_score(data, interval, date)
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
            print(f"Error processing {ticker} {interval}: {e}")
    
    return results