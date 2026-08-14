import sqlite3
import hashlib
from datetime import datetime

DB = "campusfix.db"


def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()


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

    # Create demo users only if the users table is empty
    if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:

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
                "FM001",
                "Facility Manager",
                "Facility Manager",
                "Manager123",
                "Management",
                "Available"
            )
        ]

        c.executemany(
            """
            INSERT INTO users
            (id, name, role, password_hash, skill, availability)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    user_id,
                    name,
                    role,
                    hash_pw(password),
                    skill,
                    availability
                )
                for user_id, name, role, password, skill, availability in users
            ]
        )

    c.commit()
    c.close()


def authenticate(uid, password):
    c = conn()

    r = c.execute(
        """
        SELECT id, name, role, skill, availability
        FROM users
        WHERE id = ?
        AND password_hash = ?
        """,
        (uid, hash_pw(password))
    ).fetchone()

    c.close()

    if r:
        return dict(r)

    return None


def technicians():
    c = conn()

    rows = c.execute(
        """
        SELECT id, name, skill, availability
        FROM users
        WHERE role = 'Technician'
        """
    ).fetchall()

    c.close()

    return [dict(r) for r in rows]


def create_complaint(employee_id, description, location, analysis):
    c = conn()

    # Generate complaint ID
    cid = "CAM-" + datetime.now().strftime("%m%d%H%M%S")

    # Find technician selected by AI
    tech = next(
        (
            x for x in technicians()
            if x["name"] == analysis["technician"]
        ),
        None
    )

    technician_id = tech["id"] if tech else None

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # IMPORTANT:
    # complaints table contains exactly 13 columns.
    # Therefore this INSERT uses exactly 13 values.
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


def get_user_complaints(uid):
    c = conn()

    rows = c.execute(
        """
        SELECT
            id,
            location,
            category,
            risk,
            priority,
            status,
            technician_id,
            created_at,
            resolved_at,
            resolution_report
        FROM complaints
        WHERE employee_id = ?
        ORDER BY created_at DESC
        """,
        (uid,)
    ).fetchall()

    c.close()

    return [dict(r) for r in rows]


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


def update_work_order(cid, status, report):
    c = conn()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if status == "Resolved":
        resolved = now

        # Use a professional default resolution message
        if not report or not report.strip():
            report = (
                "Problem resolved successfully. "
                "The reported facility issue has been attended to "
                "and the required corrective action has been completed."
            )
    else:
        resolved = None

    c.execute(
        """
        UPDATE complaints
        SET status=?, resolution_report=?, resolved_at=?
        WHERE id=?
        """,
        (status, report.strip(), resolved, cid)
    )

    c.commit()
    c.close()


def get_all_complaints():
    c = conn()

    rows = c.execute(
        """
        SELECT
            c.id,
            c.location,
            c.category,
            c.risk,
            c.priority,
            c.status,
            c.created_at,
            c.assigned_at,
            c.resolved_at,
            u.name AS technician_name,
            c.resolution_report
        FROM complaints c
        LEFT JOIN users u
            ON c.technician_id = u.id
        ORDER BY c.created_at DESC
        """
    ).fetchall()

    c.close()

    return [dict(r) for r in rows]


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
