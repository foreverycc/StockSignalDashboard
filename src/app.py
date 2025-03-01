import streamlit as st
import pandas as pd
import os
import time
from get_1234 import get_1234_breakout_candidates
from get_5230 import get_5230_breakout_candidates
from get_best_CD_interval import evaluate_cd_signals

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

# Create a 3-column layout for the top section
col1, col2, col3 = st.columns(3)

with col1:
    # Stock list selection
    stock_list_files = [f for f in os.listdir('./data') if f.endswith('.tab') or f.endswith('.txt')]
    selected_file = st.selectbox(
        "Select Stock List",
        stock_list_files,
        index=0 if stock_list_files else None
    )

    if selected_file:
        file_path = os.path.join('./data', selected_file)
        
        # Display stock list preview
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
    analysis_type = st.radio(
        "Select Analysis Type",
        ["1234 Breakout", "5230 Breakout", "CD Signal Evaluation"],
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
                status_text.text("Starting analysis...")
                
                # Run the selected analysis
                if analysis_type == "1234 Breakout":
                    status_text.text("Running 1234 Breakout analysis...")
                    get_1234_breakout_candidates(file_path)
                    output_base = selected_file.split('.')[0]
                    result_file = f'breakout_candidates_output_{output_base}.1234.tab'
                    
                elif analysis_type == "5230 Breakout":
                    status_text.text("Running 5230 Breakout analysis...")
                    get_5230_breakout_candidates(file_path)
                    output_base = selected_file.split('.')[0]
                    result_file = f'breakout_candidates_output_{output_base}.5230.tab'
                    
                else:  # CD Signal Evaluation
                    status_text.text("Evaluating CD signals...")
                    evaluate_cd_signals(file_path)
                    output_base = selected_file.split('.')[0]
                    result_file = f'cd_eval_custom_detailed_{output_base}.csv'
                
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

# Function to load and display results
def load_results(file_pattern, default_sort=None):
    result_files = [f for f in os.listdir('.') if f.startswith(file_pattern)]
    
    if not result_files:
        return None, "No results found. Please run an analysis first."
    
    # Get the most recent file
    latest_file = max(result_files, key=os.path.getctime)
    
    try:
        # Determine file type and load accordingly
        if latest_file.endswith('.csv'):
            df = pd.read_csv(latest_file)
        else:  # .tab files
            df = pd.read_csv(latest_file, sep='\t')
            
        if default_sort and default_sort in df.columns:
            df = df.sort_values(by=default_sort, ascending=False)
            
        return df, latest_file
    except Exception as e:
        return None, f"Error loading results: {e}"

# Results section
# st.header("Results")

# Create two columns for the two table views
col_left, col_right = st.columns(2)

# First table view with tabs 1-2 (left column)
with col_left:
    st.subheader("Breakout Analysis")
    tab1, tab2 = st.tabs(["Breakout Candidates", "Detailed Results"])

    # Display breakout candidates
    with tab1:
        # Determine which breakout type to show based on analysis type
        breakout_pattern = "breakout_candidates_"
        
        df, message = load_results(breakout_pattern)
        
        if df is not None:
            st.write(f"Showing breakout candidates from: {message}")
            
            # Add filtering options
            if 'ticker' in df.columns:
                ticker_filter = st.text_input("Filter by ticker symbol:", key="ticker_filter_breakout")
                if ticker_filter:
                    df = df[df['ticker'].str.contains(ticker_filter, case=False)]
            
            # Add date filtering if available
            if 'date' in df.columns:
                dates = sorted(df['date'].unique(), reverse=True)
                selected_dates = st.multiselect("Filter by date:", dates, default=dates[:4] if len(dates) > 4 else dates)
                if selected_dates:
                    df = df[df['date'].isin(selected_dates)]
            
            # # Add sorting options
            # if not df.empty:
            #     sort_columns = df.columns.tolist()
            #     sort_by = st.selectbox("Sort by:", sort_columns, 
            #                           index=sort_columns.index('score') if 'score' in sort_columns else 0,
            #                           key="sort_by_breakout")
            #     sort_order = st.radio("Sort order:", ["Descending", "Ascending"], horizontal=True, key="sort_order_breakout")
                
            #     df = df.sort_values(by=sort_by, ascending=(sort_order == "Ascending"))
            
            # Display the dataframe
            st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)
            
            # Add download button
            # csv = df.to_csv(index=False).encode('utf-8')
            # st.download_button(
            #     "Download filtered breakout candidates as CSV",
            #     csv,
            #     "filtered_breakout_candidates.csv",
            #     "text/csv",
            #     key='download-breakout-csv'
            # )
        else:
            st.info("No breakout candidates found. Please run a breakout analysis first.")

    # Display detailed results
    with tab2:
        df, message = load_results('output_stocks_')
        
        if df is not None:
            st.write(f"Showing results from: {message}")
            
            # Add filtering options
            if 'ticker' in df.columns:
                ticker_filter = st.text_input("Filter by ticker symbol:")
                if ticker_filter:
                    df = df[df['ticker'].str.contains(ticker_filter, case=False)]
            
            if 'interval' in df.columns:
                intervals = sorted(df['interval'].unique())
                selected_intervals = st.multiselect("Filter by interval:", intervals, default=intervals)
                if selected_intervals:
                    df = df[df['interval'].isin(selected_intervals)]
            
            # Add sorting options
            # if not df.empty:
            #     sort_columns = df.columns.tolist()
            #     sort_by = st.selectbox("Sort by:", sort_columns, index=sort_columns.index('latest_signal') if 'latest_signal' in sort_columns else 0)
            #     sort_order = st.radio("Sort order:", ["Descending", "Ascending"], horizontal=True)
                
            #     df = df.sort_values(by=sort_by, ascending=(sort_order == "Ascending"))
            
            # Display the dataframe
            st.dataframe(df.sort_values(by='signal_date', ascending=False) if 'signal_date' in df.columns else df, use_container_width=True)
            
            # Add download button
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download filtered results as CSV",
                csv,
                "filtered_results.csv",
                "text/csv",
                key='download-csv'
            )
        else:
            st.info(message)

# Second table view with tabs 3-5 (right column)
with col_right:
    st.subheader("Interval Analysis")
    tab3, tab4, tab5 = st.tabs(["Recent Signals", "Best Intervals", "Interval Details"])

    # Display recent signals
    with tab3:
        df, message = load_results('cd_eval_good_signals_', 'latest_signal')
        
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

    # Display best intervals
    with tab4:
        df, message = load_results('cd_eval_best_intervals_', 'avg_return_10')
        
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

    # Display cd eval details
    with tab5:
        df, message = load_results('cd_eval_custom_detailed_', 'avg_return_10')
        
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
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No interval summary data available. Please run CD Signal Evaluation first.")

# Footer
st.markdown("---")
st.markdown("Stock Analysis Dashboard | Created with Streamlit") 