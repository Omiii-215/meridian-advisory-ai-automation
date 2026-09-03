# -*- coding: utf-8 -*-
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "Om S Habib" in data["candidate"]

def test_list_tickets():
    res = client.get("/api/tickets")
    assert res.status_code == 200
    tickets = res.json()
    assert len(tickets) >= 10

def test_audit_anomalies():
    res = client.get("/api/audit/anomalies")
    assert res.status_code == 200
    data = res.json()
    assert data["total_anomalies_found"] >= 7
    codes = [a["code"] for a in data["anomalies"]]
    assert "EXACT_DUPLICATE" in codes
    assert "ENTITY_FRAGMENTATION" in codes
    assert "STATUTORY_DEADLINE_BREACH" in codes

def test_email_ingest_sample_1():
    # Email 1: Bank statement
    payload = {
        "sender": "finance@bluewave.com",
        "subject": "Q2 Records",
        "body": "Hi team, please find attached our Q2 bank statement for your records. Thanks.",
        "has_physical_attachment": True
    }
    res = client.post("/api/email/ingest", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["classification"]["classification_type"] == "DOCUMENT_SUBMISSION"
    assert data["routing_action"] == "ARCHIVE_DOCUMENT_RECORD"

def test_email_ingest_sample_3_ambiguous():
    # Email 3: Urgent with zero context
    payload = {
        "sender": "urgent@client.com",
        "subject": "URGENT",
        "body": "URGENT!! Please handle asap.",
        "has_physical_attachment": False
    }
    res = client.post("/api/email/ingest", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["classification"]["classification_type"] == "AMBIGUOUS_OR_INSUFFICIENT"
    assert data["requires_human_approval"] is True
    assert data["routing_action"] == "HUMAN_TRIAGE_QUEUE"
