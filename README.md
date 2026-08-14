# CampusFix AI v2

**Secure Role-Based Campus Maintenance & Complaint Resolution System**

This version extends the exhibition prototype with:
- Login using employee/technician/manager ID and password
- Three roles: Faculty, Technician, Facility Manager
- SQLite database
- AI-style complaint classification, risk and priority assessment
- Automatic technician routing
- Technician work-order status updates
- Resolution report submission
- Facility Manager visibility into all complaints and reports

## Demo accounts

| Role | ID | Password |
|---|---|---|
| Faculty | EMP001 | Faculty123 |
| Faculty | EMP002 | Faculty123 |
| Technician | TECH001 | Tech123 |
| Technician | TECH002 | Tech123 |
| Technician | TECH003 | Tech123 |
| Technician | TECH004 | Tech123 |
| Facility Manager | FM001 | Manager123 |

These are demo credentials only. Change them before any real deployment.

## Run on Mac

```bash
cd "/Users/jkp/Development/Antigravity/CampusFix_AI_v2"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open `http://localhost:8501`.

## Example exhibition flow

1. Login as Faculty `EMP001`
2. Submit:
   "There is a burning smell and sparks coming from the electrical panel in CSE Lab 3."
3. Show AI classification: Electrical
4. Show risk: Critical
5. Show priority: Emergency
6. Show assigned technician
7. Logout
8. Login as the assigned technician
9. Accept / update the work order
10. Enter a resolution report and mark it Resolved
11. Logout
12. Login as `FM001`
13. Show that the complaint and technician resolution report are visible to the Facility Manager.

## Security note

This is an exhibition/academic prototype. Passwords are stored as SHA-256 hashes for demonstration. For production deployment, use a proper identity provider, salted password hashing such as Argon2/bcrypt, HTTPS, session controls, audit logging, role-based authorization, backups and institutional authentication.
