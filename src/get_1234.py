from data_loader import load_stock_list
from processor import process_ticker_1234
from utils import save_results, identify_1234, save_breakout_candidates_1234
from multiprocessing import Pool, cpu_count

def get_1234_breakout_candidates(file_path):
    # file_path = '/Users/foreverycc/git/stock_list/stocks_nasdaq100.txt'
    # file_path = '/Users/foreverycc/git/stock_list/stocks_sp500.txt'
    # file_path = '/Users/foreverycc/git/stock_list/stocks_all.txt'
    # file_path = '/Users/foreverycc/git/stock_list/stocks_all_sel.txt'
    # file_path = './data/stocks_custom.tab'
    # file_path = './data/stocks_custom2.tab'
    # file_path = './data/stocks_test.tab'

    output_base = file_path.split('/')[-1].split('.')[0]
    stock_list = load_stock_list(file_path)
    
    # Use maximum number of available CPU cores minus 1 (to keep system responsive)
    num_processes = max(1, cpu_count() - 1)
    
    # break into batches
    results_list = []
    batch_size = 50
    for i in range(0, len(stock_list), batch_size):
        batch = stock_list[i:i+batch_size]
        # Create a pool of worker processes
        with Pool(processes=num_processes) as pool:
            # Map the process_ticker function to all tickers in parallel
            results_list.extend(pool.map(process_ticker_1234, batch))

    ## Test single process
    # results_list = []
    # for ticker in stock_list:
    #     results = process_ticker(ticker)
    #     if results:
    #         results_list.append(results)
    
    # Flatten the list of results
    all_results = []
    for results in results_list:
        if results:  # Check if results is not None
            all_results.extend(results) 
    
    save_results(all_results, f'output_{output_base}.1234.tab')

    # identify 1234
    df_breakout_candidates =  identify_1234(f'output_{output_base}.1234.tab')
    print("breakout_candidates:", df_breakout_candidates)
    save_breakout_candidates_1234(df_breakout_candidates, f'output_{output_base}.1234.tab')
