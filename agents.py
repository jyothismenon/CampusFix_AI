from database import technicians

def classify(text, selected):
    if selected!="Auto-detect": return selected
    t=text.lower()
    rules={
    "Electrical":["light","fan","switch","power","electric","socket","spark","panel"],
    "Plumbing":["leak","tap","water","pipe","washroom","toilet"],
    "HVAC":["ac","air conditioner","cooling","temperature","ventilation"],
    "IT / Network":["wifi","internet","network","router","computer","login"],
    "Furniture":["chair","desk","table","door","window"],
    "Cleaning":["clean","garbage","dust","spill"],
    "Equipment":["projector","printer","scanner","equipment"]}
    for cat,words in rules.items():
        if any(w in t for w in words): return cat
    return "General Maintenance"

def risk(text):
    t=text.lower()
    if any(w in t for w in ["fire","smoke","sparking","electric shock","gas leak","flood","security breach"]): return "Critical"
    if any(w in t for w in ["danger","unsafe","major leakage","burning smell","short circuit"]): return "High"
    if any(w in t for w in ["not working","broken","leak","urgent","exam","class","tomorrow"]): return "Medium"
    return "Low"

def priority_from_risk(r):
    return {"Critical":"Emergency","High":"High","Medium":"Medium","Low":"Low"}[r]

def choose_technician(cat):
    target={"Electrical":"Electrical","Plumbing":"Plumbing","HVAC":"HVAC","IT / Network":"IT / Network","Equipment":"IT / Network"}.get(cat,"General")
    ts=technicians()
    for t in ts:
        if t["skill"]==target and t["availability"]=="Available": return t["name"]
    return "Maintenance Supervisor"

def analyze_complaint(text,location,selected):
    cat=classify(text,selected); r=risk(text); p=priority_from_risk(r); tech=choose_technician(cat)
    trace=[
    {"agent":"Complaint Agent","decision":f"Understood the complaint at {location}."},
    {"agent":"Classification Agent","decision":f"Classified as {cat}."},
    {"agent":"Risk Agent","decision":f"Assessed risk as {r}."},
    {"agent":"Priority Agent","decision":f"Set priority to {p}."},
    {"agent":"Assignment Agent","decision":f"Selected {tech} based on skill and availability."},
    {"agent":"Notification / Follow-up Agent","decision":"Prepared routing to technician and visibility for Facility Manager."}]
    return {"category":cat,"risk":r,"priority":p,"technician":tech,"trace":trace}
