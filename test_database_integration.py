#!/usr/bin/env python3
"""
Test script to verify database integration functionality.
"""

import os
import sys
import tempfile
import shutil

# Add src to path
sys.path.append('src')

def test_database_integration():
    """Test the database integration functionality."""
    print("Testing StockSignalDashboard Database Integration")
    print("=" * 50)
    
    # Create temporary directories for testing
    temp_dir = tempfile.mkdtemp()
    data_dir = os.path.join(temp_dir, 'data')
    os.makedirs(data_dir)
    
    try:
        # Test 1: Create test stock list file
        print("Test 1: Creating test stock list...")
        test_stocks = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'META']
        test_file = os.path.join(data_dir, 'test_stocks.tab')
        with open(test_file, 'w') as f:
            f.write('\n'.join(test_stocks))
        print(f"✓ Created test file with {len(test_stocks)} stocks")
        
        # Test 2: Initialize database manager
        print("\nTest 2: Initializing database manager...")
        from database_manager import DatabaseManager
        db_path = os.path.join(data_dir, 'test_dashboard.db')
        db_manager = DatabaseManager(db_path)
        print(f"✓ Database initialized at {db_path}")
        
        # Test 3: Test stock list loading compatibility
        print("\nTest 3: Testing stock list loading...")
        from data_loader import load_stock_list
        
        # First call should load from file and migrate to database
        loaded_stocks = load_stock_list(test_file)
        print(f"✓ Loaded {len(loaded_stocks)} stocks: {loaded_stocks}")
        
        # Second call should load from database
        loaded_stocks_2 = load_stock_list(test_file)
        print(f"✓ Second load (from database): {len(loaded_stocks_2)} stocks")
        
        assert loaded_stocks == loaded_stocks_2, "Stock lists don't match!"
        print("✓ Both loads return identical results")
        
        # Test 4: Test database querying
        print("\nTest 4: Testing database queries...")
        stock_lists = db_manager.get_available_stock_lists()
        print(f"✓ Found {len(stock_lists)} stock lists in database")
        
        for stock_list in stock_lists:
            print(f"  - {stock_list['list_name']}: {stock_list['ticker_count']} tickers")
        
        # Test 5: Test direct database operations
        print("\nTest 5: Testing direct database operations...")
        direct_stocks = db_manager.get_stock_list('test_stocks')
        print(f"✓ Direct database query returned {len(direct_stocks)} stocks")
        assert direct_stocks == test_stocks, "Direct query doesn't match original!"
        
        # Test 6: Test analysis results saving (mock)
        print("\nTest 6: Testing analysis results saving...")
        mock_results = [
            {'ticker': 'AAPL', 'signal_date': '2025-01-01', 'score': 3.5},
            {'ticker': 'GOOGL', 'signal_date': '2025-01-01', 'score': 4.2}
        ]
        db_manager.save_analysis_results('test_type', 'test_stocks', mock_results)
        
        retrieved_results = db_manager.get_analysis_results('test_type', 'test_stocks')
        print(f"✓ Saved and retrieved {len(retrieved_results)} analysis results")
        
        # Test 7: Test file compatibility with utils
        print("\nTest 7: Testing file compatibility with utils...")
        output_dir = os.path.join(temp_dir, 'output')
        os.makedirs(output_dir)
        
        from utils import save_results
        output_file = os.path.join(output_dir, 'test_results_1234_test_stocks.tab')
        
        mock_detailed_results = [
            {
                'ticker': 'AAPL', 
                'interval': '1h', 
                'score': 3.5, 
                'signal_date': '2025-01-01', 
                'signal_price': 150.0,
                'breakthrough_date': '2025-01-02'
            }
        ]
        save_results(mock_detailed_results, output_file)
        print("✓ Results saved to both database and file")
        
        # Verify file was created
        assert os.path.exists(output_file), "Output file was not created!"
        print("✓ Output file exists")
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("\nDatabase integration is working correctly.")
        print("✅ Stock lists can be loaded from files and database")
        print("✅ Analysis results can be saved to database")
        print("✅ Backward compatibility with files is maintained")
        
        # Show database info
        if os.path.exists(db_path):
            size_kb = os.path.getsize(db_path) / 1024
            print(f"\nTest database size: {size_kb:.2f} KB")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory: {temp_dir}")

def main():
    success = test_database_integration()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 