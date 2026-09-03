# Candidate Assessment Submission: AI Automation Intern (PPO Track)

**Company:** Suvitt Service Solutions LLP 
**Client Scenario:** Meridian Advisory 
**Candidate Name:** Om S Habib (Applied via Internshala) 
**Role:** AI Automation Intern (PPO Track) 
**Recipient:** Aditi Singh, Human Resources: aditi.singh@suvitt.com 
**Subject Line:** AI Automation Intern - Assessment - Om S Habib via Internshala 
**Evaluation Reference Date:** Wednesday, 19 August 2026 

---

## Executive Summary & Overview

This submission presents an end-to-end technical, operational, and architectural design for **Meridian Advisory**, a compliance and finance advisory firm handling statutory tax filings, document reviews, and regulatory deadlines. The design bridges two core operational systems: an enterprise ticketing platform and incoming client email communications, while embedding strict deterministic guardrails to eliminate AI hallucination risks surrounding dates, money, and regulatory commitments.

---

# Part A - AI Prompting Skill

## A1. Prompt Design

Meridian requires an AI assistant to process unstructured client emails and return a deterministic, validated JSON classification. The prompt below is engineered for an LLM operating within an automated backend pipeline (such as LangChain, LlamaIndex, or native API calls with JSON Schema enforcement). It incorporates:
1. **Strict Output Schema Enforcement** (Pydantic-compatible JSON).
2. **Strict Taxonomy Boundaries** to prevent vague or overlapping categories.
3. **Explicit Uncertainty Signaling** (`confidence_score`, `is_confident`, `uncertainty_reasons`).
4. **Verbatim Text Anchoring** (`quote_text`) to prevent date/entity hallucination.
5. **Negative Constraints** prohibiting the AI from guessing statutory deadlines from general training memory.

### Production System Prompt

```text
You are the Senior Intake & Triage AI for Meridian Advisory, a finance and compliance advisory firm.
Your role is to read an incoming client email and return a strictly validated, structured JSON classification.
Meridian manages statutory tax filings, regulatory deadlines, and client document reviews. Accuracy is mission-critical: mistakes regarding dates, financial figures, or legal commitments carry severe legal and financial penalties.

### STRICT OPERATIONAL RULES:
1. GROUNDING & ANTI-HALLUCINATION:
 - Extract information ONLY from the verbatim text in the provided email.
 - NEVER guess, assume, or extrapolate dates, ticket numbers, monetary amounts, or client obligations.
 - If a statutory deadline or ticket ID is not explicitly written in the email, you MUST set the corresponding field to null.
 - NEVER look up general knowledge (e.g., standard GST or TDS deadlines) to fill in dates.

2. CLASSIFICATION TAXONOMY (Choose exactly ONE):
 - "NEW_SERVICE_REQUEST": Client is requesting a new advisory service, tax filing, or consultation.
 - "EXISTING_TICKET_UPDATE": Client is following up, replying, or inquiring about an ongoing engagement or existing ticket number.
 - "DOCUMENT_SUBMISSION": Client is providing files, statements, invoices, or records purely for the firm's records without requesting new work.
 - "GENERAL_INQUIRY": Client is asking a general informational question not tied to a specific filing or ticket.
 - "IRRELEVANT_OR_SPAM": Marketing, sales solicitations, newsletters, automated receipts, out-of-office replies, or forwarded non-business content.
 - "AMBIGUOUS_OR_INSUFFICIENT": The email lacks critical context, contains vague directives (e.g., "handle asap" without details), or references attachments that are absent.

3. URGENCY LEVELS:
 - "CRITICAL": Explicit mention of immediate legal action, penalty notices, imminent regulatory deadlines (<24 hours), or client distress.
 - "HIGH": Near-term deadlines mentioned (within 2-5 days), high-priority escalations, or explicit requests for urgent handling.
 - "MEDIUM": Standard business turnaround requested; ongoing project follow-ups.
 - "LOW": Routine document submissions, acknowledgments, or non-urgent queries.
 - "UNKNOWN": Ambiguous emails where urgency cannot be determined reliably.

4. CONFIDENCE & UNCERTAINTY HANDLING:
 - Provide a numerical "confidence_score" between 0.00 and 1.00.
 - If the email is vague, missing attachments, short (<10 words without context), or internally contradictory, set "is_confident" to false, give a score below 0.60, and enumerate specific "uncertainty_reasons".
 - Never artificially inflate confidence to appear helpful. Low confidence is a protected safety mechanism that routes emails to human triage.

5. DATE EXTRACTION:
 - "extracted_due_date" must ONLY be captured if the client explicitly mentions a target completion date or deadline in the text.
 - Include the exact verbatim quote in "quote_text".
 - If the date is relative (e.g., "end of month", "by Friday"), provide your normalized interpretation in "normalized_date" (ISO 8601 YYYY-MM-DD) based on the email header timestamp, and mark "is_relative": true. If unclear, set to null.

### OUTPUT JSON SCHEMA:
Respond with ONLY a single valid JSON object adhering strictly to this schema:
{
 "classification_type": "NEW_SERVICE_REQUEST" | "EXISTING_TICKET_UPDATE" | "DOCUMENT_SUBMISSION" | "GENERAL_INQUIRY" | "IRRELEVANT_OR_SPAM" | "AMBIGUOUS_OR_INSUFFICIENT",
 "ticket_reference": {
 "has_ticket_id": boolean,
 "ticket_id": string | null,
 "quote_text": string | null
 },
 "urgency": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN",
 "urgency_rationale": string,
 "extracted_due_date": {
 "has_date": boolean,
 "raw_text": string | null,
 "normalized_date": string | null,
 "is_relative": boolean,
 "is_statutory": boolean,
 "quote_text": string | null
 },
 "context_completeness": "COMPLETE" | "PARTIAL" | "INSUFFICIENT",
 "missing_elements": [string],
 "confidence_score": number,
 "is_confident": boolean,
 "uncertainty_reasons": [string],
 "recommended_action": "ROUTE_TO_TEAM_QUEUE" | "APPEND_TO_EXISTING_TICKET" | "ARCHIVE_DOCUMENT_RECORD" | "HUMAN_MANUAL_TRIAGE" | "AUTO_DISCARD"
}
```

---

## A2. Test Your Own Prompt

Running the system prompt against the three provided candidate emails (under reference email timestamp: **2026-08-19 09:00:00 IST**):

### Email 1:
> *"Hi team, please find attached our Q2 bank statement for your records. Thanks."*

```json
{
 "classification_type": "DOCUMENT_SUBMISSION",
 "ticket_reference": {
 "has_ticket_id": false,
 "ticket_id": null,
 "quote_text": null
 },
 "urgency": "LOW",
 "urgency_rationale": "Routine submission of quarterly bank statements for record-keeping; no immediate operational action or filing requested.",
 "extracted_due_date": {
 "has_date": false,
 "raw_text": null,
 "normalized_date": null,
 "is_relative": false,
 "is_statutory": false,
 "quote_text": null
 },
 "context_completeness": "COMPLETE",
 "missing_elements": [],
 "confidence_score": 0.96,
 "is_confident": true,
 "uncertainty_reasons": [],
 "recommended_action": "ARCHIVE_DOCUMENT_RECORD"
}
```
*Operational Note:* The workflow deterministic validation layer verifies that a physical file attachment actually accompanied this email before archiving.

---

### Email 2:
> *"Following up on ticket #4521 - any update on the GST filing? We need this closed by end of month."*

```json
{
 "classification_type": "EXISTING_TICKET_UPDATE",
 "ticket_reference": {
 "has_ticket_id": true,
 "ticket_id": "#4521",
 "quote_text": "ticket #4521"
 },
 "urgency": "HIGH",
 "urgency_rationale": "Client follow-up regarding an active statutory GST filing requesting closure by month-end.",
 "extracted_due_date": {
 "has_date": true,
 "raw_text": "end of month",
 "normalized_date": "2026-08-31",
 "is_relative": true,
 "is_statutory": false,
 "quote_text": "We need this closed by end of month."
 },
 "context_completeness": "COMPLETE",
 "missing_elements": [],
 "confidence_score": 0.94,
 "is_confident": true,
 "uncertainty_reasons": [],
 "recommended_action": "APPEND_TO_EXISTING_TICKET"
}
```
*Operational Note:* Marked `is_statutory: false` because "end of month" is the client's internal target, not the statutory GST deadline (which in India is typically the 20th of the month for GSTR-3B).

---

### Email 3:
> *"URGENT!! Please handle asap." (No other content, and no attachment.)*

```json
{
 "classification_type": "AMBIGUOUS_OR_INSUFFICIENT",
 "ticket_reference": {
 "has_ticket_id": false,
 "ticket_id": null,
 "quote_text": null
 },
 "urgency": "HIGH",
 "urgency_rationale": "Client used high-stress keywords ('URGENT!!', 'asap'), but the message lacks all substantive context.",
 "extracted_due_date": {
 "has_date": false,
 "raw_text": null,
 "normalized_date": null,
 "is_relative": false,
 "is_statutory": false,
 "quote_text": null
 },
 "context_completeness": "INSUFFICIENT",
 "missing_elements": [
 "Subject matter or engagement context",
 "Specific task instruction",
 "Referenced documents or attachments",
 "Ticket or filing identification"
 ],
 "confidence_score": 0.20,
 "is_confident": false,
 "uncertainty_reasons": [
 "Email body contains zero substantive information or deliverables.",
 "No attachments detected to provide context.",
 "High urgency tone without actionable subject matter."
 ],
 "recommended_action": "HUMAN_MANUAL_TRIAGE"
}
```
*Operational Note:* Immediately routes to a Senior Client Servicing Lead to contact the client via telephone or follow-up email. No automated ticket commitments are generated.

---

## A3. Prompt Failure Analysis

### Production Failure Mode: Historical Quoted-Thread Date Bleed & Relative Temporal Drift
In production, clients frequently reply to long email chains or forward previous correspondence containing historical correspondence, legal disclaimers, or holiday notices (for example, "Our office is closed on 15 August for Independence Day" or "Last month's TDS was paid on 07 July"). 

An LLM can easily suffer from **Historical Quoted-Thread Date Bleed**: it mistakenly extracts an outdated historical date or footer disclaimer as the active target due date for the new ticket. If the AI confidently flags this date as `extracted_due_date`, the system might register an erroneous statutory deadline in the ticketing database without raising an internal alert.

### Automated Detection Architecture (Zero Manual Reading Required)
To catch this failure deterministically and automatically at machine speed, we implement a **Four-Layer Automated Guardrail Pipeline**:

1. **Email Quoted-Text Boundary Truncation & Differential Parsing (Pre-LLM Rule):** 
 Before the prompt runs, a deterministic parser (such as `mail-parser` or regex standard RFC 3676) strips all quoted thread blocks (`> `, `On [date], [sender] wrote:`, and standard corporate signature footers). The LLM is provided only the new unquoted message delta.
2. **Verbatim Text Anchoring Tripwire (Post-LLM Assertion):** 
 A deterministic Python assertion executes immediately upon receiving the JSON:
 ```python
 if result["extracted_due_date"]["has_date"]:
 raw_quote = result["extracted_due_date"]["quote_text"]
 assert raw_quote is not None and raw_quote in incoming_email_unquoted_body, "TRIPWIRE_TRIGGERED: Extracted date quote does not exist verbatim in unquoted body."
 ```
3. **Temporal Bounds Sanity Filter:** 
 Any extracted `normalized_date` is evaluated against system-time rules:
 - If `normalized_date < email_received_date`: Automatically flagged as `HISTORICAL_DATE_ANOMALY`.
 - If `normalized_date > email_received_date + 90 days`: Flagged as `DISTANT_DATE_ANOMALY`.
4. **Ticketing DB Cross-Reference Tripwire:** 
 If a `ticket_id` is extracted (such as `#4521`), an automated API call queries the ticketing database:
 - Does Ticket `#4521` exist?
 - Does the client organization on Ticket `#4521` match the sender's verified email domain?
 - If either check fails, the workflow rejects the automated classification, flags `ENTITY_MISMATCH`, and routes the payload to the human exception queue.

---

# Part B - Workflow Design

## B1. Design the Workflow

### End-to-End Workflow Stages & Architectural Split

| Stage | Operation | Engine Type | Rationale & Mechanics |
| :--- | :--- | :--- | :--- |
| **1. Ingestion & Header Check** | Ingest via webhook. Inspect `Message-ID`, `In-Reply-To`, `References`. | **Deterministic (Rule-Based)** | Eliminates duplicate tickets 100% reliably if the email is part of a mail client thread. Zero cost, zero latency. |
| **2. Regex Subject/Body Scan** | Regex search for ticket ID patterns. Validate against ticketing DB. | **Deterministic (Rule-Based)** | Exact matching. Prevents AI guessing ticket numbers from invoice numbers or phone numbers. |
| **3. Sender & Domain CRM Match** | Match sender address against Meridian CRM client directory. | **Deterministic (Rule-Based)** | Verifies whether the sender is an authorized client contact; identifies client SLA tier. |
| **4. AI Intent & Entity Extraction** | Execute System Prompt (A1) on unquoted email body. | **AI-Based (LLM)** | Unstructured language understanding, sentiment/urgency, and unstructured intent classification. |
| **5. Automated Safety Guardrails** | Check schema validity, confidence >= 0.80, text-anchoring tripwires. | **Deterministic (Rule-Based)** | Catches AI hallucination, uncertainty, or schema drift before downstream systems are touched. |
| **6. Statutory Deadline Lookup** | Match service scope (e.g., "GST GSTR-3B") to official compliance calendar. | **Deterministic (Rule-Based)** | **Critical Safety Rule:** Statutory dates come from official statutory tables, NEVER from AI imagination. |
| **7. System Update & Human Gate** | Create Draft Ticket with `requires_human_approval` flag. | **Deterministic + Human Gate** | Prevents unverified client commitments or unassigned compliance liabilities. |

### Handling Low AI Confidence
If `confidence_score < 0.80` or classification is `AMBIGUOUS_OR_INSUFFICIENT`, the workflow automatically routes the item to an **Exception / Triage Queue**. A notification is dispatched to the Lead Triage Advisor with the email snippet and detected ambiguities highlighted.

### Duplicate Prevention Mechanics
Incoming emails are evaluated against three deterministic criteria: (1) matching message thread headers (`In-Reply-To` / `References`), (2) regex matching on ticket ID patterns (e.g., `#4521`), and (3) temporal subject matching for the same client domain within 48 hours. If matched, the incoming message is appended to the existing ticket rather than creating a new ticket.

---

## B2. Explain Your Reasoning
*(Constraint: 150 words or fewer. Exact word count: 138 words)*

We placed the human-approval boundary strictly before publishing external client commitments, activating statutory filing dates, and finalizing ticket closures.

Getting this boundary wrong in either direction carries severe consequences:
- **Shifting the line toward full automation (Under-supervision):** An AI misinterpreting an email could enter an incorrect statutory filing deadline or silently close an unresolved request. The firm risks missed regulatory deadlines, crippling statutory tax penalties, legal malpractice liability, and irreparable client churn.
- **Shifting the line toward manual review of everything (Over-supervision):** Forcing team leads to manually approve routine thread updates, spam filtering, and document archiving drowns senior advisors in administrative trivia. This causes employee burnout, SLA breaches on genuine client emergencies, and defeats the productivity purpose of automation.

The chosen boundary automates operational plumbing while reserving professional human judgement for regulatory and legal commitments.

---

## B3. Scale It
*(Constraint: 100 words or fewer. Exact word count: 94 words)*

We would build **one parameterized workflow** governed by a configuration-driven architecture.

The core plumbing: email ingestion, thread matching, attachment validation, SLA tracking, error trapping, and exception routing: is universal across Tax, Legal, Operations, and Client Servicing. Rather than duplicating pipelines, team-specific logic is decoupled into external configuration tables (defining inbox webhooks, routing queues, statutory calendar lookups, and approval hierarchies).

Building four separate workflows creates four times the maintenance overhead, technical debt, and risk of logic drift. A single parameterized engine ensures centralized security, unified observability, and rapid firm-wide feature deployment.

---

# Part C - Reporting and Data Logic

**Context:** 10 sample tickets provided by Meridian Advisory. 
**Reference Date ("Today"):** Wednesday, 19 August 2026. 
**Calendar Standard:** Five-day working week (Monday to Friday), zero holidays.

```
August 2026 Reference Calendar:
Mo Tu We Th Fr Sa Su
 1 2
 3 4 5 6 7 8 9
10 11 12 13 14 15 16
17 18 19 20 21 22 23 <-- Today is Wednesday, 19 August 2026
24 25 26 27 28 29 30
31
```

---

## C1. Data Quality Issues Audit

A comprehensive audit of the 10-ticket sample dataset reveals multiple severe data anomalies, deliberate traps, and integrity breaches:

| Issue Category | Description of Defect | Specific Ticket IDs Involved | Impact & Risk Analysis |
| :--- | :--- | :--- | :--- |
| **1. Exact Duplicate Records** | Identical fields across Client ("Acme Textiles"), Status ("Open"), Created Date (2026-08-10), Next Action Date (2026-08-13), and Statutory Due Date (2026-08-25). | **T-101 and T-105** | Double-counts workload, risks duplicate client filings, and wastes advisor hours chasing the same task twice. |
| **2. Inconsistent Entity Naming** | The same client is recorded under three disparate naming conventions: "Acme Textiles" (Title Case), "acme textile" (lowercase singular), and "ACME Textiles Pvt Ltd" (legal entity suffix). | **T-101, T-102, T-105, T-110** | Prevents unified client-level reporting, breaks automated CRM matching, and hides aggregate SLA risk. |
| **3. Missing Next Action Date (Open Tickets)** | Status is "Open", but Next Action Date is completely blank (NULL). | **T-102, T-107** *(also T-103, T-108 in Closed state)* | **Immediate SLA Failure:** Tickets sit completely unmonitored in the system with no owner accountability. |
| **4. Missing Statutory Due Date** | Tickets handling client compliance work lack a recorded statutory deadline. | **T-106** *(Status: Pending)*, **T-103** *(Status: Closed)* | Blind compliance risk: The firm has no visibility into regulatory exposure or filing deadlines. |
| **5. Omission of Mandatory Schema Column** | The scenario mandates: "Every client request becomes a ticket with a Client Name, a Statutory Due Date, an Assigned Owner, and a Next Action Date." The **"Assigned Owner"** column is 100% missing from the dataset. | **Systemic (All Tickets: T-101 to T-110)** | Zero individual accountability. Impossible to identify which advisor is responsible for overdue actions. |
| **6. Overdue Statutory Due Dates (Open Tickets)** | Open tickets whose statutory regulatory deadline has already passed relative to Today (19-Aug-2026). | **T-104** (Due 01-Aug, 18 calendar days / 13 working days overdue)<br/>**T-107** (Due 18-Aug, 1 day overdue) | **Critical Regulatory Violation:** Client is actively incurring statutory penalties, interest, or legal default. |
| **7. Non-Working Day / Weekend Dates** | Dates recorded on Saturdays or Sundays despite Meridian operating on a strict Monday to Friday business week. | **T-104** (Created & Due on Sat 01-Aug)<br/>**T-109** (Next Action on Sat 15-Aug)<br/>**T-110** (Created Sun 09-Aug, Due Sat 22-Aug) | Violates business calendar logic. Indicates manual data-entry errors or failure of automated date pickers. |
| **8. Chronological Contradiction** | Next Action Date is scheduled *after* the Statutory Due Date. | **T-104** (Statutory Due: 01-Aug; Next Action: 03-Aug) | Logically absurd: Scheduling an internal next step 2 days after the statutory filing has already lapsed. |
| **9. Ambiguous Lifecycle Status** | Status recorded as "Pending" with no sub-status indicating whether the firm or the client holds the ball. | **T-106** (Next Action 14-Aug is 3 working days overdue) | Hides work in progress; bypasses standard Open/Closed SLA filters unless explicitly accounted for. |

---

## C2. Working-Day SLA Breach Calculations

**Firm Rule:** "Tickets not moved forward within two working days are considered overdue." 
**Assessment Definition:** "meaning open for more than two working days without a next action."

To provide exhaustive analytical rigor, we analyze this under both industry interpretations:
- **Interpretation A (Literal Absence):** Open tickets with **NO Next Action Date** populated (`Next Action Date == NULL`) that have been open for > 2 working days since creation.
- **Interpretation B (Operational Ticketing SLA):** Open tickets where the **Next Action Date has lapsed by > 2 working days** without being updated or moved forward.

### Detailed Ticket Calculations

#### 1. Calculation for Ticket T-102 (Client: "acme textile")
- **Status:** Open | **Created Date:** Tuesday, 11 August 2026 | **Next Action Date:** `[BLANK]`
- **Statutory Due Date:** Thursday, 20 August 2026 (Tomorrow!)
- **Working Days Elapsed Calculation (Created Date to Today, 19 August 2026):**
 - Day 1: Wednesday, 12 August 2026
 - Day 2: Thursday, 13 August 2026 (SLA threshold reached at close of business)
 - Day 3: Friday, 14 August 2026
 - Weekend (15-16 August): Excluded (Saturday, Sunday)
 - Day 4: Monday, 17 August 2026
 - Day 5: Tuesday, 18 August 2026
 - Day 6: Wednesday, 19 August 2026 (Today)
- **Total Working Days Open Without Next Action:** **6 working days**.
- **SLA Threshold:** 2 working days.
- **Breach Status:** **CRITICAL SLA BREACH (4 working days overdue)**. Compounding this, its statutory filing deadline is **tomorrow**, yet no next action is scheduled.

---

#### 2. Calculation for Ticket T-107 (Client: "Bluewave Foods")
- **Status:** Open | **Created Date:** Thursday, 30 July 2026 | **Next Action Date:** `[BLANK]`
- **Statutory Due Date:** Tuesday, 18 August 2026 (Yesterday: Already Breached!)
- **Working Days Elapsed Calculation (Created Date to Today, 19 August 2026):**
 - July: Friday, 31 July (1 working day)
 - August Week 1 (3-7 Aug): Mon, Tue, Wed, Thu, Fri (5 working days)
 - August Week 2 (10-14 Aug): Mon, Tue, Wed, Thu, Fri (5 working days)
 - August Week 3 (17-19 Aug): Mon, Tue, Wed (3 working days)
- **Total Working Days Open Without Next Action:** **14 working days**.
- **SLA Threshold:** 2 working days.
- **Breach Status:** **MASSIVE SLA BREACH (12 working days overdue)**. The statutory deadline passed yesterday while the ticket sat completely abandoned without an action date.

---

#### 3. Calculation for Ticket T-101 / T-105 (Client: "Acme Textiles")
- **Status:** Open | **Created Date:** Monday, 10 August 2026 | **Next Action Date:** Thursday, 13 August 2026
- **Working Days Elapsed Since Scheduled Next Action Date (13 August 2026 to Today):**
 - Day 1 overdue: Friday, 14 August 2026
 - Weekend (15-16 August): Excluded
 - Day 2 overdue: Monday, 17 August 2026 (2 working day grace period expires)
 - Day 3 overdue: Tuesday, 18 August 2026 (Exceeds 2 working days)
 - Day 4 overdue: Wednesday, 19 August 2026 (Today)
- **Total Working Days Overdue:** **4 working days past next action date**.
- **Breach Status:** **SLA BREACH**.

---

#### 4. Calculation for Ticket T-104 (Client: "Crest Pharma")
- **Status:** Open | **Created Date:** Saturday, 01 August 2026 | **Next Action Date:** Monday, 03 August 2026
- **Statutory Due Date:** Saturday, 01 August 2026 (Expired 18 days ago!)
- **Working Days Elapsed Since Next Action Date (03 August 2026 to Today):**
 - 4 to 7 August: 4 working days (Tue, Wed, Thu, Fri)
 - 10 to 14 August: 5 working days (Mon, Tue, Wed, Thu, Fri)
 - 17 to 19 August: 3 working days (Mon, Tue, Wed)
- **Total Working Days Overdue:** **12 working days past next action date**.
- **Breach Status:** **CATASTROPHIC SLA BREACH**.

---

#### 5. Calculation for Ticket T-110 (Client: "ACME Textiles Pvt Ltd")
- **Status:** Open | **Created Date:** Sunday, 09 August 2026 | **Next Action Date:** Tuesday, 11 August 2026
- **Working Days Elapsed Since Next Action Date (11 August 2026 to Today):**
 - 12 to 14 August: 3 working days (Wed, Thu, Fri)
 - 17 to 19 August: 3 working days (Mon, Tue, Wed)
- **Total Working Days Overdue:** **6 working days past next action date**.
- **Breach Status:** **SLA BREACH (4 working days past 2-day limit)**.

---

### Comprehensive SLA Breach Summary Table

| Ticket ID | Client Name | Current Status | Next Action Date | Working Days Open w/o Next Action | Working Days Lapsed Past Next Action | SLA Breach Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **T-101** | Acme Textiles | Open | 2026-08-13 | N/A | **4 working days** | **BREACH** (Overdue > 2 working days) |
| **T-102** | acme textile | Open | `[BLANK]` | **6 working days** | N/A | **BREACH** (Missing next action > 2 days) |
| **T-103** | Bluewave Foods | Closed | `[BLANK]` | N/A (Closed) | N/A | Closed (No active SLA breach) |
| **T-104** | Crest Pharma | Open | 2026-08-03 | N/A | **12 working days** | **BREACH** (Catastrophic: 12 days stalled) |
| **T-105** | Acme Textiles | Open | 2026-08-13 | N/A | **4 working days** | **BREACH** (Duplicate of T-101) |
| **T-106** | Delta Logistics | Pending | 2026-08-14 | N/A | **3 working days** | **BREACH** (If Pending tracks SLA) |
| **T-107** | Bluewave Foods | Open | `[BLANK]` | **14 working days** | N/A | **BREACH** (Missing next action > 2 days) |
| **T-108** | Crest Pharma | Closed | `[BLANK]` | N/A (Closed) | N/A | Closed (No active SLA breach) |
| **T-109** | Everest Retail | Open | 2026-08-15 | N/A | **2-3 working days** | **AT THRESHOLD / BREACH** |
| **T-110** | ACME Textiles Pvt Ltd | Open | 2026-08-11 | N/A | **6 working days** | **BREACH** (Overdue > 2 working days) |

---

## C3. One-Page Daily Exception Report (Top Three Lines)

Designed for a Managing Director or Partner who has exactly 30 seconds to review risks and issue directives:

```text
1. [REGULATORY DEADLINE BREACH] 2 Open Tickets Have Passed Statutory Due Date: T-104 (Crest Pharma: 18 days overdue) and T-107 (Bluewave Foods: 1 day overdue). Immediate partner intervention required to mitigate penalty and legal exposure.

2. [IMMINENT FILING AT RISK] 1 Open Ticket Due Tomorrow Has No Assigned Next Action: T-102 (acme textile: Statutory Due Date 20-Aug-2026). 6 working days stalled; immediate emergency assignment required before 17:00 IST.

3. [INTERNAL SLA & DATA INTEGRITY] 5 Active Tickets in Severe SLA Breach (>2 working days stalled: T-101, T-105, T-110, T-106, T-107); 1 Confirmed Duplicate Pair (T-101 / T-105). Action: Merge duplicates and enforce next action updates today.
```

---

# Part D - AI Judgement and Risk

*(Constraint: Answer each question in three to five sentences.)*

### D1. Statutory Deadline Error: Accountability & Preventive System Design
Accountability is shared between the system designer and the team lead: the designer failed to implement basic data validation and grounding guardrails, while the team lead breached supervisory fiduciary duty by treating unverified, probabilistic AI text as an authoritative source of truth. 
Architecturally, an AI should never be permitted to unilaterally extract or update statutory compliance deadlines from conversational email text without verification. 
Instead, the workflow must deterministically cross-reference client filing scopes against an authoritative, master regulatory tax calendar maintained by the firm's compliance officers. 
Furthermore, any AI-suggested modification to a statutory date must mandate a dual-control human-in-the-loop sign-off with verbatim source citations before writing to the system of record. 
Finally, the automated reporting engine should have featured a disparity tripwire flagging whenever an extracted date diverged from the regulatory master calendar. 
*(Exact sentence count: 5 sentences)*

---

### D2. Deliberate Non-AI Automation Task & Rationale
A concrete task where I would deliberately refuse to use AI is calculating statutory payroll tax withholdings, late filing penalty interest, and compound tax liabilities. 
While a modern large language model can parse tax tables and perform arithmetic, generative models are non-deterministic, probabilistic token predictors that are fundamentally prone to rounding errors, hallucination, and numerical drift. 
Statutory financial computations require 100% mathematical precision, instantaneous execution speed, and an airtight, reproducible audit trail for tax authorities. 
Implementing this calculation through a deterministic script written in Python or SQL guarantees zero calculation error, total legal auditability, and zero API token cost. 
*(Exact sentence count: 4 sentences)*

---

### D3. Inbox Access Governance & Scoping
Before granting inbox access, I would ask what specific operational bottleneck necessitates full mailbox scanning, what data privacy and zero-retention agreements are established with the AI provider, and how privileged communications (such as attorney-client privilege, whistleblower reports, and internal HR matters) are sequestered. 
I would also ask what legal liabilities arise under data protection regulations (such as GDPR or India's DPDP Act) if unredacted client financial records are exposed to model pipelines. 
Rather than granting broad personal inbox access, the minimum access I would request is restricted read-only webhook access scoped exclusively to designated shared departmental inboxes (such as `tax-filings@meridian.com` or `compliance-support@meridian.com`). 
Finally, this integration must run through an on-premise PII redaction layer that strips banking credentials, passwords, and sensitive identifiers before payload delivery to the LLM. 
*(Exact sentence count: 4 sentences)*

---

# Part E - Communication

### E1. Handover Note to Non-Technical Team Lead
*(Constraint: No more than 200 words. Exact word count: 168 words)*

**Subject:** How your new morning compliance report works (and what to do if it ever fails)

Hi Sarah,

To ensure you never have to guess whether your automated morning report ran, we have established a simple **"Heartbeat Rule"**:

Every business morning by **8:30 AM**, you will receive an email titled **"Meridian Daily Compliance Digest - [Date]"**. If that email has not arrived in your inbox by **8:35 AM**, or if you receive a notification titled **"ALERT: Daily Report Generation Incomplete"**, the automated run has encountered an issue.

If that happens, please take two quick steps:
1. **Open Your Saved Backup View:** In your ticketing dashboard, click the bookmark titled **"00_Daily_Exceptions_Backup"**. This live view displays the exact same overdue tickets and imminent statutory deadlines, updating independently of the email service.
2. **Alert the Automation Team:** Send a quick message to our internal Teams channel **#ops-automation** or text me directly: *"Daily report missing for [Date]"*.

Our team will diagnose the pipeline immediately and deliver a manual PDF digest within 15 minutes. Your client operations can continue smoothly without interruption!

Warm regards, 
**AI Automation Team**

---

### E2. Client-Facing Role Explanation
*(Constraint: Exactly one cohesive paragraph)*

While tools like ChatGPT are conversational assistants that generate text when prompted, an AI Automation role at Meridian Advisory designs the secure, invisible operational infrastructure that guarantees your financial filings and compliance obligations are executed flawlessly. Rather than simply typing questions into a chatbot, this role builds interconnected systems that automatically route incoming client correspondence, match deadlines against official statutory tax schedules, detect missing documentation before it causes filing delays, and track team response times against strict quality standards. Crucially, this architecture is engineered with enterprise safeguards: AI is used to eliminate manual administrative friction, but every regulatory commitment, monetary figure, and tax filing is governed by deterministic rules and signed off by qualified human advisors. In short, ChatGPT is an ad-hoc drafting tool, whereas AI automation is an institutional-grade reliability engine designed to protect your firm from missed deadlines, ensure strict confidentiality, and deliver predictable compliance outcomes.

---

## Submission Checklist Verification

- [x] **Part A** - Complete system prompt design, 3 structured JSON test outputs, failure analysis, and automated detection mechanics.
- [x] **Part B** - Detailed workflow diagram, step-by-step logic, reasoning (<= 150 words), and multi-team scaling answer (<= 100 words).
- [x] **Part C** - Comprehensive data quality issues table (with Ticket IDs), working-day SLA breach calculations (showing step-by-step math for multiple tickets), and top 3 executive exception lines.
- [x] **Part D** - Three short judgement answers, strictly within 3 to 5 sentences each.
- [x] **Part E** - Non-technical handover note (<= 200 words) and client-facing explanation (single cohesive paragraph).
- [x] **Disclosure** - Detailed AI tool usage disclosure below.

---

## Disclosure of AI Tool Usage

*In adherence to candidate instructions: "You may use AI to complete this assessment. If you do, tell us where and how you used it. This is not a penalty: how you use AI is part of what we are evaluating."*

1. **AI Models & Tools Employed:**
 - **Gemini 3.8 Flash (via Google Antigravity Agentic IDE)**: Utilized as an interactive pair-programming assistant for rapid ideation, JSON schema drafting, and stress-testing edge cases.
 - **Local Python 3.14 Runtime**: Utilized to execute custom verification scripts (`verify_data_logic.py`) to perform exact calendar date math, calculate day-by-day working day intervals, and verify weekend exclusions.

2. **Where & How AI Was Applied:**
 - **Part A (Prompt Design):** AI was used to draft initial JSON schema structures, which were then manually refined with explicit guardrails, Pydantic type constraints, and verbatim quotation anchoring.
 - **Part B (Workflow Design):** AI assisted in generating initial workflow logic and syntax formatting; manual engineering was applied to delineate the deterministic versus probabilistic system split.
 - **Part C (Data Logic & Trap Identification):** A Python script was run locally to calculate working days and date deltas; AI was used to synthesize findings into an executive matrix highlighting the deliberate data traps (duplicate tickets, missing owner columns, weekend anomalies).
 - **Part D & Part E (Judgement & Communication):** AI assisted in iterative draft compression to strictly satisfy sentence count and word count constraints while preserving an authoritative, professional tone. All conceptual principles and architectural choices were guided by professional enterprise automation best practices.
