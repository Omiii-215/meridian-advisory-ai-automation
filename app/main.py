# -*- coding: utf-8 -*-
import os
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Optional, List, Dict, Any

from app.models.ticket import Ticket, TicketCreateRequest, TicketUpdateRequest
from app.models.email_triage import EmailIngestRequest, IngestResponse
from app.services.ticketing_service import ticketing_service
from app.services.audit_service import run_data_quality_audit
from app.services.email_service import ingest_client_email, human_review_queue
from app.services.reporting_service import generate_daily_exception_report, generate_report_pdf_bytes
from app.core.config import REFERENCE_DATE, TEAM_CONFIGURATIONS

app = FastAPI(
    title="Meridian Advisory - AI Workflow & Ticketing Automation API",
    description="Tool-independent AI-assisted workflow engine for finance and compliance advisory operations.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Health Check & Metadata
# -----------------------------------------------------------------------------
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Meridian Advisory Workflow Automation Engine",
        "candidate": "Om S Habib (Applied via Internshala)",
        "reference_date": REFERENCE_DATE.strftime("%Y-%m-%d"),
        "active_teams": list(TEAM_CONFIGURATIONS.keys())
    }

# -----------------------------------------------------------------------------
# Ticketing Endpoints
# -----------------------------------------------------------------------------
@app.get("/api/tickets", response_model=List[Ticket])
def list_tickets(status: Optional[str] = None, only_sla_breaches: bool = False):
    return ticketing_service.get_all(status=status, only_sla_breaches=only_sla_breaches)

@app.get("/api/tickets/{ticket_id}", response_model=Ticket)
def get_ticket(ticket_id: str):
    t = ticketing_service.get(ticket_id)
    if not t:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return t

@app.post("/api/tickets", response_model=Ticket)
def create_ticket(req: TicketCreateRequest):
    return ticketing_service.create(req)

@app.put("/api/tickets/{ticket_id}", response_model=Ticket)
def update_ticket(ticket_id: str, req: TicketUpdateRequest):
    t = ticketing_service.update(ticket_id, req)
    if not t:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return t

@app.post("/api/tickets/merge")
def merge_duplicate_tickets(primary_id: str = Query(...), duplicate_id: str = Query(...)):
    res = ticketing_service.merge_duplicates(primary_id, duplicate_id)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res

@app.post("/api/tickets/canonicalize")
def canonicalize_clients():
    return ticketing_service.canonicalize_clients()

@app.post("/api/tickets/reset")
def reset_demo_tickets():
    ticketing_service.reset_data()
    return {"success": True, "message": "Demo tickets successfully reset to assessment baseline."}

# -----------------------------------------------------------------------------
# Data Quality Audit & Anomaly Detection (Deliberate Traps Panel)
# -----------------------------------------------------------------------------
@app.get("/api/audit/anomalies")
def get_data_quality_audit():
    return run_data_quality_audit()

# -----------------------------------------------------------------------------
# AI Email Intake & Guardrail Engine
# -----------------------------------------------------------------------------
@app.post("/api/email/ingest", response_model=IngestResponse)
def ingest_email(req: EmailIngestRequest):
    return ingest_client_email(req)

# -----------------------------------------------------------------------------
# Human-in-the-Loop Review Queue
# -----------------------------------------------------------------------------
@app.get("/api/triage/queue")
def get_triage_queue():
    return human_review_queue.get_all()

@app.post("/api/triage/approve")
def approve_triage_item(review_id: str = Query(...), action: str = Query(...), notes: str = Query(default="")):
    item = human_review_queue.approve(review_id, action, notes)
    if not item:
        raise HTTPException(status_code=404, detail=f"Review item {review_id} not found")
    return {"success": True, "item": item}

# -----------------------------------------------------------------------------
# 30-Second Executive Exception Report
# -----------------------------------------------------------------------------
@app.get("/api/reports/daily-exceptions")
def get_daily_exception_report():
    return generate_daily_exception_report()

@app.get("/api/reports/daily-exceptions/pdf")
def download_daily_exception_pdf():
    pdf_bytes = generate_report_pdf_bytes()
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=Meridian_Daily_Compliance_Digest.pdf"}
    )

# -----------------------------------------------------------------------------
# Static Dashboard Mount
# -----------------------------------------------------------------------------
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
