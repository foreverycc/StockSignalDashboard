from get_1234 import get_1234_breakout_candidates
from get_5230 import get_5230_breakout_candidates

if __name__ == '__main__':
    print("get_1234_breakout_candidates")
    get_1234_breakout_candidates('/Users/foreverycc/git/stock_list/stocks_all_sel.txt')
    get_1234_breakout_candidates('/Users/foreverycc/git/stock_list/stocks_all.txt')
    
    print("get_5230_breakout_candidates")
    get_5230_breakout_candidates('/Users/foreverycc/git/stock_list/stocks_all_sel.txt')
    # get_5230_breakout_candidates('/Users/foreverycc/git/stock_list/stocks_all.txt')
    # get_5230_breakout_candidates('./data/stocks_custom.tab')
