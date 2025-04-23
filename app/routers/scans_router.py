from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import base64
import json
from ..models.database import get_db, SessionLocal, Scan
from ..scraper.scraper import scrape_posts

scans_router = APIRouter(prefix="/scans", tags=["Scraper Scans Router"])

# Pydantic Models
class ScanCreate(BaseModel):
    name: str

class ScanResponse(BaseModel):
    id: int
    name: str
    timestamp: str
    status: str
    result: dict  # Decoded JSON result

    class Config:
        from_attributes = True

class ScanCreateResponse(BaseModel):
    message: str
    scan: dict  # Changed to dict to avoid validation issues

class ScanListResponse(BaseModel):
    message: str
    scans: list[dict]  # Changed to list of dicts

class ScanDetailResponse(BaseModel):
    message: str
    scan: dict  # Changed to dict

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
        # Encode result as base64 JSON for storage
        encoded_result = base64.b64encode(json.dumps(result).encode('utf-8')).decode('utf-8')
        db_scan = get_scan(db, scan_id)
        if not db_scan:
            return
        db_scan.status = "completed"
        db_scan.result = encoded_result
        db.commit()
    except Exception as e:
        print(f"Scan error: {str(e)}")
        db_scan = get_scan(db, scan_id)
        if db_scan:
            db_scan.status = "failed"
            db_scan.result = base64.b64encode(json.dumps({"error": "Scan failed"}).encode('utf-8')).decode('utf-8')
            db.commit()
    finally:
        db.close()

# Convert a Scan database object to a dict (with decoded result)
def scan_to_dict(scan: Scan) -> dict:
    """Convert a Scan object to a dictionary with decoded result"""
    result_dict = {"message": "No result available"}
    
    if scan.result:
        try:
            # Step 1: Decode base64 to bytes
            decoded_bytes = base64.b64decode(scan.result)
            
            # Step 2: Convert bytes to string
            decoded_str = decoded_bytes.decode('utf-8')
            
            # Step 3: Parse JSON string to dict
            result_dict = json.loads(decoded_str)
        except Exception as e:
            print(f"Failed to decode scan result: {str(e)}")
            result_dict = {"error": f"Decoding error: {str(e)}"}
    
    # Create a dictionary representation
    return {
        "id": scan.id,
        "name": scan.name,
        "timestamp": scan.timestamp.isoformat(),
        "status": scan.status,
        "result": result_dict
    }

# API Endpoints
@scans_router.post("/create-scan", status_code=201)
async def create_scan_endpoint(
    scan: ScanCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_scan = create_scan(db, scan)
    background_tasks.add_task(run_scan, db_scan.id)
    
    scan_dict = scan_to_dict(db_scan)
    
    return JSONResponse(
        content={"message": "Scan started", "scan": scan_dict}
    )

@scans_router.get("/list")
async def list_scans_endpoint(
    name: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db)
):
    scans = get_scans(db, name, status)
    scan_dicts = []
    
    for scan in scans:
        try:
            scan_dict = scan_to_dict(scan)
            scan_dicts.append(scan_dict)
        except Exception as e:
            print(f"Error processing scan {scan.id}: {str(e)}")
            # Include error information
            scan_dicts.append({
                "id": scan.id,
                "name": scan.name,
                "timestamp": scan.timestamp.isoformat() if scan.timestamp else None,
                "status": scan.status,
                "result": {"error": f"Processing error: {str(e)}"}
            })
    
    return JSONResponse(
        content={"message": "Scans retrieved", "scans": scan_dicts}
    )

@scans_router.get("/{scan_id}")
async def get_scan_endpoint(
    scan_id: int,
    db: Session = Depends(get_db)
):
    db_scan = get_scan(db, scan_id)
    if not db_scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    scan_dict = scan_to_dict(db_scan)
    
    return JSONResponse(
        content={"message": "Scan retrieved", "scan": scan_dict}
    )