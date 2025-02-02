import pandas as pd
from data_loader import download_data
from indicators import compute_cd_indicator, compute_nx_break_through
import time
    
def calculate_score(data, interval, signal_date):
    interval_weights = {
        # '1m': 1, 
        # '2m': 2, 
        '5m': 3, 
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

def process_ticker(ticker):
    # intervals = ['1m', '2m', '5m', '15m', '30m', '1h', '1d']
    intervals = ['5m', '15m', '30m', '1h', '2h', '3h', '4h', '1d']
    period_map = {
            # '1m': 'max',
            # '2m': '5d',
            '5m': '5d',
            '15m': '1mo',
            '30m': '1mo',
            '1h': '3mo',
            '2h': '3mo',
            '3h': '3mo',
            '4h': '3mo',
            '1d': '6mo',
        }
    
    results = []
    
    for interval in intervals:
        print ("interval:", interval)
        data = download_data(ticker, interval, period_map[interval])
        if data.empty:
            time.sleep(0.5)
            data = download_data(ticker, interval, period_map[interval])
        print ("start:", data.index[0].strftime('%Y-%m-%d %H:%M:%S'))
        print ("end:", data.index[-1].strftime('%Y-%m-%d %H:%M:%S'))
        if data.empty:
            continue
        
        try:
            dxdx = compute_cd_indicator(data)
            breakthrough = compute_nx_break_through(data)
            buy_signals = (dxdx.astype(bool) & breakthrough) | (dxdx.astype(bool) & breakthrough.rolling(10).apply(lambda x: x[0] if x.any() else False))   
            signal_dates = data.index[buy_signals]
            breakthrough_dates = data.index[breakthrough]
            
            print ("抄底日期：", data.index[dxdx].strftime('%Y-%m-%d %H:%M:%S'))
            # print ("买入信号：", buy_signals)
            # print ("买入日期：", signal_dates)
            print ("突破日期：", breakthrough_dates.strftime('%Y-%m-%d %H:%M:%S'))
            
            # for date in signal_dates:
            for date in data.index[dxdx]:
                print(date)
                score = calculate_score(data, interval, date)
                # Find the next breakthrough date after the signal date
                future_breakthroughs = breakthrough_dates[breakthrough_dates >= date]
                next_breakthrough = future_breakthroughs[0] if len(future_breakthroughs) > 0 else None

                results.append({
                    'ticker': ticker,
                    'interval': interval,
                    'score': score,
                    'signal_date': date.strftime('%Y-%m-%d %H:%M:%S'),
                    'breakthrough_date': next_breakthrough.strftime('%Y-%m-%d %H:%M:%S') if next_breakthrough is not None else None
                })
        except Exception as e:
            print(f"Error processing {ticker} {interval}: {e}")
    
    return results