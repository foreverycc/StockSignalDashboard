#!/usr/bin/env python3
"""
Migration script to convert file-based storage to SQLite database.
This script maintains backward compatibility by keeping all existing files.
"""

import os
import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.append('src')

from database_manager import db_manager

def main():
    parser = argparse.ArgumentParser(description='Migrate StockSignalDashboard data to SQLite database')
    parser.add_argument('--data-dir', default='./data', help='Directory containing stock list files')
    parser.add_argument('--output-dir', default='./output', help='Directory containing output files')
    parser.add_argument('--db-path', default='./data/stock_dashboard.db', help='Path for SQLite database')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be migrated without doing it')
    
    args = parser.parse_args()
    
    print("StockSignalDashboard Database Migration Tool")
    print("=" * 50)
    
    if args.dry_run:
        print("DRY RUN MODE - No changes will be made")
        print()
    
    # Check if directories exist
    if not os.path.exists(args.data_dir):
        print(f"Error: Data directory {args.data_dir} does not exist")
        return 1
    
    print(f"Data directory: {args.data_dir}")
    print(f"Output directory: {args.output_dir}")
    print(f"Database path: {args.db_path}")
    print()
    
    # Initialize database manager with custom path if provided
    if args.db_path != './data/stock_dashboard.db':
        from database_manager import DatabaseManager
        global db_manager
        db_manager = DatabaseManager(args.db_path)
    
    # Count files to migrate
    stock_files = []
    for filename in os.listdir(args.data_dir):
        if filename.endswith('.tab') or filename.endswith('.txt'):
            stock_files.append(filename)
    
    print(f"Found {len(stock_files)} stock list files to migrate:")
    for filename in stock_files:
        file_path = os.path.join(args.data_dir, filename)
        try:
            with open(file_path, 'r') as f:
                line_count = sum(1 for line in f if line.strip())
            print(f"  - {filename} ({line_count} tickers)")
        except Exception as e:
            print(f"  - {filename} (error reading: {e})")
    
    print()
    
    if args.dry_run:
        print("DRY RUN COMPLETE - No changes were made")
        return 0
    
    # Perform migration
    print("Starting migration...")
    try:
        db_manager.migrate_existing_files(args.data_dir)
        print("\nMigration completed successfully!")
        
        # Show database status
        print("\nDatabase Status:")
        stock_lists = db_manager.get_available_stock_lists()
        if stock_lists:
            for stock_list in stock_lists:
                status = "ACTIVE" if stock_list['is_active'] else "INACTIVE"
                print(f"  - {stock_list['list_name']} v{stock_list['version']}: {stock_list['ticker_count']} tickers [{status}]")
        else:
            print("  No stock lists found in database")
        
        print(f"\nDatabase file: {args.db_path}")
        if os.path.exists(args.db_path):
            size_mb = os.path.getsize(args.db_path) / (1024 * 1024)
            print(f"Database size: {size_mb:.2f} MB")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return 1
    
    print("\nNOTE: All original files have been preserved.")
    print("The system now uses both database and files for backward compatibility.")
    print("Future analyses will automatically save to both database and files.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 