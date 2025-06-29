import pandas as pd
import os
from database_manager import db_manager

def save_results(results, output_file):
    """
    Save results to both database and file for compatibility.
    """
    # Save to database
    analysis_type = _extract_analysis_type_from_path(output_file)
    list_name = _extract_list_name_from_path(output_file)
    
    if analysis_type and list_name and results:
        db_manager.save_analysis_results(analysis_type, list_name, results)
        print(f"Saved {len(results)} results to database (type: {analysis_type}, list: {list_name})")
    
    # Save to file for backward compatibility
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
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df.to_csv(output_file, sep='\t', index=False, columns=columns_to_save)

def _extract_analysis_type_from_path(file_path: str) -> str:
    """Extract analysis type from file path."""
    filename = os.path.basename(file_path)
    if '1234' in filename:
        return '1234'
    elif '5230' in filename:
        return '5230'
    elif 'cd_eval' in filename:
        return 'cd_eval'
    return 'unknown'

def _extract_list_name_from_path(file_path: str) -> str:
    """Extract list name from file path."""
    filename = os.path.basename(file_path)
    # Remove file extension
    name_part = os.path.splitext(filename)[0]
    
    # Extract the list name (usually the last part after the last underscore)
    parts = name_part.split('_')
    if len(parts) > 1:
        return parts[-1]
    return name_part

def save_breakout_candidates_1234(df, file_path):
    # Extract base name and directory from the input file path
    directory = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)
    output_path = os.path.join(directory, base_name).replace("details", "summary")
    
    # Save to database
    list_name = _extract_list_name_from_path(file_path)
    if not df.empty and list_name:
        _save_breakout_candidates_to_db(df, list_name, '1234')
    
    # Handle empty DataFrame
    if df.empty:
        print("No 1234 breakout candidates to save")
        # Create empty file with headers
        empty_df = pd.DataFrame(columns=['ticker', 'date', 'intervals', 'signal_price', 'current_price', 'current_time', 'nx_1d', 'nx_30m'])
        empty_df.to_csv(output_path, sep='\t', index=False)
        return
    
    # Check which columns exist and save accordingly
    available_columns = ['ticker', 'date', 'intervals']
    if 'signal_price' in df.columns:
        available_columns.append('signal_price')
    if 'current_price' in df.columns:
        available_columns.append('current_price')
    if 'current_time' in df.columns:
        available_columns.append('current_time')
    if 'nx_1d' in df.columns:
        available_columns.append('nx_1d')
    if 'nx_30m' in df.columns:
        available_columns.append('nx_30m')
    
    df.to_csv(output_path, sep='\t', index=False, columns=available_columns)

def save_breakout_candidates_5230(df, file_path):
    # Extract base name and directory from the input file path
    directory = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)
    output_path = os.path.join(directory, base_name).replace("details", "summary")
    
    # Save to database
    list_name = _extract_list_name_from_path(file_path)
    if not df.empty and list_name:
        _save_breakout_candidates_to_db(df, list_name, '5230')
    
    # Handle empty DataFrame
    if df.empty:
        print("No 5230 breakout candidates to save")
        # Create empty file with headers
        empty_df = pd.DataFrame(columns=['ticker', 'date', 'intervals', 'signal_price', 'current_price', 'current_time', 'nx_1h'])
        empty_df.to_csv(output_path, sep='\t', index=False)
        return
    
    # Check which columns exist and save accordingly
    available_columns = ['ticker', 'date', 'intervals']
    if 'signal_price' in df.columns:
        available_columns.append('signal_price')
    if 'current_price' in df.columns:
        available_columns.append('current_price')
    if 'current_time' in df.columns:
        available_columns.append('current_time')
    if 'nx_1h' in df.columns:
        available_columns.append('nx_1h')
    
    df.to_csv(output_path, sep='\t', index=False, columns=available_columns)

def _save_breakout_candidates_to_db(df, list_name: str, analysis_type: str):
    """Helper function to save breakout candidates to database."""
    try:
        with db_manager.get_connection() as conn:
            # Get version number for this list
            cursor = conn.execute(
                "SELECT COALESCE(MAX(version), 1) FROM stock_lists WHERE list_name = ? AND is_active = 1",
                (list_name,)
            )
            version = cursor.fetchone()[0]
            
            # Clear existing breakout candidates for this list/version/type
            conn.execute(
                "DELETE FROM breakout_candidates WHERE list_name = ? AND version = ? AND analysis_type = ?",
                (list_name, version, analysis_type)
            )
            
            # Save new breakout candidates
            for _, row in df.iterrows():
                # Convert values to ensure compatibility with SQLite
                def safe_convert(value, convert_func, default=None):
                    try:
                        if value is None or (hasattr(value, '__len__') and len(str(value).strip()) == 0):
                            return default
                        return convert_func(value)
                    except (ValueError, TypeError):
                        return default
                
                conn.execute("""
                    INSERT INTO breakout_candidates 
                    (analysis_type, list_name, version, ticker, date, intervals, signal_price, 
                     current_price, current_time, nx_1d, nx_30m, nx_1h)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    analysis_type, list_name, version,
                    str(row.get('ticker', '')), str(row.get('date', '')), str(row.get('intervals', '')),
                    safe_convert(row.get('signal_price'), float, None), 
                    safe_convert(row.get('current_price'), float, None),
                    str(row.get('current_time', '')), 
                    safe_convert(row.get('nx_1d'), bool, None),
                    safe_convert(row.get('nx_30m'), bool, None), 
                    safe_convert(row.get('nx_1h'), bool, None)
                ))
            
            conn.commit()
            print(f"Saved {len(df)} breakout candidates to database (type: {analysis_type}, list: {list_name})")
            
    except Exception as e:
        print(f"Error saving breakout candidates to database: {e}")
        import traceback
        traceback.print_exc()
