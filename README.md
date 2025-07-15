# StockSignalDashboard

A comprehensive stock signal analysis dashboard that provides CD (抄底) and MC (卖出) signal analysis with backtesting capabilities.

## Features

- **CD Signal Analysis (抄底)**: Analyze bottom-fishing opportunities with multiple models
- **MC Signal Analysis (卖出)**: Analyze sell signal opportunities 
- **Backtesting Support**: Test strategies using historical data up to specific dates
- **Multiple Models**: Waikiki and Resonance models for comprehensive analysis
- **Real-time Data**: Uses yfinance API for current market data

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the Streamlit app:
```bash
streamlit run src/app.py
```

## Usage

### Basic Analysis

1. Select a stock list from the sidebar dropdown
2. Click "Run Analysis" to perform comprehensive analysis
3. View results in the CD Analysis or MC Analysis tabs

### Backtesting Feature

The backtesting feature allows you to analyze how your signals would have performed using historical data up to a specific date.

#### How to Use Backtesting

1. **Enable Backtesting**: Check the "Enable Backtesting" checkbox in the sidebar
2. **Select End Date**: Choose the date up to which you want to analyze data
3. **Run Analysis**: Click "Run Analysis" to perform backtesting analysis
4. **View Results**: Results will show historical performance up to your selected date

#### Technical Implementation

The backtesting feature works by:
- Downloading standard data periods (60d for 5m, 1y for 1h, 2y for 1d)
- Truncating data to the specified end date
- Running analysis on the truncated historical data

This approach avoids yfinance API limitations while providing accurate backtesting results.

#### Backtesting Indicators

When backtesting is enabled, the interface will show:
- 📊 **Backtesting Results** header
- 🔍 **Backtesting Mode** indicator with the end date
- Different status messages during analysis
- Results reflect historical data up to your selected date

### Stock List Management

The dashboard supports multiple stock list formats:
- `.tab` files (tab-separated)
- `.txt` files (one symbol per line)

You can edit, create, and manage stock lists directly in the sidebar.

## Data Sources

- **Market Data**: yfinance API
- **Intervals Supported**: 5m, 10m, 15m, 30m, 1h, 2h, 3h, 4h, 1d, 1w
- **Chinese Stocks**: Automatic name resolution using akshare

## Analysis Models

### CD Analysis (抄底)
- **Waikiki Model**: Best interval analysis with period returns
- **Resonance Model**: 1234 and 5230 breakout pattern detection

### MC Analysis (卖出)
- **Waikiki Model**: Sell signal timing analysis
- **Resonance Model**: Coming soon

## Output Files

Results are saved in the `./output/` directory:
- `cd_eval_*.csv`: CD signal evaluation results
- `mc_eval_*.csv`: MC signal evaluation results  
- `breakout_candidates_*.tab`: Resonance model results

## Configuration

### Signal Processing
- **MAX_SIGNALS_THRESHOLD**: Limits processing to latest 10 signals (configurable)
- **Data Ranges**: 5m (60 days), 1h (1 year), 1d (2 years)

### Backtesting
- **End Date**: Any date up to today
- **Data Truncation**: Automatic truncation to selected end date
- **Compatibility**: Works with all analysis models

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.