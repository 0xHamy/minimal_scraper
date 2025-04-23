from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from ..models.database import get_db, SessionLocal, Scan
from ..scraper.scraper import scrape_posts

scans_router = APIRouter(prefix="/scans", tags=["Scraper Scans Router"])

# Pydantic Models
class ScanCreate(BaseModel):
    name: str

class ScanResponse(BaseModel):
    id: int
    name: str
    timestamp: str  # Changed to str for JSON serialization
    status: str
    result: str

    class Config:
        from_attributes = True

class ScanCreateResponse(BaseModel):
    message: str
    scan: ScanResponse

class ScanListResponse(BaseModel):
    message: str
    scans: list[ScanResponse]

# Database Functions
def create_scan(db: Session, scan: ScanCreate):
    db_scan = Scan(
        name=scan.name,
        timestamp=datetime.utcnow(),
        status="running",
        result=""
    )
    db.add(db_scan)
    db.commit()
    db.refresh(db_scan)
    return db_scan

def get_scan(db: Session, scan_id: int):
    return db.query(Scan).filter(Scan.id == scan_id).first()

def get_scans(db: Session, name: str = None, status: str = None):
    query = db.query(Scan)
    if name:
        query = query.filter(Scan.name.contains(name))
    if status:
        query = query.filter(Scan.status == status)
    return query.all()

# Background Task
def run_scan(scan_id: int):
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

# API Endpoints
@scans_router.post("/create-scan", response_model=ScanCreateResponse, status_code=201)
async def create_scan_endpoint(
    scan: ScanCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_scan = create_scan(db, scan)
    background_tasks.add_task(run_scan, db_scan.id)
    # Convert datetime to ISO string for JSON serialization
    scan_response = ScanResponse(
        id=db_scan.id,
        name=db_scan.name,
        timestamp=db_scan.timestamp.isoformat(),
        status=db_scan.status,
        result=db_scan.result
    )
    return JSONResponse(
        content={"message": "Scan started", "scan": scan_response.dict()}
    )

@scans_router.get("/list", response_model=ScanListResponse)
async def list_scans_endpoint(
    name: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db)
):
    scans = get_scans(db, name, status)
    # Convert datetime to ISO string for each scan
    scan_responses = [
        ScanResponse(
            id=scan.id,
            name=scan.name,
            timestamp=scan.timestamp.isoformat(),
            status=scan.status,
            result=scan.result
        ) for scan in scans
    ]
    return JSONResponse(
        content={"message": "Scans retrieved", "scans": [s.dict() for s in scan_responses]}
    )