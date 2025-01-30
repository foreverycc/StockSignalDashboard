import pandas as pd

def save_results(results, output_file):
    df = pd.DataFrame(results)
    if df.empty:
        print("No results to save")
        return
    df = df.sort_values(by=['signal_date', 'breakthrough_date', 'score', 'interval'], ascending=[False, False, False, False])
    df.to_csv(output_file, sep='\t', index=False, columns=['ticker', 'interval', 'score', 'signal_date', 'breakthrough_date'])