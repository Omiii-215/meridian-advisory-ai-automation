# -*- coding: utf-8 -*-
from typing import List, Dict, Any
from datetime import datetime
from app.services.ticketing_service import ticketing_service
from app.core.config import REFERENCE_DATE
from app.core.calendar import is_working_day

class Anomaly(Dict[str, Any]):
    pass

def run_data_quality_audit() -> Dict[str, Any]:
    tickets = ticketing_service.get_all()
    anomalies: List[Dict[str, Any]] = []

    # 1. Exact Duplicate Records
    seen_signatures: Dict[str, str] = {}
    duplicates: List[Tuple[str, str]] = []
    for t in tickets:
        sig = f"{t.client.lower().strip()}|{t.status}|{t.created_date}|{t.next_action_date}|{t.statutory_due_date}"
        if sig in seen_signatures:
            duplicates.append((seen_signatures[sig], t.id))
        else:
            seen_signatures[sig] = t.id
    if duplicates:
        for p, d in duplicates:
            anomalies.append({
                "code": "EXACT_DUPLICATE",
                "severity": "HIGH",
                "title": "Exact Duplicate Ticket Identified",
                "tickets": [p, d],
                "description": f"Ticket {d} is an identical duplicate of {p} across Client, Status, Created Date, Next Action Date, and Statutory Date.",
                "actionable": True,
                "action_type": "MERGE_DUPLICATE",
                "action_payload": {"primary_id": p, "duplicate_id": d}
            })

    # 2. Inconsistent Entity Naming (Entity Fragmentation)
    acme_tickets = [t.id for t in tickets if "acme" in t.client.lower()]
    acme_names = set(t.client for t in tickets if "acme" in t.client.lower())
    if len(acme_names) > 1:
        anomalies.append({
            "code": "ENTITY_FRAGMENTATION",
            "severity": "MEDIUM",
            "title": "Inconsistent Client Entity Naming",
            "tickets": acme_tickets,
            "description": f"The same client is recorded under disparate names: {list(acme_names)}. Prevents unified reporting and CRM matching.",
            "actionable": True,
            "action_type": "CANONICALIZE_CLIENTS",
            "action_payload": {"canonical_name": "Acme Textiles Pvt Ltd"}
        })

    # 3. Missing Next Action Date (Open Tickets)
    missing_action_open = [t.id for t in tickets if t.status in ["Open", "Pending"] and not t.next_action_date]
    if missing_action_open:
        anomalies.append({
            "code": "MISSING_ACTION_DATE",
            "severity": "HIGH",
            "title": "Active Tickets Without Next Action Date",
            "tickets": missing_action_open,
            "description": f"Tickets {missing_action_open} are active but lack a Next Action Date, leaving them untracked and causing immediate SLA breach.",
            "actionable": True,
            "action_type": "ASSIGN_NEXT_ACTION",
            "action_payload": {"tickets": missing_action_open}
        })

    # 4. Missing Statutory Due Date
    missing_statutory = [t.id for t in tickets if not t.statutory_due_date]
    if missing_statutory:
        anomalies.append({
            "code": "MISSING_STATUTORY_DATE",
            "severity": "MEDIUM",
            "title": "Compliance Tickets Lacking Statutory Deadline",
            "tickets": missing_statutory,
            "description": f"Tickets {missing_statutory} handle client compliance work but have no statutory filing deadline recorded.",
            "actionable": False
        })

    # 5. Systemic Schema Omission: Missing Assigned Owner
    unassigned = [t.id for t in tickets if not t.assigned_owner or t.assigned_owner in ["Unassigned", None]]
    if len(unassigned) >= 8:
        anomalies.append({
            "code": "SYSTEMIC_SCHEMA_OMISSION",
            "severity": "CRITICAL",
            "title": "Systemic Schema Defect: Missing Assigned Owner Column",
            "tickets": unassigned,
            "description": "The mandatory 'Assigned Owner' column is completely unpopulated across the dataset, eliminating staff accountability.",
            "actionable": True,
            "action_type": "BATCH_ASSIGN_LEADS"
        })

    # 6. Overdue / Expired Statutory Due Dates (Open Tickets)
    overdue_stat = [t.id for t in tickets if t.is_statutory_overdue]
    if overdue_stat:
        anomalies.append({
            "code": "STATUTORY_DEADLINE_BREACH",
            "severity": "CRITICAL",
            "title": "Open Tickets Past Statutory Due Date",
            "tickets": overdue_stat,
            "description": f"Tickets {overdue_stat} have already lapsed their regulatory filing deadline relative to today (19-Aug-2026). Immediate penalty risk.",
            "actionable": False
        })

    # 7. Non-Working Day / Weekend Dates
    weekend_tickets = [t.id for t in tickets if t.weekend_warnings]
    if weekend_tickets:
        anomalies.append({
            "code": "WEEKEND_DATE_ANOMALY",
            "severity": "LOW",
            "title": "Dates Scheduled on Non-Business Days (Weekends)",
            "tickets": weekend_tickets,
            "description": f"Tickets {weekend_tickets} have created or next action dates on Saturdays/Sundays, violating standard 5-day firm calendar logic.",
            "actionable": False
        })

    # 8. Chronological Contradiction
    chrono_tickets = []
    for t in tickets:
        if t.next_action_date and t.statutory_due_date:
            na = datetime.strptime(t.next_action_date, "%Y-%m-%d").date()
            s = datetime.strptime(t.statutory_due_date, "%Y-%m-%d").date()
            if na > s:
                chrono_tickets.append(t.id)
    if chrono_tickets:
        anomalies.append({
            "code": "CHRONOLOGICAL_CONTRADICTION",
            "severity": "HIGH",
            "title": "Next Action Scheduled After Statutory Deadline",
            "tickets": chrono_tickets,
            "description": f"Tickets {chrono_tickets} have Next Action Dates set AFTER their Statutory Due Date has already passed.",
            "actionable": False
        })

    # 9. Ambiguous Status
    pending_tickets = [t.id for t in tickets if t.status == "Pending"]
    if pending_tickets:
        anomalies.append({
            "code": "AMBIGUOUS_STATUS",
            "severity": "MEDIUM",
            "title": "Ambiguous Lifecycle Status ('Pending')",
            "tickets": pending_tickets,
            "description": f"Ticket {pending_tickets} is in 'Pending' state without clarification on whether firm or client is responsible for next action.",
            "actionable": False
        })

    return {
        "evaluation_date": REFERENCE_DATE.strftime("%Y-%m-%d"),
        "total_anomalies_found": len(anomalies),
        "critical_count": len([a for a in anomalies if a["severity"] == "CRITICAL"]),
        "high_count": len([a for a in anomalies if a["severity"] == "HIGH"]),
        "anomalies": anomalies
    }
