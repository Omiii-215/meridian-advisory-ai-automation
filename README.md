# Meridian Advisory - AI Workflow & Compliance Automation Platform

[![CI Tests](https://img.shields.io/badge/pytest-12%20passed-brightgreen.svg)]()
[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.14-blue.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

> **Candidate Assessment Submission: AI Automation Intern (PPO Track)**  
> **Company:** Suvitt Service Solutions LLP (LLPIN: ACG-0284)  
> **Client Scenario:** Meridian Advisory (Finance & Compliance Advisory Firm)  
> **Candidate Name:** Om S Habib (Applied via Internshala)  
> **GitHub:** [@Omiii-215](https://github.com/Omiii-215)  
> **Evaluation Reference Date:** Wednesday, 19 August 2026  
> **Live Server URL:** [https://cca2aa15b0b7da.lhr.life](https://cca2aa15b0b7da.lhr.life)  

---

## Submission Documents & Artifacts

| Document Format | Description | File Link |
| :--- | :--- | :--- |
| **Official Corporate PDF** | 6-page publication-grade PDF matching assessment sections | [`AI_Automation_Intern_Candidate_Assessment.pdf`](AI_Automation_Intern_Candidate_Assessment.pdf) |
| **Microsoft Word Document** | Formatted Word `.docx` verified with zero em-dashes | [`AI_Automation_Intern_Candidate_Assessment.docx`](AI_Automation_Intern_Candidate_Assessment.docx) |
| **Markdown Assessment** | Full GitHub-flavored markdown source | [`AI_Automation_Intern_Candidate_Assessment.md`](AI_Automation_Intern_Candidate_Assessment.md) |
| **Data Logic Verification** | Standalone mathematical verification script | [`verify_data_logic.py`](verify_data_logic.py) |

---

## System Overview & Architectural Intent

Meridian Advisory manages mission-critical statutory tax filings, regulatory deadlines, and client document reviews using two primary systems: an enterprise support ticketing tool and client email communications. 

Because finance and compliance advisory carries severe regulatory, monetary, and legal penalties, this platform enforces a strict **separation of concerns**:
- **Deterministic Rules Layer:** Governs statutory tax schedules, ticket thread de-duplication, client domain validation, business-day SLA math, and legal commitments. Zero hallucination risk.
- **AI Classification & Triage Layer:** Scoped strictly to unstructured natural language comprehension, intent classification, and initial triage drafting.
- **Human-in-the-Loop Review Gate:** Dual-control approval required for low-confidence classifications, ambiguous client requests, and statutory date modifications before system updates are finalized.

---

## Key Platform Features

### 1. Operations & Ticketing Dashboard
- **Freshdesk/Zendesk Style UI:** Preloaded with the 10 sample tickets (`T-101` to `T-110`).
- **Working-Day SLA Tracker:** Computes elapsed business days (Monday to Friday only, excluding Saturdays and Sundays) and flags stalled tickets exceeding the 2-day firm SLA.
- **Statutory Alert Engine:** Identifies overdue regulatory filings (e.g. `T-104` is 18 days overdue; `T-107` is 1 day overdue) and imminent deadlines (e.g. `T-102` is due tomorrow).

### 2. Automated Data Quality Auditor (Part C1 Traps Audit)
Detects all 9 deliberate traps from the assessment in real time:
1. **Exact Duplicate Tickets:** Identifies `T-101` and `T-105` with a **1-Click Merge** action.
2. **Client Entity Fragmentation:** Detects `Acme Textiles`, `acme textile`, and `ACME Textiles Pvt Ltd` with a **1-Click Normalize** action.
3. **Missing Next Action Dates:** Flags active tickets (`T-102`, `T-107`) languishing without operational tracking.
4. **Missing Statutory Due Dates:** Identifies compliance tickets (`T-106`, `T-103`) lacking regulatory deadlines.
5. **Systemic Schema Omission:** Alerts on the missing mandatory `Assigned Owner` column.
6. **Statutory Deadline Breaches:** High-priority alerts for expired deadlines on open matters.
7. **Weekend Date Violations:** Flags tickets created or scheduled on non-business days (`T-104`, `T-109`, `T-110`).
8. **Chronological Contradictions:** Flags `T-104` where the next action date is set after the statutory due date.
9. **Ambiguous Status:** Flags `T-106` ("Pending") lacking operational clarity.

### 3. AI Email Intake & Guardrail Simulator (Part A & B)
- **Interactive Simulator:** Run test presets (Email 1: Bank Statement, Email 2: GST Ticket #4521 Follow-up, Email 3: Urgent with zero context) or compose custom client emails.
- **Four-Layer Automated Guardrails:**
  1. *RFC 3676 Boundary Stripping:* Strips quoted email reply blocks and signature footers before model ingestion.
  2. *Verbatim Text Anchoring:* Programmatically asserts that extracted date quotes exist verbatim in unquoted body text.
  3. *Temporal Bounds Sanity Filter:* Rejects past dates or distant future dates (>90 days).
  4. *Ticketing CRM Validation:* Validates referenced ticket IDs against client domain ownership.
- **Deterministic Statutory Calendar Lookup:** Maps compliance queries (e.g., GST GSTR-3B) to official regulatory schedules, prohibiting AI date guessing.

### 4. Human-in-the-Loop Review Queue
- Automatically queues low-confidence emails (`confidence_score < 0.80`), ambiguous directives, or triggered tripwires.
- Allows senior advisors to sign off, reassign, or discard with full audit logging.

### 5. 30-Second Executive Exception Report (Part C3)
- Real-time generation of the top 3 high-impact alert lines:
  1. `[REGULATORY DEADLINE BREACH]`: Expired statutory filings.
  2. `[IMMINENT FILING AT RISK]`: Filings due tomorrow with no action date.
  3. `[INTERNAL SLA & DATA INTEGRITY]`: Tickets in SLA breach and duplicate pairs.
- 1-Click Clipboard Copy and downloadable PDF Digest.

---

## REST API Specification

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status and metadata |
| `GET` | `/api/tickets` | List all tickets with computed working-day SLA metrics |
| `POST` | `/api/tickets` | Create a new ticket with schema validation |
| `PUT` | `/api/tickets/{id}` | Update ticket status, dates, or assigned owner |
| `POST` | `/api/tickets/merge` | 1-Click merge of duplicate tickets (e.g., T-105 into T-101) |
| `POST` | `/api/tickets/canonicalize` | 1-Click client entity normalization |
| `POST` | `/api/tickets/reset` | Reset tickets back to assessment baseline |
| `GET` | `/api/audit/anomalies` | Real-time scan of all 9 data traps |
| `POST` | `/api/email/ingest` | Process incoming email via AI triage and 4-layer guardrails |
| `GET` | `/api/triage/queue` | List items awaiting human review |
| `POST` | `/api/triage/approve` | Dual-control sign-off on review queue item |
| `GET` | `/api/reports/daily-exceptions` | Get 30-second executive exception summary JSON |
| `GET` | `/api/reports/daily-exceptions/pdf` | Download formatted daily exception PDF report |

---

## Local Installation & Setup

### Prerequisites
- Python 3.10+
- `pip`

```bash
# 1. Clone repository
git clone https://github.com/Omiii-215/meridian-advisory-ai-automation.git
cd meridian-advisory-ai-automation

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the platform
uvicorn app.main:app --reload --port 8000
```

Open your browser and navigate to: **`http://localhost:8000`**

---

## Running Automated Tests

```bash
# Run full test suite
python3 -m pytest -v tests/
```

Test coverage includes:
- **`tests/test_sla_logic.py`**: Business-day calendar math, weekend exclusions, and SLA breach calculations.
- **`tests/test_guardrails.py`**: RFC 3676 stripping, verbatim quote assertions, and temporal bounds.
- **`tests/test_api.py`**: Ticket endpoints, data quality audits, and email ingestion webhooks.

---

## Live Cloud Deployment

### Option A: Docker Container
```bash
docker build -t meridian-advisory-platform .
docker run -p 8000:8000 meridian-advisory-platform
```

### Option B: Render (1-Click Deployment)
Connect this repository to [Render](https://render.com) using the included `render.yaml`.

### Option C: Vercel
Deploy to Vercel using `vercel --prod` using the included `vercel.json`.

---

## Candidate Information
- **Name:** Om S Habib (Applied via Internshala)
- **Role:** AI Automation Intern (PPO Track)
- **Evaluation Date:** 19 August 2026
- **Submission To:** Aditi Singh, Human Resources (`aditi.singh@suvitt.com`)
