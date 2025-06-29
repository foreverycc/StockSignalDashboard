#!/usr/bin/env python3
"""
Database inspection script for StockSignalDashboard.
Provides an interactive way to explore database contents.
"""

import os
import sys
import argparse
from datetime import datetime

# Add src to path
sys.path.append('src')

def format_timestamp(ts_str):
    """Format timestamp string for display."""
    try:
        if ts_str:
            dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        pass
    return ts_str or 'N/A'

def show_stock_lists(db_manager):
    """Display all stock lists in the database."""
    print("\n📊 Stock Lists")
    print("-" * 50)
    
    stock_lists = db_manager.get_available_stock_lists()
    if not stock_lists:
        print("No stock lists found in database.")
        return
    
    # Group by list name
    lists_by_name = {}
    for stock_list in stock_lists:
        name = stock_list['list_name']
        if name not in lists_by_name:
            lists_by_name[name] = []
        lists_by_name[name].append(stock_list)
    
    for name, versions in lists_by_name.items():
        active_version = next((v for v in versions if v['is_active']), versions[0])
        total_versions = len(versions)
        
        status = "🟢 ACTIVE" if active_version['is_active'] else "🔴 INACTIVE"
        print(f"{name:25} | v{active_version['version']:2} | {active_version['ticker_count']:4} tickers | {status}")
        
        if total_versions > 1:
            print(f"{' '*25} | {total_versions} versions available")
        
        print(f"{' '*25} | Created: {format_timestamp(active_version['created_at'])}")
        print()

def show_analysis_summary(db_manager):
    """Display summary of analysis results."""
    print("\n🔍 Analysis Results Summary")
    print("-" * 50)
    
    with db_manager.get_connection() as conn:
        cursor = conn.execute("""
            SELECT analysis_type, list_name, COUNT(*) as result_count, 
                   MAX(created_at) as latest_analysis
            FROM analysis_results 
            GROUP BY analysis_type, list_name
            ORDER BY analysis_type, list_name
        """)
        
        results = cursor.fetchall()
        
        if not results:
            print("No analysis results found in database.")
            return
        
        current_type = None
        for row in results:
            analysis_type, list_name, count, latest = row
            
            if analysis_type != current_type:
                if current_type is not None:
                    print()
                print(f"📈 {analysis_type.upper()} Analysis:")
                current_type = analysis_type
            
            print(f"  {list_name:20} | {count:4} results | Latest: {format_timestamp(latest)}")

def show_breakout_candidates(db_manager):
    """Display breakout candidates summary."""
    print("\n🚀 Breakout Candidates")
    print("-" * 50)
    
    with db_manager.get_connection() as conn:
        cursor = conn.execute("""
            SELECT analysis_type, list_name, COUNT(*) as candidate_count,
                   MAX(created_at) as latest_analysis
            FROM breakout_candidates 
            GROUP BY analysis_type, list_name
            ORDER BY analysis_type, list_name
        """)
        
        results = cursor.fetchall()
        
        if not results:
            print("No breakout candidates found in database.")
            return
        
        for row in results:
            analysis_type, list_name, count, latest = row
            print(f"{analysis_type:4} | {list_name:20} | {count:3} candidates | {format_timestamp(latest)}")

def show_cd_evaluation(db_manager):
    """Display CD evaluation summary."""
    print("\n📊 CD Evaluation Results")
    print("-" * 50)
    
    with db_manager.get_connection() as conn:
        cursor = conn.execute("""
            SELECT list_name, COUNT(*) as eval_count,
                   COUNT(DISTINCT ticker) as unique_tickers,
                   MAX(created_at) as latest_analysis
            FROM cd_evaluation 
            GROUP BY list_name
            ORDER BY list_name
        """)
        
        results = cursor.fetchall()
        
        if not results:
            print("No CD evaluation results found in database.")
            return
        
        for row in results:
            list_name, eval_count, unique_tickers, latest = row
            print(f"{list_name:20} | {eval_count:3} evaluations | {unique_tickers:3} tickers | {format_timestamp(latest)}")

def show_database_info(db_manager):
    """Display general database information."""
    print("\n💾 Database Information")
    print("-" * 50)
    
    db_path = db_manager.db_path
    print(f"Database file: {db_path}")
    
    if os.path.exists(db_path):
        size_mb = os.path.getsize(db_path) / (1024 * 1024)
        print(f"Database size: {size_mb:.2f} MB")
        
        # Get table counts
        with db_manager.get_connection() as conn:
            tables = [
                'stock_lists', 'analysis_results', 'breakout_candidates', 
                'cd_evaluation', 'returns_distribution'
            ]
            
            print(f"\nTable Record Counts:")
            for table in tables:
                try:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"  {table:20}: {count:6} records")
                except Exception as e:
                    print(f"  {table:20}: Error - {e}")
    else:
        print("Database file does not exist!")

def interactive_query(db_manager):
    """Allow user to run custom queries."""
    print("\n🔍 Interactive Query Mode")
    print("-" * 50)
    print("Enter SQL queries (type 'exit' to quit, 'tables' to see table names)")
    print("Example: SELECT * FROM stock_lists LIMIT 5")
    print()
    
    while True:
        try:
            query = input("SQL> ").strip()
            
            if query.lower() == 'exit':
                break
            elif query.lower() == 'tables':
                print("Available tables: stock_lists, analysis_results, breakout_candidates, cd_evaluation, returns_distribution")
                continue
            elif not query:
                continue
            
            with db_manager.get_connection() as conn:
                cursor = conn.execute(query)
                results = cursor.fetchall()
                
                if results:
                    # Print column headers
                    columns = [description[0] for description in cursor.description]
                    print(" | ".join(f"{col:15}" for col in columns))
                    print("-" * (len(columns) * 18))
                    
                    # Print first 10 rows
                    for i, row in enumerate(results[:10]):
                        print(" | ".join(f"{str(val)[:15]:15}" for val in row))
                    
                    if len(results) > 10:
                        print(f"... and {len(results) - 10} more rows")
                    
                    print(f"\nTotal: {len(results)} rows")
                else:
                    print("Query executed successfully (no results returned)")
                    
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

def main():
    parser = argparse.ArgumentParser(description='Inspect StockSignalDashboard database')
    parser.add_argument('--db-path', default='./data/stock_dashboard.db', help='Path to SQLite database')
    parser.add_argument('--mode', choices=['summary', 'stocks', 'analysis', 'breakouts', 'cd', 'info', 'query'], 
                       default='summary', help='What to display')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.db_path):
        print(f"Error: Database file {args.db_path} does not exist!")
        print("Run 'python migrate_to_database.py' first to create the database.")
        return 1
    
    # Initialize database manager
    from database_manager import DatabaseManager
    db_manager = DatabaseManager(args.db_path)
    
    print("StockSignalDashboard Database Inspector")
    print("=" * 50)
    
    if args.mode == 'summary':
        show_database_info(db_manager)
        show_stock_lists(db_manager)
        show_analysis_summary(db_manager)
        show_breakout_candidates(db_manager)
        show_cd_evaluation(db_manager)
    elif args.mode == 'stocks':
        show_stock_lists(db_manager)
    elif args.mode == 'analysis':
        show_analysis_summary(db_manager)
    elif args.mode == 'breakouts':
        show_breakout_candidates(db_manager)
    elif args.mode == 'cd':
        show_cd_evaluation(db_manager)
    elif args.mode == 'info':
        show_database_info(db_manager)
    elif args.mode == 'query':
        interactive_query(db_manager)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 