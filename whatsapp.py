import os
import sqlite3
import urllib.request
import urllib.error
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CampusFix_WhatsApp")

DB_PATH = "campusfix.db"

def get_whatsapp_config():
    """
    Retrieve WhatsApp settings from environment variables or Streamlit secrets.
    """
    config = {}
    keys = [
        "WHATSAPP_ENABLED",
        "WHATSAPP_TEST_MODE",
        "WHATSAPP_ACCESS_TOKEN",
        "WHATSAPP_PHONE_NUMBER_ID",
        "WHATSAPP_BUSINESS_ACCOUNT_ID",
        "WHATSAPP_API_VERSION",
        "WHATSAPP_TEST_RECIPIENT"
    ]
    
    # Try importing Streamlit safely
    st_secrets = {}
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            st_secrets = st.secrets
    except Exception:
        pass

    for key in keys:
        val = os.environ.get(key)
        if val is None and key in st_secrets:
            val = st_secrets[key]
        
        if key in ["WHATSAPP_ENABLED", "WHATSAPP_TEST_MODE"]:
            if isinstance(val, bool):
                config[key] = val
            elif isinstance(val, str):
                config[key] = val.lower() in ("true", "1", "yes")
            else:
                config[key] = False
        else:
            config[key] = val or ""
            
    return config


def send_whatsapp_raw(to_number, message_text):
    """
    Send a raw text message via Meta WhatsApp Cloud API.
    """
    config = get_whatsapp_config()
    if not config["WHATSAPP_ENABLED"]:
        logger.info("WhatsApp notifications are globally disabled.")
        return False

    recipient = to_number
    if config["WHATSAPP_TEST_MODE"]:
        recipient = config["WHATSAPP_TEST_RECIPIENT"]

    if not recipient:
        logger.warning("No recipient specified for WhatsApp message.")
        return False

    # Standardize recipient phone number (keep digits only)
    recipient = "".join(filter(str.isdigit, recipient))
    if not recipient:
        logger.warning("Recipient phone number is invalid after cleaning.")
        return False

    token = config["WHATSAPP_ACCESS_TOKEN"]
    phone_id = config["WHATSAPP_PHONE_NUMBER_ID"]
    version = config["WHATSAPP_API_VERSION"] or "v20.0"

    if not token or not phone_id:
        logger.error("WhatsApp credentials missing (Access Token or Phone Number ID).")
        return False

    url = f"https://graph.facebook.com/{version}/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "text",
        "text": {
            "body": message_text
        }
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = response.read().decode("utf-8")
            logger.info(f"WhatsApp message successfully sent. Response: {res_body}")
            return True
    except Exception as e:
        logger.error(f"Failed to dispatch WhatsApp message. Error: {e}")
        return False


def trigger_whatsapp_notification(complaint_id, event_type):
    """
    Trigger a specific event notification. Performs deduplication using the DB
    and dispatches messages to the appropriate target recipients.
    """
    config = get_whatsapp_config()
    if not config["WHATSAPP_ENABLED"]:
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # Retrieve complaint details
        complaint = c.execute(
            """
            SELECT c.*, 
                   emp.name AS employee_name, emp.whatsapp_number AS employee_phone,
                   tech.name AS technician_name, tech.whatsapp_number AS technician_phone
            FROM complaints c
            LEFT JOIN users emp ON c.employee_id = emp.id
            LEFT JOIN users tech ON c.technician_id = tech.id
            WHERE c.id = ?
            """,
            (complaint_id,)
        ).fetchone()

        if not complaint:
            logger.error(f"Complaint {complaint_id} not found. Cannot send notification.")
            conn.close()
            return

        complaint = dict(complaint)

        # Retrieve Facility Manager details
        manager = c.execute("SELECT whatsapp_number FROM users WHERE role = 'Facility Manager' LIMIT 1").fetchone()
        manager_phone = manager["whatsapp_number"] if manager else None

        # Retrieve parts request details if relevant
        part_name = "Spare Parts"
        quantity = 1
        manager_comment = ""
        parts_req = c.execute(
            "SELECT * FROM parts_requests WHERE complaint_id = ? ORDER BY requested_at DESC LIMIT 1",
            (complaint_id,)
        ).fetchone()
        if parts_req:
            part_name = parts_req["part_name"]
            quantity = parts_req["quantity"]
            manager_comment = parts_req["manager_comment"] or ""

        conn.close()

        # Recipient mapping based on user role/recipient type
        # format: (recipient_role, phone_number, tag)
        recipients = []

        if event_type == "complaint_submitted":
            recipients = [("EMPLOYEE", complaint["employee_phone"])]
        elif event_type == "technician_assigned":
            recipients = [("TECHNICIAN", complaint["technician_phone"])]
        elif event_type == "technician_accepts":
            recipients = [
                ("EMPLOYEE", complaint["employee_phone"]),
                ("FACILITY MANAGER", manager_phone)
            ]
        elif event_type == "inspection_started":
            recipients = [("EMPLOYEE", complaint["employee_phone"])]
        elif event_type == "inspection_no_parts":
            recipients = [("EMPLOYEE", complaint["employee_phone"])]
        elif event_type == "parts_required":
            recipients = [
                ("EMPLOYEE", complaint["employee_phone"]),
                ("FACILITY MANAGER", manager_phone)
            ]
        elif event_type == "parts_approved":
            recipients = [
                ("TECHNICIAN", complaint["technician_phone"]),
                ("EMPLOYEE", complaint["employee_phone"])
            ]
        elif event_type == "parts_rejected":
            recipients = [
                ("TECHNICIAN", complaint["technician_phone"]),
                ("EMPLOYEE", complaint["employee_phone"])
            ]
        elif event_type == "work_started":
            recipients = [
                ("EMPLOYEE", complaint["employee_phone"]),
                ("FACILITY MANAGER", manager_phone)
            ]
        elif event_type == "resolved":
            recipients = [
                ("EMPLOYEE", complaint["employee_phone"]),
                ("FACILITY MANAGER", manager_phone)
            ]

        for role_tag, phone in recipients:
            if not phone and not config["WHATSAPP_TEST_MODE"]:
                # skip if no phone and not in test mode
                continue

            # Deduplicate checking
            if check_and_log_notification(complaint_id, event_type, role_tag):
                # Already sent
                continue

            # Message construction
            msg = build_message_text(complaint, event_type, role_tag, part_name, quantity, manager_comment)
            
            # Dispatch
            success = send_whatsapp_raw(phone, msg)
            if success:
                record_notification_success(complaint_id, event_type, role_tag)

    except Exception as exc:
        logger.error(f"Error in trigger_whatsapp_notification for event {event_type} on {complaint_id}: {exc}")


def check_and_log_notification(complaint_id, event_type, recipient_type):
    """
    Check if a notification has already been successfully sent/logged.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        res = c.execute(
            """
            SELECT COUNT(*) FROM whatsapp_notifications 
            WHERE complaint_id = ? AND event_type = ? AND recipient_type = ?
            """,
            (complaint_id, event_type, recipient_type)
        ).fetchone()
        conn.close()
        return res[0] > 0
    except Exception as exc:
        logger.error(f"Error checking notification log: {exc}")
        return False


def record_notification_success(complaint_id, event_type, recipient_type):
    """
    Record a notification success log.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute(
            """
            INSERT OR IGNORE INTO whatsapp_notifications (complaint_id, event_type, recipient_type, sent_at)
            VALUES (?, ?, ?, ?)
            """,
            (complaint_id, event_type, recipient_type, now_str)
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        logger.error(f"Error logging notification success: {exc}")


def build_message_text(comp, event_type, role_tag, part_name, quantity, manager_comment):
    """
    Build structured text notifications.
    """
    config = get_whatsapp_config()
    prefix = ""
    if config["WHATSAPP_TEST_MODE"]:
        prefix = f"🛠️ CampusFix AI — DEMO\nIntended recipient: {role_tag}\n\n"

    tech_name = comp["technician_name"] or "Unassigned"
    location = comp["location"] or "N/A"
    category = comp["category"] or "General"

    body = ""
    if event_type == "complaint_submitted":
        body = (
            f"📝 Complaint Submitted: {comp['id']}\n"
            f"Location: {location}\n"
            f"Category: {category}\n"
            f"Description: {comp['description']}\n\n"
            f"Status: Submitted and processing."
        )
    elif event_type == "technician_assigned":
        body = (
            f"🔧 New Work Order Assigned: {comp['id']}\n"
            f"Location: {location}\n"
            f"Priority: {comp['priority']}\n"
            f"Description: {comp['description']}\n\n"
            f"Action: Please review and accept the work order."
        )
    elif event_type == "technician_accepts":
        body = (
            f"🟡 Work Order Accepted: {comp['id']}\n"
            f"Technician: {tech_name}\n"
            f"Location: {location}\n\n"
            f"Status: Accepted (Inspection Pending)"
        )
    elif event_type == "inspection_started":
        body = (
            f"🔍 Inspection In Progress: {comp['id']}\n"
            f"Technician: {tech_name}\n"
            f"Location: {location}\n\n"
            f"Status: Technician has arrived and started inspection."
        )
    elif event_type == "inspection_no_parts":
        body = (
            f"✅ Inspection Completed: {comp['id']}\n"
            f"Technician: {tech_name}\n"
            f"Details: No parts required.\n\n"
            f"Status: Work is starting shortly."
        )
    elif event_type == "parts_required":
        body = (
            f"🧰 Spare Parts Required: {comp['id']}\n"
            f"Technician: {tech_name}\n"
            f"Part: {part_name} (Qty: {quantity})\n\n"
            f"Status: Pending approval by Facility Manager."
        )
    elif event_type == "parts_approved":
        comment_str = f"\nComment: {manager_comment}" if manager_comment else ""
        body = (
            f"🟢 Parts Approved: {comp['id']}\n"
            f"Part: {part_name}{comment_str}\n\n"
            f"Action: Technician can collect parts and start work."
        )
    elif event_type == "parts_rejected":
        comment_str = f"\nComment: {manager_comment}" if manager_comment else ""
        body = (
            f"🔴 Parts Rejected: {comp['id']}\n"
            f"Part: {part_name}{comment_str}\n\n"
            f"Status: Spare parts request was rejected."
        )
    elif event_type == "work_started":
        body = (
            f"⚡ Work Started: {comp['id']}\n"
            f"Technician: {tech_name}\n"
            f"Location: {location}\n\n"
            f"Status: Work has commenced (1-hour maintenance window active)."
        )
    elif event_type == "resolved":
        report_str = f"\nResolution Details: {comp['resolution_report']}" if comp['resolution_report'] else ""
        body = (
            f"🏁 Issue Resolved: {comp['id']}\n"
            f"Technician: {tech_name}\n"
            f"Location: {location}{report_str}\n\n"
            f"Status: Successfully resolved."
        )

    return prefix + body
