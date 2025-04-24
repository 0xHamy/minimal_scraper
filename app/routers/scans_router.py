from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import base64
import json
import requests
from ..models.database import get_db, SessionLocal, Scan
from ..services.scraper import scrape_posts

scans_router = APIRouter(prefix="/scans", tags=["Scraper Scans Router"])

# Pydantic Models
class ScanCreate(BaseModel):
    name: str
    onion_url: str
    http_proxy: str
    https_proxy: str

class ScanResponse(BaseModel):
    id: int
    name: str
    timestamp: str
    status: str
    onion_url: str
    http_proxy: str
    https_proxy: str
    result: dict  # Decoded JSON result

    class Config:
        from_attributes = True

class ScanCreateResponse(BaseModel):
    message: str
    scan: dict

class ScanListResponse(BaseModel):
    message: str
    scans: list[dict]

class ScanDetailResponse(BaseModel):
    message: str
    scan: dict

class TestConnection(BaseModel):
    onion_url: str
    http_proxy: str
    https_proxy: str

# Database Functions
def create_scan(db: Session, scan: ScanCreate):
    db_scan = Scan(
        name=scan.name,
        onion_url=scan.onion_url,
        http_proxy=scan.http_proxy,
        https_proxy=scan.https_proxy,
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

def test_connection(onion_url: str, http_proxy: str, https_proxy: str):
    """Test connectivity to the onion URL using the provided proxies."""
    proxies = {
        'http': http_proxy,
        'https': https_proxy
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        response = requests.head(onion_url, proxies=proxies, headers=headers, timeout=20)
        response.raise_for_status()
        return True
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection test failed: {str(e)}")

# Background Task
def run_scan(scan_id: int):
    db = SessionLocal()
    try:
        db_scan = get_scan(db, scan_id)
        if not db_scan:
            return
        proxies = {
            'http': db_scan.http_proxy,
            'https': db_scan.https_proxy
        }
        result = scrape_posts(db_scan.onion_url, proxies)
        db_scan.status = "completed"
        db_scan.result = result
        db.commit()
    except Exception as e:
        print(f"Scan error: {str(e)}")
        db_scan = get_scan(db, scan_id)
        if db_scan:
            db_scan.status = "failed"
            db_scan.result = base64.b64encode(json.dumps({"error": str(e)}).encode('utf-8')).decode('utf-8')
            db.commit()
    finally:
        db.close()

# Convert a Scan database object to a dict (with decoded result)
def scan_to_dict(scan: Scan) -> dict:
    """Convert a Scan object to a dictionary with decoded result"""
    result_dict = {"message": "No result available"}
    
    if scan.result:
        try:
            decoded_bytes = base64.b64decode(scan.result)
            decoded_str = decoded_bytes.decode('utf-8')
            result_dict = json.loads(decoded_str)
        except Exception as e:
            print(f"Failed to decode scan result: {str(e)}")
            result_dict = {"error": f"Decoding error: {str(e)}"}
    
    return {
        "id": scan.id,
        "name": scan.name,
        "onion_url": scan.onion_url,
        "http_proxy": scan.http_proxy,
        "https_proxy": scan.https_proxy,
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
            scan_dicts.append({
                "id": scan.id,
                "name": scan.name,
                "onion_url": scan.onion_url,
                "http_proxy": scan.http_proxy,
                "https_proxy": scan.https_proxy,
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

@scans_router.delete("/delete-all")
async def delete_all_scans(db: Session = Depends(get_db)):
    """Delete all scans from the database."""
    try:
        db.query(Scan).delete()
        db.commit()
        return JSONResponse(
            content={"message": "All scans deleted successfully"}
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete scans: {str(e)}")

@scans_router.post("/test-connection")
async def test_connection_endpoint(
    connection: TestConnection,
    db: Session = Depends(get_db)
):
    """Test connectivity to the onion URL using the provided proxies."""
    try:
        test_connection(connection.onion_url, connection.http_proxy, connection.https_proxy)
        return JSONResponse(
            content={"message": "Connection test successful"}
        )
    except HTTPException as e:
        raise e