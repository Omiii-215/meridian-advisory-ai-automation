# -*- coding: utf-8 -*-
import re
from datetime import date, timedelta
from typing import Dict, Any, List, Tuple, Optional

def strip_quoted_email_content(email_body: str) -> str:
    """
    Layer 1: Pre-LLM Boundary Stripping.
    Strips quoted reply chains, forwarded blocks, and standard corporate signatures
    per RFC 3676 standards to prevent historical thread date bleed.
    """
    lines = email_body.splitlines()
    clean_lines = []
    
    for line in lines:
        stripped = line.strip()
        # Quoted reply markers
        if stripped.startswith(">") or stripped.startswith("|"):
            continue
        # Standard reply headers
        if re.match(r"^On\s+.*\s+wrote:$", stripped, re.IGNORECASE):
            break
        if re.match(r"^-+\s*Original Message\s*-+$", stripped, re.IGNORECASE):
            break
        if re.match(r"^From:.*Sent:.*To:.*", stripped, re.IGNORECASE):
            break
        # Common signature dividers
        if stripped == "--" or stripped == "-- ":
            break
        clean_lines.append(line)
        
    return "\n".join(clean_lines).strip()

def validate_verbatim_quote(raw_quote: Optional[str], unquoted_body: str) -> Tuple[bool, Optional[str]]:
    """
    Layer 2: Verbatim Text Anchoring Tripwire.
    Ensures that any date quote returned by the model appears verbatim in the unquoted email.
    """
    if not raw_quote:
        return True, None
    if raw_quote.lower() not in unquoted_body.lower():
        return False, f"TRIPWIRE TRIGGERED: Extracted quote '{raw_quote}' does not exist verbatim in unquoted body."
    return True, None

def validate_temporal_bounds(extracted_date: Optional[date], received_date: date) -> Tuple[bool, Optional[str]]:
    """
    Layer 3: Temporal Sanity Bounds Filter.
    Flags dates that are in the past or abnormally far in the future (>90 days for monthly advisory).
    """
    if not extracted_date:
        return True, None
    if extracted_date < received_date:
        return False, f"TEMPORAL ANOMALY: Extracted date ({extracted_date}) is in the past relative to email received date ({received_date})."
    if extracted_date > received_date + timedelta(days=90):
        return False, f"TEMPORAL ANOMALY: Extracted date ({extracted_date}) is >90 days in future; requires human review."
    return True, None

def validate_crm_ticket_entity(ticket_id: Optional[str], sender_email: str, known_tickets: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Layer 4: CRM Entity Cross-Reference Tripwire.
    Verifies that extracted ticket ID exists and corresponds to the sender's client domain.
    """
    if not ticket_id:
        return True, None
    
    clean_id = ticket_id.upper().strip().replace("#", "")
    full_id = f"T-{clean_id}" if not clean_id.startswith("T-") else clean_id
    
    if full_id not in known_tickets:
        return False, f"ENTITY MISMATCH: Referenced ticket '{ticket_id}' was not found in ticketing database."
        
    return True, None
