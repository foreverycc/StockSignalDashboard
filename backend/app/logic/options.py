import yfinance as yf
import pandas as pd
import numpy as np
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
                
                # Calculate Max Pain
                # Iterate through all strikes as potential expiration prices
                # For each price P, calculate total liability:
                # Sum(max(0, P - k) * call_oi(k) + max(0, k - P) * put_oi(k))
                
                strikes = merged['strike'].values
                call_ois = merged['calls'].values
                put_ois = merged['puts'].values
                
                min_pain_value = float('inf')
                max_pain_strike = 0
                
                for price_point in strikes:
                    call_loss = np.maximum(0, price_point - strikes) * call_ois
                    put_loss = np.maximum(0, strikes - price_point) * put_ois
                    total_pain = np.sum(call_loss + put_loss)
                    
                    if total_pain < min_pain_value:
                        min_pain_value = total_pain
                        max_pain_strike = price_point
                        
                merged = merged.sort_values('strike')
                
                chain_cache[d] = {
                    'data': merged.to_dict(orient='records'),
                    'max_pain': max_pain_strike
                }
            except Exception as e:
                print(f"Error fetching chain for {d}: {e}")
                chain_cache[d] = {'data': [], 'max_pain': None}

        return {
            "current_price": current_price,
            "nearest": {
                "date": targets['nearest'], 
                "data": chain_cache.get(targets['nearest'], {}).get('data', []),
                "max_pain": chain_cache.get(targets['nearest'], {}).get('max_pain')
            },
            "week": {
                "date": targets['week'], 
                "data": chain_cache.get(targets['week'], {}).get('data', []),
                "max_pain": chain_cache.get(targets['week'], {}).get('max_pain')
            },
            "month": {
                "date": targets['month'], 
                "data": chain_cache.get(targets['month'], {}).get('data', []),
                "max_pain": chain_cache.get(targets['month'], {}).get('max_pain')
            }
        }

    except Exception as e:
        print(f"Error in get_option_data: {e}")
        return None
