# -*- coding: utf-8 -*-
from datetime import date
from app.core.calendar import count_working_days_elapsed, is_working_day, add_working_days
from app.models.ticket import Ticket
from app.core.config import REFERENCE_DATE

def test_working_day_checker():
    # August 2026: Aug 1 (Sat), Aug 2 (Sun), Aug 3 (Mon), Aug 7 (Fri)
    assert not is_working_day(date(2026, 8, 1))
    assert not is_working_day(date(2026, 8, 2))
    assert is_working_day(date(2026, 8, 3))
    assert is_working_day(date(2026, 8, 7))

def test_count_working_days_weekend_exclusion():
    # From Friday Aug 14 to Wednesday Aug 19:
    # Sat 15 & Sun 16 excluded. Days: Mon 17, Tue 18, Wed 19 -> 3 days!
    count, days = count_working_days_elapsed(date(2026, 8, 14), date(2026, 8, 19))
    assert count == 3
    assert date(2026, 8, 15) not in days
    assert date(2026, 8, 16) not in days
    assert date(2026, 8, 17) in days

def test_ticket_t102_missing_action_sla_breach():
    # T-102 created Tue Aug 11, Open, no next action date.
    # Today is Wed Aug 19: Wed 12, Thu 13, Fri 14, Mon 17, Tue 18, Wed 19 = 6 working days!
    t = Ticket(id="T-102", client="acme textile", status="Open", created_date="2026-08-11")
    t.compute_metrics(REFERENCE_DATE)
    assert t.working_days_open_without_action == 6
    assert t.is_sla_breached is True

def test_ticket_t101_lapsed_action_sla_breach():
    # T-101 created Mon Aug 10, next action Thu Aug 13.
    # Lapsed working days to Aug 19: Fri 14, Mon 17, Tue 18, Wed 19 = 4 working days!
    t = Ticket(id="T-101", client="Acme Textiles", status="Open", created_date="2026-08-10", next_action_date="2026-08-13")
    t.compute_metrics(REFERENCE_DATE)
    assert t.working_days_lapsed_past_action == 4
    assert t.is_sla_breached is True
