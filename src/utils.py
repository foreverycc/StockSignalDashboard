import pandas as pd
import os

def save_results(results, output_file):
    df = pd.DataFrame(results)
    if df.empty:
        print("No results to save")
        return
    df = df.sort_values(by=['signal_date', 'breakthrough_date', 'score', 'interval'], ascending=[False, False, False, False])
    
    # Include signal_price in the saved columns if it exists
    columns_to_save = ['ticker', 'interval', 'score', 'signal_date']
    if 'signal_price' in df.columns:
        columns_to_save.append('signal_price')
    columns_to_save.append('breakthrough_date')
    
    df.to_csv(output_file, sep='\t', index=False, columns=columns_to_save)

def save_breakout_candidates_1234(df, file_path):
    # Extract base name and directory from the input file path
    directory = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)
    output_path = os.path.join(directory, base_name).replace("details", "summary")
    
    # Handle empty DataFrame
    if df.empty:
        print("No 1234 breakout candidates to save")
        # Create empty file with headers
        empty_df = pd.DataFrame(columns=['ticker', 'date', 'intervals', 'signal_price', 'nx_1d'])
        empty_df.to_csv(output_path, sep='\t', index=False)
        return
    
    # Check which columns exist and save accordingly
    available_columns = ['ticker', 'date', 'intervals']
    if 'signal_price' in df.columns:
        available_columns.append('signal_price')
    if 'nx_1d' in df.columns:
        available_columns.append('nx_1d')
    
    df.to_csv(output_path, sep='\t', index=False, columns=available_columns)

def save_breakout_candidates_5230(df, file_path):
    # Extract base name and directory from the input file path
    directory = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)
    output_path = os.path.join(directory, base_name).replace("details", "summary")
    
    # Handle empty DataFrame
    if df.empty:
        print("No 5230 breakout candidates to save")
        # Create empty file with headers
        empty_df = pd.DataFrame(columns=['ticker', 'date', 'intervals', 'signal_price', 'nx_1h'])
        empty_df.to_csv(output_path, sep='\t', index=False)
        return
    
    # Check which columns exist and save accordingly
    available_columns = ['ticker', 'date', 'intervals']
    if 'signal_price' in df.columns:
        available_columns.append('signal_price')
    if 'nx_1h' in df.columns:
        available_columns.append('nx_1h')
    
    df.to_csv(output_path, sep='\t', index=False, columns=available_columns)
