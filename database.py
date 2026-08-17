import sqlite3
import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo


DB = "campusfix.db"


# ============================================================
# INDIA STANDARD TIME
# ============================================================

def local_now():
    """
    Return current time in India Standard Time (IST).
    This works correctly on Streamlit Cloud, where the
    server timezone is UTC.
    """
    return datetime.now(ZoneInfo("Asia/Kolkata"))


def local_timestamp():
    """
    Return current IST timestamp in database-friendly format.
    """
    return local_now().strftime("%Y-%m-%d %H:%M:%S")


# ============================================================
# DATABASE CONNECTION
# ============================================================

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_db():
    c = conn()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        skill TEXT,
        availability TEXT DEFAULT 'Available'
    );

    CREATE TABLE IF NOT EXISTS complaints(
        id TEXT PRIMARY KEY,
        employee_id TEXT NOT NULL,
        description TEXT NOT NULL,
        location TEXT,
        category TEXT,
        risk TEXT,
        priority TEXT,
        technician_id TEXT,
        status TEXT DEFAULT 'Assigned',
        created_at TEXT,
        assigned_at TEXT,
        resolved_at TEXT,
        resolution_report TEXT DEFAULT '',
        FOREIGN KEY(employee_id) REFERENCES users(id),
        FOREIGN KEY(technician_id) REFERENCES users(id)
    );
    """)

    # ========================================================
    # DATABASE MIGRATION
    # ========================================================

    cursor = c.cursor()

    cursor.execute("PRAGMA table_info(complaints)")
    columns = [row[1] for row in cursor.fetchall()]

    if "accepted_at" not in columns:
        c.execute(
            "ALTER TABLE complaints ADD COLUMN accepted_at TEXT"
        )

    if "last_status_update" not in columns:
        c.execute(
            "ALTER TABLE complaints ADD COLUMN last_status_update TEXT"
        )

    if "technician_status" not in columns:
        c.execute(
            "ALTER TABLE complaints ADD COLUMN technician_status TEXT"
        )

    if "work_started_at" not in columns:
        c.execute(
            "ALTER TABLE complaints ADD COLUMN work_started_at TEXT"
        )

    c.execute("""
    CREATE TABLE IF NOT EXISTS parts_requests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        complaint_id TEXT NOT NULL,
        technician_id TEXT NOT NULL,
        part_name TEXT NOT NULL,
        normalized_part_name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        purchase_method TEXT NOT NULL,
        offline_expected_price REAL,
        selected_online_price REAL,
        selected_source TEXT,
        selected_product_url TEXT,
        status TEXT DEFAULT 'Pending',
        manager_recommendation TEXT,
        manager_comment TEXT,
        requested_at TEXT,
        approved_at TEXT,
        FOREIGN KEY(complaint_id) REFERENCES complaints(id),
        FOREIGN KEY(technician_id) REFERENCES users(id)
    );
    """)

    cursor.execute("PRAGMA table_info(parts_requests)")
    pr_columns = [row[1] for row in cursor.fetchall()]
    
    if pr_columns:
        if "price_checked_at" not in pr_columns:
            c.execute("ALTER TABLE parts_requests ADD COLUMN price_checked_at TEXT")
        if "price_source" not in pr_columns:
            c.execute("ALTER TABLE parts_requests ADD COLUMN price_source TEXT")
        if "product_url" not in pr_columns:
            c.execute("ALTER TABLE parts_requests ADD COLUMN product_url TEXT")
        if "online_price" not in pr_columns:
            c.execute("ALTER TABLE parts_requests ADD COLUMN online_price REAL")

    # ========================================================
    # DEMO USERS
    # ========================================================

    users = [
        (
            "EMP001",
            "Dr. Priya",
            "Faculty",
            "Faculty123",
            "",
            "Available"
        ),
        (
            "EMP002",
            "Prof. Arun",
            "Faculty",
            "Faculty123",
            "",
            "Available"
        ),
        (
            "TECH001",
            "Rajesh",
            "Technician",
            "Tech123",
            "Electrical",
            "Available"
        ),
        (
            "TECH002",
            "Anil",
            "Technician",
            "Tech123",
            "Plumbing",
            "Available"
        ),
        (
            "TECH003",
            "Meena",
            "Technician",
            "Tech123",
            "HVAC",
            "Available"
        ),
        (
            "TECH004",
            "Suresh",
            "Technician",
            "Tech123",
            "IT / Network",
            "Available"
        ),
        (
            "TECH005",
            "Vikram",
            "Technician",
            "Tech123",
            "Civil / Building",
            "Available"
        ),
        (
            "TECH006",
            "Ramesh",
            "Technician",
            "Tech123",
            "Cleaning / Housekeeping",
            "Available"
        ),
        (
            "TECH007",
            "Sanjay",
            "Technician",
            "Tech123",
            "Furniture",
            "Available"
        ),
        (
            "TECH008",
            "Kiran",
            "Technician",
            "Tech123",
            "Other",
            "Available"
        ),
        (
            "FM001",
            "Facility Manager",
            "Facility Manager",
            "Manager123",
            "Management",
            "Available"
        )
    ]

    # Insert demo users only if they don't already exist
    for (
        user_id,
        name,
        role,
        password,
        skill,
        availability
    ) in users:

        exists = c.execute(
            "SELECT COUNT(*) FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()[0]

        if exists == 0:
            c.execute(
                """
                INSERT INTO users
                (
                    id,
                    name,
                    role,
                    password_hash,
                    skill,
                    availability
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    name,
                    role,
                    hash_pw(password),
                    skill,
                    availability
                )
            )

    c.commit()
    c.close()


# ============================================================
# AUTHENTICATION
# ============================================================

def authenticate(uid, password):
    c = conn()

    r = c.execute(
        """
        SELECT
            id,
            name,
            role,
            skill,
            availability
        FROM users
        WHERE id = ?
        AND password_hash = ?
        """,
        (
            uid,
            hash_pw(password)
        )
    ).fetchone()

    c.close()

    if r:
        return dict(r)

    return None


# ============================================================
# GET TECHNICIANS
# ============================================================

def technicians():
    c = conn()

    rows = c.execute(
        """
        SELECT
            id,
            name,
            skill,
            availability
        FROM users
        WHERE role = 'Technician'
        """
    ).fetchall()

    c.close()

    return [dict(r) for r in rows]


# ============================================================
# CREATE COMPLAINT
# ============================================================

def create_complaint(
    employee_id,
    description,
    location,
    analysis
):
    c = conn()

    # Complaint ID uses IST
    cid = "CAM-" + local_now().strftime("%m%d%H%M%S")

    # Find technician selected by AI
    tech = next(
        (
            x
            for x in technicians()
            if x["name"] == analysis["technician"]
        ),
        None
    )

    technician_id = tech["id"] if tech else None

    # IMPORTANT:
    # All new timestamps are generated in IST.
    now = local_timestamp()

    c.execute(
        """
        INSERT INTO complaints (
            id,
            employee_id,
            description,
            location,
            category,
            risk,
            priority,
            technician_id,
            status,
            created_at,
            assigned_at,
            resolved_at,
            resolution_report
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cid,
            employee_id,
            description,
            location,
            analysis["category"],
            analysis["risk"],
            analysis["priority"],
            technician_id,
            "Assigned",
            now,
            now,
            None,
            ""
        )
    )

    c.commit()
    c.close()

    return cid


# ============================================================
# FACULTY - MY COMPLAINTS
# ============================================================

def get_user_complaints(uid):
    c = conn()

    rows = c.execute(
        """
        SELECT
            c.*,
            u.name AS technician_name
        FROM complaints c
        LEFT JOIN users u
            ON c.technician_id = u.id
        WHERE c.employee_id = ?
        ORDER BY c.created_at DESC
        """,
        (uid,)
    ).fetchall()

    c.close()

    return [dict(r) for r in rows]


# ============================================================
# TECHNICIAN - ASSIGNED COMPLAINTS
# ============================================================

def get_assigned_complaints(technician_id):
    c = conn()

    rows = c.execute(
        """
        SELECT
            c.*,
            u.name AS technician_name
        FROM complaints c
        LEFT JOIN users u
            ON c.technician_id = u.id
        WHERE c.technician_id = ?
        ORDER BY c.created_at DESC
        """,
        (technician_id,)
    ).fetchall()

    c.close()

    return [dict(r) for r in rows]


# ============================================================
# UPDATE WORK ORDER
# ============================================================

def update_work_order(cid, status, report):

    c = conn()

    # Current time in IST
    now = local_timestamp()

    # Fetch technician associated with complaint
    comp = c.execute(
        """
        SELECT technician_id
        FROM complaints
        WHERE id = ?
        """,
        (cid,)
    ).fetchone()

    tech_id = comp["technician_id"] if comp else None

    if status == "Resolved":

        resolved = now

        # Professional default resolution message
        if not report or not report.strip():
            report = (
                "Problem resolved successfully. "
                "The reported facility issue has been attended to "
                "and the required corrective action has been completed."
            )

        # Technician becomes available after resolution
        if tech_id:
            c.execute(
                """
                UPDATE users
                SET availability = 'Available'
                WHERE id = ?
                """,
                (tech_id,)
            )

    else:
        resolved = None

    c.execute(
        """
        UPDATE complaints
        SET
            status = ?,
            resolution_report = ?,
            resolved_at = ?,
            last_status_update = ?
        WHERE id = ?
        """,
        (
            status,
            report.strip(),
            resolved,
            now,
            cid
        )
    )

    c.commit()
    c.close()


# ============================================================
# ACCEPT WORK ORDER
# ============================================================

def accept_work_order(cid, tech_id):

    c = conn()

    # Acceptance time in IST
    now = local_timestamp()

    c.execute(
        """
        UPDATE complaints
        SET
            status = 'Accepted',
            accepted_at = ?,
            last_status_update = ?
        WHERE id = ?
        """,
        (
            now,
            now,
            cid
        )
    )

    # Technician becomes Busy
    c.execute(
        """
        UPDATE users
        SET availability = 'Busy'
        WHERE id = ?
        """,
        (tech_id,)
    )

    c.commit()
    c.close()


# ============================================================
# UPDATE TECHNICIAN AVAILABILITY
# ============================================================

def update_user_availability(user_id, availability):

    c = conn()

    c.execute(
        """
        UPDATE users
        SET availability = ?
        WHERE id = ?
        """,
        (
            availability,
            user_id
        )
    )

    c.commit()
    c.close()


# ============================================================
# DELETE COMPLAINT
# ============================================================

def delete_complaint(cid):

    c = conn()

    comp = c.execute(
        """
        SELECT
            technician_id,
            status
        FROM complaints
        WHERE id = ?
        """,
        (cid,)
    ).fetchone()

    if comp:

        tech_id = comp["technician_id"]
        status = comp["status"]

        # Release technician if active work is deleted
        if (
            tech_id
            and status == "Accepted/In Progress"
        ):
            c.execute(
                """
                UPDATE users
                SET availability = 'Available'
                WHERE id = ?
                """,
                (tech_id,)
            )

    c.execute(
        """
        DELETE FROM complaints
        WHERE id = ?
        """,
        (cid,)
    )

    c.commit()
    c.close()


# ============================================================
# EDIT COMPLAINT
# ============================================================

def edit_complaint(
    cid,
    description,
    location,
    category,
    risk,
    priority,
    technician_id,
    status=None
):

    c = conn()

    # Edit/update time in IST
    now = local_timestamp()

    old = c.execute(
        """
        SELECT
            technician_id,
            status
        FROM complaints
        WHERE id = ?
        """,
        (cid,)
    ).fetchone()

    if old:

        old_tech = old["technician_id"]
        old_status = old["status"]

        # Release old technician if active assignment changes
        if (
            old_tech
            and old_tech != technician_id
            and old_status == "Accepted/In Progress"
        ):
            c.execute(
                """
                UPDATE users
                SET availability = 'Available'
                WHERE id = ?
                """,
                (old_tech,)
            )

    if status:

        c.execute(
            """
            UPDATE complaints
            SET
                description = ?,
                location = ?,
                category = ?,
                risk = ?,
                priority = ?,
                technician_id = ?,
                status = ?,
                last_status_update = ?
            WHERE id = ?
            """,
            (
                description,
                location,
                category,
                risk,
                priority,
                technician_id,
                status,
                now,
                cid
            )
        )

    else:

        c.execute(
            """
            UPDATE complaints
            SET
                description = ?,
                location = ?,
                category = ?,
                risk = ?,
                priority = ?,
                technician_id = ?
            WHERE id = ?
            """,
            (
                description,
                location,
                category,
                risk,
                priority,
                technician_id,
                cid
            )
        )

    c.commit()
    c.close()


# ============================================================
# FACILITY MANAGER - ALL COMPLAINTS
# ============================================================

def get_all_complaints():

    c = conn()

    rows = c.execute(
        """
        SELECT
            c.id,
            c.description,
            c.location,
            c.category,
            c.risk,
            c.priority,
            c.status,
            c.created_at,
            c.assigned_at,
            c.accepted_at,
            c.last_status_update,
            c.resolved_at,
            c.technician_id,
            u.name AS technician_name,
            u.availability AS technician_availability,
            c.resolution_report
        FROM complaints c
        LEFT JOIN users u
            ON c.technician_id = u.id
        ORDER BY c.created_at DESC
        """
    ).fetchall()

    c.close()

    return [dict(r) for r in rows]


# ============================================================
# GET SINGLE COMPLAINT
# ============================================================

def get_complaint(complaint_id):

    c = conn()

    r = c.execute(
        """
        SELECT
            c.*,
            u.name AS technician_name
        FROM complaints c
        LEFT JOIN users u
            ON c.technician_id = u.id
        WHERE c.id = ?
        """,
        (complaint_id,)
    ).fetchone()

    c.close()

    if r:
        return dict(r)

    return {}


# ============================================================
# GET ALL USERS
# ============================================================

def get_users():

    c = conn()

    rows = c.execute(
        """
        SELECT
            id,
            name,
            role,
            skill,
            availability
        FROM users
        ORDER BY role, name
        """
    ).fetchall()

    c.close()

    return [dict(r) for r in rows]


# ============================================================
# PARTS REQUESTS MANAGEMENT
# ============================================================

def create_parts_request(complaint_id, technician_id, part_name, normalized_part_name, quantity, purchase_method, offline_expected_price=None, selected_online_price=None, selected_source=None, selected_product_url=None):
    c = conn()
    now = local_timestamp()
    c.execute(
        """
        INSERT INTO parts_requests (
            complaint_id, technician_id, part_name, normalized_part_name, quantity,
            purchase_method, offline_expected_price, selected_online_price,
            selected_source, selected_product_url, status, requested_at,
            price_checked_at, price_source, product_url, online_price
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?, ?, ?, ?, ?)
        """,
        (
            complaint_id, technician_id, part_name, normalized_part_name, quantity,
            purchase_method, offline_expected_price, selected_online_price,
            selected_source, selected_product_url, now, now, selected_source, selected_product_url, selected_online_price
        )
    )
    # Update complaints status to 'Waiting for Manager Approval'
    c.execute(
        """
        UPDATE complaints
        SET status = 'Waiting for Manager Approval',
            last_status_update = ?
        WHERE id = ?
        """,
        (now, complaint_id)
    )
    c.commit()
    c.close()


def get_parts_requests_by_complaint(complaint_id):
    c = conn()
    rows = c.execute(
        "SELECT * FROM parts_requests WHERE complaint_id = ? ORDER BY requested_at DESC",
        (complaint_id,)
    ).fetchall()
    c.close()
    return [dict(r) for r in rows]

def get_pending_parts_requests():
    c = conn()
    rows = c.execute(
        """
        SELECT pr.*, c.location, u.name AS technician_name
        FROM parts_requests pr
        JOIN complaints c ON pr.complaint_id = c.id
        JOIN users u ON pr.technician_id = u.id
        WHERE pr.status = 'Pending'
        ORDER BY pr.requested_at DESC
        """
    ).fetchall()
    c.close()
    return [dict(r) for r in rows]

def get_all_parts_requests():
    c = conn()
    rows = c.execute(
        """
        SELECT pr.*, u.name AS technician_name
        FROM parts_requests pr
        JOIN users u ON pr.technician_id = u.id
        ORDER BY pr.requested_at DESC
        """
    ).fetchall()
    c.close()
    return [dict(r) for r in rows]

def update_parts_request_status(request_id, status, recommendation=None, comment=None):
    c = conn()
    now = local_timestamp()
    
    # Get complaint_id
    req = c.execute("SELECT complaint_id FROM parts_requests WHERE id = ?", (request_id,)).fetchone()
    if not req:
        c.close()
        return
    complaint_id = req["complaint_id"]

    c.execute(
        """
        UPDATE parts_requests
        SET status = ?,
            manager_recommendation = ?,
            manager_comment = ?,
            approved_at = ?
        WHERE id = ?
        """,
        (status, recommendation, comment, now, request_id)
    )

    # Set complaint status depending on approved/rejected
    complaint_status = "Parts Approved" if status == "Approved" else "Parts Rejected"
    c.execute(
        """
        UPDATE complaints
        SET status = ?,
            last_status_update = ?
        WHERE id = ?
        """,
        (complaint_status, now, complaint_id)
    )
    c.commit()
    c.close()

def start_work_on_complaint(complaint_id):
    c = conn()
    now = local_timestamp()
    c.execute(
        """
        UPDATE complaints
        SET status = 'Work Started',
            work_started_at = ?,
            last_status_update = ?
        WHERE id = ?
        """,
        (now, now, complaint_id)
    )
    c.commit()
    c.close()