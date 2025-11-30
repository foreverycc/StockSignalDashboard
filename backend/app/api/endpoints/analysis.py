import os
import pandas as pd
import numpy as np
import yfinance as yf
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.services.engine import job_manager

logger = logging.getLogger(__name__)

router = APIRouter()

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../output"))

class AnalysisRequest(BaseModel):
    stock_list_file: str
    end_date: Optional[str] = None

class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: int
    error: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None

@router.post("/run", response_model=JobStatus)
async def run_analysis(request: AnalysisRequest):
    """Start a new analysis job."""
    try:
        job_id = job_manager.start_analysis(request.stock_list_file, request.end_date)
        job = job_manager.get_job(job_id)
        return {
            "job_id": job.job_id,
            "status": job.status,
            "progress": job.progress,
            "error": job.error,
            "start_time": job.start_time.isoformat() if job.start_time else None,
            "end_time": job.end_time.isoformat() if job.end_time else None
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/status/current", response_model=Optional[JobStatus])
async def get_current_status():
    """Get status of the current or last job."""
    job = job_manager.get_current_job()
    if not job:
        return None
    return {
        "job_id": job.job_id,
        "status": job.status,
        "progress": job.progress,
        "error": job.error,
        "start_time": job.start_time.isoformat() if job.start_time else None,
        "end_time": job.end_time.isoformat() if job.end_time else None
    }

@router.get("/results/files")
async def list_result_files(stock_list: Optional[str] = None):
    """List available result files, optionally filtered by stock list."""
    if not os.path.exists(OUTPUT_DIR):
        return []
    
    files = []
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith('.csv') or f.endswith('.tab'):
            if stock_list:
                # Simple matching logic from original app
                stock_list_name = os.path.splitext(stock_list)[0]
                base_name = f.rsplit('.', 1)[0]
                if base_name.endswith('_' + stock_list_name) or base_name == stock_list_name:
                    files.append(f)
            else:
                files.append(f)
    
    # Sort by modification time (newest first)
    files.sort(key=lambda x: os.path.getmtime(os.path.join(OUTPUT_DIR, x)), reverse=True)
    return files

import numpy as np
import traceback

@router.get("/results/content/{filename}")
async def get_result_content(filename: str):
    """Get content of a result file as JSON."""
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_csv(file_path, sep='\t')
        
        # Replace NaN with None for JSON compatibility
        df = df.replace({np.nan: None})
        
        # Replace Infinity with None
        df = df.replace([np.inf, -np.inf], None)
        
        return df.to_dict(orient='records')
    except Exception as e:
        print(f"Error reading file {filename}:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

@router.get("/logs")
async def get_logs(lines: int = 100):
    """Get the last N lines of the server log."""
    log_file = 'backend_server.log'
    if not os.path.exists(log_file):
        return {"logs": []}
    
    try:
        with open(log_file, 'r') as f:
            # Efficiently read last N lines
            # For simplicity, reading all and slicing (log file is rotated so shouldn't be huge)
            all_lines = f.readlines()
            return {"logs": [line.strip() for line in all_lines[-lines:]]}
    except Exception as e:
        return {"logs": [f"Error reading logs: {str(e)}"]}

@router.get("/results/latest_update")
async def get_latest_update(stock_list: str):
    """Get the latest update timestamp for a stock list."""
    if not os.path.exists(OUTPUT_DIR):
        return {"timestamp": None}
    
    stock_list_name = os.path.splitext(stock_list)[0]
    latest_time = 0
    
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith('.csv') or f.endswith('.tab'):
            base_name = f.rsplit('.', 1)[0]
            if base_name.endswith('_' + stock_list_name) or base_name == stock_list_name:
                mod_time = os.path.getmtime(os.path.join(OUTPUT_DIR, f))
                if mod_time > latest_time:
                    latest_time = mod_time
    
    return {"timestamp": latest_time if latest_time > 0 else None}

@router.get("/price_data/{ticker}")
async def get_price_data(
    ticker: str,
    interval: str = "1d",
    days: int = 60
):
    """Get OHLCV price data for a ticker."""
    try:
        # Map interval to yfinance format
        interval_map = {
            '5m': '5m', '10m': '10m', '15m': '15m', '30m': '30m',
            '1h': '1h', '2h': '2h', '3h': '3h', '4h': '4h',
            '1d': '1d', '1w': '1wk'
        }
        yf_interval = interval_map.get(interval, '1d')
        
        # Calculate period
        period = f"{days}d" if days <= 730 else "2y"
        
        # Fetch data
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=yf_interval)
        
        if df.empty:
            return []
        
        # Convert to list of dicts
        df = df.reset_index()
        df = df.replace({np.nan: None, np.inf: None, -np.inf: None})
        
        records = []
        for _, row in df.iterrows():
            record = {
                'date': row.get('Date', row.get('Datetime', None)),
                'open': float(row['Open']) if pd.notna(row['Open']) else None,
                'high': float(row['High']) if pd.notna(row['High']) else None,
                'low': float(row['Low']) if pd.notna(row['Low']) else None,
                'close': float(row['Close']) if pd.notna(row['Close']) else None,
                'volume': int(row['Volume']) if pd.notna(row['Volume']) else 0
            }
            if record['date']:
                record['date'] = record['date'].isoformat() if hasattr(record['date'], 'isoformat') else str(record['date'])
            records.append(record)
        
        return records
        
    except Exception as e:
        logger.error(f"Error fetching price data for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching price data: {str(e)}")

