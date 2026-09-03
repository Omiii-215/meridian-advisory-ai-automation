# -*- coding: utf-8 -*-
from typing import Optional, List, Literal
from pydantic import BaseModel, Field

class TicketReference(BaseModel):
    has_ticket_id: bool = False
    ticket_id: Optional[str] = None
    quote_text: Optional[str] = None

class ExtractedDueDate(BaseModel):
    has_date: bool = False
    raw_text: Optional[str] = None
    normalized_date: Optional[str] = None
    is_relative: bool = False
    is_statutory: bool = False
    quote_text: Optional[str] = None

class ClassificationResult(BaseModel):
    classification_type: Literal[
        "NEW_SERVICE_REQUEST",
        "EXISTING_TICKET_UPDATE",
        "DOCUMENT_SUBMISSION",
        "GENERAL_INQUIRY",
        "IRRELEVANT_OR_SPAM",
        "AMBIGUOUS_OR_INSUFFICIENT"
    ]
    ticket_reference: TicketReference
    urgency: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]
    urgency_rationale: str
    extracted_due_date: ExtractedDueDate
    context_completeness: Literal["COMPLETE", "PARTIAL", "INSUFFICIENT"]
    missing_elements: List[str] = []
    confidence_score: float = Field(ge=0.0, le=1.0)
    is_confident: bool
    uncertainty_reasons: List[str] = []
    recommended_action: Literal[
        "ROUTE_TO_TEAM_QUEUE",
        "APPEND_TO_EXISTING_TICKET",
        "ARCHIVE_DOCUMENT_RECORD",
        "HUMAN_MANUAL_TRIAGE",
        "AUTO_DISCARD"
    ]

class EmailIngestRequest(BaseModel):
    sender: str
    subject: str
    body: str
    in_reply_to: Optional[str] = None
    references: Optional[str] = None
    has_physical_attachment: bool = False
    received_date: Optional[str] = "2026-08-19"
    team: Optional[str] = "Tax"

class IngestResponse(BaseModel):
    success: bool
    email_id: str
    routing_action: str
    message: str
    classification: ClassificationResult
    tripwires_passed: bool
    tripwire_warnings: List[str] = []
    requires_human_approval: bool = False
    assigned_ticket_id: Optional[str] = None
    is_duplicate_thread: bool = False
