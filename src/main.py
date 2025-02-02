from data_loader import load_stock_list
from processor import process_ticker
from utils import save_results
from multiprocessing import Pool, cpu_count

def main():
    # file_path = '/Users/foreverycc/git/stock_list/stocks_nasdaq100.txt'
    file_path = '/Users/foreverycc/git/stock_list/stocks_sp500.txt'
    # file_path = './data/stocks_custom.tab'
    # file_path = './data/stocks_custom2.tab'
    output_base = file_path.split('/')[-1].split('.')[0]
    stock_list = load_stock_list(file_path)
    
    # Use maximum number of available CPU cores minus 1 (to keep system responsive)
    num_processes = max(1, cpu_count() - 1)
    
    # Create a pool of worker processes
    with Pool(processes=num_processes) as pool:
        # Map the process_ticker function to all tickers in parallel
        results_list = pool.map(process_ticker, stock_list)
    
    # Flatten the list of results
    all_results = []
    for results in results_list:
        if results:  # Check if results is not None
            all_results.extend(results)
    
    save_results(all_results, f'output_{output_base}.tab')

if __name__ == '__main__':
    main()