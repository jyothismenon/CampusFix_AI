import os
import streamlit as st
from datetime import datetime

from database import (
    init_db,
    authenticate,
    create_complaint,
    get_user_complaints,
    get_assigned_complaints,
    update_work_order,
    get_all_complaints,
    get_complaint,
    get_users,
)

from agents import analyze_complaint


# ============================================================
# CAMPUSFIX AI
# Intelligent Campus Facilities Management System
# ============================================================

st.set_page_config(
    page_title="CampusFix AI | DSATM",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Database
init_db()

# Session state
if "user" not in st.session_state:
    st.session_state["user"] = None

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

def get_user_by_id(user_id):
    import sqlite3
    conn_obj = sqlite3.connect("campusfix.db")
    conn_obj.row_factory = sqlite3.Row
    c = conn_obj.cursor()
    r = c.execute(
        "SELECT id, name, role, skill, availability FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()
    conn_obj.close()
    if r:
        return dict(r)
    return None

# Restore session from cookie if available
if st.session_state["user"] is None:
    cookie_user_id = st.context.cookies.get("campusfix_user_id")
    if cookie_user_id:
        restored = get_user_by_id(cookie_user_id)
        if restored:
            st.session_state["user"] = restored


# ============================================================
# GLOBAL CSS
# ============================================================

st.markdown(
    """
    <style>
    /* ---------- GLOBAL & TYPOGRAPHY ---------- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        font-family: 'Inter', sans-serif !important;
        background-color: #0A0E1A !important;
        color: #E2E8F0 !important;
    }
    
    #MainMenu {visibility:hidden;}
    footer {visibility:hidden;}
    header {visibility:hidden;}

    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 1300px !important;
        animation: fadeIn 0.6s ease-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    /* All headings & markdown texts to be white/light */
    h1, h2, h3, h4, h5, h6, p, span, li, b, strong, small {
        color: #FFFFFF !important;
    }
    
    /* Caption and helper text */
    .stMarkdown p, .stMarkdown span {
        color: #CBD5E1 !important;
    }

    /* ---------- INPUTS & FORM CONTROLS ---------- */
    div[data-baseweb="input"], div[data-baseweb="base-input"] {
        border-radius: 10px !important;
        border: 1px solid #1E293B !important;
        transition: all 0.25s ease-in-out !important;
        background-color: #131B2E !important;
    }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="base-input"]:focus-within {
        border-color: #3B82F6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.25) !important;
        background-color: #172237 !important;
    }
    div[data-baseweb="input"] input, div[data-baseweb="base-input"] input {
        color: #FFFFFF !important;
    }
    
    div[data-baseweb="textarea"] textarea {
        border-radius: 10px !important;
        border: 1px solid #1E293B !important;
        transition: all 0.25s ease-in-out !important;
        background-color: #131B2E !important;
        color: #FFFFFF !important;
    }
    div[data-baseweb="textarea"] textarea:focus {
        border-color: #3B82F6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.25) !important;
        background-color: #172237 !important;
    }
    
    div[role="combobox"] {
        background-color: #131B2E !important;
        border-color: #1E293B !important;
        color: #FFFFFF !important;
    }
    div[data-baseweb="select"] {
        background-color: #131B2E !important;
        border-radius: 10px !important;
    }
    div[data-baseweb="select"] * {
        color: #FFFFFF !important;
        background-color: transparent !important;
    }
    
    label[data-testid="stWidgetLabel"] {
        color: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        margin-bottom: 6px !important;
    }
    label[data-testid="stWidgetLabel"] p {
        color: #FFFFFF !important;
    }
    
    ::placeholder {
        color: #94A3B8 !important;
        opacity: 1;
    }

    /* ---------- BUTTONS ---------- */
    div.stButton > button {
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
        padding: 10px 20px !important;
        border: 1px solid #1E293B !important;
        background-color: #131B2E !important;
        color: #E2E8F0 !important;
    }
    div.stButton > button p {
        color: #E2E8F0 !important;
    }
    div.stButton > button:hover {
        transform: translateY(-1.5px) !important;
        box-shadow: 0 6px 15px rgba(0,0,0,0.2) !important;
        border-color: #3B82F6 !important;
        color: #FFFFFF !important;
        background-color: #172237 !important;
    }
    div.stButton > button:hover p {
        color: #FFFFFF !important;
    }
    
    /* Primary buttons */
    .st-key-login_button button,
    div[data-testid="stFormSubmitButton"] button {
        background: linear-gradient(135deg, #0B3B82, #1769D1) !important;
        color: #FFFFFF !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(23, 105, 209, 0.3) !important;
    }
    .st-key-login_button button p,
    div[data-testid="stFormSubmitButton"] button p {
        color: #FFFFFF !important;
    }
    .st-key-login_button button:hover,
    div[data-testid="stFormSubmitButton"] button:hover {
        background: linear-gradient(135deg, #0F386B, #2563EB) !important;
        color: #FFFFFF !important;
        box-shadow: 0 8px 20px rgba(23, 105, 209, 0.5) !important;
    }
    .st-key-login_button button:hover p,
    div[data-testid="stFormSubmitButton"] button:hover p {
        color: #FFFFFF !important;
    }

    /* ---------- BANNER ---------- */
    .banner-container {
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
        margin-bottom: 24px;
        animation: slideDown 0.6s ease-out;
    }
    @keyframes slideDown {
        from { transform: translateY(-20px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    .banner-container img {
        border-radius: 16px;
        width: 100%;
        height: auto;
        max-height: 240px;
        object-fit: cover;
        display: block;
    }

    /* ---------- BRAND BAR ---------- */
    .brand-bar {
        background: linear-gradient(135deg, #131B2E, #1E293B);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 16px 24px;
        color: white;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
        margin-bottom: 20px;
    }
    .brand-name {
        font-size: 26px;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #FFFFFF !important;
    }
    .brand-caption {
        opacity: 0.85;
        font-size: 13px;
        margin-top: 2px;
        color: #CBD5E1 !important;
    }
    .user-pill {
        text-align: right;
        padding: 12px 16px;
        background: #131B2E;
        border: 1px solid #334155;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        font-size: 13px;
        color: #FFFFFF;
    }
    .user-pill b, .user-pill span {
        color: #FFFFFF !important;
    }

    /* ---------- CARDS ---------- */
    .metric-card {
        background: #131B2E;
        border: 1px solid #1E293B;
        border-radius: 16px;
        padding: 20px;
        min-height: 120px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
        transition: all 0.25s ease;
    }
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.25);
        border-color: #334155;
    }
    .metric-label {
        color: #94A3B8;
        font-size: 13px;
        font-weight: 600;
    }
    .metric-value {
        color: #FFFFFF;
        font-size: 32px;
        font-weight: 800;
        margin-top: 6px;
    }
    .status-card {
        border-radius: 16px;
        padding: 16px 20px;
        background: #131B2E;
        border: 1px solid #1E293B;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transition: all 0.2s ease;
    }
    .status-card:hover {
        border-color: #3B82F6;
        box-shadow: 0 6px 18px rgba(59, 130, 246, 0.15);
    }
    .status-id {
        color: #3B82F6;
        font-weight: 800;
    }
    .status-meta {
        color: #94A3B8;
        font-size: 12px;
        margin-top: 6px;
    }
    .status-meta b {
        color: #FFFFFF !important;
    }
    .ai-badge {
        display: inline-block;
        background: #1E293B;
        color: #3B82F6;
        border: 1px solid #334155;
        border-radius: 999px;
        padding: 3px 10px;
        font-size: 11px;
        font-weight: 700;
        margin-right: 6px;
    }
    .section-title {
        color: #FFFFFF;
        font-size: 24px;
        font-weight: 800;
        margin-top: 15px;
        margin-bottom: 4px;
        letter-spacing: -0.3px;
    }
    .section-caption {
        color: #94A3B8;
        font-size: 14px;
        margin-bottom: 20px;
    }
    .role-card {
        background: linear-gradient(135deg, #131B2E, #172237);
        border: 1px solid #1E293B;
        border-radius: 12px;
        padding: 14px 18px;
        margin-top: 20px;
        color: #E2E8F0;
        font-size: 13px;
        line-height: 1.6;
        text-align: center;
    }
    .role-card b {
        color: #3B82F6 !important;
    }
    .login-footer {
        text-align: center;
        color: #94A3B8;
        font-size: 13.5px;
        line-height: 1.6;
        margin-top: 50px;
        margin-bottom: 20px;
    }
    .login-footer b {
        color: #FFFFFF !important;
    }

    /* ---------- LOGIN SPECIFIC OVERRIDES ---------- */
    .st-key-login_card {
        background: #131B2E !important;
        border: 1px solid #1E293B !important;
        border-radius: 20px !important;
        padding: 35px !important;
        box-shadow: 0 15px 45px rgba(0, 0, 0, 0.3) !important;
        animation: slideUp 0.7s cubic-bezier(0.16, 1, 0.3, 1) both;
    }
    @keyframes slideUp {
        from { transform: translateY(30px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    .login-brand-icon {
        font-size: 56px;
        display: inline-block;
        animation: floatIcon 3.5s ease-in-out infinite;
    }
    @keyframes floatIcon {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-8px); }
    }
    .login-brand-title {
        color: #FFFFFF;
        font-size: 42px;
        font-weight: 800;
        margin-top: 8px;
        margin-bottom: 2px;
        text-align: center;
        letter-spacing: -0.5px;
    }
    .login-brand-subtitle {
        color: #94A3B8;
        font-size: 16px;
        font-weight: 500;
        margin-bottom: 24px;
        text-align: center;
    }
    .login-card-header {
        text-align: center;
        color: #FFFFFF;
        font-size: 20px;
        font-weight: 750;
        margin-bottom: 4px;
    }
    .login-card-subheader {
        text-align: center;
        color: #94A3B8;
        font-size: 13px;
        margin-bottom: 24px;
    }

    /* ---------- SIDEBAR ---------- */
    [data-testid="stSidebar"] {
        background-color: #0A0E1A !important;
        border-right: 1px solid #1E293B !important;
    }
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] div.stButton > button {
        background-color: #131B2E !important;
        border: 1px solid #1E293B !important;
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] div.stButton > button:hover {
        background-color: #172237 !important;
        border-color: #3B82F6 !important;
    }

    /* ---------- TABLES / DATAFRAMES ---------- */
    div[data-testid="stTable"] table {
        background-color: #131B2E !important;
        color: #E2E8F0 !important;
        border: 1px solid #1E293B !important;
    }
    div[data-testid="stTable"] th {
        background-color: #172237 !important;
        color: #FFFFFF !important;
        border-bottom: 2px solid #1E293B !important;
    }
    div[data-testid="stTable"] td {
        border-bottom: 1px solid #1E293B !important;
        color: #E2E8F0 !important;
    }
    
    div[data-testid="stDataFrame"] {
        background-color: #131B2E !important;
        border: 1px solid #1E293B !important;
        border-radius: 12px !important;
        overflow: hidden !important;
    }

    /* ---------- ALERTS & INFOS ---------- */
    div[data-testid="stAlert"] {
        background-color: #172237 !important;
        border: 1px solid #3B82F6 !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
    }
    div[data-testid="stAlert"] * {
        color: #FFFFFF !important;
    }

    /* ---------- RESPONSIVE ---------- */
    @media (max-width: 800px) {
        .brand-name { font-size: 20px; }
        .user-pill { text-align: left; margin-top: 10px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================

def logout():
    st.session_state["user"] = None
    st.session_state.page = "Dashboard"
    st.html("""
    <script>
    document.cookie = "campusfix_user_id=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Strict";
    parent.window.location.reload();
    </script>
    """)
    st.stop()


def safe_value(value, default="—"):
    return default if value in (None, "", "None") else str(value)


def show_banner():
    banner_path = os.path.join("Images", "Banner_DSATM.jpg")
    if os.path.exists(banner_path):
        st.markdown('<div class="banner-container">', unsafe_allow_html=True)
        st.image(banner_path, width="stretch")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning(
            f"DSATM banner not found. Expected: {banner_path}"
        )


def header():
    user = st.session_state["user"]

    left, right = st.columns([3.3, 1.5])

    with left:
        st.markdown(
            """
            <div class="brand-bar">
                <div class="brand-name">🛠️ CampusFix AI</div>
                <div class="brand-caption">
                    Intelligent Campus Facilities Management System
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        col_user, col_logout = st.columns([2, 1])
        with col_user:
            st.markdown(
                f"""
                <div class="user-pill" style="padding: 8px 12px; font-size: 12px;">
                    <b>{safe_value(user.get("name"))}</b><br>
                    {safe_value(user.get("role"))}<br>
                    <span style="color:#94A3B8">{safe_value(user.get("id"))}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_logout:
            if st.button("🚪 Logout", key="header_logout_btn", use_container_width=True):
                logout()


def sidebar():
    user = st.session_state["user"]

    with st.sidebar:
        st.markdown("## 🛠️ CampusFix AI")
        st.caption("DSATM Facilities Intelligence")

        st.divider()

        role = user["role"]

        if role == "Faculty":
            pages = [
                ("Dashboard", "🏠"),
                ("Submit Complaint", "📝"),
                ("My Complaints", "📋"),
            ]
        elif role == "Technician":
            pages = [
                ("Dashboard", "🏠"),
                ("Assigned Work", "🔧"),
            ]
        else:
            pages = [
                ("Dashboard", "🏠"),
                ("All Complaints", "📊"),
                ("Technicians", "👨‍🔧"),
            ]

        for page, icon in pages:
            if st.button(
                f"{icon}  {page}",
                key=f"nav_{page}",
                use_container_width=True,
            ):
                st.session_state.page = page
                st.rerun()

        st.divider()

        st.markdown(
            f"""
            **Logged in as**  
            {user["name"]}

            **Role**  
            {user["role"]}
            """
        )

        if st.button(
            "🚪 Logout",
            use_container_width=True,
        ):
            logout()


def metric(label, value, icon):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{icon} &nbsp; {label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def complaint_card(row):
    st.markdown(
        f"""
        <div class="status-card">
            <div>
                <span class="status-id">{safe_value(row.get("id"))}</span>
                &nbsp;&nbsp;
                <span class="ai-badge">{safe_value(row.get("priority"))}</span>
                <span class="ai-badge">{safe_value(row.get("risk"))}</span>
            </div>
            <div style="margin-top:7px;">
                <b>{safe_value(row.get("category"))}</b>
                &nbsp; · &nbsp;
                {safe_value(row.get("location"))}
            </div>
            <div class="status-meta">
                Status: <b>{safe_value(row.get("status"))}</b>
                &nbsp; · &nbsp;
                Created: {safe_value(row.get("created_at"))}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# LOGIN SCREEN
# ============================================================

if st.session_state["user"] is None:

    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {display:none;}
        .block-container {
            padding-top: 1rem !important;
            max-width: 1200px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    show_banner()

    _, center, _ = st.columns([1, 1.1, 1])

    with center:
        st.markdown(
            '<div style="text-align:center;"><span class="login-brand-icon">🛠️</span></div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="login-brand-title">CampusFix AI</div>
            <div class="login-brand-subtitle">
                Intelligent Campus Facilities Management System
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.container(key="login_card"):
            st.markdown(
                """
                <div class="login-card-header">
                    🔐 Secure Institutional Login
                </div>
                <div class="login-card-subheader">
                    Sign in using your institutional credentials
                </div>
                """,
                unsafe_allow_html=True,
            )

            user_id = st.text_input(
                "Employee / Technician / Manager ID",
                placeholder="Example: 180762",
                key="login_user_id",
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password",
            )

            login_clicked = st.button(
                "🚀  Login to CampusFix AI",
                key="login_button",
                use_container_width=True,
            )

            st.markdown(
                """
                <div class="role-card">
                    <b style="color:#3B82F6;">👥 Authorized Users</b><br>
                    👨‍🏫 Faculty / Employees &nbsp; · &nbsp;
                    🧑‍🔧 Maintenance Technicians &nbsp; · &nbsp;
                    👨‍💼 Facility Manager
                </div>
                """,
                unsafe_allow_html=True,
            )

        if login_clicked:
            if not user_id.strip() or not password:
                st.warning("Please enter both User ID and Password.")
            else:
                user = authenticate(
                    user_id.strip(),
                    password,
                )

                if user:
                    st.session_state["user"] = user
                    st.session_state.page = "Dashboard"
                    st.html(f"""
                    <script>
                    document.cookie = "campusfix_user_id={user['id']}; path=/; max-age=86400; SameSite=Strict";
                    parent.window.location.reload();
                    </script>
                    """)
                    st.stop()
                else:
                    st.error("Invalid Employee ID or password.")

        st.markdown(
            """
            <div class="login-footer">
                <b>CampusFix AI</b><br>
                Intelligent Maintenance & Decision Support<br>
                Dayananda Sagar Academy of Technology & Management
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.stop()


# ============================================================
# AUTHENTICATED APPLICATION
# ============================================================

sidebar()
show_banner()
header()

user = st.session_state["user"]
role = user["role"]
page = st.session_state.page


# ============================================================
# FACULTY DASHBOARD
# ============================================================

def faculty_dashboard():
    rows = get_user_complaints(user["id"])

    total = len(rows)
    open_count = len(
        [r for r in rows if r["status"] not in ("Resolved", "Closed")]
    )
    resolved = len(
        [r for r in rows if r["status"] == "Resolved"]
    )

    st.markdown(
        '<div class="section-title">Welcome to CampusFix AI 👋</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-caption">'
        'Submit and track campus facility complaints with AI-assisted '
        'classification, risk assessment and technician assignment.'
        '</div>',
        unsafe_allow_html=True,
    )

    a, b, c = st.columns(3)
    with a:
        metric("My Complaints", total, "📋")
    with b:
        metric("Open Complaints", open_count, "⏳")
    with c:
        metric("Resolved", resolved, "✅")

    st.divider()

    st.markdown("### 🚀 Quick Actions")

    a, b = st.columns(2)

    with a:
        if st.button(
            "📝 Submit New Complaint",
            use_container_width=True,
        ):
            st.session_state.page = "Submit Complaint"
            st.rerun()

    with b:
        if st.button(
            "📋 Track My Complaints",
            use_container_width=True,
        ):
            st.session_state.page = "My Complaints"
            st.rerun()

    st.markdown("### 🕒 Recent Complaints")

    for row in rows[:5]:
        complaint_card(row)

    if not rows:
        st.info(
            "No complaints submitted yet. Use 'Submit Complaint' "
            "to report a facility issue."
        )


# ============================================================
# FACULTY - SUBMIT COMPLAINT
# ============================================================

def submit_complaint():
    st.markdown(
        '<div class="section-title">📝 Submit a Facility Complaint</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-caption">'
        'CampusFix AI will analyse the complaint and recommend the '
        'appropriate category, risk level, priority and technician.'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.form("complaint_form", clear_on_submit=False):

        description = st.text_area(
            "Describe the problem",
            placeholder=(
                "Example: Water is leaking continuously from the washroom "
                "pipeline near Block A, First Floor."
            ),
            height=150,
        )

        location = st.text_input(
            "Location",
            placeholder="Example: Block A - First Floor",
        )

        submitted = st.form_submit_button(
            "🤖 Analyse & Submit Complaint",
            use_container_width=True,
        )

    if submitted:

        if not description.strip():
            st.warning("Please describe the problem.")
            return

        if not location.strip():
            st.warning("Please enter the location.")
            return

        with st.spinner("CampusFix AI is analysing the complaint..."):
            try:
                analysis = analyze_complaint(
                    description,
                    location,
                )

                cid = create_complaint(
                    user["id"],
                    description,
                    location,
                    analysis,
                )

            except TypeError:
                # Compatibility with agents.py implementations that
                # accept only the complaint text.
                try:
                    analysis = analyze_complaint(description)
                    cid = create_complaint(
                        user["id"],
                        description,
                        location,
                        analysis,
                    )
                except Exception as exc:
                    st.error(f"AI analysis failed: {exc}")
                    return

            except Exception as exc:
                st.error(f"Unable to submit complaint: {exc}")
                return

        st.success(f"Complaint {cid} submitted successfully.")

        st.markdown("### 🤖 AI Analysis")

        a, b, c, d = st.columns(4)

        with a:
            st.metric(
                "Category",
                safe_value(analysis.get("category")),
            )

        with b:
            st.metric(
                "Risk",
                safe_value(analysis.get("risk")),
            )

        with c:
            st.metric(
                "Priority",
                safe_value(analysis.get("priority")),
            )

        with d:
            st.metric(
                "Technician",
                safe_value(analysis.get("technician")),
            )

        st.info(
            "The complaint has been recorded in the CampusFix AI database "
            "and assigned according to the AI analysis."
        )


# ============================================================
# FACULTY - MY COMPLAINTS
# ============================================================

def my_complaints():

    rows = get_user_complaints(user["id"])

    st.markdown(
        '<div class="section-title">📋 My Complaints</div>',
        unsafe_allow_html=True,
    )

    if not rows:
        st.info("You have not submitted any complaints.")
        return

    for row in rows:

        complaint_card(row)

        with st.expander(
            f"View details — {safe_value(row.get('id'))}"
        ):

            st.write(
                f"**Location:** {safe_value(row.get('location'))}"
            )

            st.write(
                f"**Category:** {safe_value(row.get('category'))}"
            )

            st.write(
                f"**Risk:** {safe_value(row.get('risk'))}"
            )

            st.write(
                f"**Priority:** {safe_value(row.get('priority'))}"
            )

            st.write(
                f"**Status:** {safe_value(row.get('status'))}"
            )

            st.write(
                f"**Technician:** {safe_value(row.get('technician_id'))}"
            )

            st.write(
                f"**Created:** {safe_value(row.get('created_at'))}"
            )

            if row.get("resolved_at"):
                st.write(
                    f"**Resolved:** {row['resolved_at']}"
                )

            if row.get("resolution_report"):
                st.markdown("**Resolution Report:**")
                st.info(
                    safe_value(row.get("resolution_report"))
                )

# ============================================================
# TECHNICIAN DASHBOARD
# ============================================================

def technician_dashboard():
    rows = get_assigned_complaints(user["id"])

    total = len(rows)
    active = len(
        [r for r in rows if r["status"] != "Resolved"]
    )
    resolved = len(
        [r for r in rows if r["status"] == "Resolved"]
    )

    st.markdown(
        '<div class="section-title">🔧 Technician Work Centre</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-caption">'
        'View AI-assigned work orders, update progress and submit '
        'resolution reports.'
        '</div>',
        unsafe_allow_html=True,
    )

    a, b, c = st.columns(3)

    with a:
        metric("Assigned", total, "📋")

    with b:
        metric("Active", active, "🔧")

    with c:
        metric("Resolved", resolved, "✅")

    st.divider()

    if not rows:
        st.success("No work orders are currently assigned to you.")
        return

    for row in rows:

        complaint_card(row)

        with st.expander(
            f"🔧 Work Order — {safe_value(row.get('id'))}"
        ):

            st.write(
                f"**Location:** {safe_value(row.get('location'))}"
            )

            st.write(
                f"**Category:** {safe_value(row.get('category'))}"
            )

            st.write(
                f"**Risk:** {safe_value(row.get('risk'))}"
            )

            st.write(
                f"**Priority:** {safe_value(row.get('priority'))}"
            )

            st.write(
                f"**Current Status:** {safe_value(row.get('status'))}"
            )

            status = st.selectbox(
                "Update Status",
                [
                    "Assigned",
                    "In Progress",
                    "Resolved",
                ],
                index=(
                    [
                        "Assigned",
                        "In Progress",
                        "Resolved",
                    ].index(row["status"])
                    if row["status"] in
                    ["Assigned", "In Progress", "Resolved"]
                    else 0
                ),
                key=f"status_{row['id']}",
            )

            report = st.text_area(
                "Resolution Report",
                value=safe_value(
                    row.get("resolution_report"),
                    "",
                ),
                placeholder=(
                    "Describe the work carried out, parts replaced, "
                    "tests performed and final condition."
                ),
                key=f"report_{row['id']}",
            )

            if st.button(
                "💾 Update Work Order",
                key=f"update_{row['id']}",
                use_container_width=True,
            ):

                update_work_order(
                    row["id"],
                    status,
                    report,
                )

                st.success(
                    "Work order updated successfully."
                )

                st.rerun()


# ============================================================
# FACILITY MANAGER DASHBOARD
# ============================================================

def manager_dashboard():
    rows = get_all_complaints()

    total = len(rows)
    active = len(
        [r for r in rows if r["status"] != "Resolved"]
    )
    resolved = len(
        [r for r in rows if r["status"] == "Resolved"]
    )
    high_risk = len(
        [r for r in rows if str(r["risk"]).lower() == "high"]
    )

    st.markdown(
        '<div class="section-title">📊 Facility Management Dashboard</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-caption">'
        'Central monitoring of complaints, AI risk assessment, '
        'priority and maintenance resolution.'
        '</div>',
        unsafe_allow_html=True,
    )

    a, b, c, d = st.columns(4)

    with a:
        metric("Total Complaints", total, "📋")

    with b:
        metric("Active", active, "⏳")

    with c:
        metric("Resolved", resolved, "✅")

    with d:
        metric("High Risk", high_risk, "🚨")

    st.divider()

    if not rows:
        st.info("No complaints are available.")
        return

    st.markdown("### 📈 Complaint Overview")

    categories = {}
    for row in rows:
        category = safe_value(row.get("category"), "Unknown")
        categories[category] = categories.get(category, 0) + 1

    if categories:
        st.bar_chart(categories)

    st.markdown("### 🛠️ Latest Complaints")

    for row in rows[:10]:

        complaint_card(row)

        with st.expander(
            f"View {safe_value(row.get('id'))}"
        ):

            st.write(
                f"**Technician:** "
                f"{safe_value(row.get('technician_name'))}"
            )

            st.write(
                f"**Assigned:** "
                f"{safe_value(row.get('assigned_at'))}"
            )

            st.write(
                f"**Resolved:** "
                f"{safe_value(row.get('resolved_at'))}"
            )

            if row.get("resolution_report"):
                st.success(
                    row["resolution_report"]
                )


# ============================================================
# FACILITY MANAGER - ALL COMPLAINTS
# ============================================================

def all_complaints_page():
    rows = get_all_complaints()

    st.markdown(
        '<div class="section-title">📋 All Facility Complaints</div>',
        unsafe_allow_html=True,
    )

    if not rows:
        st.info("No complaints recorded.")
        return

    for row in rows:
        complaint_card(row)


# ============================================================
# FACILITY MANAGER - TECHNICIANS
# ============================================================

def technicians_page():
    users = get_users()

    techs = [
        u for u in users
        if u.get("role") == "Technician"
    ]

    st.markdown(
        '<div class="section-title">👨‍🔧 Technician Availability</div>',
        unsafe_allow_html=True,
    )

    if not techs:
        st.info("No technicians found.")
        return

    for tech in techs:

        availability = safe_value(
            tech.get("availability"),
            "Available",
        )

        st.markdown(
            f"""
            <div class="status-card">
                <b style="color:#123B75;">
                    {safe_value(tech.get("name"))}
                </b><br>
                ID: {safe_value(tech.get("id"))}<br>
                Skill: {safe_value(tech.get("skill"))}<br>
                Availability:
                <b>{availability}</b>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# ROUTING
# ============================================================

if role == "Faculty":

    if page == "Dashboard":
        faculty_dashboard()

    elif page == "Submit Complaint":
        submit_complaint()

    elif page == "My Complaints":
        my_complaints()

    else:
        faculty_dashboard()


elif role == "Technician":

    if page == "Dashboard":
        technician_dashboard()

    elif page == "Assigned Work":
        technician_dashboard()

    else:
        technician_dashboard()


elif role == "Facility Manager":

    if page == "Dashboard":
        manager_dashboard()

    elif page == "All Complaints":
        all_complaints_page()

    elif page == "Technicians":
        technicians_page()

    else:
        manager_dashboard()

else:

    st.error(
        f"Unsupported user role: {role}"
    )

    if st.button("Logout"):
        logout()
