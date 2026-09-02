from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Report
from app.schemas import ReportDetail, ReportSummary

router = APIRouter()


@router.get("/reports", response_model=list[ReportSummary])
def list_reports(db: Session = Depends(get_db)):
    reports = db.execute(select(Report).order_by(Report.created_at.desc())).scalars().all()
    return reports


@router.get("/reports/{report_id}", response_model=ReportDetail)
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found.")
    return report


@router.delete("/reports/{report_id}", status_code=204)
def delete_report(report_id: int, db: Session = Depends(get_db)):
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found.")
    db.delete(report)
    db.commit()
    return None
