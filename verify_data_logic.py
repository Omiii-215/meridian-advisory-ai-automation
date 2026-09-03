import datetime

# Reference Date
today = datetime.date(2026, 8, 19)

tickets = [
    {"id": "T-101", "client": "Acme Textiles", "status": "Open", "created": "2026-08-10", "next_action": "2026-08-13", "statutory": "2026-08-25"},
    {"id": "T-102", "client": "acme textile", "status": "Open", "created": "2026-08-11", "next_action": None, "statutory": "2026-08-20"},
    {"id": "T-103", "client": "Bluewave Foods", "status": "Closed", "created": "2026-08-05", "next_action": None, "statutory": None},
    {"id": "T-104", "client": "Crest Pharma", "status": "Open", "created": "2026-08-01", "next_action": "2026-08-03", "statutory": "2026-08-01"},
    {"id": "T-105", "client": "Acme Textiles", "status": "Open", "created": "2026-08-10", "next_action": "2026-08-13", "statutory": "2026-08-25"},
    {"id": "T-106", "client": "Delta Logistics", "status": "Pending", "created": "2026-08-12", "next_action": "2026-08-14", "statutory": None},
    {"id": "T-107", "client": "Bluewave Foods", "status": "Open", "created": "2026-07-30", "next_action": None, "statutory": "2026-08-18"},
    {"id": "T-108", "client": "Crest Pharma", "status": "Closed", "created": "2026-08-10", "next_action": None, "statutory": "2026-08-10"},
    {"id": "T-109", "client": "Everest Retail", "status": "Open", "created": "2026-08-13", "next_action": "2026-08-15", "statutory": "2026-09-01"},
    {"id": "T-110", "client": "ACME Textiles Pvt Ltd", "status": "Open", "created": "2026-08-09", "next_action": "2026-08-11", "statutory": "2026-08-22"},
]

def parse(d):
    return datetime.datetime.strptime(d, "%Y-%m-%d").date() if d else None

def get_working_days(start, end):
    # Excludes start day, includes end day
    cur = start + datetime.timedelta(days=1)
    days = []
    while cur <= end:
        if cur.weekday() < 5:
            days.append(cur)
        cur += datetime.timedelta(days=1)
    return len(days), days

print("=== PART C VERIFICATION SCRIPT ===")
print(f"Evaluation Date (Today): {today} ({today.strftime('%A')})\n")

for t in tickets:
    c = parse(t['created'])
    na = parse(t['next_action'])
    stat = parse(t['statutory'])
    
    c_wd, _ = get_working_days(c, today)
    
    print(f"Ticket {t['id']} [{t['status']}]: Client='{t['client']}'")
    print(f"  Created: {c} ({c.strftime('%a')}) -> Elapsed Working Days: {c_wd}")
    if na:
        na_wd, na_list = get_working_days(na, today)
        print(f"  Next Action Date: {na} ({na.strftime('%a')}) -> Working Days Overdue: {na_wd} ({[d.strftime('%a %d-%b') for d in na_list]})")
    else:
        print(f"  Next Action Date: [MISSING] -> Open without next action for {c_wd} working days")
    
    if stat:
        diff = (today - stat).days
        if diff > 0:
            print(f"  Statutory Due Date: {stat} ({stat.strftime('%a')}) -> EXPIRED / OVERDUE by {diff} calendar days!")
        elif diff == 0:
            print(f"  Statutory Due Date: {stat} ({stat.strftime('%a')}) -> DUE TODAY!")
        else:
            print(f"  Statutory Due Date: {stat} ({stat.strftime('%a')}) -> Due in {-diff} days")
    else:
        print(f"  Statutory Due Date: [MISSING]")
    print("-" * 50)
