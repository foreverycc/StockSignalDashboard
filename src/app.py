import streamlit as st
import pandas as pd
import os
import time
from stock_analyzer import analyze_stocks
import re

# Set page configuration
st.set_page_config(
    page_title="Stock Analysis App",
    page_icon="📈",
    layout="wide"
)

# Function to get Chinese stock name mapping
def get_chinese_stock_mapping():
    """Get mapping of Chinese stock codes to names using akshare."""
    mapping_file = './data/chinese_stocks_mapping.csv'
    
    # Check if the mapping file exists
    if os.path.exists(mapping_file):
        try:
            # Read from existing file
            df = pd.read_csv(mapping_file)
            mapping = {}
            for _, row in df.iterrows():
                code = str(row['code']).zfill(6)  # Ensure 6 digits with leading zeros
                name = row['name']
                # Add different formats that might be used
                mapping[code] = name
                mapping[f"{code}.SH"] = name  # Shanghai
                mapping[f"{code}.SZ"] = name  # Shenzhen
                mapping[f"{code}.SS"] = name  # Shanghai (alternative)
            
            return mapping
        except Exception as e:
            st.warning(f"Failed to read Chinese stock mapping file: {e}")
            return {}
    else:
        # File doesn't exist, fetch from akshare and save
        try:
            import akshare as ak
            df = ak.stock_info_a_code_name()
            
            # Save to file for future use
            os.makedirs('./data', exist_ok=True)
            df.to_csv(mapping_file, index=False)
            st.success(f"Chinese stock mapping saved to {mapping_file}")
            
            # Create a mapping dictionary: code -> name
            mapping = {}
            for _, row in df.iterrows():
                code = str(row['code']).zfill(6)  # Ensure 6 digits with leading zeros
                name = row['name']
                # Add different formats that might be used
                mapping[code] = name
                mapping[f"{code}.SH"] = name  # Shanghai
                mapping[f"{code}.SZ"] = name  # Shenzhen
                mapping[f"{code}.SS"] = name  # Shanghai (alternative)
            return mapping
        except Exception as e:
            st.warning(f"Failed to load Chinese stock names from akshare: {e}")
            return {}

def is_chinese_stock_code(ticker):
    """Check if a ticker is a Chinese stock code (starts with digits)."""
    if not isinstance(ticker, str):
        return False
    # Chinese stock codes typically start with digits and may have .SH/.SZ/.SS suffix
    pattern = r'^\d{6}(\.(SH|SZ|SS))?$'
    return bool(re.match(pattern, ticker))

def replace_chinese_tickers_in_df(df, chinese_mapping):
    """Replace Chinese ticker symbols with names in a dataframe."""
    if df is None or df.empty or 'ticker' not in df.columns:
        return df
    
    df_copy = df.copy()
    
    # Replace ticker symbols with names where applicable
    def replace_ticker(ticker):
        if is_chinese_stock_code(ticker) and ticker in chinese_mapping:
            return f"{chinese_mapping[ticker]} ({ticker})"
        return ticker
    
    df_copy['ticker'] = df_copy['ticker'].apply(replace_ticker)
    return df_copy

def update_output_files_with_chinese_names(chinese_mapping):
    """Update all output files with Chinese stock names."""
    output_dir = './output'
    if not os.path.exists(output_dir) or not chinese_mapping:
        return
    
    updated_files = []
    
    # Get all CSV and TAB files in output directory
    for filename in os.listdir(output_dir):
        if filename.endswith('.csv') or filename.endswith('.tab'):
            file_path = os.path.join(output_dir, filename)
            
            try:
                # Read the file
                if filename.endswith('.csv'):
                    df = pd.read_csv(file_path)
                else:  # .tab files
                    df = pd.read_csv(file_path, sep='\t')
                
                # Check if file has ticker column and Chinese stocks
                if 'ticker' in df.columns:
                    # Check if any Chinese stocks exist in this file
                    has_chinese_stocks = any(is_chinese_stock_code(ticker) for ticker in df['ticker'])
                    
                    if has_chinese_stocks:
                        # Check if names are already applied (avoid double processing)
                        has_names_already = any('(' in str(ticker) and ')' in str(ticker) 
                                               for ticker in df['ticker'] if pd.notna(ticker))
                        
                        if not has_names_already:
                            # Apply Chinese name mapping
                            df_updated = replace_chinese_tickers_in_df(df, chinese_mapping)
                            
                            # Save back to file
                            if filename.endswith('.csv'):
                                df_updated.to_csv(file_path, index=False)
                            else:  # .tab files
                                df_updated.to_csv(file_path, sep='\t', index=False)
                            
                            updated_files.append(filename)
                
            except Exception as e:
                st.warning(f"Error updating file {filename}: {e}")
    
    if updated_files:
        st.success(f"Updated {len(updated_files)} output files with Chinese stock names")
        with st.expander("Updated files:", expanded=False):
            for file in updated_files:
                st.write(f"- {file}")
    else:
        st.info("No output files required Chinese stock name updates")

# App title and description
# st.title("Stock Analysis Dashboard")
# st.markdown("""
# This app allows you to analyze stocks using various technical indicators and timeframes.
# Select a stock list and run the desired analysis to view results.
# """)

# Top configuration section (replaces sidebar)
# st.header("Configuration")

# Stock list selection (moved outside columns to make it globally available)
stock_list_files = [f for f in os.listdir('./data') if f.endswith('.tab') or f.endswith('.txt')]
selected_file = st.selectbox(
    "Select Stock List",
    stock_list_files,
    index=0 if stock_list_files else None
)

# Create a 2-column layout for the top section
col1, col2 = st.columns(2)

with col1:
    # Display and edit stock list
    if selected_file:
        file_path = os.path.join('./data', selected_file)
        
        try:
            with open(file_path, 'r') as f:
                original_stocks = f.read().strip()
            
            # Show basic info about the selected stock list
            current_stocks_list = original_stocks.strip().splitlines() if original_stocks.strip() else []
            # st.write(f"**Selected: {selected_file}**")
            st.write(f"📊 {len(current_stocks_list)} stocks")
            if current_stocks_list:
                st.write(f"Preview: {', '.join(current_stocks_list[:3])}{'...' if len(current_stocks_list) > 3 else ''}")
            
            # Expandable stock list management section
            with st.expander("📋 Manage Stock List", expanded=False):
                # Create tabs for stock list management
                tab_edit, tab_delete, tab_create = st.tabs(["✏️ Edit", "🗑️ Delete", "➕ Create New"])
                
                # Edit tab
                with tab_edit:
                    st.write(f"**Editing: {selected_file}**")
                    
                    # Handle temporary stocks from utility functions
                    if 'temp_stocks' in st.session_state:
                        display_stocks = st.session_state.temp_stocks
                        del st.session_state.temp_stocks
                    else:
                        display_stocks = original_stocks
                    
                    # Editable text area for stock list
                    edited_stocks = st.text_area(
                        "Stock symbols (one per line):",
                        value=display_stocks,
                        height=200,
                        help="Enter stock symbols, one per line. Changes will be saved when you click 'Save Changes'."
                    )
                    
                    # Save button and status
                    col_save, col_status = st.columns([1, 2])
                    
                    with col_save:
                        if st.button("Save Changes", type="primary"):
                            try:
                                # Save the edited content back to the file
                                with open(file_path, 'w') as f:
                                    f.write(edited_stocks.strip())
                                st.success("✅ Saved!")
                                # Force a rerun to refresh the preview
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error saving file: {e}")
                    
                    with col_status:
                        # Show if there are unsaved changes
                        if edited_stocks.strip() != original_stocks:
                            st.warning("⚠️ Unsaved changes")
                        else:
                            st.info("📄 No changes")
                    
                    # Utility buttons
                    col_util1, col_util2, col_util3 = st.columns(3)
                    
                    with col_util1:
                        if st.button("Remove Duplicates", help="Remove duplicate stock symbols"):
                            lines = edited_stocks.strip().splitlines()
                            unique_lines = list(dict.fromkeys([line.strip().upper() for line in lines if line.strip()]))
                            st.session_state.temp_stocks = '\n'.join(unique_lines)
                            st.rerun()
                    
                    with col_util2:
                        if st.button("Sort A-Z", help="Sort stock symbols alphabetically"):
                            lines = edited_stocks.strip().splitlines()
                            sorted_lines = sorted([line.strip().upper() for line in lines if line.strip()])
                            st.session_state.temp_stocks = '\n'.join(sorted_lines)
                            st.rerun()
                    
                    with col_util3:
                        if st.button("Validate Symbols", help="Check for invalid stock symbols"):
                            lines = edited_stocks.strip().splitlines()
                            invalid_symbols = []
                            valid_symbols = []
                            
                            for line in lines:
                                symbol = line.strip().upper()
                                if symbol:
                                    # Basic validation: should be 1-5 characters, letters only
                                    if len(symbol) >= 1 and len(symbol) <= 5 and symbol.isalpha():
                                        valid_symbols.append(symbol)
                                    else:
                                        invalid_symbols.append(symbol)
                            
                            if invalid_symbols:
                                st.warning(f"⚠️ Potentially invalid symbols: {', '.join(invalid_symbols)}")
                            else:
                                st.success("✅ All symbols appear valid")
                    
                    # Show preview of current stocks in editor
                    current_stocks = edited_stocks.strip().splitlines() if edited_stocks.strip() else []
                    if current_stocks:
                        st.write(f"**Preview ({len(current_stocks)} stocks):**")
                        st.write(", ".join(current_stocks[:5]) + ("..." if len(current_stocks) > 5 else ""))
                    else:
                        st.write("**Preview:** No stocks in list")
                
                # Delete tab
                with tab_delete:
                    st.warning(f"⚠️ This will permanently delete '{selected_file}'")
                    
                    # Confirmation checkbox
                    confirm_delete = st.checkbox(f"I confirm I want to delete '{selected_file}'")
                    
                    if st.button("Delete Stock List", type="secondary", disabled=not confirm_delete):
                        try:
                            os.remove(file_path)
                            st.success(f"✅ Deleted '{selected_file}' successfully!")
                            st.info("Please refresh the page to update the dropdown.")
                            # Clear the selection by rerunning
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting file: {e}")
                
                # Create new tab
                with tab_create:
                    new_file_name = st.text_input(
                        "New file name (without extension):",
                        placeholder="e.g., my_custom_stocks"
                    )
                    
                    new_file_extension = st.selectbox(
                        "File extension:",
                        [".tab", ".txt"],
                        index=0
                    )
                    
                    new_stocks_content = st.text_area(
                        "Stock symbols (one per line):",
                        placeholder="AAPL\nMSFT\nGOOGL\nTSLA",
                        height=150
                    )
                    
                    if st.button("Create Stock List", type="primary"):
                        if new_file_name and new_stocks_content:
                            try:
                                new_file_path = os.path.join('./data', f"{new_file_name}{new_file_extension}")
                                
                                # Check if file already exists
                                if os.path.exists(new_file_path):
                                    st.error(f"File '{new_file_name}{new_file_extension}' already exists!")
                                else:
                                    # Create the new file
                                    with open(new_file_path, 'w') as f:
                                        f.write(new_stocks_content.strip())
                                    
                                    st.success(f"✅ Created '{new_file_name}{new_file_extension}' successfully!")
                                    st.info("Please refresh the page to see the new file in the dropdown.")
                                    
                            except Exception as e:
                                st.error(f"Error creating file: {e}")
                        else:
                            st.error("Please provide both a file name and stock symbols.")
                
        except Exception as e:
            st.error(f"Error reading file: {e}")
    else:
        st.info("Select a stock list to edit")

with col2:
    # Analysis selection
    st.write("**Analysis Algorithms:**")
    
    # Keep the analysis type radio button for UI consistency
    # But we'll run all analyses regardless of selection
    # analysis_type = st.radio(       
    #     "Select Analysis Type (all will run)",
    #     ["1234, 5230, CD Signal Evaluation"],
    #     horizontal=True
    # )
    st.write("1234, 5230, CD Signal Evaluation")
    
    # Run analysis button
    if st.button("Run Analysis", use_container_width=True, type="primary"):
        if not selected_file:
            st.error("Please select a stock list file first.")
        else:
            file_path = os.path.join('./data', selected_file)
            
            # Show progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("Starting comprehensive analysis...")
                progress_bar.progress(25)
                
                # Check if the stock list file exists and is readable
                if not os.path.exists(file_path):
                    st.error(f"Stock list file not found: {file_path}")
                    progress_bar.empty()
                    status_text.empty()
                elif True:  # Continue with analysis
                    # Check if the file has content
                    with open(file_path, 'r') as f:
                        content = f.read().strip()
                        if not content:
                            st.error("Stock list file is empty.")
                            progress_bar.empty()
                            status_text.empty()
                        else:
                            stock_symbols = content.splitlines()
                            stock_symbols = [s.strip() for s in stock_symbols if s.strip()]
                            
                            if not stock_symbols:
                                st.error("No valid stock symbols found in the file.")
                                progress_bar.empty()
                                status_text.empty()
                            else:
                                status_text.text(f"Analyzing {len(stock_symbols)} stocks...")
                                progress_bar.progress(50)
                                
                                # Run the consolidated analysis function
                                analyze_stocks(file_path)
                                
                                progress_bar.progress(100)
                                status_text.text("Analysis complete!")
                                time.sleep(1)
                                status_text.empty()
                                progress_bar.empty()
                                
                                st.success(f"Analysis completed successfully for {len(stock_symbols)} stocks!")
                
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                
                # More detailed error reporting
                import traceback
                error_details = traceback.format_exc()
                
                st.error(f"Error during analysis: {str(e)}")
                
                # Show detailed error in an expander for debugging
                with st.expander("🔍 Error Details (for debugging)", expanded=False):
                    st.code(error_details, language="python")
                    
                    # Additional debugging info
                    st.write("**Debugging Information:**")
                    st.write(f"- Selected file: {selected_file}")
                    st.write(f"- File path: {file_path}")
                    st.write(f"- File exists: {os.path.exists(file_path)}")
                    
                    if os.path.exists(file_path):
                        try:
                            with open(file_path, 'r') as f:
                                content = f.read().strip()
                                lines = content.splitlines()
                                st.write(f"- File size: {len(content)} characters")
                                st.write(f"- Number of lines: {len(lines)}")
                                st.write(f"- First few symbols: {lines[:5] if lines else 'None'}")
                        except Exception as read_error:
                            st.write(f"- Error reading file: {read_error}")
                
                # Suggest solutions
                st.info("""
                **Possible solutions:**
                1. Check if the stock symbols in your list are valid
                2. Ensure you have internet connection for data download
                3. Try with a smaller stock list first
                4. Check if the stock symbols are properly formatted (one per line)
                """)


# Horizontal line to separate configuration from results
st.markdown("---")

# Function to get the latest update time for a stock list
def get_latest_update_time(stock_list_file):
    if not stock_list_file:
        return None
    
    output_dir = './output'
    if not os.path.exists(output_dir):
        return None
    
    # Extract stock list name from file (remove extension)
    stock_list_name = os.path.splitext(stock_list_file)[0]
    
    # Find all result files for this specific stock list (exact match)
    result_files = []
    for f in os.listdir(output_dir):
        if f.endswith('.csv') or f.endswith('.tab'):
            # Simple approach: check if the file ends with the stock list name + extension
            # This handles cases like "breakout_candidates_summary_1234_stocks_all.tab"
            base_name = f.rsplit('.', 1)[0]  # Remove file extension
            if base_name.endswith('_' + stock_list_name) or base_name == stock_list_name:
                result_files.append(f)
    
    if not result_files:
        return None
    
    # Get the most recent modification time
    latest_time = 0
    for file in result_files:
        file_path = os.path.join(output_dir, file)
        mod_time = os.path.getmtime(file_path)
        if mod_time > latest_time:
            latest_time = mod_time
    
    return latest_time

# Results section header with stock list indicator
if selected_file:
    latest_time = get_latest_update_time(selected_file)
    if latest_time:
        import datetime
        
        try:
            # Try to use pytz for PST conversion
            import pytz
            utc_time = datetime.datetime.fromtimestamp(latest_time, tz=pytz.UTC)
            pst_tz = pytz.timezone('US/Pacific')
            pst_time = utc_time.astimezone(pst_tz)
            formatted_time = pst_time.strftime("%Y-%m-%d %H:%M:%S PST")
        except ImportError:
            # Fallback: manually adjust for PST (UTC-8, or UTC-7 during DST)
            # This is a simple approximation
            utc_time = datetime.datetime.fromtimestamp(latest_time)
            pst_time = utc_time - datetime.timedelta(hours=8)  # Approximate PST
            formatted_time = pst_time.strftime("%Y-%m-%d %H:%M:%S PST")
        
        st.header(f"Results for: {selected_file} (Last updated: {formatted_time})")
    else:
        st.header(f"Results for: {selected_file} (No results found)")
else:
    st.header("Results")
    st.info("Please select a stock list to view corresponding results.")

# Function to load and display results
def load_results(file_pattern, stock_list_file=None, default_sort=None):
    # Look in output directory for result files
    output_dir = './output'
    if not os.path.exists(output_dir):
        return None, "No output directory found. Please run an analysis first."
    
    # Extract stock list name from file (remove extension)
    if stock_list_file:
        stock_list_name = os.path.splitext(stock_list_file)[0]
        # Look for files that match both the pattern and the stock list
        result_files = [f for f in os.listdir(output_dir) 
                       if f.startswith(file_pattern) and stock_list_name in f]
    else:
        # Fallback to original behavior if no stock list specified
        result_files = [f for f in os.listdir(output_dir) if f.startswith(file_pattern)]
    
    if not result_files:
        if stock_list_file:
            return None, f"No results found for stock list '{stock_list_file}'. Please run analysis first."
        else:
            return None, "No results found. Please run an analysis first."
    
    # Get the most recent file
    latest_file = max(result_files, key=lambda f: os.path.getctime(os.path.join(output_dir, f)))
    file_path = os.path.join(output_dir, latest_file)
    
    try:
        # Determine file type and load accordingly
        if latest_file.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:  # .tab files
            df = pd.read_csv(file_path, sep='\t')
            
        if default_sort and default_sort in df.columns:
            df = df.sort_values(by=default_sort, ascending=False)
            
        return df, latest_file
    except Exception as e:
        return None, f"Error loading results: {e}"

# Load Chinese stock mapping once for all tables
chinese_stock_mapping = get_chinese_stock_mapping() if selected_file else {}

# Update output files with Chinese names if mapping is available
if chinese_stock_mapping and selected_file:
    update_output_files_with_chinese_names(chinese_stock_mapping)

# Create two columns for the two table views
if selected_file:
    col_left, col_middle, col_right = st.columns([1, 2, 1])     

    # First table view with tabs 1-4 (left column)
    with col_left:
        st.subheader("Resonance Model")
        tab1, tab2, tab3, tab4 = st.tabs([
            "1234 Candidates", 
            "5230 Candidates", 
            "1234 Details", 
            "5230 Details"
        ])

        # Display 1234 breakout candidates
        with tab1:
            df, message = load_results('breakout_candidates_summary_1234_', selected_file, 'score')
            
            if df is not None and '1234' in message:
                # Add filtering options
                if 'ticker' in df.columns:
                    ticker_filter = st.text_input("Filter by ticker symbol:", key="ticker_filter_1234")
                    if ticker_filter:
                        df = df[df['ticker'].str.contains(ticker_filter, case=False)]
                
                # Add NX filtering if available
                if 'nx_1d' in df.columns:
                    nx_values = sorted(df['nx_1d'].unique())
                    selected_nx = st.multiselect("Filter by NX:", nx_values, 
                                               default=[True] if True in nx_values else nx_values,
                                               key="nx_filter_1234")
                    if selected_nx:
                        df = df[df['nx_1d'].isin(selected_nx)]
                
                # Display the dataframe
                st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)
            else:
                st.info("No 1234 breakout candidates found. Please run analysis first.")

        # Display 5230 breakout candidates
        with tab2:
            df, message = load_results('breakout_candidates_summary_5230_', selected_file, 'score')
            
            if df is not None and '5230' in message:
                # Add filtering options
                if 'ticker' in df.columns:
                    ticker_filter = st.text_input("Filter by ticker symbol:", key="ticker_filter_5230")
                    if ticker_filter:
                        df = df[df['ticker'].str.contains(ticker_filter, case=False)]
                
                # Add NX filtering if available
                if 'nx_1h' in df.columns:
                    nx_values = sorted(df['nx_1h'].unique())
                    selected_nx = st.multiselect("Filter by NX:", nx_values, 
                                               default=[True] if True in nx_values else nx_values,
                                               key="nx_filter_5230")
                    if selected_nx:
                        df = df[df['nx_1h'].isin(selected_nx)]
                
                # Display the dataframe
                st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)
            else:
                st.info("No 5230 breakout candidates found. Please run analysis first.")

        # Display 1234 detailed results
        with tab3:
            df, message = load_results('breakout_candidates_details_1234_', selected_file, 'signal_date')
            
            if df is not None and '1234' in message:
                # Add filtering options
                if 'ticker' in df.columns:
                    ticker_filter = st.text_input("Filter by ticker symbol:", key="ticker_filter_details_1234")
                    if ticker_filter:
                        df = df[df['ticker'].str.contains(ticker_filter, case=False)]
                
                if 'interval' in df.columns:
                    intervals = sorted(df['interval'].unique())
                    selected_intervals = st.multiselect("Filter by interval:", intervals, 
                                                       default=intervals,
                                                       key="interval_filter_1234")
                    if selected_intervals:
                        df = df[df['interval'].isin(selected_intervals)]
                
                # Display the dataframe
                st.dataframe(df.sort_values(by='signal_date', ascending=False), use_container_width=True)
                
                # Add download button
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Download filtered 1234 details as CSV",
                    csv,
                    "filtered_1234_details.csv",
                    "text/csv",
                    key='download-1234-csv'
                )
            else:
                st.info("No 1234 detailed results found. Please run analysis first.")

        # Display 5230 detailed results
        with tab4:
            df, message = load_results('breakout_candidates_details_5230_', selected_file, 'signal_date')
            
            if df is not None and '5230' in message:
                # Add filtering options
                if 'ticker' in df.columns:
                    ticker_filter = st.text_input("Filter by ticker symbol:", key="ticker_filter_details_5230")
                    if ticker_filter:
                        df = df[df['ticker'].str.contains(ticker_filter, case=False)]
                
                if 'interval' in df.columns:
                    intervals = sorted(df['interval'].unique())
                    selected_intervals = st.multiselect("Filter by interval:", intervals, 
                                                       default=intervals,
                                                       key="interval_filter_5230")
                    if selected_intervals:
                        df = df[df['interval'].isin(selected_intervals)]
                
                # Display the dataframe
                st.dataframe(df.sort_values(by='signal_date', ascending=False), use_container_width=True)
                
                # Add download button
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Download filtered 5230 details as CSV",
                    csv,
                    "filtered_5230_details.csv",
                    "text/csv",
                    key='download-5230-csv'
                )
            else:
                st.info("No 5230 detailed results found. Please run analysis first.")

    # Second table view with tabs 3-5 (right column)
    with col_middle:
        st.subheader("Waikiki Model")
        tabs = st.tabs([
            "Best Intervals (50)", 
            "Best Intervals (20)", 
            "Best Intervals (100)", 
            "High Return Intervals",
            "Interval Details"
        ])

        # Display best intervals (50)
        with tabs[0]:
            df, message = load_results('cd_eval_best_intervals_50_', selected_file, 'avg_return_10')
            
            if df is not None:
                # Add filtering options
                if 'ticker' in df.columns:
                    ticker_filter = st.text_input("Filter by ticker symbol:", key="ticker_filter_best_50")
                    if ticker_filter:
                        df = df[df['ticker'].str.contains(ticker_filter, case=False)]
                
                if 'interval' in df.columns:
                    intervals = sorted(df['interval'].unique())
                    selected_intervals = st.multiselect("Filter by interval:", intervals, default=intervals, key="interval_filter_best_50")
                    if selected_intervals:
                        df = df[df['interval'].isin(selected_intervals)]
                
                # Display the dataframe
                st.dataframe(df.sort_values(by='latest_signal', ascending=False), use_container_width=True)
            else:
                st.info("No best intervals data available for 50-period analysis. Please run CD Signal Evaluation first.")

        # Display best intervals (20)
        with tabs[1]:
            df, message = load_results('cd_eval_best_intervals_20_', selected_file, 'avg_return_10')
            
            if df is not None:
                # Add filtering options
                if 'ticker' in df.columns:
                    ticker_filter = st.text_input("Filter by ticker symbol:", key="ticker_filter_best_20")
                    if ticker_filter:
                        df = df[df['ticker'].str.contains(ticker_filter, case=False)]
                
                if 'interval' in df.columns:
                    intervals = sorted(df['interval'].unique())
                    selected_intervals = st.multiselect("Filter by interval:", intervals, default=intervals, key="interval_filter_best_20")
                    if selected_intervals:
                        df = df[df['interval'].isin(selected_intervals)]
                
                # Display the dataframe
                st.dataframe(df.sort_values(by='latest_signal', ascending=False), use_container_width=True)
            else:
                st.info("No best intervals data available for 20-period analysis. Please run CD Signal Evaluation first.")

        # Display best intervals (100)
        with tabs[2]:
            df, message = load_results('cd_eval_best_intervals_100_', selected_file, 'avg_return_10')
            
            if df is not None:
                # Add filtering options
                if 'ticker' in df.columns:
                    ticker_filter = st.text_input("Filter by ticker symbol:", key="ticker_filter_best_100")
                    if ticker_filter:
                        df = df[df['ticker'].str.contains(ticker_filter, case=False)]
                
                if 'interval' in df.columns:
                    intervals = sorted(df['interval'].unique())
                    selected_intervals = st.multiselect("Filter by interval:", intervals, default=intervals, key="interval_filter_best_100")
                    if selected_intervals:
                        df = df[df['interval'].isin(selected_intervals)]
                
                # Display the dataframe
                st.dataframe(df.sort_values(by='latest_signal', ascending=False), use_container_width=True)
            else:
                st.info("No best intervals data available for 100-period analysis. Please run CD Signal Evaluation first.")

        # Display high return intervals
        with tabs[3]:
            df, message = load_results('cd_eval_good_signals_', selected_file, 'latest_signal')
            
            if df is not None:
                # Filter for rows with recent signals (non-null latest_signal)
                if 'latest_signal' in df.columns:
                    df = df[df['latest_signal'].notna()]
                    df = df.sort_values(by='latest_signal', ascending=False)
                    
                    # Add filtering options
                    if 'ticker' in df.columns:
                        ticker_filter = st.text_input("Filter by ticker symbol:", key="ticker_filter_recent")
                        if ticker_filter:
                            df = df[df['ticker'].str.contains(ticker_filter, case=False)]
                    
                    if 'interval' in df.columns:
                        intervals = sorted(df['interval'].unique())
                        selected_intervals = st.multiselect("Filter by interval:", intervals, default=intervals, key="interval_filter_recent")
                        if selected_intervals:
                            df = df[df['interval'].isin(selected_intervals)]
                    
                    # Display the dataframe
                    st.dataframe(df.sort_values(by='latest_signal', ascending=False), use_container_width=True)
                else:
                    st.info("No signal date information available in the results.")
            else:
                st.info("No recent signals data available. Please run an analysis first.")

        # Display interval details
        with tabs[4]:
            df, message = load_results('cd_eval_custom_detailed_', selected_file, 'avg_return_10')
            
            if df is not None:
                # Add filtering options
                if 'ticker' in df.columns:
                    ticker_filter = st.text_input("Filter by ticker symbol:", key="ticker_filter_details")
                    if ticker_filter:
                        df = df[df['ticker'].str.contains(ticker_filter, case=False)]
                
                if 'interval' in df.columns:
                    intervals = sorted(df['interval'].unique())
                    selected_intervals = st.multiselect("Filter by interval:", intervals, default=intervals, key="interval_filter_details")
                    if selected_intervals:
                        df = df[df['interval'].isin(selected_intervals)]

                # Add sorting options
                # if not df.empty:
                #     sort_columns = df.columns.tolist()
                #     sort_by = st.selectbox("Sort by:", sort_columns, 
                #                           index=sort_columns.index('avg_return_10') if 'avg_return_10' in sort_columns else 0,
                #                           key="sort_by_summary")
                #     sort_order = st.radio("Sort order:", ["Descending", "Ascending"], horizontal=True, key="sort_order_summary")
                    
                #     df = df.sort_values(by=sort_by, ascending=(sort_order == "Ascending"))
                
                # Display the dataframe
                st.dataframe(df.sort_values(by = "latest_signal", ascending = False), use_container_width=True)
            else:
                st.info("No interval summary data available. Please run CD Signal Evaluation first.")
else:
    st.info("👆 Please select a stock list above to view results.")

# Footer
st.markdown("---")
st.markdown("Stock Analysis Dashboard | Created with Streamlit") 