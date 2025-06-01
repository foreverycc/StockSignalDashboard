import pandas as pd
import os
from data_loader import load_stock_list, download_stock_data
from processor import process_ticker_1234, process_ticker_5230
from utils import save_results, identify_1234, save_breakout_candidates_1234, identify_5230, save_breakout_candidates_5230
from get_best_CD_interval import evaluate_interval
from multiprocessing import Pool, cpu_count

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
    num_processes = max(1, cpu_count() - 1)
    print(f"Using {num_processes} processes for analysis")
    
    # Process stocks in batches to avoid memory issues
    batch_size = 50
    results_1234 = []
    results_5230 = []
    cd_eval_results = []
    
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
        valid_df = valid_df[(valid_df['avg_return_3'] >= 5) | (valid_df['avg_return_5'] >=5 ) | 
                            (valid_df['avg_return_10'] >= 5) | (valid_df['avg_return_20'] >= 5)]
        
        if not valid_df.empty:
            # Find max return across all time periods for each ticker/interval combination
            valid_df['max_return'] = valid_df[['avg_return_3', 'avg_return_5', 'avg_return_10', 'avg_return_20', 'avg_return_50']].max(axis=1)
            valid_df['best_period'] = valid_df[['avg_return_3', 'avg_return_5', 'avg_return_10', 'avg_return_20', 'avg_return_50']].idxmax(axis=1).str.extract('(\d+)').astype(int)
            
            # Get row with highest max_return for each ticker
            best_intervals = valid_df.loc[valid_df.groupby('ticker')['max_return'].idxmax()]
            
            # Select and rename columns
            best_intervals = best_intervals.assign(
                test_count=best_intervals.apply(lambda x: x[f'test_count_{int(x.best_period)}'], axis=1),
                success_rate=best_intervals.apply(lambda x: x[f'success_rate_{int(x.best_period)}'], axis=1),
                avg_return=best_intervals['max_return']
            )[['ticker', 'interval', 'signal_count', 'latest_signal', 'latest_signal_price', 'test_count', 
               'success_rate', 'best_period', 'avg_return']].sort_values('latest_signal', ascending=False)
            
            best_intervals.to_csv(os.path.join(output_dir, f'cd_eval_best_intervals_{output_base}.csv'), index=False)

            # Good signals - all signals that meet criteria, sorted by date
            good_signals = valid_df.sort_values('latest_signal', ascending=False)
            good_signals.to_csv(os.path.join(output_dir, f'cd_eval_good_signals_{output_base}.csv'), index=False)
        else:
            print("Not enough data to determine best intervals (need at least 2 tests)")
            # Create empty files with proper headers
            empty_best_intervals = pd.DataFrame(columns=['ticker', 'interval', 'signal_count', 'latest_signal', 'latest_signal_price', 'test_count', 'success_rate', 'best_period', 'avg_return'])
            empty_best_intervals.to_csv(os.path.join(output_dir, f'cd_eval_best_intervals_{output_base}.csv'), index=False)
            
            empty_good_signals = pd.DataFrame(columns=df_cd_eval.columns.tolist() + ['max_return', 'best_period'])
            empty_good_signals.to_csv(os.path.join(output_dir, f'cd_eval_good_signals_{output_base}.csv'), index=False)
            
        # Create a summary by interval (always create this if we have any CD results)
            interval_summary = df_cd_eval.groupby('interval').agg({
                'signal_count': 'sum',
                'test_count_3': 'sum',
                'test_count_5': 'sum',
                'test_count_10': 'sum',
                'test_count_20': 'sum',
                'success_rate_3': 'mean',
                'success_rate_5': 'mean',
                'success_rate_10': 'mean',
                'success_rate_20': 'mean',
                'avg_return_3': 'mean',
                'avg_return_5': 'mean',
                'avg_return_10': 'mean',
                'avg_return_20': 'mean'
            }).reset_index()
            
            interval_summary.to_csv(os.path.join(output_dir, f'cd_eval_interval_summary_{output_base}.csv'), index=False)
    else:
        print("No CD evaluation results to save")
        # Create empty files with proper headers when no CD results at all
        empty_detailed = pd.DataFrame(columns=['ticker', 'interval', 'signal_count', 'latest_signal', 'latest_signal_price', 'test_count_3', 'test_count_5', 'test_count_10', 'test_count_20', 'test_count_50', 'success_rate_3', 'success_rate_5', 'success_rate_10', 'success_rate_20', 'success_rate_50', 'avg_return_3', 'avg_return_5', 'avg_return_10', 'avg_return_20', 'avg_return_50', 'max_return', 'min_return'])
        empty_detailed.to_csv(os.path.join(output_dir, f'cd_eval_custom_detailed_{output_base}.csv'), index=False)
        
        empty_best_intervals = pd.DataFrame(columns=['ticker', 'interval', 'signal_count', 'latest_signal', 'latest_signal_price', 'test_count', 'success_rate', 'best_period', 'avg_return'])
        empty_best_intervals.to_csv(os.path.join(output_dir, f'cd_eval_best_intervals_{output_base}.csv'), index=False)
        
        empty_good_signals = pd.DataFrame(columns=['ticker', 'interval', 'signal_count', 'latest_signal', 'latest_signal_price', 'test_count_3', 'test_count_5', 'test_count_10', 'test_count_20', 'test_count_50', 'success_rate_3', 'success_rate_5', 'success_rate_10', 'success_rate_20', 'success_rate_50', 'avg_return_3', 'avg_return_5', 'avg_return_10', 'avg_return_20', 'avg_return_50', 'max_return', 'min_return', 'best_period'])
        empty_good_signals.to_csv(os.path.join(output_dir, f'cd_eval_good_signals_{output_base}.csv'), index=False)
        
        empty_interval_summary = pd.DataFrame(columns=['interval', 'signal_count', 'test_count_3', 'test_count_5', 'test_count_10', 'test_count_20', 'success_rate_3', 'success_rate_5', 'success_rate_10', 'success_rate_20', 'avg_return_3', 'avg_return_5', 'avg_return_10', 'avg_return_20'])
        empty_interval_summary.to_csv(os.path.join(output_dir, f'cd_eval_interval_summary_{output_base}.csv'), index=False)
    
    print("All analyses completed successfully!")