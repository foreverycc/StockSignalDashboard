from data_loader import load_stock_list
from processor import process_ticker
from utils import save_results

def main():
    # stock_list = load_stock_list('./data/stocks_custom2.tab')
    # stock_list = load_stock_list('/Users/foreverycc/git/stock_list/stocks_all_interesting.txt')
    # stock_list = load_stock_list('/Users/foreverycc/git/stock_list/stocks_nasdaq100.txt')
    stock_list = load_stock_list('./data/stocks_custom.tab')
    all_results = []
    
    for ticker in stock_list:
        print(f"Processing {ticker}...")
        results = process_ticker(ticker)
        print(results)
        all_results.extend(results)
    
    save_results(all_results, 'output2.tab')

if __name__ == '__main__':
    main()