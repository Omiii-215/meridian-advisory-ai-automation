// State
let allTickets = [];
let activeFilter = 'all';

document.addEventListener('DOMContentLoaded', () => {
    fetchTickets();
    fetchAuditAnomalies();
    fetchHumanReviewQueue();
    fetchDailyExceptionReport();
});

// Tab Switching
function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

    const activeBtn = Array.from(document.querySelectorAll('.tab-btn')).find(b => b.getAttribute('onclick').includes(tabId));
    if (activeBtn) activeBtn.classList.add('active');

    const content = document.getElementById(tabId);
    if (content) content.classList.add('active');

    if (tabId === 'auditorTab') fetchAuditAnomalies();
    if (tabId === 'reviewTab') fetchHumanReviewQueue();
    if (tabId === 'reportTab') fetchDailyExceptionReport();
}

// -----------------------------------------------------------------------------
// 1. TICKETS DASHBOARD
// -----------------------------------------------------------------------------
async function fetchTickets() {
    try {
        const res = await fetch('/api/tickets');
        allTickets = await res.json();
        updateMetrics(allTickets);
        renderTickets();
    } catch (err) {
        console.error('Error fetching tickets:', err);
    }
}

function updateMetrics(tickets) {
    document.getElementById('metricTotal').textContent = tickets.length;
    document.getElementById('metricOpen').textContent = tickets.filter(t => t.status === 'Open').length;
    document.getElementById('metricSlaBreach').textContent = tickets.filter(t => t.is_sla_breached).length;
    document.getElementById('metricStatOverdue').textContent = tickets.filter(t => t.is_statutory_overdue).length;
}

function filterTickets(filter, chipEl) {
    activeFilter = filter;
    document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
    if (chipEl) chipEl.classList.add('active');
    renderTickets();
}

function renderTickets() {
    const tbody = document.getElementById('ticketsTableBody');
    tbody.innerHTML = '';

    let filtered = allTickets;
    if (activeFilter === 'SLA_BREACH') {
        filtered = allTickets.filter(t => t.is_sla_breached);
    } else if (activeFilter !== 'all') {
        filtered = allTickets.filter(t => t.status.toLowerCase() === activeFilter.toLowerCase());
    }

    filtered.forEach(t => {
        const tr = document.createElement('tr');

        // Status badge
        let statusBadge = `<span class="badge badge-open">Open</span>`;
        if (t.status === 'Pending') statusBadge = `<span class="badge badge-pending">Pending</span>`;
        if (t.status === 'Closed') statusBadge = `<span class="badge badge-closed">Closed</span>`;

        // SLA status badge
        let slaBadge = `<span class="badge badge-success">${t.sla_status_label}</span>`;
        if (t.is_sla_breached) {
            slaBadge = `<span class="badge badge-danger"><i class="fa-solid fa-triangle-exclamation"></i> ${t.sla_status_label}</span>`;
        } else if (t.sla_status_label.includes('LIMIT')) {
            slaBadge = `<span class="badge badge-warning">${t.sla_status_label}</span>`;
        }

        // Statutory highlight
        let statDateDisplay = t.statutory_due_date || '<span style="color:#94a3b8;">[Missing]</span>';
        if (t.is_statutory_overdue) {
            statDateDisplay += ` <span class="badge badge-danger">OVERDUE (+${t.statutory_days_diff}d)</span>`;
        } else if (t.is_statutory_imminent) {
            statDateDisplay += ` <span class="badge badge-warning">DUE TOMORROW</span>`;
        }

        // Weekend warnings
        let weekendNotice = '';
        if (t.weekend_warnings && t.weekend_warnings.length > 0) {
            weekendNotice = `<div style="font-size:10px; color:#d97706;"><i class="fa-regular fa-clock"></i> ${t.weekend_warnings[0]}</div>`;
        }

        tr.innerHTML = `
            <td><strong>${t.id}</strong></td>
            <td><strong>${escapeHtml(t.client)}</strong> ${weekendNotice}</td>
            <td>${statusBadge}</td>
            <td>${t.created_date}</td>
            <td>${t.next_action_date || '<span style="color:#ef4444; font-weight:600;">[None - SLA Breach]</span>'}</td>
            <td>${statDateDisplay}</td>
            <td>${t.assigned_owner || '<span style="color:#94a3b8; font-style:italic;">Unassigned</span>'}</td>
            <td>${slaBadge}</td>
            <td>
                <button class="btn btn-secondary" style="padding:4px 8px; font-size:11px;" onclick="openEditTicketModal('${t.id}')">
                    <i class="fa-solid fa-pen-to-square"></i> Edit
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function resetTickets() {
    if (!confirm("Reset all tickets back to the original assessment baseline?")) return;
    await fetch('/api/tickets/reset', { method: 'POST' });
    await fetchTickets();
    await fetchAuditAnomalies();
    alert("Tickets reset to baseline!");
}

// -----------------------------------------------------------------------------
// 2. DATA QUALITY AUDITOR & 1-CLICK FIXES
// -----------------------------------------------------------------------------
async function fetchAuditAnomalies() {
    try {
        const res = await fetch('/api/audit/anomalies');
        const data = await res.json();
        document.getElementById('metricAnomalies').textContent = data.total_anomalies_found;
        renderAnomalies(data.anomalies);
    } catch (err) {
        console.error('Error fetching audit:', err);
    }
}

function renderAnomalies(anomalies) {
    const container = document.getElementById('anomaliesList');
    container.innerHTML = '';

    anomalies.forEach(a => {
        const card = document.createElement('div');
        card.className = `anomaly-card ${a.severity}`;

        let actionBtn = '';
        if (a.action_type === 'MERGE_DUPLICATE') {
            actionBtn = `<button class="btn btn-primary" style="padding:4px 10px; font-size:12px;" onclick="fixMergeDuplicates()"><i class="fa-solid fa-code-merge"></i> Merge T-105 into T-101</button>`;
        } else if (a.action_type === 'CANONICALIZE_CLIENTS') {
            actionBtn = `<button class="btn btn-secondary" style="padding:4px 10px; font-size:12px;" onclick="fixCanonicalizeClients()"><i class="fa-solid fa-wand-magic-sparkles"></i> Normalize Names</button>`;
        }

        card.innerHTML = `
            <div>
                <div class="anomaly-title">
                    <span>${escapeHtml(a.title)}</span>
                    <span class="badge badge-${a.severity === 'CRITICAL' ? 'danger' : a.severity === 'HIGH' ? 'warning' : 'pending'}">${a.severity}</span>
                </div>
                <p class="anomaly-desc">${escapeHtml(a.description)}</p>
                <div style="font-size:11.5px; color:#475569; margin-bottom:8px;">
                    <strong>Involved Tickets:</strong> ${a.tickets.map(tid => `<span class="badge" style="background:#e2e8f0; margin-right:3px;">${tid}</span>`).join('')}
                </div>
            </div>
            <div class="anomaly-footer">
                <span style="font-size:11px; color:#64748b;">Code: <code>${a.code}</code></span>
                ${actionBtn}
            </div>
        `;
        container.appendChild(card);
    });
}

async function fixMergeDuplicates() {
    try {
        const res = await fetch('/api/tickets/merge?primary_id=T-101&duplicate_id=T-105', { method: 'POST' });
        const data = await res.json();
        alert(data.message);
        await fetchTickets();
        await fetchAuditAnomalies();
    } catch (err) {
        alert("Merge error: " + err);
    }
}

async function fixCanonicalizeClients() {
    try {
        const res = await fetch('/api/tickets/canonicalize', { method: 'POST' });
        const data = await res.json();
        alert(`Normalized ${data.updated_count} tickets to canonical entity: '${data.canonical_name}'`);
        await fetchTickets();
        await fetchAuditAnomalies();
    } catch (err) {
        alert("Normalization error: " + err);
    }
}

// -----------------------------------------------------------------------------
// 3. AI EMAIL INTAKE SIMULATOR
// -----------------------------------------------------------------------------
const EMAIL_PRESETS = {
    "1": {
        sender: "finance@bluewavefoods.com",
        subject: "Q2 Bank Statements",
        body: "Hi team, please find attached our Q2 bank statement for your records. Thanks.",
        attachment: true,
        reply: false
    },
    "2": {
        sender: "compliance@crestpharma.com",
        subject: "Re: Ticket #4521 - Urgent Filing Update",
        body: "Following up on ticket #4521 - any update on the GST filing? We need this closed by end of month.",
        attachment: false,
        reply: true
    },
    "3": {
        sender: "md@everestretail.com",
        subject: "Action Required",
        body: "URGENT!! Please handle asap.",
        attachment: false,
        reply: false
    }
};

function loadEmailTemplate() {
    const val = document.getElementById('emailTemplateSelect').value;
    if (val in EMAIL_PRESETS) {
        const p = EMAIL_PRESETS[val];
        document.getElementById('emailSender').value = p.sender;
        document.getElementById('emailSubject').value = p.subject;
        document.getElementById('emailBody').value = p.body;
        document.getElementById('emailAttachment').checked = p.attachment;
        document.getElementById('emailThreadReply').checked = p.reply;
    }
}

async function handleEmailSubmit(e) {
    e.preventDefault();
    const btn = document.getElementById('btnRunTriage');
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing Guardrails...';

    const payload = {
        sender: document.getElementById('emailSender').value,
        subject: document.getElementById('emailSubject').value,
        body: document.getElementById('emailBody').value,
        has_physical_attachment: document.getElementById('emailAttachment').checked,
        in_reply_to: document.getElementById('emailThreadReply').checked ? "<msg-101@mail.meridian.com>" : null,
        received_date: "2026-08-19",
        team: "Tax"
    };

    try {
        const res = await fetch('/api/email/ingest', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await res.json();
        renderSimulatorResult(result);
        await fetchHumanReviewQueue();
    } catch (err) {
        alert("Error executing email intake: " + err);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-bolt"></i> Run AI Intake & Guardrail Engine';
    }
}

function renderSimulatorResult(res) {
    document.getElementById('simEmptyState').style.display = 'none';
    const container = document.getElementById('simResultContainer');
    container.style.display = 'block';

    const cl = res.classification;
    const isSuccess = res.tripwires_passed && cl.confidence_score >= 0.80;

    let tripwireHtml = '';
    if (!res.tripwires_passed) {
        tripwireHtml = `
            <div class="tripwire-alert-box danger">
                <strong><i class="fa-solid fa-triangle-exclamation"></i> Safety Tripwires Triggered:</strong>
                <ul style="margin-left: 18px; margin-top: 4px;">
                    ${res.tripwire_warnings.map(w => `<li>${escapeHtml(w)}</li>`).join('')}
                </ul>
            </div>
        `;
    } else {
        tripwireHtml = `
            <div class="tripwire-alert-box success">
                <strong><i class="fa-solid fa-circle-check"></i> All 4 Automated Safety Guardrails Passed:</strong>
                <div style="font-size:11px; margin-top:3px;">RFC 3676 stripping verified | Verbatim quote verified | Temporal bounds valid | CRM entity valid</div>
            </div>
        `;
    }

    container.innerHTML = `
        <div style="margin-bottom: 12px; display:flex; justify-content:space-between; align-items:center;">
            <div>
                <span class="badge badge-open">Tracking ID: ${res.email_id}</span>
                ${res.is_duplicate_thread ? '<span class="badge badge-warning">Thread Reply (De-duplicated)</span>' : ''}
            </div>
            <div>
                <strong>Routing Action:</strong> <span class="badge ${res.requires_human_approval ? 'badge-danger' : 'badge-success'}">${res.routing_action}</span>
            </div>
        </div>

        ${tripwireHtml}

        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; margin-bottom:12px;">
            <div style="background:#f8fafc; padding:10px; border-radius:6px; border:1px solid #e2e8f0;">
                <div style="font-size:11px; color:#64748b;">CLASSIFICATION TYPE</div>
                <div style="font-weight:700; color:#0f2b48;">${cl.classification_type}</div>
            </div>
            <div style="background:#f8fafc; padding:10px; border-radius:6px; border:1px solid #e2e8f0;">
                <div style="font-size:11px; color:#64748b;">URGENCY & CONFIDENCE</div>
                <div style="font-weight:700; color:#0f2b48;">${cl.urgency} (Score: ${(cl.confidence_score * 100).toFixed(0)}%)</div>
            </div>
        </div>

        <div style="margin-bottom: 10px;">
            <strong>System Action Message:</strong>
            <p style="font-size:12.5px; color:#334155; margin-top:2px;">${escapeHtml(res.message)}</p>
        </div>

        <div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                <strong>Structured Pydantic JSON Output:</strong>
                <span style="font-size:11px; color:#64748b;">Strict Schema Compliance</span>
            </div>
            <pre class="json-viewer"><code>${escapeHtml(JSON.stringify(cl, null, 2))}</code></pre>
        </div>
    `;
}

// -----------------------------------------------------------------------------
// 4. HUMAN REVIEW QUEUE
// -----------------------------------------------------------------------------
async function fetchHumanReviewQueue() {
    try {
        const res = await fetch('/api/triage/queue');
        const items = await res.json();
        document.getElementById('reviewBadgeCount').textContent = items.filter(i => i.status === 'PENDING_REVIEW').length;
        renderReviewQueue(items);
    } catch (err) {
        console.error('Error fetching review queue:', err);
    }
}

function renderReviewQueue(items) {
    const container = document.getElementById('reviewQueueList');
    container.innerHTML = '';

    if (items.length === 0) {
        container.innerHTML = `<div class="empty-state" style="grid-column:1/-1;"><i class="fa-solid fa-check-double"></i><p>No items pending human review. All automations operating normally.</p></div>`;
        return;
    }

    items.forEach(item => {
        const card = document.createElement('div');
        card.className = 'anomaly-card HIGH';
        const isPending = item.status === 'PENDING_REVIEW';

        card.innerHTML = `
            <div>
                <div class="anomaly-title">
                    <span>${escapeHtml(item.subject)}</span>
                    <span class="badge ${isPending ? 'badge-danger' : 'badge-success'}">${item.status}</span>
                </div>
                <div style="font-size:12px; color:#64748b; margin-bottom:8px;">
                    From: <strong>${escapeHtml(item.sender)}</strong> | Ref: <code>${item.review_id}</code>
                </div>
                <div style="background:#f8fafc; padding:8px 10px; border-radius:4px; font-size:12px; font-style:italic; margin-bottom:10px;">
                    "${escapeHtml(item.clean_body)}"
                </div>
                ${item.tripwire_warnings && item.tripwire_warnings.length > 0 ? `
                    <div style="font-size:11.5px; color:#dc2626; margin-bottom:8px;">
                        <strong>Triggered Warnings:</strong> ${item.tripwire_warnings.join('; ')}
                    </div>
                ` : ''}
            </div>
            <div class="anomaly-footer">
                ${isPending ? `
                    <button class="btn btn-secondary" style="padding:4px 10px; font-size:11px;" onclick="approveReviewItem('${item.review_id}', 'REJECT_SPAM')">Discard</button>
                    <button class="btn btn-primary" style="padding:4px 12px; font-size:11px;" onclick="approveReviewItem('${item.review_id}', 'CREATE_VERIFIED_TICKET')">
                        <i class="fa-solid fa-check"></i> Sign-off & Create Ticket
                    </button>
                ` : `
                    <span style="font-size:12px; color:#047857;">Signed off: ${item.approved_action}</span>
                `}
            </div>
        `;
        container.appendChild(card);
    });
}

async function approveReviewItem(reviewId, action) {
    try {
        const res = await fetch(`/api/triage/approve?review_id=${reviewId}&action=${action}`, { method: 'POST' });
        const data = await res.json();
        alert(`Item ${reviewId} successfully approved with action: ${action}`);
        await fetchHumanReviewQueue();
        await fetchTickets();
    } catch (err) {
        alert("Approval error: " + err);
    }
}

// -----------------------------------------------------------------------------
// 5. 30-SECOND EXECUTIVE REPORT
// -----------------------------------------------------------------------------
let cachedReport = null;

async function fetchDailyExceptionReport() {
    try {
        const res = await fetch('/api/reports/daily-exceptions');
        cachedReport = await res.json();
        renderExecutiveReport(cachedReport);
    } catch (err) {
        console.error('Error fetching report:', err);
    }
}

function renderExecutiveReport(report) {
    const container = document.getElementById('executiveLinesContainer');
    container.innerHTML = '';

    report.top_three_executive_lines.forEach(line => {
        const div = document.createElement('div');
        div.className = 'alert-item';
        div.textContent = line;
        container.appendChild(div);
    });

    const m = report.metrics;
    document.getElementById('reportMetricsBox').innerHTML = `
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(160px, 1fr)); gap:12px; margin-top:14px;">
            <div style="background:#fff; padding:12px; border:1px solid #e2e8f0; border-radius:6px;">
                <div style="font-size:11px; color:#64748b;">TOTAL TICKETS</div>
                <div style="font-size:18px; font-weight:700;">${m.total_tickets}</div>
            </div>
            <div style="background:#fff; padding:12px; border:1px solid #e2e8f0; border-radius:6px;">
                <div style="font-size:11px; color:#64748b;">ACTIVE OPEN</div>
                <div style="font-size:18px; font-weight:700;">${m.open_tickets}</div>
            </div>
            <div style="background:#fff; padding:12px; border:1px solid #e2e8f0; border-radius:6px;">
                <div style="font-size:11px; color:#64748b;">SLA BREACHES (>2d)</div>
                <div style="font-size:18px; font-weight:700; color:#ef4444;">${m.sla_breach_count}</div>
            </div>
            <div style="background:#fff; padding:12px; border:1px solid #e2e8f0; border-radius:6px;">
                <div style="font-size:11px; color:#64748b;">STATUTORY OVERDUE</div>
                <div style="font-size:18px; font-weight:700; color:#dc2626;">${m.statutory_overdue_count}</div>
            </div>
            <div style="background:#fff; padding:12px; border:1px solid #e2e8f0; border-radius:6px;">
                <div style="font-size:11px; color:#64748b;">DUE TOMORROW</div>
                <div style="font-size:18px; font-weight:700; color:#d97706;">${m.statutory_imminent_count}</div>
            </div>
        </div>
    `;
}

function copyReportLines() {
    if (!cachedReport) return;
    const text = cachedReport.top_three_executive_lines.join('\n\n');
    navigator.clipboard.writeText(text).then(() => {
        alert("Top three executive exception lines copied to clipboard!");
    });
}

// -----------------------------------------------------------------------------
// 6. MODAL HANDLERS
// -----------------------------------------------------------------------------
function openNewTicketModal() {
    document.getElementById('modalTitle').textContent = 'Create New Ticket';
    document.getElementById('modalTicketId').value = '';
    document.getElementById('modalClient').value = '';
    document.getElementById('modalStatus').value = 'Open';
    document.getElementById('modalOwner').value = 'Rajesh Sharma';
    document.getElementById('modalNextAction').value = '2026-08-21';
    document.getElementById('modalStatutory').value = '2026-08-28';
    document.getElementById('ticketModal').classList.add('open');
}

function openEditTicketModal(ticketId) {
    const t = allTickets.find(x => x.id === ticketId);
    if (!t) return;
    document.getElementById('modalTitle').textContent = `Edit Ticket ${t.id}`;
    document.getElementById('modalTicketId').value = t.id;
    document.getElementById('modalClient').value = t.client;
    document.getElementById('modalStatus').value = t.status;
    document.getElementById('modalOwner').value = t.assigned_owner || '';
    document.getElementById('modalNextAction').value = t.next_action_date || '';
    document.getElementById('modalStatutory').value = t.statutory_due_date || '';
    document.getElementById('ticketModal').classList.add('open');
}

function closeTicketModal() {
    document.getElementById('ticketModal').classList.remove('open');
}

async function handleTicketSave(e) {
    e.preventDefault();
    const id = document.getElementById('modalTicketId').value;
    const payload = {
        client: document.getElementById('modalClient').value,
        status: document.getElementById('modalStatus').value,
        assigned_owner: document.getElementById('modalOwner').value,
        next_action_date: document.getElementById('modalNextAction').value,
        statutory_due_date: document.getElementById('modalStatutory').value
    };

    try {
        if (id) {
            await fetch(`/api/tickets/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        } else {
            await fetch('/api/tickets', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        }
        closeTicketModal();
        await fetchTickets();
        await fetchAuditAnomalies();
    } catch (err) {
        alert("Error saving ticket: " + err);
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
