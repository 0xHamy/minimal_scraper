from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .models.database import engine, Base, Scan, get_db
from .routers.scans_router import scans_router

Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

# Template-rendering Endpoints
@app.get("/")
def dashboard(request: Request, db: Session = Depends(get_db)):
    total_scans = db.query(Scan).count()
    latest_scan = db.query(Scan).order_by(Scan.timestamp.desc()).first()
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "total_scans": total_scans, "latest_scan": latest_scan}
    )

@app.get("/scans")
def scans_page(request: Request, db: Session = Depends(get_db)):
    scans = get_scans(db)
    return templates.TemplateResponse("scans.html", {"request": request, "scans": scans})

@app.get("/scans/table")
def scans_table(
    request: Request,
    name: str = None,
    status: str = None,
    db: Session = Depends(get_db)
):
    scans = get_scans(db, name, status)
    return templates.TemplateResponse(
        "scans.html",
        {"request": request, "scans": scans},
        block_name="table_content"
    )

# Register Scans Router
app.include_router(scans_router)
