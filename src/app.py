import streamlit as st
import pandas as pd
import os
import time
from stock_analyzer import analyze_stocks

# Set page configuration
st.set_page_config(
    page_title="Stock Analysis App",
    page_icon="📈",
    layout="wide"
)

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

# Create a 3-column layout for the top section
col1, col2, col3 = st.columns(3)

with col1:
    # Display stock list preview
    if selected_file:
        file_path = os.path.join('./data', selected_file)
        
        try:
            with open(file_path, 'r') as f:
                stocks = f.read().splitlines()
            st.write(f"Preview ({len(stocks)} stocks):")
            st.write(", ".join(stocks[:5]) + ("..." if len(stocks) > 5 else ""))
        except Exception as e:
            st.error(f"Error reading file: {e}")

with col2:
    # Analysis selection
    st.subheader("Analysis Options")
    
    # Keep the analysis type radio button for UI consistency
    # But we'll run all analyses regardless of selection
    analysis_type = st.radio(
        "Select Analysis Type (all will run)",
        ["1234, 5230, CD Signal Evaluation"],
        horizontal=True
    )

with col3:
    # Run analysis button (with some vertical spacing to align with other elements)
    st.write("")
    st.write("")
    if st.button("Run Analysis", use_container_width=True):
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
                
                # Run the consolidated analysis function
                analyze_stocks(file_path)
                
                progress_bar.progress(100)
                status_text.text("Analysis complete!")
                time.sleep(1)
                status_text.empty()
                progress_bar.empty()
                
                st.success(f"Analysis completed successfully!")
                
            except Exception as e:
                st.error(f"Error during analysis: {e}")

# Horizontal line to separate configuration from results
st.markdown("---")

# Results section header with stock list indicator
if selected_file:
    st.header(f"Results for: {selected_file}")
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

# Create two columns for the two table views
if selected_file:
    col_left, col_right = st.columns(2)

    # First table view with tabs 1-4 (left column)
    with col_left:
        st.subheader("Breakout Analysis")
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
                st.write(f"Showing 1234 breakout candidates from: {message}")
                
                # Add filtering options
                if 'ticker' in df.columns:
                    ticker_filter = st.text_input("Filter by ticker symbol:", key="ticker_filter_1234")
                    if ticker_filter:
                        df = df[df['ticker'].str.contains(ticker_filter, case=False)]
                
                # Add date filtering if available
                if 'date' in df.columns:
                    dates = sorted(df['date'].unique(), reverse=True)
                    selected_dates = st.multiselect("Filter by date:", dates, 
                                                   default=dates[:4] if len(dates) > 4 else dates,
                                                   key="date_filter_1234")
                    if selected_dates:
                        df = df[df['date'].isin(selected_dates)]
                
                # Display the dataframe
                st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)
            else:
                st.info("No 1234 breakout candidates found. Please run analysis first.")

        # Display 5230 breakout candidates
        with tab2:
            df, message = load_results('breakout_candidates_summary_5230_', selected_file, 'score')
            
            if df is not None and '5230' in message:
                st.write(f"Showing 5230 breakout candidates from: {message}")
                
                # Add filtering options
                if 'ticker' in df.columns:
                    ticker_filter = st.text_input("Filter by ticker symbol:", key="ticker_filter_5230")
                    if ticker_filter:
                        df = df[df['ticker'].str.contains(ticker_filter, case=False)]
                
                # Add date filtering if available
                if 'date' in df.columns:
                    dates = sorted(df['date'].unique(), reverse=True)
                    selected_dates = st.multiselect("Filter by date:", dates, 
                                                   default=dates[:4] if len(dates) > 4 else dates,
                                                   key="date_filter_5230")
                    if selected_dates:
                        df = df[df['date'].isin(selected_dates)]
                
                # Display the dataframe
                st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)
            else:
                st.info("No 5230 breakout candidates found. Please run analysis first.")

        # Display 1234 detailed results
        with tab3:
            df, message = load_results('breakout_candidates_details_1234_', selected_file, 'signal_date')
            
            if df is not None and '1234' in message:
                st.write(f"Showing 1234 detailed results from: {message}")
                
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
                st.write(f"Showing 5230 detailed results from: {message}")
                
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
    with col_right:
        st.subheader("Interval Analysis")
        tab1, tab2, tab3 = st.tabs(["Best Intervals", "High Return Intervals",  "Interval Details"])

    # Display best intervals
        with tab1:
            df, message = load_results('cd_eval_best_intervals_', selected_file, 'avg_return_10')
            
            if df is not None:
                st.write(f"Showing results from: {message}")
                
                # Add filtering options
                if 'ticker' in df.columns:
                    ticker_filter = st.text_input("Filter by ticker symbol:", key="ticker_filter_best")
                    if ticker_filter:
                        df = df[df['ticker'].str.contains(ticker_filter, case=False)]
                
                if 'interval' in df.columns:
                        intervals = sorted(df['interval'].unique())
                        selected_intervals = st.multiselect("Filter by interval:", intervals, default=intervals, key="interval_filter_best")
                        if selected_intervals:
                            df = df[df['interval'].isin(selected_intervals)]

                # Add sorting options
                # if not df.empty:
                #     sort_columns = df.columns.tolist()
                #     sort_by = st.selectbox("Sort by:", sort_columns, 
                #                           index=sort_columns.index('latest_signal') if 'latest_signal' in sort_columns else 0,
                #                           key="sort_by_best")
                #     sort_order = st.radio("Sort order:", ["Descending", "Ascending"], horizontal=True, key="sort_order_best")
                    
                #     df = df.sort_values(by=sort_by, ascending=(sort_order == "Ascending"))
                
                # Display the dataframe
                st.dataframe(df.sort_values(by='latest_signal', ascending=False), use_container_width=True)
            else:
                st.info("No best intervals data available. Please run CD Signal Evaluation first.")

        # Display recent signals
        with tab2:
            df, message = load_results('cd_eval_good_signals_', selected_file, 'latest_signal')
            
            if df is not None:
                # Filter for rows with recent signals (non-null latest_signal)
                if 'latest_signal' in df.columns:
                    df = df[df['latest_signal'].notna()]
                    df = df.sort_values(by='latest_signal', ascending=False)
                    
                    st.write(f"Showing recent signals from: {message}")
                    
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

        
        # Display cd eval details
        with tab3:
            df, message = load_results('cd_eval_custom_detailed_', selected_file, 'avg_return_10')
            
            if df is not None:
                st.write(f"Showing results from: {message}")

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