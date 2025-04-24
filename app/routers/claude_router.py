from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import base64
import json
from ..models.database import get_db, SessionLocal, Scan, AIReport
from ..services.claude import claude_classify

claude_router = APIRouter(prefix="/claude", tags=["Claude AI Router"])

class StartClassification(BaseModel):
    scan_id: int
    api_key: str
    model_name: str
    temperature: float = 0.1
    max_tokens: int = 100

def classify_posts(scan: Scan, api_key: str, model_name: str, temperature: float, max_tokens: int):
    try:
        decoded_result = base64.b64decode(scan.result).decode('utf-8')
        posts_data = json.loads(decoded_result)
        posts = posts_data.get('posts', [])

        classified_posts = []
        for post in posts:
            content_base64 = post.get('content', '')
            content = base64.b64decode(content_base64).decode('utf-8')
            classification_result = claude_classify(
                api_key=api_key,
                model_name=model_name,
                post_content=content,
                max_tokens=max_tokens,
                temperature=temperature
            )
            classified_posts.append({
                "content": content,
                "classification": classification_result.get("classification"),
                "scores": classification_result.get("scores")
            })

        return {"posts": classified_posts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")

def run_classification(report_id: int, scan_id: int, api_key: str, model_name: str, temperature: float, max_tokens: int):
    db = SessionLocal()
    try:
        db_report = db.query(AIReport).filter(AIReport.id == report_id).first()
        if not db_report:
            return

        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            db_report.status = "failed"
            db_report.classification = json.dumps({"error": "Scan not found"})
            db.commit()
            return

        classification_result = classify_posts(scan, api_key, model_name, temperature, max_tokens)
        db_report.status = "completed"
        db_report.classification = json.dumps(classification_result)
        db.commit()
    except Exception as e:
        db_report.status = "failed"
        db_report.classification = json.dumps({"error": str(e)})
        db.commit()
    finally:
        db.close()

@claude_router.post("/start-classification", status_code=201)
async def start_classification_endpoint(
    classification: StartClassification,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    scan = db.query(Scan).filter(Scan.id == classification.scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    db_report = AIReport(
        scan_id=scan.id,
        name=scan.name,  # Use the scan's name
        timestamp=datetime.utcnow(),
        status="running",
        classification=""
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)

    background_tasks.add_task(
        run_classification,
        db_report.id,
        scan.id,
        classification.api_key,
        classification.model_name,
        classification.temperature,
        classification.max_tokens
    )

    return JSONResponse(
        content={"message": "Classification started", "report_id": db_report.id}
    )

@claude_router.get("/reports/{report_id}")
async def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(AIReport).filter(AIReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return JSONResponse(content={"classification": report.classification})

