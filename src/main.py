from get_1234 import get_1234_breakout_candidates
from get_5230 import get_5230_breakout_candidates
from get_best_CD_interval import evaluate_cd_signals

if __name__ == '__main__':
    print("get_1234_breakout_candidates")
    # get_1234_breakout_candidates('/Users/foreverycc/git/stock_list/stocks_all_sel.txt')
    # get_1234_breakout_candidates('/Users/foreverycc/git/stock_list/stocks_all.txt')
    # get_1234_breakout_candidates('./data/stocks_custom.tab')
    
    print("get_5230_breakout_candidates")
    # get_5230_breakout_candidates('/Users/foreverycc/git/stock_list/stocks_all_sel.txt')
    # get_5230_breakout_candidates('/Users/foreverycc/git/stock_list/stocks_all.txt')
    # get_5230_breakout_candidates('./data/stocks_custom.tab')

    print("get_best_CD_interval")
    evaluate_cd_signals('/Users/foreverycc/git/stock_list/stocks_all_sel.txt')
    # evaluate_cd_signals('/Users/foreverycc/git/stock_list/stocks_all.txt')
    # evaluate_cd_signals('./data/stocks_custom.tab')
