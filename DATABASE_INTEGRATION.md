# Database Integration for StockSignalDashboard

## Overview

The StockSignalDashboard now supports SQLite database storage while maintaining full backward compatibility with the existing file-based system. This enhancement provides:

- **Historical Data Storage**: Keep track of analysis results over time
- **Better Organization**: All data centralized in a single database file
- **Improved Performance**: Faster data retrieval and querying capabilities
- **Data Integrity**: ACID transactions and consistent data structure
- **Backward Compatibility**: All existing functionality continues to work unchanged

## Key Features

### 🔄 Seamless Migration
- Automatically migrates existing `.tab` and `.txt` files to database
- Preserves all original files for safety
- Zero downtime migration

### 📊 Comprehensive Data Storage
- **Stock Lists**: All ticker lists with versioning support
- **Analysis Results**: 1234, 5230, and CD evaluation results
- **Breakout Candidates**: Summary and detailed breakout data
- **Returns Distribution**: Historical return data for visualizations
- **Historical Tracking**: All data timestamped for historical analysis

### 🔌 Backward Compatibility
- All existing functions work unchanged
- Results saved to both database and files
- Streamlit app automatically uses database when available
- Falls back to file-based loading if database unavailable

## Database Schema

### Stock Lists (`stock_lists`)
- Stores all ticker lists with versioning
- Tracks active/inactive versions
- Supports multiple versions of the same list

### Analysis Results (`analysis_results`)
- Unified storage for all analysis types (1234, 5230, CD evaluation)
- JSON-based storage for flexible result structures
- Linked to specific stock list versions

### Breakout Candidates (`breakout_candidates`)
- Summary data for 1234 and 5230 breakout candidates
- Structured fields for common attributes
- Supports both 1h and 30m/1d signals

### CD Evaluation (`cd_evaluation`)
- Detailed CD signal evaluation results
- Optimized for dashboard queries
- Includes all period-specific metrics

### Returns Distribution (`returns_distribution`)
- Individual return values for visualization
- Supports boxplot and distribution analysis
- Linked to specific tickers and time periods

## Getting Started

### 1. Migration

Migrate your existing data to the database:

```bash
# Dry run to see what will be migrated
python migrate_to_database.py --dry-run

# Perform the migration
python migrate_to_database.py

# Custom database location
python migrate_to_database.py --db-path ./custom/path/dashboard.db
```

### 2. Usage

The system automatically uses the database when available. No code changes needed!

```python
# This automatically uses database if available, falls back to files
from data_loader import load_stock_list
stocks = load_stock_list('./data/stocks_hot.tab')

# Analysis results are automatically saved to both database and files
from stock_analyzer import analyze_stocks
analyze_stocks('./data/test.tab')
```

### 3. Database Management

```python
from database_manager import db_manager

# View available stock lists
stock_lists = db_manager.get_available_stock_lists()
for stock_list in stock_lists:
    print(f"{stock_list['list_name']}: {stock_list['ticker_count']} tickers")

# Get specific stock list
tickers = db_manager.get_stock_list('stocks_hot')

# Query analysis results
results = db_manager.get_analysis_results('1234', 'stocks_hot')
```

## Migration Status

After running the migration, you should see output like:

```
Migration completed successfully!

Database Status:
  - 00-stocks_hot v1: 102 tickers [ACTIVE]
  - stocks_AI v1: 11 tickers [ACTIVE]
  - stocks_all v1: 1105 tickers [ACTIVE]
  - test v1: 7 tickers [ACTIVE]
  ... (more lists)

Database file: ./data/stock_dashboard.db
Database size: 0.16 MB
```

## Benefits

### For Users
- **Faster Loading**: Database queries are faster than file parsing
- **Historical Data**: Track analysis results over time
- **Data Integrity**: No more corrupted or missing files
- **Space Efficient**: Single database file vs. hundreds of output files

### For Developers
- **Structured Data**: Well-defined schema for all data types
- **Easy Querying**: SQL-based data retrieval
- **Extensible**: Easy to add new data types and fields
- **Version Control**: Built-in versioning for stock lists

## File Structure

After integration, your project structure includes:

```
StockSignalDashboard_dev/
├── data/
│   ├── stock_dashboard.db          # New: SQLite database
│   ├── *.tab files                 # Existing: Stock lists (preserved)
│   └── chinese_stocks_mapping.csv  # Existing: Stock mappings
├── output/                         # Existing: Output files (still generated)
├── src/
│   ├── database_manager.py         # New: Database management
│   ├── data_loader.py              # Updated: Database compatibility
│   ├── utils.py                    # Updated: Database saving
│   ├── stock_analyzer.py           # Updated: Database integration
│   ├── app.py                      # Updated: Database loading
│   └── ... (other existing files)
├── migrate_to_database.py          # New: Migration script
└── test_database_integration.py    # New: Test script
```

## Technical Details

### Database Location
- Default: `./data/stock_dashboard.db`
- Customizable via environment variable or script parameter
- Automatically creates directory structure if needed

### Data Integrity
- ACID transactions ensure data consistency
- Foreign key relationships maintain referential integrity
- Indexes optimize query performance

### Performance
- Optimized queries for dashboard loading
- Efficient storage with JSON for flexible data
- Minimal memory footprint

### Security
- Local SQLite file (no network exposure)
- Same security model as existing file system
- Can be backed up like any other file

## Troubleshooting

### Migration Issues
```bash
# Check current directory structure
ls -la data/

# Verify database was created
ls -la data/stock_dashboard.db

# Check database contents
python -c "
from src.database_manager import db_manager
lists = db_manager.get_available_stock_lists()
print(f'Found {len(lists)} stock lists')
"
```

### Loading Issues
- Database automatically falls back to files if unavailable
- Check file permissions on database file
- Verify database file isn't corrupted

### Performance Issues
- Database should be faster than files for most operations
- If slower, check disk space and file system performance
- Consider database location (SSD vs HDD)

## Future Enhancements

The database integration enables future features:

- **Advanced Analytics**: Complex queries across historical data
- **Data Export**: Easy export to other formats (CSV, Excel, etc.)
- **API Endpoints**: RESTful API for external integrations
- **Dashboard Enhancements**: Real-time data updates
- **Multi-user Support**: Shared database for team usage

## Backward Compatibility Guarantee

- All existing scripts and functions continue to work
- File-based workflows remain supported
- No breaking changes to existing APIs
- Gradual migration path available

---

**Note**: This integration maintains full compatibility with your existing workflow while adding powerful database capabilities. You can continue using the system exactly as before, with the added benefit of centralized data storage and historical tracking. 