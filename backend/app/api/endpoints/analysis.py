import os
import pandas as pd
import numpy as np
import yfinance as yf
import logging
import traceback
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.services.engine import job_manager
from app.logic.indicators import compute_cd_indicator, compute_mc_indicator
from app.db.database import SessionLocal
from app.db.models import AnalysisRun, AnalysisResult, PriceBar
from app.logic.db_utils import save_price_history

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
        # job_manager still manages the background thread/process
        # The process itself now writes to DB
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

@router.get("/runs")
async def get_analysis_runs(db: Session = Depends(get_db)):
    """List all analysis runs."""
    runs = db.query(AnalysisRun).order_by(desc(AnalysisRun.timestamp)).all()
    return [{
        "id": r.id,
        "timestamp": r.timestamp.isoformat(),
        "status": r.status,
        "stock_list_name": r.stock_list_name
    } for r in runs]

@router.get("/runs/{run_id}/results/{result_type}")
async def get_analysis_result(run_id: int, result_type: str, db: Session = Depends(get_db)):
    """Get specific results for a run."""
    # Try to find a single record first (summary tables are stored as one row with JSON data)
    result = db.query(AnalysisResult).filter(
        AnalysisResult.run_id == run_id,
        AnalysisResult.result_type == result_type
    ).first()
    
    if result and result.data:
        data = result.data
        # If it's a list, return it directly (it's likely a summary table)
        if isinstance(data, list):
             return data
        # If it's a dict, valid JSON object
        return data

    # If no single record, check if it's aggregated from multiple rows
    # (Not used in current stock_analyzer.py refactor, but for future proofing)
    results = db.query(AnalysisResult).filter(
        AnalysisResult.run_id == run_id,
        AnalysisResult.result_type == result_type
    ).all()
    
    if not results:
        # Fallback for empty results (return empty list instead of 404 to be friendly to frontend)
        return []

    return [r.data for r in results]


@router.get("/logs")
async def get_logs(lines: int = 100):
    """Get the last N lines of the server log."""
    log_file = 'backend_server.log'
    if not os.path.exists(log_file):
        return {"logs": []}
    
    try:
        with open(log_file, 'r') as f:
            # Efficiently read last N lines
            all_lines = f.readlines()
            return {"logs": [line.strip() for line in all_lines[-lines:]]}
    except Exception as e:
        return {"logs": [f"Error reading logs: {str(e)}"]}


@router.get("/price_history/{ticker}/{interval}")
async def get_price_history(
    ticker: str,
    interval: str,
    db: Session = Depends(get_db)
):
    """Get OHLCV price data for a ticker with calculated signals."""
    days = 60 # Default period length
    ticker_upper = ticker.upper()
    
    try:
        # 1. Try to fetch from Database
        # We need to sort by timestamp
        prices = db.query(PriceBar).filter(
            PriceBar.ticker == ticker_upper,
            PriceBar.interval == interval
        ).order_by(PriceBar.timestamp).all()
        
        df = None
        if prices:
            # Convert to DataFrame
            data = []
            for p in prices:
                data.append({
                    'Date': p.timestamp,
                    'Open': p.open,
                    'High': p.high,
                    'Low': p.low,
                    'Close': p.close,
                    'Volume': p.volume
                })
            df = pd.DataFrame(data).set_index('Date')

        # 2. If not in DB or empty, fetch from yfinance
        if df is None or df.empty:
            # Map interval to yfinance format
            interval_map = {
                '5m': '5m', '10m': '10m', '15m': '15m', '30m': '30m',
                '1h': '1h', '2h': '2h', '3h': '3h', '4h': '4h',
                '1d': '1d', '1w': '1wk'
            }
            yf_interval = interval_map.get(interval, '1d')
            period = f"{days}d" if days <= 730 else "2y"
            
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=yf_interval)
            
            if df.empty:
                return []
            
            # Save to DB for next time
            # Note: This might be slow for a read endpoint if saving many rows
            # But it ensures consistency.
            # Convert Index to naive datetime before saving? 
            # save_price_history handles timezone conversion.
            try:
               save_price_history(ticker_upper, interval, df)
            except Exception as e:
               logger.error(f"Failed to save fetched data to DB: {e}")

        # 3. Process Data (Timezone & Signals)
        # Ensure index is datetime
        if df.index.tzinfo is not None:
             df.index = df.index.tz_convert('America/New_York').tz_localize(None)
        
        # Calculate Signals on-the-fly
        try:
            cd_signals = compute_cd_indicator(df)
            mc_signals = compute_mc_indicator(df)
        except Exception as e:
            logger.warning(f"Error computing signals for {ticker}: {e}")
            cd_signals = pd.Series(False, index=df.index)
            mc_signals = pd.Series(False, index=df.index)

        # Format response
        records = []
        for date, row in df.iterrows():
            if pd.isna(row['Open']) or pd.isna(row['Close']):
                continue
            
            try:
                is_cd = bool(cd_signals.loc[date]) if date in cd_signals.index and pd.notna(cd_signals.loc[date]) else False
            except Exception:
                is_cd = False
                
            try:
                is_mc = bool(mc_signals.loc[date]) if date in mc_signals.index and pd.notna(mc_signals.loc[date]) else False
            except Exception:
                is_mc = False

            record = {
                'time': date.isoformat(),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': int(row['Volume']) if pd.notna(row['Volume']) else 0,
                'cd_signal': is_cd,
                'mc_signal': is_mc
            }
            records.append(record)
            
        return records
        
    except Exception as e:
        logger.error(f"Error fetching price data for {ticker}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching price data: {str(e)}")
