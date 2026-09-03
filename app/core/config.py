# -*- coding: utf-8 -*-
from datetime import date
from pydantic import BaseModel
from typing import Dict, List

# Evaluation reference date from candidate assessment: Wednesday, 19 August 2026
REFERENCE_DATE = date(2026, 8, 19)

class TeamConfig(BaseModel):
    name: str
    inbox_email: str
    sla_limit_working_days: int = 2
    statutory_calendar_enabled: bool = True
    default_assignee: str
    routing_tags: List[str]

# Parameterized team configurations (Answer to Part B3)
TEAM_CONFIGURATIONS: Dict[str, TeamConfig] = {
    "Tax": TeamConfig(
        name="Tax Advisory & Compliance",
        inbox_email="tax-filings@meridian.com",
        sla_limit_working_days=2,
        statutory_calendar_enabled=True,
        default_assignee="Rajesh Sharma (Tax Lead)",
        routing_tags=["GST", "TDS", "IncomeTax", "AdvanceTax", "Filing"]
    ),
    "Legal": TeamConfig(
        name="Corporate Legal Advisory",
        inbox_email="legal@meridian.com",
        sla_limit_working_days=2,
        statutory_calendar_enabled=True,
        default_assignee="Ananya Iyer (Legal Counsel)",
        routing_tags=["ROC", "Contract", "BoardMeeting", "ComplianceNotice"]
    ),
    "Operations": TeamConfig(
        name="Operations & Data Management",
        inbox_email="operations@meridian.com",
        sla_limit_working_days=2,
        statutory_calendar_enabled=False,
        default_assignee="Vikas Verma (Ops Lead)",
        routing_tags=["BankStatement", "Invoicing", "DataReconciliation", "Record"]
    ),
    "Client Servicing": TeamConfig(
        name="Client Relationship & Servicing",
        inbox_email="client-support@meridian.com",
        sla_limit_working_days=1,
        statutory_calendar_enabled=False,
        default_assignee="Pooja Mehta (Client Servicing Lead)",
        routing_tags=["Inquiry", "Escalation", "Onboarding", "GeneralQuery"]
    ),
}
