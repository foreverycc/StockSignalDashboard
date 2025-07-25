import pandas as pd
import os
from data_loader import load_stock_list, download_stock_data
from get_resonance_signal_CD import process_ticker_1234, process_ticker_5230, identify_1234, identify_5230
from get_resonance_signal_MC import process_ticker_mc_1234, process_ticker_mc_5230, identify_mc_1234, identify_mc_5230
from utils import save_results, save_breakout_candidates_1234, save_breakout_candidates_5230, save_mc_breakout_candidates_1234, save_mc_breakout_candidates_5230
from get_best_CD_interval import evaluate_interval
from get_best_MC_interval import evaluate_interval as evaluate_mc_interval
from multiprocessing import Pool, cpu_count
import functools

# Suppress pandas FutureWarnings about downcasting
pd.set_option('future.no_silent_downcasting', True)

# Define column configurations at module level for reusability
best_intervals_columns = ['ticker', 'interval', 'hold_time',  
                          'avg_return', 'latest_signal', 'latest_signal_price', 
                          'current_time', 'current_price', 'current_period',
                          'test_count', 'success_rate', 'best_period', 'signal_count',
                          'mc_signals_before_cd', 'mc_at_top_price_count', 'mc_at_top_price_rate',
                          'avg_mc_price_percentile', 'avg_mc_decline_after', 'avg_mc_criteria_met',
                          'latest_mc_date', 'latest_mc_price', 'latest_mc_at_top_price',
                          'latest_mc_price_percentile', 'latest_mc_decline_after', 'latest_mc_criteria_met']

# Define MC column configurations with CD analysis columns (needed for symmetry with CD analysis)
mc_best_intervals_columns = ['ticker', 'interval', 'hold_time',  
                             'avg_return', 'latest_signal', 'latest_signal_price', 
                             'current_time', 'current_price', 'current_period',
                             'test_count', 'success_rate', 'best_period', 'signal_count',
                             'cd_signals_before_mc', 'cd_at_bottom_price_count', 'cd_at_bottom_price_rate',
                             'avg_cd_price_percentile', 'avg_cd_increase_after', 'avg_cd_criteria_met',
                             'latest_cd_date', 'latest_cd_price', 'latest_cd_at_bottom_price',
                             'latest_cd_price_percentile', 'latest_cd_increase_after', 'latest_cd_criteria_met']

# Define all periods for dynamic handling
periods = [0] + list(range(1, 101))  # Full range from 0 to 100

# Define period ranges for different best intervals tables
period_ranges = {
    '20': [3, 5, 10, 15, 20],
    '50': [3, 5, 10, 15, 20, 25, 30, 40, 50],
    '100': [3, 5, 10, 15, 20, 25, 30, 40, 50, 60, 80, 100]
}

# Build good_signals_columns dynamically
good_signals_columns = ['ticker', 'interval', 'hold_time', 
                        'exp_return', 'latest_signal', 'latest_signal_price',
                        'current_time', 'current_price', 'current_period',
                        'test_count', 'success_rate', 'best_period', 'signal_count',
                        'mc_signals_before_cd', 'mc_at_top_price_count', 'mc_at_top_price_rate',
                        'avg_mc_price_percentile', 'avg_mc_decline_after', 'avg_mc_criteria_met',
                        'latest_mc_date', 'latest_mc_price', 'latest_mc_at_top_price',
                        'latest_mc_price_percentile', 'latest_mc_decline_after', 'latest_mc_criteria_met']

# Add all period-specific columns to good_signals_columns
for period in periods:
    good_signals_columns.extend([f'test_count_{period}', f'success_rate_{period}', f'avg_return_{period}'])
good_signals_columns.extend(['max_return', 'min_return'])

# Build MC good_signals_columns dynamically with CD analysis columns (needed for symmetry with CD analysis)
mc_good_signals_columns = ['ticker', 'interval', 'hold_time', 
                           'exp_return', 'latest_signal', 'latest_signal_price',
                           'current_time', 'current_price', 'current_period',
                           'test_count', 'success_rate', 'best_period', 'signal_count',
                           'cd_signals_before_mc', 'cd_at_bottom_price_count', 'cd_at_bottom_price_rate',
                           'avg_cd_price_percentile', 'avg_cd_increase_after', 'avg_cd_criteria_met',
                           'latest_cd_date', 'latest_cd_price', 'latest_cd_at_bottom_price',
                           'latest_cd_price_percentile', 'latest_cd_increase_after', 'latest_cd_criteria_met']

# Add all period-specific columns to MC good_signals_columns
for period in periods:
    mc_good_signals_columns.extend([f'test_count_{period}', f'success_rate_{period}', f'avg_return_{period}'])
mc_good_signals_columns.extend(['max_return', 'min_return'])

def parse_interval_to_minutes(interval_str):
    """
    Parse interval string to minutes.
    Examples: '5m' -> 5, '1h' -> 60, '1d' -> 480 (8 hours), '1w' -> 2400 (5 trading days * 8 hours)
    """
    if interval_str.endswith('m'):
        return int(interval_str[:-1])
    elif interval_str.endswith('h'):
        return int(interval_str[:-1]) * 60
    elif interval_str.endswith('d'):
        return int(interval_str[:-1]) * 8 * 60  # 8 trading hours per day
    elif interval_str.endswith('w'):
        return int(interval_str[:-1]) * 5 * 8 * 60  # 5 trading days * 8 hours per day
    else:
        return 0

def format_hold_time(total_minutes):
    """
    Format total minutes into readable format.
    Examples: 150 -> '2hr30min', 600 -> '1day2hr', 250 -> '4hr10min'
    """
    if total_minutes < 60:
        return f"{total_minutes}min"
    
    # Convert to trading time (8 hours per day)
    trading_hours_per_day = 8
    
    days = total_minutes // (trading_hours_per_day * 60)
    remaining_minutes = total_minutes % (trading_hours_per_day * 60)
    hours = remaining_minutes // 60
    minutes = remaining_minutes % 60
    
    result = []
    if days > 0:
        result.append(f"{days}day{'s' if days > 1 else ''}")
    if hours > 0:
        result.append(f"{hours}hr")
    if minutes > 0:
        result.append(f"{minutes}min")
    
    return "".join(result) if result else "0min"

# Move this function outside the analyze_stocks function so it can be pickled
def process_ticker_all(ticker, end_date=None):
    """Process a single ticker for all analysis types"""
    try:
        print(f"Processing {ticker}")
        # Download data once for all analyses
        data = download_stock_data(ticker, end_date=end_date)
        
        # Skip if no data available
        if all(df.empty for df in data.values()):
            print(f"No data available for {ticker}")
            return None, None, [], [], None
        
        # Process for 1234 breakout (CD signals)
        results_1234 = process_ticker_1234(ticker, data)
        
        # Process for 5230 breakout (CD signals)
        results_5230 = process_ticker_5230(ticker, data)
        
        # Process for MC 1234 breakout (MC signals)
        mc_results_1234 = process_ticker_mc_1234(ticker, data)
        
        # Process for MC 5230 breakout (MC signals)
        mc_results_5230 = process_ticker_mc_5230(ticker, data)
        
        # Process for CD signal evaluation
        cd_results = []
        intervals = ['5m', '10m', '15m', '30m', '1h', '2h', '3h', '4h', '1d', '1w']
        for interval in intervals:
            result = evaluate_interval(ticker, interval, data=data)
            if result:
                cd_results.append(result)
        
        # Process for MC signal evaluation
        mc_results = []
        for interval in intervals:
            result = evaluate_mc_interval(ticker, interval, data=data)
            if result:
                mc_results.append(result)
        
        return results_1234, results_5230, mc_results_1234, mc_results_5230, cd_results, mc_results, data
        
    except Exception as e:
        print(f"Error processing {ticker}: {e}")
        return None, None, [], [], [], [], None

def analyze_stocks(file_path, end_date=None):
    """
    Comprehensive stock analysis function that performs all three types of analysis:
    - 1234 Breakout candidates
    - 5230 Breakout candidates
    - CD Signal Evaluation
    
    Args:
        file_path: Path to the file containing stock ticker symbols
        end_date: Optional end date for backtesting (format: 'YYYY-MM-DD')
    
    Returns:
        None: Results are saved to output files
    """
    # Create output directory if it doesn't exist
    output_dir = './output'
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract base name for output files
    output_base = file_path.split('/')[-1].split('.')[0]
    
    # Load stock list
    stock_list = load_stock_list(file_path)
    print(f"Analyzing {len(stock_list)} stocks from {file_path}")
    
    # Configure multiprocessing
    num_processes = max(1, min(8, cpu_count() - 1)) # limit to 8 processes to avoid API rate limit
    print(f"Using {num_processes} processes for analysis")
    
    # Process stocks in batches to avoid memory issues
    batch_size = 50
    results_1234 = []
    results_5230 = []
    mc_results_1234 = []
    mc_results_5230 = []
    cd_eval_results = []
    mc_eval_results = []
    all_ticker_data = {}
    failed_tickers = []

    for i in range(0, len(stock_list), batch_size):
        batch = stock_list[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(stock_list) + batch_size - 1)//batch_size}: {batch}")
        
        # Process the batch with multiprocessing
        # Use functools.partial to bind end_date parameter
        process_ticker_with_end_date = functools.partial(process_ticker_all, end_date=end_date)
        with Pool(processes=num_processes) as pool:
            batch_results = pool.map(process_ticker_with_end_date, batch)
        
        # Collect results from batch
        for i, (r1234, r5230, mc_r1234, mc_r5230, cd_eval, mc_eval, data) in enumerate(batch_results):
            ticker = batch[i]
            if r1234:
                results_1234.extend(r1234)
            if r5230:
                results_5230.extend(r5230)
            if mc_r1234:
                mc_results_1234.extend(mc_r1234)
            if mc_r5230:
                mc_results_5230.extend(mc_r5230)
            if cd_eval:
                cd_eval_results.extend(cd_eval)
            if mc_eval:
                mc_eval_results.extend(mc_eval)
            if data:
                all_ticker_data[ticker] = data
            else:
                failed_tickers.append(ticker)
    
    # 1. Save 1234 results and identify breakout candidates
    print("Saving 1234 breakout results...")
    output_file_1234 = os.path.join(output_dir, f'cd_breakout_candidates_details_1234_{output_base}.tab')
    save_results(results_1234, output_file_1234)
    df_breakout_1234 = identify_1234(output_file_1234, all_ticker_data)
    save_breakout_candidates_1234(df_breakout_1234, output_file_1234)
    
    # 2. Save 5230 results and identify breakout candidates
    print("Saving 5230 breakout results...")
    output_file_5230 = os.path.join(output_dir, f'cd_breakout_candidates_details_5230_{output_base}.tab')
    save_results(results_5230, output_file_5230)
    df_breakout_5230 = identify_5230(output_file_5230, all_ticker_data)
    save_breakout_candidates_5230(df_breakout_5230, output_file_5230)
    
    # 3. Save MC 1234 results and identify breakout candidates
    print("Saving MC 1234 breakout results...")
    output_file_mc_1234 = os.path.join(output_dir, f'mc_breakout_candidates_details_1234_{output_base}.tab')
    save_results(mc_results_1234, output_file_mc_1234)
    df_mc_breakout_1234 = identify_mc_1234(output_file_mc_1234, all_ticker_data)
    save_mc_breakout_candidates_1234(df_mc_breakout_1234, output_file_mc_1234)
    
    # 4. Save MC 5230 results and identify breakout candidates
    print("Saving MC 5230 breakout results...")
    output_file_mc_5230 = os.path.join(output_dir, f'mc_breakout_candidates_details_5230_{output_base}.tab')
    save_results(mc_results_5230, output_file_mc_5230)
    df_mc_breakout_5230 = identify_mc_5230(output_file_mc_5230, all_ticker_data)
    save_mc_breakout_candidates_5230(df_mc_breakout_5230, output_file_mc_5230)
    
    # 5. Save CD evaluation results
    print("Saving CD evaluation results...")
    # Convert CD evaluation results to DataFrame
    if cd_eval_results:
        df_cd_eval = pd.DataFrame(cd_eval_results)
        
        # Round numeric columns to 3 decimal places to reduce file size and improve loading performance
        for col in df_cd_eval.columns:
            if df_cd_eval[col].dtype in ['float64', 'float32']:
                df_cd_eval[col] = df_cd_eval[col].round(3)
        
        # Save detailed results with ticker information
        df_cd_eval.to_csv(os.path.join(output_dir, f'cd_eval_custom_detailed_{output_base}.csv'), index=False)
        
        # Create a separate file with individual returns for boxplot visualization
        returns_data = []
        for result in cd_eval_results:
            ticker = result['ticker']
            interval = result['interval']
            for period in periods:
                returns_key = f'returns_{period}'
                volumes_key = f'volumes_{period}'
                if returns_key in result and result[returns_key]:
                    # Get individual returns and volumes for this period
                    individual_returns = result[returns_key]
                    individual_volumes = result.get(volumes_key, [])
                    
                    # Ensure volumes list has same length as returns
                    if len(individual_volumes) < len(individual_returns):
                        individual_volumes.extend([None] * (len(individual_returns) - len(individual_volumes)))
                    
                    for i, return_value in enumerate(individual_returns):
                        volume_value = individual_volumes[i] if i < len(individual_volumes) else None
                        returns_data.append({
                            'ticker': ticker,
                            'interval': interval,
                            'period': period,
                            'return': return_value,
                            'volume': volume_value
                        })
        
        if returns_data:
            df_returns = pd.DataFrame(returns_data)
            # Round numeric columns to 3 decimal places for returns and 0 decimal places for volumes
            if 'return' in df_returns.columns:
                df_returns['return'] = df_returns['return'].round(3)
            if 'volume' in df_returns.columns:
                df_returns['volume'] = df_returns['volume'].round(0)
            df_returns.to_csv(os.path.join(output_dir, f'cd_eval_returns_distribution_{output_base}.csv'), index=False)
        else:
            # Create empty returns distribution file
            empty_returns = pd.DataFrame(columns=['ticker', 'interval', 'period', 'return', 'volume'])
            empty_returns.to_csv(os.path.join(output_dir, f'cd_eval_returns_distribution_{output_base}.csv'), index=False)

        # Find the best interval for each ticker based on success rate and returns
        # Only consider intervals with at least 2 tests for period 10
        valid_df = df_cd_eval[df_cd_eval['test_count_10'] >= 2]
        
        # Create filter condition for any period having >= 5% average return
        filter_conditions = []
        for period in periods:
            if f'avg_return_{period}' in df_cd_eval.columns:
                filter_conditions.append(valid_df[f'avg_return_{period}'] >= 5)
        
        if filter_conditions:
            # Combine all conditions with OR
            combined_filter = filter_conditions[0]
            for condition in filter_conditions[1:]:
                combined_filter = combined_filter | condition
            valid_df = valid_df[combined_filter]
        
        if not valid_df.empty:
            # Create separate best intervals for each period range
            for range_name, range_periods in period_ranges.items():
                # Filter columns for this range
                avg_return_cols = [f'avg_return_{period}' for period in range_periods if f'avg_return_{period}' in valid_df.columns]
                
                # Calculate max return and best period for this range
                range_df = valid_df.copy()
                range_df['max_return'] = range_df[avg_return_cols].max(axis=1)
                range_df['best_period'] = range_df[avg_return_cols].idxmax(axis=1).str.extract('(\d+)').astype(int)
                
                # Get row with highest max_return for each ticker
                best_intervals = range_df.loc[range_df.groupby('ticker')['max_return'].idxmax()]
                
                # Select and rename columns
                best_intervals = best_intervals.assign(
                    test_count=best_intervals.apply(lambda x: x[f'test_count_{int(x.best_period)}'], axis=1),
                    success_rate=best_intervals.apply(lambda x: x[f'success_rate_{int(x.best_period)}'], axis=1),
                    avg_return=best_intervals['max_return']
                )
                
                # Keep all columns that are in best_intervals_columns
                available_columns = [col for col in best_intervals_columns if col in best_intervals.columns]
                best_intervals = best_intervals[available_columns].sort_values('latest_signal', ascending=False)
                
                # Calculate hold_time as interval * best_period
                best_intervals['hold_time'] = best_intervals.apply(
                    lambda row: format_hold_time(parse_interval_to_minutes(row['interval']) * row['best_period']), axis=1
                )
                
                # Reorder columns to put hold_time after interval
                final_columns = [col for col in best_intervals_columns if col in best_intervals.columns]
                best_intervals = best_intervals[final_columns]
                best_intervals = best_intervals[best_intervals['avg_return'] >= 5]
                best_intervals = best_intervals[best_intervals['success_rate'] >= 50]
                best_intervals = best_intervals[best_intervals['current_period'] <= best_intervals['best_period']]
                
                # Round numeric columns to 3 decimal places to reduce file size
                for col in best_intervals.columns:
                    if best_intervals[col].dtype in ['float64', 'float32']:
                        best_intervals[col] = best_intervals[col].round(3)
                        
                best_intervals.to_csv(os.path.join(output_dir, f'cd_eval_best_intervals_{range_name}_{output_base}.csv'), index=False)

            # Good signals - all signals that meet criteria, sorted by date
            good_signals = valid_df.sort_values('latest_signal', ascending=False)
            
            # Calculate max return and best period for good signals
            avg_return_cols = [f'avg_return_{period}' for period in periods if f'avg_return_{period}' in good_signals.columns]
            good_signals['max_return'] = good_signals[avg_return_cols].max(axis=1)
            good_signals['best_period'] = good_signals[avg_return_cols].idxmax(axis=1).str.extract('(\d+)').astype(int)
            
            # Calculate hold_time as interval * best_period
            good_signals['hold_time'] = good_signals.apply(
                lambda row: format_hold_time(parse_interval_to_minutes(row['interval']) * row['best_period']), axis=1
            )
            
            # Calculate exp_return as the avg_return for the best_period
            good_signals['exp_return'] = good_signals.apply(
                lambda row: row[f'avg_return_{int(row.best_period)}'], axis=1
            )
            good_signals['test_count'] = good_signals.apply(
                lambda row: row[f'test_count_{int(row.best_period)}'], axis=1
            )
            good_signals['success_rate'] = good_signals.apply(
                lambda row: row[f'success_rate_{int(row.best_period)}'], axis=1
            )
            
            # Reorder columns to put hold_time after interval and exp_return after signal_count
            available_good_columns = [col for col in good_signals_columns if col in good_signals.columns]
            good_signals = good_signals[available_good_columns]
            good_signals = good_signals[good_signals['success_rate'] >= 50]
            
            # Round numeric columns to 3 decimal places to reduce file size
            for col in good_signals.columns:
                if good_signals[col].dtype in ['float64', 'float32']:
                    good_signals[col] = good_signals[col].round(3)
            
            good_signals.to_csv(os.path.join(output_dir, f'cd_eval_good_signals_{output_base}.csv'), index=False)
        else:
            print("Not enough data to determine best intervals (need at least 2 tests)")
            # Create empty files with proper headers for each range
            for range_name in period_ranges.keys():
                empty_best_intervals = pd.DataFrame(columns=best_intervals_columns)
                empty_best_intervals.to_csv(os.path.join(output_dir, f'cd_eval_best_intervals_{range_name}_{output_base}.csv'), index=False)
            
            # For good_signals, we need to include all the original columns plus hold_time after interval and exp_return after signal_count
            empty_good_signals = pd.DataFrame(columns=good_signals_columns)
            empty_good_signals.to_csv(os.path.join(output_dir, f'cd_eval_good_signals_{output_base}.csv'), index=False)
            
        # Create a summary by interval (always create this if we have any CD results)
            agg_dict = {'signal_count': 'sum'}
            
            # Add aggregation for all periods dynamically
            for period in periods:
                if f'test_count_{period}' in df_cd_eval.columns:
                    agg_dict[f'test_count_{period}'] = 'sum'
                if f'success_rate_{period}' in df_cd_eval.columns:
                    agg_dict[f'success_rate_{period}'] = 'mean'
                if f'avg_return_{period}' in df_cd_eval.columns:
                    agg_dict[f'avg_return_{period}'] = 'mean'
                    
            interval_summary = df_cd_eval.groupby('interval').agg(agg_dict).reset_index()
            interval_summary.to_csv(os.path.join(output_dir, f'cd_eval_interval_summary_{output_base}.csv'), index=False)
    else:
        print("No CD evaluation results to save")
        # Create empty files with proper headers when no CD results at all
        empty_detailed_columns = ['ticker', 'interval', 'signal_count', 'latest_signal', 'latest_signal_price']
        
        # Add all period-specific columns
        for period in periods:
            empty_detailed_columns.extend([f'test_count_{period}', f'success_rate_{period}', f'avg_return_{period}'])
        
        empty_detailed_columns.extend(['max_return', 'min_return',
                                      'mc_signals_before_cd', 'mc_at_top_price_count', 'mc_at_top_price_rate',
                                      'avg_mc_price_percentile', 'avg_mc_decline_after', 'avg_mc_criteria_met',
                                      'latest_mc_date', 'latest_mc_price', 'latest_mc_at_top_price',
                                      'latest_mc_price_percentile', 'latest_mc_decline_after', 'latest_mc_criteria_met'])
        empty_detailed = pd.DataFrame(columns=empty_detailed_columns)
        empty_detailed.to_csv(os.path.join(output_dir, f'cd_eval_custom_detailed_{output_base}.csv'), index=False)
        
        # Create empty returns distribution file
        empty_returns = pd.DataFrame(columns=['ticker', 'interval', 'period', 'return', 'volume'])
        empty_returns.to_csv(os.path.join(output_dir, f'cd_eval_returns_distribution_{output_base}.csv'), index=False)
        
        # Create empty files with proper headers for each range
        for range_name in period_ranges.keys():
            empty_best_intervals = pd.DataFrame(columns=best_intervals_columns)
            empty_best_intervals.to_csv(os.path.join(output_dir, f'cd_eval_best_intervals_{range_name}_{output_base}.csv'), index=False)
        
        empty_good_signals = pd.DataFrame(columns=good_signals_columns)
        empty_good_signals.to_csv(os.path.join(output_dir, f'cd_eval_good_signals_{output_base}.csv'), index=False)
        
    # 6. Save MC evaluation results
    print("Saving MC evaluation results...")
    # Convert MC evaluation results to DataFrame
    if mc_eval_results:
        df_mc_eval = pd.DataFrame(mc_eval_results)
        
        # Round numeric columns to 3 decimal places to reduce file size and improve loading performance
        for col in df_mc_eval.columns:
            if df_mc_eval[col].dtype in ['float64', 'float32']:
                df_mc_eval[col] = df_mc_eval[col].round(3)
        
        # Save detailed results with ticker information
        df_mc_eval.to_csv(os.path.join(output_dir, f'mc_eval_custom_detailed_{output_base}.csv'), index=False)
        
        # Create a separate file with individual returns for boxplot visualization
        returns_data = []
        for result in mc_eval_results:
            ticker = result['ticker']
            interval = result['interval']
            for period in periods:
                returns_key = f'returns_{period}'
                volumes_key = f'volumes_{period}'
                if returns_key in result and result[returns_key]:
                    # Get individual returns and volumes for this period
                    individual_returns = result[returns_key]
                    individual_volumes = result.get(volumes_key, [])
                    
                    # Ensure volumes list has same length as returns
                    if len(individual_volumes) < len(individual_returns):
                        individual_volumes.extend([None] * (len(individual_returns) - len(individual_volumes)))
                    
                    for i, return_value in enumerate(individual_returns):
                        volume_value = individual_volumes[i] if i < len(individual_volumes) else None
                        returns_data.append({
                            'ticker': ticker,
                            'interval': interval,
                            'period': period,
                            'return': return_value,
                            'volume': volume_value
                        })
        
        if returns_data:
            df_returns = pd.DataFrame(returns_data)
            # Round numeric columns to 3 decimal places for returns and 0 decimal places for volumes
            if 'return' in df_returns.columns:
                df_returns['return'] = df_returns['return'].round(3)
            if 'volume' in df_returns.columns:
                df_returns['volume'] = df_returns['volume'].round(0)
            df_returns.to_csv(os.path.join(output_dir, f'mc_eval_returns_distribution_{output_base}.csv'), index=False)
        else:
            # Create empty returns distribution file
            empty_returns = pd.DataFrame(columns=['ticker', 'interval', 'period', 'return', 'volume'])
            empty_returns.to_csv(os.path.join(output_dir, f'mc_eval_returns_distribution_{output_base}.csv'), index=False)

        # Find the best interval for each ticker based on success rate and returns
        # Only consider intervals with at least 2 tests for period 10
        valid_df = df_mc_eval[df_mc_eval['test_count_10'] >= 2]
        
        # For MC signals, we want negative returns (price decline after sell signal)
        # So we filter for periods having <= -5% average return
        filter_conditions = []
        for period in periods:
            if f'avg_return_{period}' in df_mc_eval.columns:
                filter_conditions.append(valid_df[f'avg_return_{period}'] <= -5)
        
        if filter_conditions:
            # Combine all conditions with OR
            combined_filter = filter_conditions[0]
            for condition in filter_conditions[1:]:
                combined_filter = combined_filter | condition
            valid_df = valid_df[combined_filter]
        
        if not valid_df.empty:
            # Create separate best intervals for each period range
            for range_name, range_periods in period_ranges.items():
                # Filter columns for this range
                avg_return_cols = [f'avg_return_{period}' for period in range_periods if f'avg_return_{period}' in valid_df.columns]
                
                # Calculate min return and best period for this range (most negative is best for MC)
                range_df = valid_df.copy()
                range_df['min_return'] = range_df[avg_return_cols].min(axis=1)
                range_df['best_period'] = range_df[avg_return_cols].idxmin(axis=1).str.extract('(\d+)').astype(int)
                
                # Get row with lowest min_return for each ticker
                best_intervals = range_df.loc[range_df.groupby('ticker')['min_return'].idxmin()]
                
                # Select and rename columns
                best_intervals = best_intervals.assign(
                    test_count=best_intervals.apply(lambda x: x[f'test_count_{int(x.best_period)}'], axis=1),
                    success_rate=best_intervals.apply(lambda x: x[f'success_rate_{int(x.best_period)}'], axis=1),
                    avg_return=best_intervals['min_return']
                )
                
                # Keep all columns that are in mc_best_intervals_columns
                available_columns = [col for col in mc_best_intervals_columns if col in best_intervals.columns]
                best_intervals = best_intervals[available_columns].sort_values('latest_signal', ascending=False)
                
                # Calculate hold_time as interval * best_period
                best_intervals['hold_time'] = best_intervals.apply(
                    lambda row: format_hold_time(parse_interval_to_minutes(row['interval']) * row['best_period']), axis=1
                )
                
                # Reorder columns to put hold_time after interval
                final_columns = [col for col in mc_best_intervals_columns if col in best_intervals.columns]
                best_intervals = best_intervals[final_columns]
                best_intervals = best_intervals[best_intervals['avg_return'] <= -5]
                best_intervals = best_intervals[best_intervals['success_rate'] >= 50]
                best_intervals = best_intervals[best_intervals['current_period'] <= best_intervals['best_period']]
                
                # Round numeric columns to 3 decimal places to reduce file size
                for col in best_intervals.columns:
                    if best_intervals[col].dtype in ['float64', 'float32']:
                        best_intervals[col] = best_intervals[col].round(3)
                        
                best_intervals.to_csv(os.path.join(output_dir, f'mc_eval_best_intervals_{range_name}_{output_base}.csv'), index=False)

            # Good signals - all signals that meet criteria, sorted by date
            good_signals = valid_df.sort_values('latest_signal', ascending=False)
            
            # Calculate min return and best period for good signals
            avg_return_cols = [f'avg_return_{period}' for period in periods if f'avg_return_{period}' in good_signals.columns]
            good_signals['min_return'] = good_signals[avg_return_cols].min(axis=1)
            good_signals['best_period'] = good_signals[avg_return_cols].idxmin(axis=1).str.extract('(\d+)').astype(int)
            
            # Calculate hold_time as interval * best_period
            good_signals['hold_time'] = good_signals.apply(
                lambda row: format_hold_time(parse_interval_to_minutes(row['interval']) * row['best_period']), axis=1
            )
            
            # Calculate exp_return as the avg_return for the best_period
            good_signals['exp_return'] = good_signals.apply(
                lambda row: row[f'avg_return_{int(row.best_period)}'], axis=1
            )
            good_signals['test_count'] = good_signals.apply(
                lambda row: row[f'test_count_{int(row.best_period)}'], axis=1
            )
            good_signals['success_rate'] = good_signals.apply(
                lambda row: row[f'success_rate_{int(row.best_period)}'], axis=1
            )
            
            # Reorder columns to put hold_time after interval and exp_return after signal_count
            available_good_columns = [col for col in mc_good_signals_columns if col in good_signals.columns]
            good_signals = good_signals[available_good_columns]
            good_signals = good_signals[good_signals['success_rate'] >= 50]
            
            # Round numeric columns to 3 decimal places to reduce file size
            for col in good_signals.columns:
                if good_signals[col].dtype in ['float64', 'float32']:
                    good_signals[col] = good_signals[col].round(3)
            
            good_signals.to_csv(os.path.join(output_dir, f'mc_eval_good_signals_{output_base}.csv'), index=False)
        else:
            print("Not enough data to determine best MC intervals (need at least 2 tests)")
            # Create empty files with proper headers for each range
            for range_name in period_ranges.keys():
                empty_best_intervals = pd.DataFrame(columns=mc_best_intervals_columns)
                empty_best_intervals.to_csv(os.path.join(output_dir, f'mc_eval_best_intervals_{range_name}_{output_base}.csv'), index=False)
            
            # For good_signals, we need to include all the original columns plus hold_time after interval and exp_return after signal_count
            empty_good_signals = pd.DataFrame(columns=mc_good_signals_columns)
            empty_good_signals.to_csv(os.path.join(output_dir, f'mc_eval_good_signals_{output_base}.csv'), index=False)
            
        # Create a summary by interval (always create this if we have any MC results)
            agg_dict = {'signal_count': 'sum'}
            
            # Add aggregation for all periods dynamically
            for period in periods:
                if f'test_count_{period}' in df_mc_eval.columns:
                    agg_dict[f'test_count_{period}'] = 'sum'
                if f'success_rate_{period}' in df_mc_eval.columns:
                    agg_dict[f'success_rate_{period}'] = 'mean'
                if f'avg_return_{period}' in df_mc_eval.columns:
                    agg_dict[f'avg_return_{period}'] = 'mean'
                    
            interval_summary = df_mc_eval.groupby('interval').agg(agg_dict).reset_index()
            interval_summary.to_csv(os.path.join(output_dir, f'mc_eval_interval_summary_{output_base}.csv'), index=False)
    else:
        print("No MC evaluation results to save")
        # Create empty files with proper headers when no MC results at all
        empty_detailed_columns = ['ticker', 'interval', 'signal_count', 'latest_signal', 'latest_signal_price']
        
        # Add all period-specific columns
        for period in periods:
            empty_detailed_columns.extend([f'test_count_{period}', f'success_rate_{period}', f'avg_return_{period}'])
        
        empty_detailed_columns.extend(['max_return', 'min_return'])
        empty_detailed = pd.DataFrame(columns=empty_detailed_columns)
        empty_detailed.to_csv(os.path.join(output_dir, f'mc_eval_custom_detailed_{output_base}.csv'), index=False)
        
        # Create empty returns distribution file
        empty_returns = pd.DataFrame(columns=['ticker', 'interval', 'period', 'return', 'volume'])
        empty_returns.to_csv(os.path.join(output_dir, f'mc_eval_returns_distribution_{output_base}.csv'), index=False)
        
        # Create empty files with proper headers for each range
        for range_name in period_ranges.keys():
            empty_best_intervals = pd.DataFrame(columns=mc_best_intervals_columns)
            empty_best_intervals.to_csv(os.path.join(output_dir, f'mc_eval_best_intervals_{range_name}_{output_base}.csv'), index=False)
        
        empty_good_signals = pd.DataFrame(columns=mc_good_signals_columns)
        empty_good_signals.to_csv(os.path.join(output_dir, f'mc_eval_good_signals_{output_base}.csv'), index=False)
        
    print("All analyses completed successfully!")

    # Report failed tickers
    if failed_tickers:
        print("\n----------------------")
        print("Failed to process the following tickers:")
        print(", ".join(failed_tickers))
        print("----------------------\n")