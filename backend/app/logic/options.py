import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_option_data(ticker_symbol: str):
    """
    Fetch option chain data for nearest day, week, and month.
     Returns a structured dictionary with aggregated OI data.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        
        # Get expiration dates
        try:
            expirations = ticker.options
        except Exception as e:
            # Handle case where no options exist or API fails
            print(f"No options found for {ticker_symbol}: {e}")
            return None

        if not expirations:
            return None

        # Helper to parse date
        def parse_date(d_str):
            return datetime.strptime(d_str, '%Y-%m-%d')

        today = datetime.now()
        exp_dates = [parse_date(d) for d in expirations]

        # 1. Nearest Expiration
        nearest_date = expirations[0]

        # 2. Next Week (Closest to Today + 7 days)
        target_week = today + timedelta(days=7)
        # Find date closest to target_week
        # We want closest absolute difference
        week_date_obj = min(exp_dates, key=lambda d: abs(d - target_week))
        week_date = week_date_obj.strftime('%Y-%m-%d')
        
        # 3. Next Month (Closest to Today + 30 days)
        target_month = today + timedelta(days=30)
        month_date_obj = min(exp_dates, key=lambda d: abs(d - target_month))
        month_date = month_date_obj.strftime('%Y-%m-%d')

        targets = {
            'nearest': nearest_date,
            'week': week_date,
            'month': month_date
        }
        
        # Avoid duplicate fetches if dates are the same (e.g. if nearest is 7 days away)
        # We will fetch for unique dates and then map back
        unique_dates = list(set(targets.values()))
        chain_cache = {}

        current_price = None
        try:
             # Try fast info first
             current_price = ticker.fast_info.last_price
        except:
             try:
                 hist = ticker.history(period='1d')
                 if not hist.empty:
                     current_price = hist['Close'].iloc[-1]
             except:
                 pass

        for d in unique_dates:
            try:
                chain = ticker.option_chain(d)
                # Combine matching strikes
                # We need a DataFrame with Strike, Call OI, Put OI
                
                calls = chain.calls[['strike', 'openInterest']].rename(columns={'openInterest': 'calls'})
                puts = chain.puts[['strike', 'openInterest']].rename(columns={'openInterest': 'puts'})
                
                # Merge on strike
                merged = pd.merge(calls, puts, on='strike', how='outer').fillna(0)
                
                # Filter useful range? 
                # Showing ALL strikes might be too much. 
                # Let's filter to e.g. +/- 20% or 30% of current price if available, 
                # or just top N active strikes?
                # User didn't specify, but for UI performance, maybe not hundreds of bars.
                # However, for now, let's just sort by strike and return.
                
                merged = merged.sort_values('strike')
                
                chain_cache[d] = merged.to_dict(orient='records')
            except Exception as e:
                print(f"Error fetching chain for {d}: {e}")
                chain_cache[d] = []

        return {
            "current_price": current_price,
            "nearest": {"date": targets['nearest'], "data": chain_cache.get(targets['nearest'], [])},
            "week": {"date": targets['week'], "data": chain_cache.get(targets['week'], [])},
            "month": {"date": targets['month'], "data": chain_cache.get(targets['month'], [])}
        }

    except Exception as e:
        print(f"Error in get_option_data: {e}")
        return None
