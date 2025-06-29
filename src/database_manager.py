import sqlite3
import pandas as pd
import os
from datetime import datetime
from typing import List, Dict, Optional, Union
import logging
import json
import numpy as np

class DatabaseManager:
    """
    Database manager for StockSignalDashboard that provides seamless migration
    from file-based storage to SQLite while maintaining existing API compatibility.
    """
    
    def __init__(self, db_path: str = './data/stock_dashboard.db'):
        self.db_path = db_path
        self.ensure_db_directory()
        self.init_database()
        
    def ensure_db_directory(self):
        """Ensure the database directory exists."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
    def init_database(self):
        """Initialize database with all required tables."""
        with sqlite3.connect(self.db_path) as conn:
            # Stock lists table - stores different stock lists with versions
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stock_lists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    list_name TEXT NOT NULL,
                    version INTEGER DEFAULT 1,
                    ticker TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # Analysis results table - unified table for all analysis types
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_type TEXT NOT NULL, -- '1234', '5230', 'cd_eval'
                    list_name TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    ticker TEXT NOT NULL,
                    result_data TEXT NOT NULL, -- JSON string of the result data
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Breakout candidates table - for summary results
            conn.execute("""
                CREATE TABLE IF NOT EXISTS breakout_candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_type TEXT NOT NULL, -- '1234' or '5230'
                    list_name TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    ticker TEXT NOT NULL,
                    date TEXT NOT NULL,
                    intervals TEXT NOT NULL,
                    signal_price REAL,
                    current_price REAL,
                    current_time TIMESTAMP,
                    nx_1d BOOLEAN,
                    nx_30m BOOLEAN,
                    nx_1h BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # CD evaluation detailed results
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cd_evaluation (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    list_name TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    ticker TEXT NOT NULL,
                    interval TEXT NOT NULL,
                    signal_count INTEGER,
                    latest_signal TIMESTAMP,
                    latest_signal_price REAL,
                    current_time TIMESTAMP,
                    current_price REAL,
                    current_period INTEGER,
                    result_data TEXT NOT NULL, -- JSON for all period data
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Returns distribution for visualization
            conn.execute("""
                CREATE TABLE IF NOT EXISTS returns_distribution (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    list_name TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    ticker TEXT NOT NULL,
                    interval TEXT NOT NULL,
                    period INTEGER NOT NULL,
                    return_value REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_stock_lists_name ON stock_lists(list_name, is_active)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_analysis_results_type ON analysis_results(analysis_type, list_name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_breakout_candidates_type ON breakout_candidates(analysis_type, list_name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cd_evaluation_list ON cd_evaluation(list_name, ticker)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_returns_distribution_list ON returns_distribution(list_name, ticker)")
            
            conn.commit()
            
    def get_connection(self):
        """Get database connection."""
        return sqlite3.connect(self.db_path)
    
    def _convert_numpy_types(self, obj):
        """Convert NumPy types to JSON-serializable Python types."""
        if isinstance(obj, dict):
            return {key: self._convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        else:
            return obj
        
    # Stock List Management
    def load_stock_list_from_file(self, file_path: str) -> List[str]:
        """Load stock list from file."""
        try:
            with open(file_path, 'r') as f:
                content = f.read().strip()
            tickers = [ticker.strip() for ticker in content.splitlines() if ticker.strip()]
            return tickers
        except Exception as e:
            logging.error(f"Error loading stock list from {file_path}: {e}")
            return []
    
    def save_stock_list(self, list_name: str, tickers: List[str], update_existing: bool = True):
        """Save stock list to database."""
        with sqlite3.connect(self.db_path) as conn:
            # Get next version number
            cursor = conn.execute(
                "SELECT COALESCE(MAX(version), 0) + 1 FROM stock_lists WHERE list_name = ?",
                (list_name,)
            )
            version = cursor.fetchone()[0]
            
            # Mark previous versions as inactive if updating
            if update_existing:
                conn.execute(
                    "UPDATE stock_lists SET is_active = 0 WHERE list_name = ?",
                    (list_name,)
                )
            
            # Insert new tickers
            for ticker in tickers:
                conn.execute(
                    "INSERT INTO stock_lists (list_name, version, ticker) VALUES (?, ?, ?)",
                    (list_name, version, ticker)
                )
            
            conn.commit()
            return version
    
    def get_stock_list(self, list_name: str, version: Optional[int] = None) -> List[str]:
        """Get stock list from database."""
        with sqlite3.connect(self.db_path) as conn:
            if version is None:
                # Get latest active version
                cursor = conn.execute(
                    "SELECT ticker FROM stock_lists WHERE list_name = ? AND is_active = 1 ORDER BY ticker",
                    (list_name,)
                )
            else:
                cursor = conn.execute(
                    "SELECT ticker FROM stock_lists WHERE list_name = ? AND version = ? ORDER BY ticker",
                    (list_name, version)
                )
            
            return [row[0] for row in cursor.fetchall()]
    
    def get_available_stock_lists(self) -> List[Dict]:
        """Get all available stock lists with their versions."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT list_name, version, COUNT(*) as ticker_count, created_at, is_active
                FROM stock_lists 
                GROUP BY list_name, version 
                ORDER BY list_name, version DESC
            """)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'list_name': row[0],
                    'version': row[1],
                    'ticker_count': row[2],
                    'created_at': row[3],
                    'is_active': bool(row[4])
                })
            
            return results
    
    def load_stock_list_compatible(self, file_path: str) -> List[str]:
        """
        Compatible method that works like the original load_stock_list function.
        First tries to load from database, falls back to file, and saves to database.
        """
        # Extract list name from file path
        list_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # Try to get from database first
        tickers = self.get_stock_list(list_name)
        
        if not tickers:
            # Load from file and save to database
            tickers = self.load_stock_list_from_file(file_path)
            if tickers:
                self.save_stock_list(list_name, tickers)
                print(f"Migrated stock list {list_name} from file to database ({len(tickers)} tickers)")
        
        return tickers
    
    # Analysis Results Management
    def save_analysis_results(self, analysis_type: str, list_name: str, results: List[Dict]):
        """Save analysis results to database."""
        if not results:
            return
            
        with sqlite3.connect(self.db_path) as conn:
            # Get version number for this list
            cursor = conn.execute(
                "SELECT COALESCE(MAX(version), 1) FROM stock_lists WHERE list_name = ? AND is_active = 1",
                (list_name,)
            )
            version = cursor.fetchone()[0]
            
            # Save each result
            for result in results:
                # Convert NumPy types to JSON-serializable types
                clean_result = self._convert_numpy_types(result)
                conn.execute(
                    "INSERT INTO analysis_results (analysis_type, list_name, version, ticker, result_data) VALUES (?, ?, ?, ?, ?)",
                    (analysis_type, list_name, version, result.get('ticker', ''), json.dumps(clean_result))
                )
            
            conn.commit()
    
    def get_analysis_results(self, analysis_type: str, list_name: str, version: Optional[int] = None) -> List[Dict]:
        """Get analysis results from database."""
        with sqlite3.connect(self.db_path) as conn:
            if version is None:
                cursor = conn.execute(
                    "SELECT result_data FROM analysis_results WHERE analysis_type = ? AND list_name = ? ORDER BY created_at DESC",
                    (analysis_type, list_name)
                )
            else:
                cursor = conn.execute(
                    "SELECT result_data FROM analysis_results WHERE analysis_type = ? AND list_name = ? AND version = ? ORDER BY created_at DESC",
                    (analysis_type, list_name, version)
                )
            
            results = []
            for row in cursor.fetchall():
                try:
                    results.append(json.loads(row[0]))
                except json.JSONDecodeError:
                    continue
            
            return results
    
    # File-compatible result saving
    def save_results_compatible(self, results: List[Dict], output_file: str):
        """
        Compatible method that saves results to both database and file for backward compatibility.
        """
        # Save to database
        analysis_type = self._extract_analysis_type_from_path(output_file)
        list_name = self._extract_list_name_from_path(output_file)
        
        if analysis_type and list_name:
            self.save_analysis_results(analysis_type, list_name, results)
        
        # Also save to file for backward compatibility
        df = pd.DataFrame(results)
        if df.empty:
            print("No results to save")
            return
            
        df = df.sort_values(by=['signal_date', 'breakthrough_date', 'score', 'interval'], 
                           ascending=[False, False, False, False])
        
        columns_to_save = ['ticker', 'interval', 'score', 'signal_date']
        if 'signal_price' in df.columns:
            columns_to_save.append('signal_price')
        columns_to_save.append('breakthrough_date')
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        df.to_csv(output_file, sep='\t', index=False, columns=columns_to_save)
    
    def _extract_analysis_type_from_path(self, file_path: str) -> str:
        """Extract analysis type from file path."""
        filename = os.path.basename(file_path)
        if '1234' in filename:
            return '1234'
        elif '5230' in filename:
            return '5230'
        elif 'cd_eval' in filename:
            return 'cd_eval'
        return 'unknown'
    
    def _extract_list_name_from_path(self, file_path: str) -> str:
        """Extract list name from file path."""
        filename = os.path.basename(file_path)
        # Remove file extension
        name_part = os.path.splitext(filename)[0]
        
        # Extract the list name (usually the last part after the last underscore)
        parts = name_part.split('_')
        if len(parts) > 1:
            return parts[-1]
        return name_part
    
    # CD Evaluation specific methods
    def save_cd_evaluation_results(self, list_name: str, results: List[Dict]):
        """Save CD evaluation results to database."""
        if not results:
            return
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT COALESCE(MAX(version), 1) FROM stock_lists WHERE list_name = ? AND is_active = 1",
                (list_name,)
            )
            version = cursor.fetchone()[0]
            
            # Clear existing results for this list/version
            conn.execute(
                "DELETE FROM cd_evaluation WHERE list_name = ? AND version = ?",
                (list_name, version)
            )
            
            # Save new results
            for result in results:
                # Convert NumPy types to JSON-serializable types
                clean_result = self._convert_numpy_types(result)
                
                # Extract basic fields (also clean them)
                ticker = str(clean_result.get('ticker', ''))
                interval = str(clean_result.get('interval', ''))
                signal_count = int(clean_result.get('signal_count', 0)) if clean_result.get('signal_count') is not None else 0
                latest_signal = str(clean_result.get('latest_signal', ''))
                latest_signal_price = float(clean_result.get('latest_signal_price', 0)) if clean_result.get('latest_signal_price') is not None else 0
                current_time = str(clean_result.get('current_time', ''))
                current_price = float(clean_result.get('current_price', 0)) if clean_result.get('current_price') is not None else 0
                current_period = int(clean_result.get('current_period', 0)) if clean_result.get('current_period') is not None else 0
                
                conn.execute("""
                    INSERT INTO cd_evaluation 
                    (list_name, version, ticker, interval, signal_count, latest_signal, 
                     latest_signal_price, current_time, current_price, current_period, result_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (list_name, version, ticker, interval, signal_count, latest_signal,
                      latest_signal_price, current_time, current_price, current_period,
                      json.dumps(clean_result)))
            
            conn.commit()
    
    def save_returns_distribution(self, list_name: str, returns_data: List[Dict]):
        """Save returns distribution data."""
        if not returns_data:
            return
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT COALESCE(MAX(version), 1) FROM stock_lists WHERE list_name = ? AND is_active = 1",
                (list_name,)
            )
            version = cursor.fetchone()[0]
            
            # Clear existing data
            conn.execute(
                "DELETE FROM returns_distribution WHERE list_name = ? AND version = ?",
                (list_name, version)
            )
            
            # Save new data
            for item in returns_data:
                # Convert NumPy types to ensure compatibility
                clean_item = self._convert_numpy_types(item)
                conn.execute("""
                    INSERT INTO returns_distribution (list_name, version, ticker, interval, period, return_value)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (list_name, version, str(clean_item['ticker']), str(clean_item['interval']), 
                      int(clean_item['period']), float(clean_item['return'])))
            
            conn.commit()
    
    # Data retrieval methods for Streamlit app
    def get_results_as_dataframe(self, file_pattern: str, list_name: str) -> Optional[pd.DataFrame]:
        """
        Get results as DataFrame compatible with existing load_results function.
        """
        try:
            if 'cd_eval_custom_detailed' in file_pattern:
                return self._get_cd_evaluation_detailed_df(list_name)
            elif 'cd_eval_returns_distribution' in file_pattern:
                return self._get_returns_distribution_df(list_name)
            elif 'cd_eval_good_signals' in file_pattern:
                return self._get_cd_good_signals_df(list_name)
            elif 'cd_eval_best_intervals' in file_pattern:
                return self._get_cd_best_intervals_df(list_name, file_pattern)
            elif 'breakout_candidates_summary' in file_pattern:
                analysis_type = '1234' if '1234' in file_pattern else '5230'
                return self._get_breakout_summary_df(list_name, analysis_type)
            elif 'breakout_candidates_details' in file_pattern:
                analysis_type = '1234' if '1234' in file_pattern else '5230'
                return self._get_breakout_details_df(list_name, analysis_type)
            else:
                return None
        except Exception as e:
            logging.error(f"Error getting results as DataFrame: {e}")
            return None
    
    def _get_cd_evaluation_detailed_df(self, list_name: str) -> Optional[pd.DataFrame]:
        """Get CD evaluation detailed results as DataFrame."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT result_data FROM cd_evaluation 
                WHERE list_name = ? 
                ORDER BY latest_signal DESC
            """, (list_name,))
            
            results = []
            for row in cursor.fetchall():
                try:
                    result_data = json.loads(row[0])
                    results.append(result_data)
                except json.JSONDecodeError:
                    continue
            
            if not results:
                return None
                
            # Convert to DataFrame
            df = pd.DataFrame(results)
            
            # Fix price_history format - convert string keys to integer keys
            if 'price_history' in df.columns:
                def fix_price_history(price_history):
                    if isinstance(price_history, dict):
                        # Convert string keys to integer keys
                        fixed_history = {}
                        for key, value in price_history.items():
                            try:
                                int_key = int(key)
                                fixed_history[int_key] = value
                            except ValueError:
                                # Skip non-numeric keys
                                continue
                        return fixed_history
                    return price_history
                
                df['price_history'] = df['price_history'].apply(fix_price_history)
            
            # Ensure all expected columns exist with proper data types
            for col in df.columns:
                if col.startswith(('avg_return_', 'success_rate_')):
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
                elif col.startswith('test_count_'):
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                elif col == 'signal_count':
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                elif col == 'current_period':
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                elif col in ['current_price', 'latest_signal_price']:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
            return df
    
    def _get_returns_distribution_df(self, list_name: str) -> Optional[pd.DataFrame]:
        """Get returns distribution as DataFrame."""
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query("""
                SELECT ticker, interval, period, return_value as return
                FROM returns_distribution 
                WHERE list_name = ?
                ORDER BY ticker, interval, period
            """, conn, params=(list_name,))
            return df if not df.empty else None
    
    def _get_cd_good_signals_df(self, list_name: str) -> Optional[pd.DataFrame]:
        """Get CD good signals as DataFrame with calculated fields."""
        detailed_df = self._get_cd_evaluation_detailed_df(list_name)
        if detailed_df is None or detailed_df.empty:
            return None
        
        # Filter for valid signals (test_count_10 >= 2)
        valid_df = detailed_df[detailed_df.get('test_count_10', 0) >= 2].copy()
        
        if valid_df.empty:
            return None
        
        # Calculate derived fields
        periods = [3, 5, 10, 15, 20, 25, 30, 40, 50, 60, 80, 100]
        
        # Find best period for each row
        best_periods = []
        max_returns = []
        exp_returns = []
        test_counts = []
        success_rates = []
        
        for _, row in valid_df.iterrows():
            # Find available periods with sufficient data
            available_periods = []
            for period in periods:
                if (f'avg_return_{period}' in row and 
                    f'test_count_{period}' in row and 
                    f'success_rate_{period}' in row and
                    row.get(f'test_count_{period}', 0) >= 2):
                    available_periods.append(period)
            
            if not available_periods:
                best_periods.append(None)
                max_returns.append(0)
                exp_returns.append(0)
                test_counts.append(0)
                success_rates.append(0)
                continue
            
            # Find period with highest avg_return
            best_period = None
            best_return = float('-inf')
            
            for period in available_periods:
                avg_return = row.get(f'avg_return_{period}', 0)
                if avg_return > best_return:
                    best_return = avg_return
                    best_period = period
            
            best_periods.append(best_period)
            max_returns.append(best_return)
            
            if best_period:
                exp_returns.append(row.get(f'avg_return_{best_period}', 0))
                test_counts.append(row.get(f'test_count_{best_period}', 0))
                success_rates.append(row.get(f'success_rate_{best_period}', 0))
            else:
                exp_returns.append(0)
                test_counts.append(0)
                success_rates.append(0)
        
        # Add calculated columns
        valid_df['best_period'] = best_periods
        valid_df['max_return'] = max_returns
        valid_df['exp_return'] = exp_returns
        valid_df['test_count'] = test_counts
        valid_df['success_rate'] = success_rates
        
        # Filter for good signals (success_rate >= 50)
        good_signals_df = valid_df[valid_df['success_rate'] >= 50].copy()
        
        if good_signals_df.empty:
            return None
        
        # Sort by latest signal date
        if 'latest_signal' in good_signals_df.columns:
            # Convert to datetime for proper sorting
            good_signals_df['latest_signal'] = pd.to_datetime(good_signals_df['latest_signal'], errors='coerce')
            good_signals_df = good_signals_df.sort_values('latest_signal', ascending=False)
        
        return good_signals_df
    
    def _get_cd_best_intervals_df(self, list_name: str, file_pattern: str) -> Optional[pd.DataFrame]:
        """Get CD best intervals as DataFrame."""
        # Extract period range from file pattern
        if '20' in file_pattern:
            max_period = 20
        elif '50' in file_pattern:
            max_period = 50
        elif '100' in file_pattern:
            max_period = 100
        else:
            max_period = 100
        
        # Get detailed data
        detailed_df = self._get_cd_evaluation_detailed_df(list_name)
        if detailed_df is None or detailed_df.empty:
            return None
        
        # Filter for valid signals (test_count_10 >= 2)
        valid_df = detailed_df[detailed_df.get('test_count_10', 0) >= 2].copy()
        
        if valid_df.empty:
            return None
        
        # Calculate best intervals
        best_intervals = []
        
        for _, row in valid_df.iterrows():
            ticker = row['ticker']
            interval = row['interval']
            
            # Find available periods up to max_period
            periods = [3, 5, 10, 15, 20, 25, 30, 40, 50, 60, 80, 100]
            available_periods = [p for p in periods if p <= max_period and f'avg_return_{p}' in row and row.get(f'test_count_{p}', 0) >= 2]
            
            if not available_periods:
                continue
                
            # Find the best period (highest avg_return with sufficient test count)
            best_period = None
            best_return = float('-inf')
            
            for period in available_periods:
                avg_return = row.get(f'avg_return_{period}', 0)
                test_count = row.get(f'test_count_{period}', 0)
                success_rate = row.get(f'success_rate_{period}', 0)
                
                # Only consider periods with good success rate and test count
                if test_count >= 2 and success_rate >= 50 and avg_return > best_return:
                    best_return = avg_return
                    best_period = period
            
            if best_period is None:
                continue
                
            # Calculate hold time (convert period to readable format)
            if interval.endswith('m'):
                interval_mins = int(interval[:-1])
            elif interval.endswith('h'):
                interval_mins = int(interval[:-1]) * 60
            elif interval == '1d':
                interval_mins = 24 * 60
            elif interval == '1w':
                interval_mins = 7 * 24 * 60
            else:
                interval_mins = 60  # default
                
            hold_mins = best_period * interval_mins
            
            # Convert to readable format
            if hold_mins < 60:
                hold_time = f"{hold_mins}min"
            elif hold_mins < 24 * 60:
                hours = hold_mins // 60
                mins = hold_mins % 60
                if mins == 0:
                    hold_time = f"{hours}hr"
                else:
                    hold_time = f"{hours}hr{mins}min"
            else:
                days = hold_mins // (24 * 60)
                remaining_mins = hold_mins % (24 * 60)
                hours = remaining_mins // 60
                mins = remaining_mins % 60
                
                if hours == 0 and mins == 0:
                    hold_time = f"{days}days"
                elif mins == 0:
                    hold_time = f"{days}days{hours}hr"
                else:
                    hold_time = f"{days}days{hours}hr{mins}min"
            
            # Create best interval record
            best_interval = {
                'ticker': ticker,
                'interval': interval,
                'hold_time': hold_time,
                'avg_return': row.get(f'avg_return_{best_period}', 0),
                'latest_signal': row.get('latest_signal', ''),
                'latest_signal_price': row.get('latest_signal_price', 0),
                'current_time': row.get('current_time', ''),
                'current_price': row.get('current_price', 0),
                'current_period': row.get('current_period', 0),
                'test_count': row.get(f'test_count_{best_period}', 0),
                'success_rate': row.get(f'success_rate_{best_period}', 0),
                'best_period': best_period,
                'signal_count': row.get('signal_count', 0)
            }
            
            best_intervals.append(best_interval)
        
        if not best_intervals:
            return None
            
        # Convert to DataFrame and sort
        result_df = pd.DataFrame(best_intervals)
        
        # Remove duplicates (keep the first occurrence)
        result_df = result_df.drop_duplicates(subset=['ticker', 'interval'], keep='first')
        
        # Apply the same filters as the original file-based system
        # Filter 1: Only show intervals with at least 5% average return
        result_df = result_df[result_df['avg_return'] >= 5]
        
        # Filter 2: Only show intervals where current_period <= best_period (still within optimal holding period)
        result_df = result_df[result_df['current_period'] <= result_df['best_period']]
        
        if result_df.empty:
            return None
            
        # Sort by latest signal date (descending) for consistency with file-based system
        if 'latest_signal' in result_df.columns:
            result_df['latest_signal'] = pd.to_datetime(result_df['latest_signal'], errors='coerce')
            result_df = result_df.sort_values('latest_signal', ascending=False)
        
        return result_df
    
    def _get_breakout_summary_df(self, list_name: str, analysis_type: str) -> Optional[pd.DataFrame]:
        """Get breakout candidates summary as DataFrame."""
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query("""
                SELECT ticker, date, intervals, signal_price, current_price, current_time, 
                       nx_1d, nx_30m, nx_1h
                FROM breakout_candidates 
                WHERE list_name = ? AND analysis_type = ?
                ORDER BY date DESC
            """, conn, params=(list_name, analysis_type))
            
            if df.empty:
                return None
                
            # Remove duplicates by ticker+date combination (since one signal can apply to multiple intervals)
            # Keep the most recent record for each unique ticker+date
            df = df.drop_duplicates(subset=['ticker', 'date'], keep='first')
            
            return df
    
    def _get_breakout_details_df(self, list_name: str, analysis_type: str) -> Optional[pd.DataFrame]:
        """Get breakout candidates details as DataFrame."""
        results = self.get_analysis_results(analysis_type, list_name)
        
        if not results:
            return None
            
        df = pd.DataFrame(results)
        
        # Remove duplicates based on ticker and interval (keep the most recent/first occurrence)
        if 'ticker' in df.columns and 'interval' in df.columns:
            df = df.drop_duplicates(subset=['ticker', 'interval'], keep='first')
        elif 'ticker' in df.columns:
            df = df.drop_duplicates(subset=['ticker'], keep='first')
            
        return df
    
    # Migration methods
    def migrate_existing_files(self, data_dir: str = './data'):
        """Migrate existing files to database."""
        print("Starting migration of existing files to database...")
        
        # Migrate stock lists
        if os.path.exists(data_dir):
            for filename in os.listdir(data_dir):
                if filename.endswith('.tab') or filename.endswith('.txt'):
                    file_path = os.path.join(data_dir, filename)
                    list_name = os.path.splitext(filename)[0]
                    
                    tickers = self.load_stock_list_from_file(file_path)
                    if tickers:
                        self.save_stock_list(list_name, tickers)
                        print(f"Migrated stock list: {list_name} ({len(tickers)} tickers)")
        
        print("Migration completed!")
    
    def get_latest_update_time(self, list_name: str) -> Optional[float]:
        """Get latest update time for compatibility with existing code."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT MAX(created_at) FROM (
                    SELECT created_at FROM analysis_results WHERE list_name = ?
                    UNION ALL
                    SELECT created_at FROM breakout_candidates WHERE list_name = ?
                    UNION ALL
                    SELECT created_at FROM cd_evaluation WHERE list_name = ?
                )
            """, (list_name, list_name, list_name))
            
            result = cursor.fetchone()[0]
            if result:
                # Convert to timestamp
                try:
                    dt = datetime.fromisoformat(result.replace('Z', '+00:00'))
                    return dt.timestamp()
                except:
                    return None
            return None


# Global database manager instance
db_manager = DatabaseManager() 