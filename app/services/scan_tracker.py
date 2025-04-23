from sqlalchemy.orm import Session
from ..models.scan import Scan
from ..schemas.scan_create import ScanCreate
from ..schemas.scan import Scan as ScanSchema
from datetime import datetime

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

