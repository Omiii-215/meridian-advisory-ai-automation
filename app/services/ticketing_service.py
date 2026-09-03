# -*- coding: utf-8 -*-
from typing import Dict, List, Optional
from datetime import date
from app.models.ticket import Ticket, TicketCreateRequest, TicketUpdateRequest
from app.core.config import REFERENCE_DATE

# Preloaded 10 sample tickets from candidate assessment
INITIAL_TICKETS: List[Dict[str, any]] = [
    {"id": "T-101", "client": "Acme Textiles", "status": "Open", "created_date": "2026-08-10", "next_action_date": "2026-08-13", "statutory_due_date": "2026-08-25", "assigned_owner": None},
    {"id": "T-102", "client": "acme textile", "status": "Open", "created_date": "2026-08-11", "next_action_date": None, "statutory_due_date": "2026-08-20", "assigned_owner": None},
    {"id": "T-103", "client": "Bluewave Foods", "status": "Closed", "created_date": "2026-08-05", "next_action_date": None, "statutory_due_date": None, "assigned_owner": None},
    {"id": "T-104", "client": "Crest Pharma", "status": "Open", "created_date": "2026-08-01", "next_action_date": "2026-08-03", "statutory_due_date": "2026-08-01", "assigned_owner": None},
    {"id": "T-105", "client": "Acme Textiles", "status": "Open", "created_date": "2026-08-10", "next_action_date": "2026-08-13", "statutory_due_date": "2026-08-25", "assigned_owner": None},
    {"id": "T-106", "client": "Delta Logistics", "status": "Pending", "created_date": "2026-08-12", "next_action_date": "2026-08-14", "statutory_due_date": None, "assigned_owner": None},
    {"id": "T-107", "client": "Bluewave Foods", "status": "Open", "created_date": "2026-07-30", "next_action_date": None, "statutory_due_date": "2026-08-18", "assigned_owner": None},
    {"id": "T-108", "client": "Crest Pharma", "status": "Closed", "created_date": "2026-08-10", "next_action_date": None, "statutory_due_date": "2026-08-10", "assigned_owner": None},
    {"id": "T-109", "client": "Everest Retail", "status": "Open", "created_date": "2026-08-13", "next_action_date": "2026-08-15", "statutory_due_date": "2026-09-01", "assigned_owner": None},
    {"id": "T-110", "client": "ACME Textiles Pvt Ltd", "status": "Open", "created_date": "2026-08-09", "next_action_date": "2026-08-11", "statutory_due_date": "2026-08-22", "assigned_owner": None},
]

class TicketingService:
    def __init__(self):
        self._tickets: Dict[str, Ticket] = {}
        self.reset_data()

    def reset_data(self):
        self._tickets.clear()
        for t_data in INITIAL_TICKETS:
            t = Ticket(**t_data)
            t.compute_metrics(REFERENCE_DATE)
            self._tickets[t.id] = t

    def get_all(self, status: Optional[str] = None, only_sla_breaches: bool = False) -> List[Ticket]:
        results = []
        for t in self._tickets.values():
            t.compute_metrics(REFERENCE_DATE)
            if status and t.status.lower() != status.lower():
                continue
            if only_sla_breaches and not t.is_sla_breached:
                continue
            results.append(t)
        return sorted(results, key=lambda x: x.id)

    def get(self, ticket_id: str) -> Optional[Ticket]:
        clean_id = ticket_id.upper().strip()
        t = self._tickets.get(clean_id)
        if t:
            t.compute_metrics(REFERENCE_DATE)
        return t

    def create(self, req: TicketCreateRequest) -> Ticket:
        # Auto-generate next Ticket ID (e.g. T-111)
        existing_nums = [int(tid.replace("T-", "")) for tid in self._tickets.keys() if tid.startswith("T-") and tid.replace("T-", "").isdigit()]
        next_num = max(existing_nums, default=100) + 1
        new_id = f"T-{next_num}"
        
        created = req.created_date or REFERENCE_DATE.strftime("%Y-%m-%d")
        t = Ticket(
            id=new_id,
            client=req.client,
            status=req.status,
            created_date=created,
            next_action_date=req.next_action_date,
            statutory_due_date=req.statutory_due_date,
            assigned_owner=req.assigned_owner or "Unassigned"
        )
        t.compute_metrics(REFERENCE_DATE)
        self._tickets[new_id] = t
        return t

    def update(self, ticket_id: str, req: TicketUpdateRequest) -> Optional[Ticket]:
        t = self.get(ticket_id)
        if not t:
            return None
        
        if req.client is not None:
            t.client = req.client
        if req.status is not None:
            t.status = req.status
        if req.next_action_date is not None:
            t.next_action_date = req.next_action_date if req.next_action_date != "" else None
        if req.statutory_due_date is not None:
            t.statutory_due_date = req.statutory_due_date if req.statutory_due_date != "" else None
        if req.assigned_owner is not None:
            t.assigned_owner = req.assigned_owner

        t.compute_metrics(REFERENCE_DATE)
        self._tickets[t.id] = t
        return t

    def merge_duplicates(self, primary_id: str, duplicate_id: str) -> Dict[str, any]:
        primary = self.get(primary_id)
        duplicate = self.get(duplicate_id)
        if not primary or not duplicate:
            return {"success": False, "message": "One or both tickets not found"}
        
        # Mark duplicate closed with merged note
        duplicate.status = "Closed"
        duplicate.assigned_owner = f"MERGED_INTO_{primary_id}"
        self._tickets[duplicate_id] = duplicate
        return {
            "success": True,
            "message": f"Successfully merged {duplicate_id} into primary ticket {primary_id}.",
            "primary": primary,
            "merged": duplicate
        }

    def canonicalize_clients(self) -> Dict[str, any]:
        """Normalizes inconsistent entity names across Acme Textiles variations."""
        count = 0
        canonical_name = "Acme Textiles Pvt Ltd"
        for t in self._tickets.values():
            if t.client.lower().startswith("acme"):
                t.client = canonical_name
                count += 1
        return {"success": True, "updated_count": count, "canonical_name": canonical_name}

ticketing_service = TicketingService()
