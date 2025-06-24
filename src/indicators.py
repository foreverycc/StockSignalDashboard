import pandas as pd
import numpy as np

def compute_cd_indicator(data):
    close = data['Close']
    # 计算MACD
    fast_ema = close.ewm(span=12, adjust=False).mean()
    slow_ema = close.ewm(span=26, adjust=False).mean()
    diff = fast_ema - slow_ema
    dea = diff.ewm(span=9, adjust=False).mean()
    mcd = (diff - dea) * 2

    # 计算交叉事件
    cross_down = (mcd.shift(1) >= 0) & (mcd < 0)
    cross_up = (mcd.shift(1) <= 0) & (mcd > 0)

    # 计算N1和MM1
    n1 = _compute_barslast(cross_down, len(data))
    mm1 = _compute_barslast(cross_up, len(data))

    # 计算N1_SAFE和MM1_SAFE
    n1_safe = n1 + 1
    mm1_safe = mm1 + 1

    # 计算CC系列
    cc1 = _compute_llv(close, n1_safe)
    cc2 = _compute_ref(cc1, mm1_safe)
    cc3 = _compute_ref(cc2, mm1_safe)

    # 计算DIFL系列
    difl1 = _compute_llv(diff, n1_safe)
    difl2 = _compute_ref(difl1, mm1_safe)
    difl3 = _compute_ref(difl2, mm1_safe)

    # 生成条件信号
    aaa = (cc1 < cc2) & (difl1 > difl2) & (mcd.shift(1) < 0) & (diff < 0)
    bbb = (cc1 < cc3) & (difl1 < difl2) & (difl1 > difl3) & (mcd.shift(1) < 0) & (diff < 0)
    ccc = aaa | bbb
    jjj = ccc.shift(1) & (abs(diff.shift(1)) >= abs(diff) * 1.01)
    dxdx = jjj & ~jjj.shift(1, fill_value=False).fillna(False)

    return dxdx

def compute_nx_break_through(data):
    high = data['High']
    short_upper = high.ewm(span=24, adjust=False).mean()
    break_through = (data['Close'] > short_upper) & (data['Close'].shift(1) <= short_upper.shift(1))
    return break_through

def _compute_barslast(cross_events, length):
    barslast = np.zeros(length, dtype=int)
    last_event = -1
    for i in range(length):
        if cross_events.iloc[i]:
            last_event = i
        barslast[i] = i - last_event if last_event != -1 else 0
    return pd.Series(barslast, index=cross_events.index)

def _compute_llv(series, periods):
    llv = pd.Series(index=series.index, dtype=float)
    for i in range(len(series)):
        period = periods.iloc[i]
        if period > 0:
            start = max(0, i - period + 1)
            llv.iloc[i] = series.iloc[start:i+1].min()
        else:
            llv.iloc[i] = np.nan
    return llv

def _compute_ref(series, lags):
    ref = pd.Series(index=series.index, dtype=float)
    for i in range(len(series)):
        lag = lags.iloc[i]
        if lag <= i:
            ref.iloc[i] = series.iloc[i - lag]
        else:
            ref.iloc[i] = np.nan
    return ref