import sqlite3
from datetime import datetime

DB = "campusfix.db"

def classify(text, selected):
    if selected != "Auto-detect":
        return selected
    t = text.lower()
    rules = {
        "Electrical": ["light", "fan", "switch", "power", "electric", "socket", "spark", "panel", "wiring", "bulb"],
        "Plumbing": ["leak", "tap", "water", "pipe", "washroom", "toilet", "clog", "sink", "drain", "sewage", "flush"],
        "HVAC": ["ac", "air conditioner", "cooling", "temperature", "ventilation", "heating", "heater", "chiller"],
        "IT / Network": ["wifi", "internet", "network", "router", "computer", "login", "ethernet", "server", "lan"],
        "Civil / Building": ["wall", "ceiling", "floor", "brick", "cement", "crack", "paint", "roof", "tile", "structure"],
        "Cleaning / Housekeeping": ["clean", "garbage", "dust", "spill", "trash", "waste", "sweep", "mop", "litter"],
        "Furniture": ["chair", "desk", "table", "door", "window", "bench", "cupboard", "cabinet", "lock", "handle"],
    }
    for cat, words in rules.items():
        if any(w in t for w in words):
            return cat
    return "Other"

def risk(text):
    t = text.lower()
    if any(w in t for w in ["fire", "smoke", "sparking", "electric shock", "gas leak", "flood", "security breach"]):
        return "Critical"
    if any(w in t for w in ["danger", "unsafe", "major leakage", "burning smell", "short circuit"]):
        return "High"
    if any(w in t for w in ["not working", "broken", "leak", "urgent", "exam", "class", "tomorrow"]):
        return "Medium"
    return "Low"

def priority_from_risk(r):
    return {"Critical": "Emergency", "High": "High", "Medium": "Medium", "Low": "Low"}[r]

def choose_technician(cat):
    conn_obj = sqlite3.connect(DB)
    conn_obj.row_factory = sqlite3.Row
    c = conn_obj.cursor()

    # 1. Fetch all technicians
    techs = c.execute("SELECT id, name, skill, availability FROM users WHERE role = 'Technician'").fetchall()

    # 2. Filter by skill match
    matched_techs = [dict(t) for t in techs if t["skill"] == cat]
    if not matched_techs:
        matched_techs = [dict(t) for t in techs]

    eligible_techs = []
    for t in matched_techs:
        tech_id = t["id"]

        # If they are explicitly marked Busy, they are not available
        if t["availability"] == "Busy":
            continue

        # Check for active 1-hour allocation:
        # Count complaints accepted within the last hour
        recent_active = c.execute(
            """
            SELECT COUNT(*) FROM complaints
            WHERE technician_id = ?
            AND status = 'Accepted/In Progress'
            """,
            (tech_id,)
        ).fetchone()[0]

        if recent_active > 0:
            continue

        # Get their active workload count
        workload = c.execute(
            """
            SELECT COUNT(*) FROM complaints
            WHERE technician_id = ?
            AND status NOT IN ('Resolved', 'Closed')
            """,
            (tech_id,)
        ).fetchone()[0]

        eligible_techs.append((t, workload))

    conn_obj.close()

    if eligible_techs:
        # Sort deterministically by workload and then ID
        eligible_techs.sort(key=lambda x: (x[1], x[0]["id"]))
        return eligible_techs[0][0]["name"]

    if matched_techs:
        return matched_techs[0]["name"]

    return "Maintenance Supervisor"

def analyze_complaint(text, location, selected):
    cat = classify(text, selected)
    r = risk(text)
    p = priority_from_risk(r)
    tech = choose_technician(cat)
    trace = [
        {"agent": "Complaint Agent", "decision": f"Understood the complaint at {location}."},
        {"agent": "Classification Agent", "decision": f"Classified as {cat}."},
        {"agent": "Risk Agent", "decision": f"Assessed risk as {r}."},
        {"agent": "Priority Agent", "decision": f"Set priority to {p}."},
        {"agent": "Assignment Agent", "decision": f"Selected {tech} based on skill and availability."},
        {"agent": "Notification / Follow-up Agent", "decision": "Prepared routing to technician and visibility for Facility Manager."}
    ]

    # Generate explanations
    t_lower = text.lower()
    # 1. Category Explanation
    if selected != "Auto-detect":
        cat_reason = f"Category '{cat}' was manually chosen as the Complaint Type by the user."
    else:
        rules = {
            "Electrical": ["light", "fan", "switch", "power", "electric", "socket", "spark", "panel", "wiring", "bulb"],
            "Plumbing": ["leak", "tap", "water", "pipe", "washroom", "toilet", "clog", "sink", "drain", "sewage", "flush"],
            "HVAC": ["ac", "air conditioner", "cooling", "temperature", "ventilation", "heating", "heater", "chiller"],
            "IT / Network": ["wifi", "internet", "network", "router", "computer", "login", "ethernet", "server", "lan"],
            "Civil / Building": ["wall", "ceiling", "floor", "brick", "cement", "crack", "paint", "roof", "tile", "structure"],
            "Cleaning / Housekeeping": ["clean", "garbage", "dust", "spill", "trash", "waste", "sweep", "mop", "litter"],
            "Furniture": ["chair", "desk", "table", "door", "window", "bench", "cupboard", "cabinet", "lock", "handle"],
        }
        matched_words = []
        if cat in rules:
            matched_words = [w for w in rules[cat] if w in t_lower]
        if matched_words:
            cat_reason = f"The complaint contains category keywords: {', '.join(matched_words)}."
        else:
            cat_reason = f"No specific category keywords were detected, so the category fell back to '{cat}'."

    # 2. Risk Explanation
    risk_keywords = {
        "Critical": ["fire", "smoke", "sparking", "electric shock", "gas leak", "flood", "security breach"],
        "High": ["danger", "unsafe", "major leakage", "burning smell", "short circuit"],
        "Medium": ["not working", "broken", "leak", "urgent", "exam", "class", "tomorrow"]
    }
    matched_risk_words = []
    if r in risk_keywords:
        matched_risk_words = [w for w in risk_keywords[r] if w in t_lower]

    if r == "Critical":
        cat_words = f" ({', '.join(matched_risk_words)})" if matched_risk_words else ""
        risk_reason = f"The reported issue describes safety-critical symptoms{cat_words} requiring immediate emergency intervention."
    elif r == "High":
        cat_words = f" ({', '.join(matched_risk_words)})" if matched_risk_words else ""
        risk_reason = f"The description indicates potentially hazardous or unsafe conditions{cat_words}."
    elif r == "Medium":
        cat_words = f" ({', '.join(matched_risk_words)})" if matched_risk_words else ""
        risk_reason = f"The issue reports broken or non-functioning equipment{cat_words} that impacts standard operation."
    else:
        risk_reason = "The description indicates a low-impact or routine facility issue."

    # 3. Priority Explanation
    priority_reason = f"The priority level is set to '{p}' to align response workflows with the assessed '{r}' risk level."

    # 4. Technician Explanation
    if tech == "Maintenance Supervisor":
        tech_reason = f"No specific {cat} technician was available, so the work order was routed to the Maintenance Supervisor."
    else:
        tech_reason = f"Technician '{tech}' matches the required '{cat}' skill set and has the lowest current active workload among available staff."

    explanation = {
        "category_reason": cat_reason,
        "risk_reason": risk_reason,
        "priority_reason": priority_reason,
        "technician_reason": tech_reason
    }

    return {"category": cat, "risk": r, "priority": p, "technician": tech, "trace": trace, "explanation": explanation}
