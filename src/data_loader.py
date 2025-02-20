import pandas as pd
import yfinance as yf
import time
def load_stock_list(file_path):
    return pd.read_csv(file_path, sep='\t', header=None, names=['ticker'])['ticker'].tolist()

def download_data_1234(ticker):
    period_map = {
            # '1m': 'max',
            # '2m': '5d',
            # '5m': '5d',
            # '15m': '1mo',
            # '30m': '1mo',
            '1h': '3mo',
            '2h': '3mo',
            '3h': '3mo',
            '4h': '3mo',
        }
    data_ticker = {}
    stock = yf.Ticker(ticker)
    # data_ticker['1h'] = stock.history(interval='60m', period=period_map['1h'], actions=False, auto_adjust=True)
    try:
        data_ticker['1h'] = stock.history(interval='60m', period=period_map['1h'])
    except Exception as e:
        print(f"Error downloading {ticker} 1h: {e}")
        data_ticker['1h'] = pd.DataFrame()
    print("ticker:", ticker)
    # print(data_ticker['1h'])

    for interval in period_map:
        print("interval:", interval)
        try:
            if interval in ['1h', '2h', '3h', '4h']:
                data_ticker[interval] = data_ticker['1h']
                data_ticker[interval] = transform_1h_data(data_ticker[interval], interval)
            else:
                # data_ticker[interval] = stock.history(interval=interval, period=period_map[interval], actions=False, auto_adjust=True)
                data_ticker[interval] = stock.history(interval=interval, period=period_map[interval])
        except Exception as e:
            print(f"Error downloading {ticker} {interval}: {e}")
            data_ticker[interval] = pd.DataFrame()
        # time.sleep(0.1)

    # print(data_ticker)
    return data_ticker
    
def transform_1h_data(df_1h, new_interval = '2h'):
    if df_1h.empty:
        return pd.DataFrame()
    # 确保DatetimeIndex
    df_1h.index = pd.to_datetime(df_1h.index)
    df_1h.sort_index(inplace=True)  # 排序一下，以防万一

    # ============== 2) 只保留日盘 (9:30-16:00) ==============
    #   如果你也想包括盘前/盘后，则可不做这步，或改成更广时间段
    df_1h = df_1h.between_time("09:30", "16:00")

    # ============== 3) 按"每个自然日"分组 ==============
    #   这样做可以保证日内聚合，跨日不拼接。
    grouped = df_1h.groupby(df_1h.index.date)

    # ============== 4) 对单日数据做 "2H" 重采样 ==============
    def resample_xh(daily_df):
        """
        对当日(9:30~16:00)的 1 小时数据做 x 小时的重采样:
        - Bar起点对齐到 9:30
        - 最后不足x小时的也生成单独一根
        """
        # 注意这里 origin="start_day", offset="9h30min" 是关键
        # 使得日内区间从 当日00:00+9h30 => 当日09:30 开始切分
        # 结果区间: 9:30~11:30, 11:30~13:30, 13:30~15:30, 15:30~17:30(只到16:00)
        return daily_df.resample(
            rule=new_interval.replace('h', 'H'),
            closed="left",   # 区间左闭右开
            label="left",    # 用区间左端做时间戳
            origin="start_day", 
            offset="9h30min"
        ).agg({
            "Open":  "first",
            "High":  "max",
            "Low":   "min",
            "Close": "last",
            "Volume":"sum"
        })

    # ============== 5) 分日重采样，再拼接回总表 ==============
    df_xh_list = []
    for date_key, daily_data in grouped:
        # 做 xH 重采样
        bar_xh = resample_xh(daily_data)
        
        # 有时遇到完全没数据或NaN的行，可自行选择是否 dropna()
        bar_xh.dropna(subset=["Open","High","Low","Close"], how="any", inplace=True)
        
        df_xh_list.append(bar_xh)

    # 合并成完整的X小时数据表
    df_xh = pd.concat(df_xh_list).sort_index()
    # print(df_xh.tail(20))
    return df_xh

def download_data_5230(ticker):
    period_map = {
            '5m': '1mo',
            '10m': '1mo',
            '15m': '1mo',
            '30m': '1mo',
        }
    data_ticker = {}
    stock = yf.Ticker(ticker)
    # data_ticker['1h'] = stock.history(interval='60m', period=period_map['1h'], actions=False, auto_adjust=True)
    try:
        data_ticker['5m'] = stock.history(interval='5m', period=period_map['5m'])
        # print(data_ticker['5m'])
    except Exception as e:
        print(f"Error downloading {ticker} 5m: {e}")
        data_ticker['5m'] = pd.DataFrame()
    print("ticker:", ticker)

    for interval in period_map:
        print("interval:", interval)
        try:
            if interval in ['5m', '10m', '15m', '30m']:
                data_ticker[interval] = data_ticker['5m']
                data_ticker[interval] = transform_5m_data(data_ticker[interval], interval)
            else:
                # data_ticker[interval] = stock.history(interval=interval, period=period_map[interval], actions=False, auto_adjust=True)
                data_ticker[interval] = stock.history(interval=interval, period=period_map[interval])
        except Exception as e:
            print(f"Error downloading {ticker} {interval}: {e}")
            data_ticker[interval] = pd.DataFrame()
        # time.sleep(0.1)

    # print(data_ticker)
    return data_ticker
    
def transform_5m_data(df_5m, new_interval = '10m'):
    if df_5m.empty:
        return pd.DataFrame()
    # 确保DatetimeIndex
    df_5m.index = pd.to_datetime(df_5m.index)
    df_5m.sort_index(inplace=True)  # 排序一下，以防万一
    
    # ============== 2) 只保留日盘 (9:30-16:00) ==============
    #   如果你也想包括盘前/盘后，则可不做这步，或改成更广时间段
    df_5m = df_5m.between_time("09:30", "16:00")

    # ============== 3) 按"每个自然日"分组 ==============
    #   这样做可以保证日内聚合，跨日不拼接。
    grouped = df_5m.groupby(df_5m.index.date)

    # ============== 4) 对单日数据做 "10m" 重采样 ==============
    def resample_xh(daily_df):
        """
        对当日(9:30~16:00)的 5 分钟数据做 x 分钟的重采样:
        - Bar起点对齐到 9:30
        - 最后不足x分钟的也生成单独一根
        """
        # 注意这里 origin="start_day", offset="9h30min" 是关键
        # 使得日内区间从 当日00:00+9h30 => 当日09:30 开始切分
        # 结果区间: 9:30~11:30, 11:30~13:30, 13:30~15:30, 15:30~17:30(只到16:00)
        return daily_df.resample(
            rule=new_interval.replace('m', 'T'),
            closed="left",   # 区间左闭右开
            label="left",    # 用区间左端做时间戳
            origin="start_day", 
            offset="9h30min"
        ).agg({
            "Open":  "first",
            "High":  "max",
            "Low":   "min",
            "Close": "last",
            "Volume":"sum"
        })

    # ============== 5) 分日重采样，再拼接回总表 ==============
    df_xh_list = []
    for date_key, daily_data in grouped:
        # 做 xH 重采样
        bar_xh = resample_xh(daily_data)
        
        # 有时遇到完全没数据或NaN的行，可自行选择是否 dropna()
        bar_xh.dropna(subset=["Open","High","Low","Close"], how="any", inplace=True)
        
        df_xh_list.append(bar_xh)

    # 合并成完整的X小时数据表
    df_xh = pd.concat(df_xh_list).sort_index()
    # print(df_xh.tail(20))
    return df_xh
