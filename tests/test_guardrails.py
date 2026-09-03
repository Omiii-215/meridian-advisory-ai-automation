# -*- coding: utf-8 -*-
from datetime import date
from app.core.guardrails import strip_quoted_email_content, validate_verbatim_quote, validate_temporal_bounds

def test_strip_quoted_email_content():
    raw_email = """Hi team, please find attached files.
Thanks,
John

> On Aug 10, 2026, at 10:00 AM, Support wrote:
> Previous historical quote with date 15 August.
-- 
Corporate Disclaimer Footer"""
    cleaned = strip_quoted_email_content(raw_email)
    assert "> On Aug 10" not in cleaned
    assert "Previous historical quote" not in cleaned
    assert "Hi team, please find attached files." in cleaned

def test_verbatim_quote_assertion():
    body = "Please close this filing by end of month."
    ok, err = validate_verbatim_quote("by end of month", body)
    assert ok is True
    assert err is None

    bad_ok, bad_err = validate_verbatim_quote("by next Friday", body)
    assert bad_ok is False
    assert "TRIPWIRE TRIGGERED" in bad_err

def test_temporal_bounds_filter():
    received = date(2026, 8, 19)
    # Past date
    ok1, err1 = validate_temporal_bounds(date(2026, 8, 10), received)
    assert ok1 is False
    assert "in the past" in err1

    # Valid near-term future
    ok2, err2 = validate_temporal_bounds(date(2026, 8, 31), received)
    assert ok2 is True

    # Distant future (>90 days)
    ok3, err3 = validate_temporal_bounds(date(2026, 12, 1), received)
    assert ok3 is False
    assert ">90 days" in err3
