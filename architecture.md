# CampusFix AI v2 Architecture

```text
Employee Login
     |
     v
Faculty Dashboard
     |
Submit Complaint
     |
     v
+-----------------------+
| AI Decision Pipeline  |
| Classification        |
| Risk Assessment       |
| Priority              |
| Technician Assignment |
+-----------+-----------+
            |
            v
   Technician Dashboard
            |
    Accept / Work / Resolve
            |
            v
    Resolution Report
            |
       +----+----+
       |         |
       v         v
   Faculty   Facility Manager
               Dashboard
```

## Database entities

- Users
- Complaints
- Work orders (represented by complaint workflow/status)
- Resolution reports

## Future production extensions

- PostgreSQL
- FastAPI backend
- Proper authentication/SSO
- RAG over maintenance SOPs
- LLM-based complaint understanding
- MCP-compatible tools
- Email/SMS/WhatsApp notifications
- Photo evidence and attachments
- SLA escalation
- Audit trail
