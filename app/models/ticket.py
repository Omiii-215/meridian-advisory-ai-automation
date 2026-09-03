# -*- coding: utf-8 -*-
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.core.config import REFERENCE_DATE
from app.core.calendar import count_working_days_elapsed, is_working_day

class TicketBase(BaseModel):
    id: str
    client: str
    status: str = Field(default="Open", description="Open, Pending, or Closed")
    created_date: str
    next_action_date: Optional[str] = None
    statutory_due_date: Optional[str] = None
    assigned_owner: Optional[str] = None

class Ticket(TicketBase):
    # Dynamic computed fields based on REFERENCE_DATE (2026-08-19)
    working_days_open_without_action: Optional[int] = None
    working_days_lapsed_past_action: Optional[int] = None
    is_sla_breached: bool = False
    sla_status_label: str = "COMPLIANT"
    is_statutory_overdue: bool = False
    is_statutory_imminent: bool = False
    statutory_days_diff: Optional[int] = None
    weekend_warnings: List[str] = []

    def compute_metrics(self, today: date = REFERENCE_DATE):
        c_dt = datetime.strptime(self.created_date, "%Y-%m-%d").date()
        na_dt = datetime.strptime(self.next_action_date, "%Y-%m-%d").date() if self.next_action_date else None
        s_dt = datetime.strptime(self.statutory_due_date, "%Y-%m-%d").date() if self.statutory_due_date else None
        
        self.weekend_warnings = []
        if not is_working_day(c_dt):
            self.weekend_warnings.append(f"Created on non-business day ({c_dt.strftime('%A')})")
        if na_dt and not is_working_day(na_dt):
            self.weekend_warnings.append(f"Next Action scheduled on weekend ({na_dt.strftime('%A')})")
        if s_dt and not is_working_day(s_dt):
            self.weekend_warnings.append(f"Statutory Due Date falls on weekend ({s_dt.strftime('%A')})")

        # Statutory calculations
        if s_dt:
            diff = (today - s_dt).days
            self.statutory_days_diff = diff
            if diff > 0 and self.status != "Closed":
                self.is_statutory_overdue = True
            elif diff == -1 and self.status != "Closed": # Due tomorrow
                self.is_statutory_imminent = True
            elif diff == 0 and self.status != "Closed": # Due today
                self.is_statutory_imminent = True

        # SLA Breach calculations (5-day working week, > 2 working days)
        if self.status in ["Open", "Pending"]:
            if not na_dt:
                # Interpretation A: Open with NO Next Action Date
                wd, _ = count_working_days_elapsed(c_dt, today)
                self.working_days_open_without_action = wd
                if wd > 2:
                    self.is_sla_breached = True
                    self.sla_status_label = f"BREACH ({wd}d open without action)"
            else:
                # Interpretation B: Next Action Date lapsed by > 2 working days
                if na_dt < today:
                    wd_lapsed, _ = count_working_days_elapsed(na_dt, today)
                    self.working_days_lapsed_past_action = wd_lapsed
                    if wd_lapsed > 2:
                        self.is_sla_breached = True
                        self.sla_status_label = f"BREACH ({wd_lapsed}d overdue)"
                    elif wd_lapsed == 2:
                        self.sla_status_label = "AT SLA LIMIT (2d overdue)"
                    else:
                        self.sla_status_label = f"PENDING ({wd_lapsed}d overdue)"
                else:
                    self.sla_status_label = "ON TRACK"
        else:
            self.sla_status_label = "CLOSED"

class TicketCreateRequest(BaseModel):
    client: str
    status: str = "Open"
    created_date: Optional[str] = None
    next_action_date: Optional[str] = None
    statutory_due_date: Optional[str] = None
    assigned_owner: Optional[str] = None

class TicketUpdateRequest(BaseModel):
    client: Optional[str] = None
    status: Optional[str] = None
    next_action_date: Optional[str] = None
    statutory_due_date: Optional[str] = None
    assigned_owner: Optional[str] = None
