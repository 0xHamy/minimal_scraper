from fastapi import APIRouter, Depends, BackgroundTasks, JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from ..models.database import get_db, SessionLocal
from ..services.scan_tracker import create_scan, get_scans, get_scan
from ..scraper.scraper import scrape_posts

scans_router = APIRouter(prefix="/scans", tags=["Scraper Scans Router"])

# Pydantic Models
class ScanCreate(BaseModel):
    name: str

class ScanResponse(BaseModel):
    id: int
    name: str
    timestamp: datetime
    status: str
    result: str

    class Config:
        from_attributes = True

class ScanApiResponse(BaseModel):
    message: str
    scan: ScanResponse | None = None
    scans: list[ScanResponse] | None = None

def run_scan(scan_id: int):
    """Background task to run the scraper and update scan status."""
    db = SessionLocal()
    try:
        result = scrape_posts()
        db_scan = get_scan(db, scan_id)
        if not db_scan:
            return
        db_scan.status = "completed"
        db_scan.result = result
        db.commit()
    except Exception:
        db_scan = get_scan(db, scan_id)
        if db_scan:
            db_scan.status = "failed"
            db.commit()
    finally:
        db.close()

@scans_router.post("", response_model=ScanApiResponse)
async def scans_endpoint(
    scan: ScanCreate | None = None,
    name: str | None = None,
    status: str | None = None,
    background_tasks: BackgroundTasks = Depends(),
    db: Session = Depends(get_db)
):
    if scan and scan.name:
        # Create a new scan
        db_scan = create_scan(db, scan)
        background_tasks.add_task(run_scan, db_scan.id)
        return JSONResponse(
            status_code=202,
            content={"message": "Scan started", "scan": ScanResponse.from_orm(db_scan).dict()}
        )
    else:
        # List scans with optional filters
        scans = get_scans(db, name, status)
        return JSONResponse(
            status_code=200,
            content={"message": "Scans retrieved", "scans": [ScanResponse.from_orm(s).dict() for s in scans]}
        )

