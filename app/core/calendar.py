# -*- coding: utf-8 -*-
from datetime import date, timedelta
from typing import List, Tuple, Optional, Dict

def is_working_day(d: date) -> bool:
    """Returns True if the day falls between Monday and Friday (standard 5-day week)."""
    return d.weekday() < 5

def count_working_days_elapsed(start: date, end: date) -> Tuple[int, List[date]]:
    """
    Computes the number of business days elapsed strictly after start date up to and including end date.
    Excludes Saturdays and Sundays.
    """
    if start >= end:
        return 0, []
    
    cur = start + timedelta(days=1)
    working_days = []
    while cur <= end:
        if is_working_day(cur):
            working_days.append(cur)
        cur += timedelta(days=1)
    return len(working_days), working_days

def add_working_days(start: date, n_days: int) -> date:
    """Adds n working days to a start date, skipping weekends."""
    cur = start
    added = 0
    while added < n_days:
        cur += timedelta(days=1)
        if is_working_day(cur):
            added += 1
    return cur

# Master Statutory Compliance Calendar (Authoritative Source of Truth)
# Used to deterministically validate compliance dates rather than relying on AI guessing
MASTER_STATUTORY_CALENDAR: Dict[str, Dict[str, any]] = {
    "GST_GSTR3B": {
        "name": "GST Monthly Return (GSTR-3B)",
        "day_of_month": 20,
        "description": "Monthly summary return for outward and inward supplies with tax payment",
        "grace_period_days": 0
    },
    "GST_GSTR1": {
        "name": "GST Outward Supplies (GSTR-1)",
        "day_of_month": 11,
        "description": "Monthly statement of outward supplies",
        "grace_period_days": 0
    },
    "TDS_PAYMENT": {
        "name": "TDS Deposit Payment",
        "day_of_month": 7,
        "description": "Monthly deposit of tax deducted at source",
        "grace_period_days": 0
    },
    "ADVANCE_TAX_Q2": {
        "name": "Advance Tax Installment (Q2)",
        "fixed_date": "2026-09-15",
        "description": "Second statutory installment of advance tax (45%)",
        "grace_period_days": 0
    }
}

def lookup_statutory_deadline(service_keyword: str, reference_year: int = 2026, reference_month: int = 8) -> Optional[date]:
    """Deterministically queries the official regulatory schedule."""
    kw = service_keyword.upper()
    if "GST" in kw or "GSTR" in kw:
        return date(reference_year, reference_month, 20)
    elif "TDS" in kw:
        return date(reference_year, reference_month, 7)
    elif "ADVANCE TAX" in kw:
        return date(2026, 9, 15)
    return None
