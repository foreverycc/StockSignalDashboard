#!/usr/bin/env python3
"""
Database Cleanup Script for StockSignalDashboard

This script removes duplicate records from the database, keeping only the latest records.
Useful for maintaining database performance and data integrity.

Usage:
    python cleanup_database.py              # Clean all lists
    python cleanup_database.py --list test  # Clean specific list only
    python cleanup_database.py --dry-run    # Show what would be cleaned without making changes
"""

import argparse
import sys
import os

# Add src directory to path
sys.path.append('src')

from database_manager import db_manager

def main():
    parser = argparse.ArgumentParser(description='Clean up duplicate records in the stock dashboard database')
    parser.add_argument('--list', '-l', type=str, help='Clean specific list only (e.g., "test", "stocks_all")')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Show what would be cleaned without making changes')
    
    args = parser.parse_args()
    
    print("🗄️ StockSignalDashboard Database Cleanup Tool")
    print("=" * 50)
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
        
        # Show current record counts
        with db_manager.get_connection() as conn:
            print("\n📊 Current Database Status:")
            
            if args.list:
                list_filter = f"WHERE list_name = '{args.list}'"
            else:
                list_filter = ""
            
            # CD evaluation
            cursor = conn.execute(f'SELECT COUNT(*) FROM cd_evaluation {list_filter}')
            cd_count = cursor.fetchone()[0]
            print(f"  - CD evaluation: {cd_count} records")
            
            # Breakout candidates
            cursor = conn.execute(f'SELECT COUNT(*) FROM breakout_candidates {list_filter}')
            breakout_count = cursor.fetchone()[0]
            print(f"  - Breakout candidates: {breakout_count} records")
            
            # Analysis results
            cursor = conn.execute(f'SELECT COUNT(*) FROM analysis_results {list_filter}')
            analysis_count = cursor.fetchone()[0]
            print(f"  - Analysis results: {analysis_count} records")
            
            # Returns distribution
            cursor = conn.execute(f'SELECT COUNT(*) FROM returns_distribution {list_filter}')
            returns_count = cursor.fetchone()[0]
            print(f"  - Returns distribution: {returns_count} records")
            
            total_records = cd_count + breakout_count + analysis_count + returns_count
            print(f"\n📈 Total records: {total_records}")
            
        print("\n💡 Run without --dry-run to perform actual cleanup")
        
    else:
        # Get database size before cleanup
        if os.path.exists('data/stock_dashboard.db'):
            db_size_before = os.path.getsize('data/stock_dashboard.db') / (1024 * 1024)
            print(f"📦 Database size before cleanup: {db_size_before:.2f} MB")
        
        # Perform cleanup
        if args.list:
            print(f"🧹 Cleaning duplicates for list: {args.list}")
            deleted_count = db_manager.cleanup_duplicate_records(args.list)
        else:
            print("🧹 Cleaning duplicates for all lists")
            deleted_count = db_manager.cleanup_duplicate_records()
        
        # Get database size after cleanup
        if os.path.exists('data/stock_dashboard.db'):
            db_size_after = os.path.getsize('data/stock_dashboard.db') / (1024 * 1024)
            size_saved = db_size_before - db_size_after
            print(f"📦 Database size after cleanup: {db_size_after:.2f} MB")
            print(f"💾 Space saved: {size_saved:.2f} MB")
        
        print(f"\n✅ Cleanup completed successfully!")
        print(f"🗑️ Total duplicate records removed: {deleted_count}")
        print("\n🚀 Your dashboard will now load faster with cleaner data!")

if __name__ == "__main__":
    main() 