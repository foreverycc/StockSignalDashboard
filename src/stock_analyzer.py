import pandas as pd
import os
from data_loader import load_stock_list, download_stock_data
from processor import process_ticker_1234, process_ticker_5230
from utils import save_results, identify_1234, save_breakout_candidates_1234, identify_5230, save_breakout_candidates_5230
from get_best_CD_interval import evaluate_interval
from multiprocessing import Pool, cpu_count

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
def process_ticker_all(ticker):
    """Process a single ticker for all analysis types"""
    try:
        print(f"Processing {ticker}")
        # Download data once for all analyses
        data = download_stock_data(ticker)
        
        # Skip if no data available
        if all(df.empty for df in data.values()):
            print(f"No data available for {ticker}")
            return None, None, []
        
        # Process for 1234 breakout
        results_1234 = process_ticker_1234(ticker, data)
        
        # Process for 5230 breakout
        results_5230 = process_ticker_5230(ticker, data)
        
        # Process for CD signal evaluation
        cd_results = []
        intervals = ['5m', '10m', '15m', '30m', '1h', '2h', '3h', '4h', '1d', '1w']
        for interval in intervals:
            result = evaluate_interval(ticker, interval, data=data)
            if result:
                cd_results.append(result)
        
        return results_1234, results_5230, cd_results
        
    except Exception as e:
        print(f"Error processing {ticker}: {e}")
        return None, None, []

def analyze_stocks(file_path):
    """
    Comprehensive stock analysis function that performs all three types of analysis:
    - 1234 Breakout candidates
    - 5230 Breakout candidates
    - CD Signal Evaluation
    
    Args:
        file_path: Path to the file containing stock ticker symbols
    
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
    cd_eval_results = []
    best_intervals_columns = ['ticker', 'interval', 'hold_time',  
                              'avg_return', 'latest_signal', 'latest_signal_price', 
                              'current_time', 'current_price', 'current_period',
                              'test_count', 'success_rate', 'best_period', 'signal_count']
    # Define all periods for dynamic handling
    periods = [3, 5, 10, 15, 20, 25, 30, 40, 50, 60, 80, 100]
    
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
                            'test_count', 'success_rate', 'best_period', 'signal_count']
    
    # Add all period-specific columns
    for period in periods:
        good_signals_columns.extend([f'test_count_{period}', f'success_rate_{period}', f'avg_return_{period}'])
    
    good_signals_columns.extend(['max_return', 'min_return'])

    for i in range(0, len(stock_list), batch_size):
        batch = stock_list[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(stock_list) + batch_size - 1)//batch_size}: {batch}")
        
        # Process the batch with multiprocessing
        with Pool(processes=num_processes) as pool:
            batch_results = pool.map(process_ticker_all, batch)
        
        # Collect results from batch
        for r1234, r5230, cd_eval in batch_results:
            if r1234:
                results_1234.extend(r1234)
            if r5230:
                results_5230.extend(r5230)
            if cd_eval:
                cd_eval_results.extend(cd_eval)
    
    # 1. Save 1234 results and identify breakout candidates
    print("Saving 1234 breakout results...")
    output_file_1234 = os.path.join(output_dir, f'breakout_candidates_details_1234_{output_base}.tab')
    save_results(results_1234, output_file_1234)
    df_breakout_1234 = identify_1234(output_file_1234)
    save_breakout_candidates_1234(df_breakout_1234, output_file_1234)
    
    # 2. Save 5230 results and identify breakout candidates
    print("Saving 5230 breakout results...")
    output_file_5230 = os.path.join(output_dir, f'breakout_candidates_details_5230_{output_base}.tab')
    save_results(results_5230, output_file_5230)
    df_breakout_5230 = identify_5230(output_file_5230)
    save_breakout_candidates_5230(df_breakout_5230, output_file_5230)
    
    # 3. Save CD evaluation results
    print("Saving CD evaluation results...")
    # Convert CD evaluation results to DataFrame
    if cd_eval_results:
        df_cd_eval = pd.DataFrame(cd_eval_results)
        
        # Save detailed results with ticker information
        df_cd_eval.to_csv(os.path.join(output_dir, f'cd_eval_custom_detailed_{output_base}.csv'), index=False)

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
                )[['ticker', 'interval', 'signal_count', 'latest_signal', 'latest_signal_price', 
                   'current_time', 'current_price', 'current_period',
                   'test_count', 'success_rate', 'best_period', 'avg_return']].sort_values('latest_signal', ascending=False)
                
                # Calculate hold_time as interval * best_period
                best_intervals['hold_time'] = best_intervals.apply(
                    lambda row: format_hold_time(parse_interval_to_minutes(row['interval']) * row['best_period']), axis=1
                )
                
                # Reorder columns to put hold_time after interval
                best_intervals = best_intervals[best_intervals_columns]
                best_intervals = best_intervals[best_intervals['avg_return'] >= 5]
                best_intervals = best_intervals[best_intervals['success_rate'] >= 50]
                best_intervals = best_intervals[best_intervals['current_period'] <= best_intervals['best_period']]
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
            good_signals = good_signals[good_signals_columns]
            good_signals = good_signals[good_signals['success_rate'] >= 50]
            
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
        
        empty_detailed_columns.extend(['max_return', 'min_return'])
        empty_detailed = pd.DataFrame(columns=empty_detailed_columns)
        empty_detailed.to_csv(os.path.join(output_dir, f'cd_eval_custom_detailed_{output_base}.csv'), index=False)
        
        # Create empty files with proper headers for each range
        for range_name in period_ranges.keys():
            empty_best_intervals = pd.DataFrame(columns=best_intervals_columns)
            empty_best_intervals.to_csv(os.path.join(output_dir, f'cd_eval_best_intervals_{range_name}_{output_base}.csv'), index=False)
        
        empty_good_signals = pd.DataFrame(columns=good_signals_columns)
        empty_good_signals.to_csv(os.path.join(output_dir, f'cd_eval_good_signals_{output_base}.csv'), index=False)
        
    print("All analyses completed successfully!")