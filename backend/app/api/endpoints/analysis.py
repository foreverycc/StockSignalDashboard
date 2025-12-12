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
        # Append Z to indicate UTC timezone, as timestamps in DB are naive UTC
        "timestamp": r.timestamp.isoformat() + "Z", 
        "status": r.status,
        "stock_list_name": r.stock_list_name
    } for r in runs]

@router.get("/runs/{run_id}/results/{result_type}")
async def get_analysis_result(
    run_id: int, 
    result_type: str, 
    ticker: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get specific results for a run, optionally filtered by ticker."""
    
    # 1. First check if we have individual rows stored for this result_type + ticker
    # This matches usage where we might store per-ticker items (not currently used for big blobs, but good practice)
    query = db.query(AnalysisResult).filter(
        AnalysisResult.run_id == run_id,
        AnalysisResult.result_type == result_type
    )
    
    if ticker:
        # If filtering by ticker, only return results for that ticker
        # Note: If data is stored in a master blob with no ticker column, this query might return empty or everything depending on storage
        # Our Logic: "ALL" items usually have ticker='ALL'. Specific items have ticker='AAPL'.
        # If user asks for 'AAPL' and we stored 'AAPL' separately, good.
        # If we stored "ALL" containing 'AAPL', we must fetch "ALL" and filter in python.
        
        # Try finding specific entry first
        specific_result = query.filter(AnalysisResult.ticker == ticker).all()
        if specific_result:
            results = []
            for res in specific_result:
                if res.data:
                    # If data is a list, extend. If dict, append.
                    if isinstance(res.data, list):
                        results.extend(res.data)
                    else:
                        results.append(res.data)
            return results
            
    # 2. Fallback or "ALL" query
    # Fetch generic result (ticker="ALL")
    generic_results = query.filter(AnalysisResult.ticker == "ALL").all()
    
    combined_data = []
    for res in generic_results:
        if res.data:
            if isinstance(res.data, list):
                combined_data.extend(res.data)
            else:
                combined_data.append(res.data)
                
    # 3. Apply Ticker Filtering in Python if we fetched a blob and user wants specific ticker
    if ticker and combined_data:
        # Filter the list of dictionaries
        filtered_data = [
            item for item in combined_data 
            if isinstance(item, dict) and item.get('ticker') == ticker
        ]
        return filtered_data
        
    return combined_data

@router.get("/price_history/{ticker}/{interval}")
async def get_price_history(
    ticker: str,
    interval: str,
    db: Session = Depends(get_db)
):
    """Get price history for a ticker with computed signals."""
    
    # Fetch from DB
    prices = db.query(PriceBar).filter(
        PriceBar.ticker == ticker,
        PriceBar.interval == interval
    ).order_by(PriceBar.timestamp).all()
    
    if not prices:
        return []

    # Convert to DataFrame for indicator calculation
    # We used "Open", "High", "Low", "Close", "Volume" in indicators.py (Case Sensitive often in pandas? logic uses dict keys usually)
    # The indicators.py likely expects DataFrame columns. Let's check keys.
    # Usually yfinance gives Capitalized. indicators.py likely uses Capitalized.
    
    data = [{
        "timestamp": p.timestamp,
        "Open": p.open,
        "High": p.high,
        "Low": p.low,
        "Close": p.close,
        "Volume": p.volume
    } for p in prices]
    
    df = pd.DataFrame(data)
    if df.empty:
        return []
        
    df.set_index("timestamp", inplace=True)
    
    # Compute Indicators
    try:
        cd_signals = compute_cd_indicator(df)
        mc_signals = compute_mc_indicator(df)
        
        # Fill NaNs with False
        cd_signals = cd_signals.fillna(False).astype(bool)
        mc_signals = mc_signals.fillna(False).astype(bool)
    except Exception as e:
        logger.error(f"Error computing indicators for {ticker}: {e}")
        # Fallback to no signals if error
        cd_signals = pd.Series(False, index=df.index)
        mc_signals = pd.Series(False, index=df.index)

    # Construct response
    response = []
    for p in prices:
        # p.timestamp is naive usually. Ensure alignment with df index.
        ts = p.timestamp
        is_cd = bool(cd_signals.get(ts, False))
        is_mc = bool(mc_signals.get(ts, False))
        
        response.append({
            "time": p.timestamp.isoformat(),
            "open": p.open,
            "high": p.high,
            "low": p.low,
            "close": p.close,
            "volume": p.volume,
            "cd_signal": is_cd,
            "mc_signal": is_mc
        })
        
    return response
