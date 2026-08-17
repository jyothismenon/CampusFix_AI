import os
import streamlit as st
from datetime import datetime
import plotly.graph_objects as go

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
    accept_work_order,
    update_user_availability,
    delete_complaint,
    edit_complaint,
    create_parts_request,
    get_parts_requests_by_complaint,
    get_pending_parts_requests,
    get_all_parts_requests,
    update_parts_request_status,
    start_work_on_complaint,
)

from agents import analyze_complaint, normalize_part_name, search_online_prices


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
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "campusfix.db")
    conn_obj = sqlite3.connect(db_path)
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

# Restore session after browser refresh.
# Cookie is preferred; query parameter is a fallback for browsers where
# Streamlit does not immediately expose the cookie after a refresh.
if st.session_state["user"] is None:
    cookie_user_id = st.context.cookies.get("campusfix_user_id")
    query_user_id = st.query_params.get("user_id")

    restore_user_id = cookie_user_id or query_user_id

    if restore_user_id:
        restored = get_user_by_id(restore_user_id)
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
    st.query_params.clear()
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
    role = user.get("role")
    
    # Define role-specific themes
    if role == "Faculty":
        primary_color = "#3B82F6"
        rgba_accent = "rgba(59, 130, 246, 0.25)"
        rgba_shadow = "rgba(59, 130, 246, 0.3)"
        gradient = "linear-gradient(135deg, #1E3A8A, #3B82F6)"
        banner_text = "👨‍🏫 EMPLOYEE WORKSPACE"
        page_title = "👨‍🏫 Employee Workspace"
        subtitle = "CampusFix AI — Facility Complaint Portal"
        display_role = "Employee / Faculty"
    elif role == "Technician":
        primary_color = "#F59E0B"
        rgba_accent = "rgba(245, 158, 11, 0.25)"
        rgba_shadow = "rgba(245, 158, 11, 0.3)"
        gradient = "linear-gradient(135deg, #78350F, #F59E0B)"
        banner_text = "🛠️ TECHNICIAN WORK CENTER"
        page_title = "🛠️ Technician Work Center"
        subtitle = "CampusFix AI — Maintenance Operations"
        display_role = "Technician"
    elif role == "Facility Manager":
        primary_color = "#8B5CF6"
        rgba_accent = "rgba(139, 92, 246, 0.25)"
        rgba_shadow = "rgba(139, 92, 246, 0.3)"
        gradient = "linear-gradient(135deg, #4C1D95, #8B5CF6)"
        banner_text = "📊 FACILITY MANAGER COMMAND CENTER"
        page_title = "📊 Facility Manager Command Center"
        subtitle = "CampusFix AI — Facilities Intelligence"
        display_role = "Facility Manager"
    else:
        # Fallback
        primary_color = "#3B82F6"
        rgba_accent = "rgba(59, 130, 246, 0.25)"
        rgba_shadow = "rgba(59, 130, 246, 0.3)"
        gradient = "linear-gradient(135deg, #131B2E, #1E293B)"
        banner_text = "🛠️ CAMPUSFIX AI WORKSPACE"
        page_title = "CampusFix AI"
        subtitle = "Intelligent Campus Facilities Management"
        display_role = role

    # Inject dynamic css style overrides for input fields, buttons, etc.
    st.markdown(
        f"""
        <style>
        div[data-baseweb="input"]:focus-within, div[data-baseweb="base-input"]:focus-within {{
            border-color: {primary_color} !important;
            box-shadow: 0 0 0 3px {rgba_accent} !important;
        }}
        div[data-baseweb="textarea"] textarea:focus {{
            border-color: {primary_color} !important;
            box-shadow: 0 0 0 3px {rgba_accent} !important;
        }}
        div.stButton > button:hover {{
            border-color: {primary_color} !important;
        }}
        div[data-testid="stFormSubmitButton"] button {{
            background: {gradient} !important;
            color: #FFFFFF !important;
            border: none !important;
            box-shadow: 0 4px 12px {rgba_shadow} !important;
        }}
        div[data-testid="stFormSubmitButton"] button p {{
            color: #FFFFFF !important;
        }}
        div[data-testid="stFormSubmitButton"] button:hover {{
            background: {gradient} !important;
            opacity: 0.9 !important;
            box-shadow: 0 8px 20px {rgba_shadow} !important;
        }}
        /* Subtle card entrance animations */
        .metric-card, .status-card, .complaint-card, .role-card {{
            animation: cardEntrance 0.5s ease-out;
        }}
        @keyframes cardEntrance {{
            from {{ opacity: 0; transform: translateY(15px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        /* Subtle progress transitions */
        .timeline-step {{
            transition: all 0.3s ease;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

    # Render Header layout
    left, right = st.columns([3.3, 1.5])

    with left:
        st.markdown(
            f"""
            <div class="brand-bar role-banner-container" style="background: {gradient}; border-color: {primary_color}; animation: fadeInSlide 0.5s ease-out;">
                <div style="font-size: 11px; font-weight: 800; letter-spacing: 1.5px; opacity: 0.85; color: #FFFFFF; text-transform: uppercase; margin-bottom: 4px;">
                    {banner_text}
                </div>
                <div class="brand-name" style="font-size: 26px; font-weight: 800; color: #FFFFFF;">
                    {page_title}
                </div>
                <div class="brand-caption" style="color: #F8FAFC !important; opacity: 0.9; font-size: 13px; margin-top: 2px;">
                    {subtitle}
                </div>
            </div>
            <style>
            @keyframes fadeInSlide {{
                from {{ opacity: 0; transform: translateY(-10px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )

    with right:
        col_user, col_logout = st.columns([2.2, 1])
        with col_user:
            st.markdown(
                f"""
                <div class="user-pill" style="padding: 10px 14px; font-size: 12px; border-left: 4px solid {primary_color}; animation: fadeInSlide 0.5s ease-out; background: #131B2E; border-top: 1px solid #1E293B; border-bottom: 1px solid #1E293B; border-right: 1px solid #1E293B; border-radius: 12px;">
                    Logged in as: <b style="color: #FFFFFF;">{safe_value(user.get("name"))}</b><br>
                    Role: <span style="color: {primary_color}; font-weight: 600;">{display_role}</span><br>
                    ID: <span style="color:#94A3B8">{safe_value(user.get("id"))}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_logout:
            if st.button("🚪 Logout", key="header_logout_btn", use_container_width=True):
                logout()


def sidebar():
    user = st.session_state.get("user")

    if user is None:
        return

    role = user["role"]

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
    raw_status = safe_value(row.get("status"))
    status_map = {
        "Assigned": "🔵 Assigned",
        "Accepted": "🟡 Accepted (Inspection Pending)",
        "Inspection in Progress": "🟡 Inspection in Progress",
        "Parts Required": "🟠 Parts Required",
        "Waiting for Manager Approval": "🟣 Waiting Approval",
        "Parts Approved": "🟢 Approved",
        "Parts Rejected": "🔴 Rejected",
        "Work Started": "🔵 Work Started",
        "Resolved": "✅ Resolved",
    }
    display_status = status_map.get(raw_status, raw_status)
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
                Status: <b>{display_status}</b>
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
                    st.query_params["user_id"] = user["id"]
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

if st.session_state.get("user") is not None:
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
    if st.button("← Back to Dashboard", key="submit_back_btn"):
        st.session_state.page = "Dashboard"
        st.rerun()

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
        selected = st.selectbox(
            "Complaint Type",
            [
                "Auto-detect",
                "Electrical",
                "Plumbing",
                "HVAC",
                "IT / Network",
                "Civil / Building",
                "Cleaning / Housekeeping",
                "Furniture",
                "Other",
            ],
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

        if not selected:
            st.warning("Please select a complaint type.")
            return

        with st.spinner("CampusFix AI is analysing the complaint..."):
            try:
                analysis = analyze_complaint(
                    description,
                    location,
                    selected,
                )

                cid = create_complaint(
                    user["id"],
                    description,
                    location,
                    analysis,
                )

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

        exp = analysis.get("explanation")
        if exp:
            with st.expander("🧠 Why did CampusFix AI make this decision?", expanded=True):
                st.markdown(f"**Category: {safe_value(analysis.get('category'))}**")
                st.write(f"Reason: {exp.get('category_reason')}")
                st.markdown(f"**Risk: {safe_value(analysis.get('risk'))}**")
                st.write(f"Reason: {exp.get('risk_reason')}")
                st.markdown(f"**Priority: {safe_value(analysis.get('priority'))}**")
                st.write(f"Reason: {exp.get('priority_reason')}")
                st.markdown(f"**Technician: {safe_value(analysis.get('technician'))}**")
                st.write(f"Reason: {exp.get('technician_reason')}")
                st.caption("AI Decision Explanation (CampusFix AI Rule Engine & Database Layer)")


# ============================================================
# FACULTY - MY COMPLAINTS
# ============================================================

def render_timeline(row):
    status = row.get("status")
    tech_name = row.get("technician_name") or "Technician"
    
    from database import get_parts_requests_by_complaint
    reqs = get_parts_requests_by_complaint(row["id"])
    has_parts = len(reqs) > 0
    parts_status = reqs[0]["status"] if has_parts else None
    
    steps = []
    
    # 1. Assigned
    steps.append(("Assigned", "✓ Assigned", True))
    
    # 2. Accepted
    is_accepted = status in ["Accepted", "Inspection in Progress", "Waiting for Manager Approval", "Parts Approved", "Parts Rejected", "Work Started", "Resolved"]
    steps.append(("Accepted", f"✓ Accepted by {tech_name}" if is_accepted else f"○ Accepted by {tech_name}", is_accepted))
    
    # 3. Inspection
    is_inspected = status in ["Waiting for Manager Approval", "Parts Approved", "Parts Rejected", "Work Started", "Resolved"]
    if status == "Inspection in Progress":
        steps.append(("Inspection", "⏳ Inspection in Progress", True))
    else:
        steps.append(("Inspection", "✓ Inspection completed" if is_inspected else "○ Inspection Pending", is_inspected))
        
    # 4. Parts (if requested)
    if has_parts:
        steps.append(("PartsRequested", "✓ Parts requested", True))
        if parts_status == "Pending":
            steps.append(("Approval", "⏳ Waiting for Facility Manager approval", True))
        elif parts_status == "Approved":
            steps.append(("Approval", "✓ Parts Approved by Manager", True))
        elif parts_status == "Rejected":
            steps.append(("Approval", "❌ Parts Request Rejected by Manager", True))
    
    # 5. Work Started
    is_started = status in ["Work Started", "Resolved"]
    if status == "Work Started":
        steps.append(("WorkStarted", "⏳ Work Started (In Progress)", True))
    else:
        steps.append(("WorkStarted", "✓ Work Started" if status == "Resolved" else "○ Work Started", is_started))
        
    # 6. Resolved
    is_resolved = status == "Resolved"
    steps.append(("Resolved", "✓ Resolved" if is_resolved else "○ Resolved", is_resolved))
    
    html_lines = []
    for idx, (code, text, active) in enumerate(steps):
        color = "#10B981" if "✓" in text else ("#F59E0B" if "⏳" in text else ("#EF4444" if "❌" in text else "#64748B"))
        bold = "font-weight: bold; color: #FFFFFF !important;" if active else "color: #64748B !important;"
        html_lines.append(f'<div style="{bold} margin: 4px 0;">{text}</div>')
        if idx < len(steps) - 1:
            html_lines.append('<div style="color:#475569; margin-left: 10px; font-weight: bold;">↓</div>')
            
    return f"""
    <div style="background-color: #131B2E; border: 1px solid #1E293B; border-radius: 12px; padding: 16px; margin: 12px 0;">
        <h4 style="margin-top:0; color:#FFFFFF !important;">📋 Complaint Progress Tracker</h4>
        {''.join(html_lines)}
    </div>
    """


def my_complaints():
    if st.button("← Back to Dashboard", key="my_complaints_back_btn"):
        st.session_state.page = "Dashboard"
        st.rerun()

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

        with st.expander(f"View details — {safe_value(row.get('id'))}"):
            st.write(f"**Description:** {safe_value(row.get('description'))}")
            st.write(f"**Location:** {safe_value(row.get('location'))}")
            st.write(f"**Category:** {safe_value(row.get('category'))}")
            st.write(f"**Risk:** {safe_value(row.get('risk'))}")
            st.write(f"**Priority:** {safe_value(row.get('priority'))}")
            st.write(f"**Status:** {safe_value(row.get('status'))}")
            st.write(f"**Technician:** {safe_value(row.get('technician_name'))} ({safe_value(row.get('technician_id'))})")
            st.write(f"**Created:** {safe_value(row.get('created_at'))}")

            # Display Timeline
            st.markdown(render_timeline(row), unsafe_allow_html=True)

            if row.get("accepted_at"):
                st.write(f"**Accepted/Started:** {row['accepted_at']}")
            if row.get("resolved_at"):
                st.write(f"**Resolved:** {row['resolved_at']}")
            if row.get("resolution_report"):
                st.markdown("**Resolution Report:**")
                st.info(safe_value(row.get("resolution_report")))

            st.divider()

            # Faculty Edit / Delete
            status = row.get("status")
            if status == "Assigned":
                st.markdown("### ✏️ Edit Complaint")
                edit_desc = st.text_area("Edit Description", value=row.get("description"), key=f"edit_desc_{row['id']}")
                edit_loc = st.text_input("Edit Location", value=row.get("location"), key=f"edit_loc_{row['id']}")
                edit_selected = st.selectbox(
                    "Edit Complaint Type",
                    ["Auto-detect", "Electrical", "Plumbing", "HVAC", "IT / Network", "Civil / Building", "Cleaning / Housekeeping", "Furniture", "Other"],
                    index=["Auto-detect", "Electrical", "Plumbing", "HVAC", "IT / Network", "Civil / Building", "Cleaning / Housekeeping", "Furniture", "Other"].index(row.get("category") if row.get("category") in ["Electrical", "Plumbing", "HVAC", "IT / Network", "Civil / Building", "Cleaning / Housekeeping", "Furniture", "Other"] else "Auto-detect"),
                    key=f"edit_selected_{row['id']}"
                )

                if st.button("💾 Save Changes", key=f"save_edit_faculty_{row['id']}", use_container_width=True):
                    if not edit_desc.strip():
                        st.warning("Description cannot be empty.")
                    elif not edit_loc.strip():
                        st.warning("Location cannot be empty.")
                    else:
                        with st.spinner("Re-analysing complaint..."):
                            analysis = analyze_complaint(edit_desc, edit_loc, edit_selected)
                            from database import technicians
                            techs = technicians()
                            new_tech = next((x for x in techs if x["name"] == analysis["technician"]), None)
                            new_tech_id = new_tech["id"] if new_tech else None

                            edit_complaint(
                                row["id"],
                                edit_desc,
                                edit_loc,
                                analysis["category"],
                                analysis["risk"],
                                analysis["priority"],
                                new_tech_id
                            )
                        st.success("Complaint updated successfully!")
                        st.rerun()

                st.markdown("### ❌ Delete Complaint")
                confirm = st.checkbox("I confirm that I want to delete this complaint permanently.", key=f"confirm_del_faculty_{row['id']}")
                if st.button("🗑️ Delete Complaint", key=f"delete_faculty_{row['id']}", use_container_width=True):
                    if confirm:
                        delete_complaint(row["id"])
                        st.success("Complaint deleted successfully!")
                        st.rerun()
                    else:
                        st.warning("Please confirm deletion by ticking the box.")
            else:
                st.info("🔒 This complaint is accepted or in progress and cannot be edited or deleted by faculty.")

# ============================================================
# TECHNICIAN DASHBOARD
# ============================================================

def technician_dashboard():

    rows = get_assigned_complaints(user["id"])

    total = len(rows)

    active = len(
        [
            r for r in rows
            if str(r.get("status", "")).strip().lower()
            not in ("resolved", "closed")
        ]
    )

    resolved = len(
        [
            r for r in rows
            if str(r.get("status", "")).strip().lower()
            in ("resolved", "closed")
        ]
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

    # --------------------------------------------------------
    # SHOW A PERSISTENT UPDATE MESSAGE AFTER SAVE
    # --------------------------------------------------------

    if st.session_state.get("work_order_message"):
        message = st.session_state.pop("work_order_message")

        if message.get("status") == "Resolved":
            st.success(
                f"✅ {message.get('text', 'Problem resolved successfully.')}"
            )
            st.info(
                "The resolution has been recorded and is now visible "
                "to the faculty member and Facility Manager."
            )
        else:
            st.success(message.get("text", "Work order updated successfully."))

    st.divider()

    if not rows:
        st.success("No work orders are currently assigned to you.")
        return

    for row in rows:

        complaint_card(row)

        with st.expander(
            f"🔧 Work Order — {safe_value(row.get('id'))}"
        ):

            # ------------------------------------------------
            # COMPLETE COMPLAINT INFORMATION
            # ------------------------------------------------

            st.markdown("### 📝 Complaint Description")

            description = safe_value(
                row.get("description"),
                "No description available.",
            )

            st.markdown(
                f"""
                <div style="
                    background:#131B2E;
                    border:1px solid #334155;
                    border-left:4px solid #3B82F6;
                    border-radius:12px;
                    padding:16px;
                    margin-bottom:18px;
                    color:#E2E8F0;
                    line-height:1.6;
                ">
                    {description}
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.write(
                f"**Location:** "
                f"{safe_value(row.get('location'))}"
            )

            st.write(
                f"**Category:** "
                f"{safe_value(row.get('category'))}"
            )

            st.write(
                f"**AI Risk:** "
                f"{safe_value(row.get('risk'))}"
            )

            st.write(
                f"**AI Priority:** "
                f"{safe_value(row.get('priority'))}"
            )

            st.write(
                f"**Current Status:** "
                f"{safe_value(row.get('status'))}"
            )

            if row.get("created_at"):
                st.write(
                    f"**Reported:** "
                    f"{safe_value(row.get('created_at'))}"
                )

            if row.get("resolved_at"):
                st.write(
                    f"**Resolved At:** "
                    f"{safe_value(row.get('resolved_at'))}"
                )

            # ------------------------------------------------
            # STATUS UPDATE / ACCEPTANCE WORKFLOW
            # ------------------------------------------------
            current_status = row.get("status")

            if current_status == "Assigned":
                st.warning("🟡 Pending Acceptance — You must accept this work order to start.")
                if st.button("👉 Accept Work Order", key=f"accept_{row['id']}", use_container_width=True):
                    try:
                        accept_work_order(row["id"], user["id"])
                        st.session_state["work_order_message"] = {
                            "status": "Accepted",
                            "text": f"Work order {row['id']} accepted. Please proceed to Inspection."
                        }
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Unable to accept work order: {exc}")

            elif current_status == "Accepted":
                st.warning("🔍 Inspection Required")
                if st.button("Start Inspection", key=f"start_inspect_{row['id']}", use_container_width=True):
                    try:
                        update_work_order(row["id"], "Inspection in Progress", "")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Error starting inspection: {exc}")

            elif current_status == "Inspection in Progress":
                st.info("🔍 Inspection in Progress")
                st.markdown("**Are spare parts/materials required?**")
                
                parts_required = st.radio(
                    "Are spare parts/materials required?",
                    ["NO", "YES"],
                    index=0,
                    key=f"parts_required_{row['id']}",
                    horizontal=True,
                    label_visibility="collapsed"
                )
                
                if parts_required == "NO":
                    st.success("Inspection completed — No parts required.")
                    if st.button("Start Work", key=f"start_work_noparts_{row['id']}", use_container_width=True):
                        try:
                            start_work_on_complaint(row["id"])
                            st.session_state["work_order_message"] = {
                                "status": "Work Started",
                                "text": "Work has started. The 1-hour countdown is active."
                            }
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Error starting work: {exc}")
                            
                else:
                    st.markdown("### 🧰 Parts Required")
                    
                    part_name_input = st.text_input(
                        "Part name / description",
                        placeholder="e.g. 16A modular electrical switch",
                        key=f"part_name_{row['id']}"
                    )
                    
                    part_qty = st.number_input(
                        "Quantity",
                        min_value=1,
                        value=1,
                        step=1,
                        key=f"part_qty_{row['id']}"
                    )
                    
                    part_remarks = st.text_area(
                        "Remarks (optional)",
                        placeholder="Any additional remarks...",
                        key=f"part_remarks_{row['id']}"
                    )
                    
                    if part_name_input.strip():
                        # AI Part Identification
                        normalized_name = normalize_part_name(part_name_input)
                        
                        if normalized_name == "Part identification uncertain":
                            st.warning("⚠️ Part identification uncertain")
                            
                        # Allow technician to edit/confirm normalized term
                        search_term = st.text_input(
                            "Confirm / Edit Normalized Part Name for Live Price Search",
                            value=part_name_input if normalized_name == "Part identification uncertain" else normalized_name,
                            key=f"search_term_edit_{row['id']}"
                        )
                        
                        st.markdown("### 🔎 Live Price Search")
                        
                        online_options = []
                        search_error_msg = None
                        search_configured = True
                        
                        if search_term.strip():
                            try:
                                with st.spinner("Searching current web results..."):
                                    online_options = search_online_prices(search_term.strip())
                            except ValueError as ve:
                                search_configured = False
                                search_error_msg = str(ve)
                            except Exception as e:
                                search_configured = True
                                search_error_msg = "Live price search temporarily unavailable."
                        
                        purchase_method = st.radio(
                            "Purchase Method",
                            ["Online Purchase", "Offline / Physical Store"],
                            key=f"purch_method_{row['id']}"
                        )
                        
                        selected_option = None
                        offline_price = 0.0
                        offline_store = ""
                        
                        if purchase_method == "Online Purchase":
                            if not search_configured:
                                st.error("Live price search is not configured. Add SEARCH_API_KEY in Streamlit Secrets.")
                                purchase_method = "Offline / Physical Store"
                            elif search_error_msg:
                                st.error(search_error_msg)
                                purchase_method = "Offline / Physical Store"
                            elif not online_options:
                                st.warning("Live price search returned no results. Technician may enter expected offline price.")
                                purchase_method = "Offline / Physical Store"
                            else:
                                # Show Lowest Price Highlight Card
                                lowest_opt = online_options[0]
                                st.markdown(
                                    f"""
                                    <div style="background-color: #112F20; border: 2px solid #10B981; border-radius: 12px; padding: 16px; margin-bottom: 16px;">
                                        <span style="color: #10B981; font-weight: bold; font-size: 14px;">🟢 LOWEST PRICE</span><br>
                                        <span style="font-size: 28px; font-weight: bold; color: #FFFFFF;">₹{lowest_opt['price']}</span><br>
                                        <b>{lowest_opt['product_name']}</b><br>
                                        Source: {lowest_opt['seller']}<br>
                                        <a href="{lowest_opt['link']}" target="_blank" style="color: #10B981; font-weight: bold; text-decoration: underline;">[View Product]</a>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                                
                                st.markdown("#### Other available options:")
                                options_list = []
                                for idx, opt in enumerate(online_options):
                                    badge = " [Lowest Price]" if idx == 0 else ""
                                    options_list.append(f"{opt['seller']} — ₹{opt['price']}{badge}")
                                
                                selected_opt_str = st.radio(
                                    "Select Online Option",
                                    options_list,
                                    key=f"sel_online_{row['id']}"
                                )
                                
                                selected_idx = options_list.index(selected_opt_str)
                                selected_option = online_options[selected_idx]
                                
                                from database import local_now
                                price_checked_at_str = local_now().strftime("%d-%b-%Y %I:%M %p") + " IST"
                                st.caption(f"Price checked: {price_checked_at_str}. Online price is indicative and may change at the seller website.")
                                
                        if purchase_method == "Offline / Physical Store":
                            offline_price = st.number_input(
                                "Expected offline purchase price (₹)",
                                min_value=0.0,
                                value=0.0,
                                step=10.0,
                                key=f"offline_price_{row['id']}"
                            )
                            offline_store = st.text_input(
                                "Optional supplier/store name",
                                placeholder="e.g. Local Electricals",
                                key=f"offline_store_{row['id']}"
                            )
                        
                        if st.button("Submit Parts Request", key=f"submit_parts_{row['id']}", use_container_width=True):
                            try:
                                create_parts_request(
                                    complaint_id=row["id"],
                                    technician_id=user["id"],
                                    part_name=part_name_input.strip(),
                                    normalized_part_name=search_term.strip() if search_term.strip() else normalized_name,
                                    quantity=int(part_qty),
                                    purchase_method="Online" if purchase_method == "Online Purchase" else "Offline",
                                    offline_expected_price=offline_price if purchase_method == "Offline / Physical Store" else None,
                                    selected_online_price=selected_option["price"] if (purchase_method == "Online Purchase" and selected_option) else None,
                                    selected_source=selected_option["seller"] if (purchase_method == "Online Purchase" and selected_option) else offline_store,
                                    selected_product_url=selected_option["link"] if (purchase_method == "Online Purchase" and selected_option) else None
                                )
                                st.session_state["work_order_message"] = {
                                    "status": "Waiting for Manager Approval",
                                    "text": "Parts request submitted. Waiting for Facility Manager approval."
                                }
                                st.rerun()
                            except Exception as exc:
                                st.error(f"Error submitting parts request: {exc}")

            elif current_status == "Waiting for Manager Approval":
                st.warning("⏳ Waiting for Facility Manager approval")
                reqs = get_parts_requests_by_complaint(row["id"])
                if reqs:
                    req = reqs[0]
                    st.markdown(
                        f"""
                        <div style="background-color: #131B2E; border:1px solid #1E293B; border-radius: 8px; padding: 12px; font-size: 14px;">
                            <b>Requested Part:</b> {req['part_name']} ({req['normalized_part_name']})<br>
                            <b>Quantity:</b> {req['quantity']}<br>
                            <b>Method:</b> {req['purchase_method']}<br>
                            <b>Cost:</b> ₹{req['selected_online_price'] or req['offline_expected_price']}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            elif current_status == "Parts Approved":
                st.success("🟢 Facility Manager approved the parts request.")
                reqs = get_parts_requests_by_complaint(row["id"])
                if reqs:
                    req = reqs[0]
                    rec_method = req['manager_recommendation'] or 'As requested'
                    st.markdown(
                        f"""
                        <div style="background-color: #112F20; border: 1px solid #10B981; border-radius: 8px; padding: 12px; font-size: 14px; margin-bottom: 12px;">
                            <b>Approved Purchase:</b> {req['normalized_part_name']} ({req['quantity']} units)<br>
                            <b>Recommended Method:</b> {rec_method}<br>
                            <b>Comment:</b> {req['manager_comment'] or 'None'}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                if st.button("Start Work", key=f"start_work_approved_{row['id']}", use_container_width=True):
                    try:
                        start_work_on_complaint(row["id"])
                        st.session_state["work_order_message"] = {
                            "status": "Work Started",
                            "text": "Work has started. The 1-hour countdown is active."
                        }
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Error starting work: {exc}")

            elif current_status == "Parts Rejected":
                st.error("🔴 Parts Request Rejected")
                reqs = get_parts_requests_by_complaint(row["id"])
                if reqs:
                    req = reqs[0]
                    st.markdown(
                        f"""
                        <div style="background-color: #3F1B1F; border: 1px solid #EF4444; border-radius: 8px; padding: 12px; font-size: 14px; margin-bottom: 12px;">
                            <b>Reason/Comment:</b> {req['manager_comment'] or 'No comment provided.'}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                st.markdown("#### Revise & Resubmit Parts Request")
                if st.button("🔄 Resubmit / Revise Parts Request", key=f"revise_parts_{row['id']}", use_container_width=True):
                    try:
                        update_work_order(row["id"], "Inspection in Progress", "")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Error revising request: {exc}")

            elif current_status == "Work Started":
                start_time_str = row.get("work_started_at") or row.get("last_status_update") or row.get("accepted_at")
                elapsed_mins = 0
                if start_time_str:
                    try:
                        dt = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
                        elapsed_mins = int((datetime.now() - dt).total_seconds() / 60)
                    except Exception as e:
                        pass

                st.info(f"🔴 Work in Progress (Started at {start_time_str})")

                if elapsed_mins < 60:
                    st.write(f"⏳ Allocated for 1 hour. Time remaining: {60 - elapsed_mins} mins.")
                    with st.expander("Resolve Work Order Early"):
                        early_report = st.text_area(
                            "Resolution Report",
                            placeholder="Describe the work carried out, parts replaced, etc.",
                            key=f"early_report_{row['id']}"
                        )
                        if st.button("✅ Resolve Early", key=f"early_resolve_btn_{row['id']}", use_container_width=True):
                            try:
                                update_work_order(row["id"], "Resolved", early_report)
                                st.session_state["work_order_message"] = {
                                    "status": "Resolved",
                                    "text": f"Work order {row['id']} has been marked as Resolved successfully."
                                }
                                st.rerun()
                            except Exception as exc:
                                st.error(f"Error resolving work order: {exc}")
                else:
                    st.warning("⚠️ 1-Hour Allocation completed. You must update the work status to continue or resolve.")
                    
                    status = st.selectbox(
                        "Update Status",
                        ["Work Started", "Resolved"],
                        index=0,
                        key=f"status_{row['id']}",
                    )

                    report = st.text_area(
                        "Resolution Report",
                        value=safe_value(row.get("resolution_report"), ""),
                        placeholder="Describe the work carried out, parts replaced, and final condition.",
                        key=f"report_{row['id']}",
                    )

                    if st.button("💾 Update Work Status", key=f"update_{row['id']}", use_container_width=True):
                        try:
                            update_work_order(row["id"], status, report)
                            st.session_state["work_order_message"] = {
                                "status": status,
                                "text": f"Work order {row['id']} updated successfully."
                            }
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Unable to update work order: {exc}")

            elif current_status == "Resolved":
                st.success("✅ Resolved")
                if row.get("resolution_report"):
                    st.markdown("**Resolution Report:**")
                    st.info(safe_value(row.get("resolution_report")))


# ============================================================
# FACILITY MANAGER DASHBOARD
# ============================================================

def manager_dashboard():
    rows = get_all_complaints()

    st.markdown(
        '<div class="section-title">📊 Facility Management Dashboard</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-caption">'
        'Central command centre for AI-assisted complaint monitoring, '
        'risk assessment, technician workload and resolution performance.'
        '</div>',
        unsafe_allow_html=True,
    )

    tab_overview, tab_reports = st.tabs(["📊 Overview & Insights", "📋 Institutional Reports"])

    with tab_overview:
        # --------------------------------------------------------
        # CORE KPIs
        # --------------------------------------------------------
        total = len(rows)
        active = len([r for r in rows if str(r.get("status", "")).strip().lower() not in ("resolved", "closed")])
        resolved = len([r for r in rows if str(r.get("status", "")).strip().lower() in ("resolved", "closed")])
        high_risk = len([r for r in rows if str(r.get("risk", "")).strip().lower() == "high"])
        medium_risk = len([r for r in rows if str(r.get("risk", "")).strip().lower() == "medium"])
        low_risk = len([r for r in rows if str(r.get("risk", "")).strip().lower() == "low"])
        resolution_rate = round((resolved / total) * 100, 1) if total else 0

        # AI ATTENTION ALERT
        active_critical_high = [
            r for r in rows
            if str(r.get("status", "")).strip().lower() not in ("resolved", "closed")
            and str(r.get("risk", "")).strip().lower() in ("critical", "high")
        ]

        if active_critical_high:
            def crit_sort_key(comp):
                risk_val = {"critical": 3, "high": 2, "medium": 1, "low": 0}.get(str(comp.get("risk", "")).strip().lower(), 0)
                pri_val = {"emergency": 4, "high": 3, "medium": 2, "low": 1}.get(str(comp.get("priority", "")).strip().lower(), 0)
                return (risk_val, pri_val)
            active_critical_high.sort(key=crit_sort_key, reverse=True)
            most_crit = active_critical_high[0]
            count = len(active_critical_high)
            st.markdown(
                f"""
                <div style="background-color: #3F1B1F; border: 1px solid #EF4444; border-radius: 12px; padding: 18px; margin-bottom: 24px;">
                    <h4 style="color: #EF4444 !important; margin: 0 0 10px 0; display: flex; align-items: center;">🔴 AI Attention Required</h4>
                    <p style="color: #FEE2E2 !important; margin: 0 0 14px 0; font-size: 15px;"><b>{count}</b> high-risk/critical complaints currently require attention.</p>
                    <div style="background-color: #241113; border: 1px solid #7F1D1D; border-radius: 8px; padding: 12px; font-size: 14px;">
                        <b style="color: #EF4444 !important;">Most critical active complaint:</b><br>
                        <span style="color: #3B82F6 !important; font-weight: bold;">ID: {safe_value(most_crit.get("id"))}</span> | <b>{safe_value(most_crit.get("category"))}</b> at <b>{safe_value(most_crit.get("location"))}</b><br>
                        Risk Level: <span style="color: #EF4444; font-weight: bold;">{safe_value(most_crit.get("risk"))}</span> | Priority: <span style="color: #EF4444; font-weight: bold;">{safe_value(most_crit.get("priority"))}</span><br>
                        Assigned Technician: <b>{safe_value(most_crit.get("technician_name"), "Unassigned")}</b> | Status: <b>{safe_value(most_crit.get("status"))}</b>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div style="background-color: #112F20; border: 1px solid #10B981; border-radius: 12px; padding: 18px; margin-bottom: 24px;">
                    <h4 style="color: #10B981 !important; margin: 0 0 6px 0; display: flex; align-items: center;">🟢 No Critical AI Alerts</h4>
                    <p style="color: #D1FAE5 !important; margin: 0; font-size: 14px;">All current active complaints are within normal risk levels.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # --------------------------------------------------------
        # KPI CARDS
        # --------------------------------------------------------
        a, b, c, d = st.columns(4)
        with a:
            metric("Total Complaints", total, "📋")
        with b:
            metric("Active", active, "⏳")
        with c:
            metric("Resolved", resolved, "✅")
        with d:
            metric("High Risk", high_risk, "🚨")

        if not rows:
            st.divider()
            st.info("No complaints are available.")
        else:
            # --------------------------------------------------------
            # PARTS & PROCUREMENT CONTROL (STATS & APPROVALS)
            # --------------------------------------------------------
            st.divider()
            st.markdown("### 🧰 Parts & Procurement Control")
            
            all_reqs = get_all_parts_requests()
            pending_reqs = [r for r in all_reqs if r["status"] == "Pending"]
            approved_reqs = [r for r in all_reqs if r["status"] == "Approved"]
            rejected_reqs = [r for r in all_reqs if r["status"] == "Rejected"]
            
            total_est_cost = sum((r["selected_online_price"] or r["offline_expected_price"] or 0) * r["quantity"] for r in approved_reqs)
            online_count = sum(1 for r in all_reqs if r["purchase_method"] == "Online")
            offline_count = sum(1 for r in all_reqs if r["purchase_method"] == "Offline")
            
            potential_savings = 0.0
            for r in all_reqs:
                if r["offline_expected_price"] and r["selected_online_price"]:
                    diff = r["offline_expected_price"] - r["selected_online_price"]
                    if diff > 0:
                        potential_savings += diff * r["quantity"]
            
            col_p1, col_p2, col_p3, col_p4 = st.columns(4)
            with col_p1:
                metric("Pending Approvals", len(pending_reqs), "⏳")
            with col_p2:
                metric("Approved Requests", len(approved_reqs), "✅")
            with col_p3:
                metric("Total Estimated Cost", f"₹{total_est_cost:.2f}", "💰")
            with col_p4:
                metric("Potential Savings", f"₹{potential_savings:.2f}", "🛡️")
                
            st.write(f"📊 **Purchase Requests Breakdown**: {online_count} Online vs {offline_count} Offline Store requests.")

            if pending_reqs:
                st.markdown("### 🧰 Pending Parts Approvals")
                for req in pending_reqs:
                    with st.container(key=f"pending_container_{req['id']}"):
                        st.markdown(
                            f"""
                            <div style="background-color: #131B2E; border: 1px solid #1E293B; border-left: 4px solid #F59E0B; border-radius: 12px; padding: 16px; margin-bottom: 12px;">
                                <h4 style="margin: 0 0 8px 0; color: #FFFFFF !important;">Complaint {req['complaint_id']}</h4>
                                <b>Requested Part:</b> {req['part_name']} (AI Normalized: {req['normalized_part_name']})<br>
                                <b>Technician:</b> {req['technician_name']} ({req['technician_id']})<br>
                                <b>Quantity:</b> {req['quantity']}<br>
                                <b>Requested Purchase Method:</b> {req['purchase_method']}<br>
                                <b>Remarks:</b> {req['manager_comment'] or 'No remarks provided.'}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        
                        cheaper_rec = ""
                        online_val = req["selected_online_price"]
                        offline_val = req["offline_expected_price"]
                        
                        # Highlighting Comparison
                        if online_val and offline_val:
                            unit_diff = abs(offline_val - online_val)
                            total_diff = unit_diff * req["quantity"]
                            cheaper_side = "Online" if online_val < offline_val else "Offline"
                            st.markdown(
                                f"""
                                <div style="background-color: #172237; border: 1px solid #334155; border-radius: 8px; padding: 12px; margin-bottom: 12px; font-size: 14px;">
                                    <span style="color: #60A5FA; font-weight: bold;">⚖️ Highlight Comparison:</span><br>
                                    - Online lowest: <b>₹{online_val}</b> ({req['selected_source'] or 'Online Seller'})<br>
                                    - Offline estimate: <b>₹{offline_val}</b><br>
                                    - Potential difference: <b>₹{unit_diff:.2f} per unit</b><br>
                                    - Quantity: <b>{req['quantity']}</b><br>
                                    - Potential difference: <b>₹{total_diff:.2f} ({cheaper_side} is cheaper)</b>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        
                        a_col, b_col = st.columns(2)
                        with a_col:
                            if online_val:
                                st.write(f"🌐 **Online lowest price**: ₹{online_val}")
                            else:
                                st.write("🌐 **Online price**: Not available")
                            if offline_val:
                                st.write(f"🏪 **Offline expected price**: ₹{offline_val}")
                            else:
                                st.write("🏪 **Offline price**: Not specified")
                                
                        with b_col:
                            if online_val and offline_val:
                                diff = offline_val - online_val
                                if diff > 0:
                                    cheaper_rec = "🌐 Online option is cheaper"
                                    st.success(f"🤖 AI Recommendation: Buy Online (Saves ₹{diff * req['quantity']:.2f})")
                                elif diff < 0:
                                    cheaper_rec = "🏪 Offline option is cheaper"
                                    st.success(f"🤖 AI Recommendation: Buy Offline (Saves ₹{abs(diff) * req['quantity']:.2f})")
                                else:
                                    cheaper_rec = "Equal prices"
                                    st.info("🤖 AI Recommendation: Price matches exactly.")
                            elif online_val:
                                st.info("🤖 AI Recommendation: Recommended Buy Online.")
                            elif offline_val:
                                st.info("🤖 AI Recommendation: Recommended Buy Offline.")
                        
                        rec_method = st.radio(
                            "Recommended Purchase Method",
                            ["Buy Online", "Buy Offline"],
                            index=0 if "Online" in cheaper_rec or not offline_val else 1,
                            key=f"mgr_rec_{req['id']}"
                        )
                        
                        comment = st.text_input(
                            "Manager Comment / Reason",
                            placeholder="Add approval comment or rejection reason...",
                            key=f"mgr_cmt_{req['id']}"
                        )
                        
                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1:
                            if st.button("✅ Approve", key=f"appr_btn_{req['id']}", use_container_width=True):
                                try:
                                    update_parts_request_status(req["id"], "Approved", rec_method, comment)
                                    st.success("Parts request approved.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                        with btn_col2:
                            if st.button("❌ Reject", key=f"rej_btn_{req['id']}", use_container_width=True):
                                try:
                                    update_parts_request_status(req["id"], "Rejected", rec_method, comment)
                                    st.warning("Parts request rejected.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")

                                    
                st.divider()

            # --------------------------------------------------------
            # PREPARE ANALYTICS
            # --------------------------------------------------------
            categories = {}
            priorities = {}
            risks = {}
            technicians = {}
            status_counts = {"Resolved": resolved, "Active": active}

            for row in rows:
                category = safe_value(row.get("category"), "Unknown")
                categories[category] = categories.get(category, 0) + 1

                priority = safe_value(row.get("priority"), "Unknown")
                priorities[priority] = priorities.get(priority, 0) + 1

                risk = safe_value(row.get("risk"), "Unknown")
                risks[risk] = risks.get(risk, 0) + 1

                technician = safe_value(row.get("technician_name"), "Unassigned")
                technicians[technician] = technicians.get(technician, 0) + 1

            # --------------------------------------------------------
            # DASHBOARD ANALYTICS
            # --------------------------------------------------------
            st.divider()
            st.markdown("### 📈 Facilities Intelligence Overview")

            chart1, chart2 = st.columns(2)
            with chart1:
                st.markdown("#### 🎯 Complaint Status")
                fig_status = go.Figure(data=[go.Pie(labels=list(status_counts.keys()), values=list(status_counts.values()), hole=0.64, textinfo="label+percent", textfont=dict(size=13))])
                fig_status.update_layout(height=350, margin=dict(l=10, r=10, t=20, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", legend=dict(orientation="h", y=-0.05))
                st.plotly_chart(fig_status, use_container_width=True, config={"displayModeBar": False})

            with chart2:
                st.markdown("#### ✅ Resolution Performance")
                fig_gauge = go.Figure(go.Indicator(mode="gauge+number", value=resolution_rate, number={"suffix": "%", "font": {"size": 42}}, title={"text": "Overall Resolution Rate"}, gauge={"axis": {"range": [0, 100], "ticksuffix": "%"}, "bar": {"thickness": 0.28}, "steps": [{"range": [0, 50]}, {"range": [50, 80]}, {"range": [80, 100]}], "threshold": {"line": {"width": 4}, "thickness": 0.75, "value": resolution_rate}}))
                fig_gauge.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False})

            chart3, chart4 = st.columns(2)
            with chart3:
                st.markdown("#### 🚨 AI Risk Distribution")
                fig_risk = go.Figure(data=[go.Pie(labels=list(risks.keys()), values=list(risks.values()), hole=0.58, textinfo="label+value")])
                fig_risk.update_layout(height=350, margin=dict(l=10, r=10, t=20, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", legend=dict(orientation="h", y=-0.05))
                st.plotly_chart(fig_risk, use_container_width=True, config={"displayModeBar": False})

            with chart4:
                st.markdown("#### 🛠️ Complaint Categories")
                fig_category = go.Figure(data=[go.Pie(labels=list(categories.keys()), values=list(categories.values()), hole=0.58, textinfo="label+value")])
                fig_category.update_layout(height=350, margin=dict(l=10, r=10, t=20, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", legend=dict(orientation="h", y=-0.05))
                st.plotly_chart(fig_category, use_container_width=True, config={"displayModeBar": False})

            chart5, chart6 = st.columns(2)
            with chart5:
                st.markdown("#### ⚡ Priority Distribution")
                priority_order = ["High", "Medium", "Low"]
                ordered_priorities = {key: priorities[key] for key in priority_order if key in priorities}
                for key, value in priorities.items():
                    if key not in ordered_priorities:
                        ordered_priorities[key] = value
                fig_priority = go.Figure(data=[go.Bar(x=list(ordered_priorities.keys()), y=list(ordered_priorities.values()), text=list(ordered_priorities.values()), textposition="auto")])
                fig_priority.update_layout(height=350, margin=dict(l=30, r=20, t=20, b=40), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_title="Priority", yaxis_title="Complaints")
                st.plotly_chart(fig_priority, use_container_width=True, config={"displayModeBar": False})

            with chart6:
                st.markdown("#### 👨‍🔧 Technician Workload")
                technician_items = sorted(technicians.items(), key=lambda item: item[1], reverse=True)
                fig_technician = go.Figure(data=[go.Bar(x=[x[1] for x in technician_items], y=[x[0] for x in technician_items], orientation="h", text=[x[1] for x in technician_items], textposition="auto")])
                fig_technician.update_layout(height=350, margin=dict(l=30, r=20, t=20, b=40), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_title="Assigned Complaints", yaxis_title="Technician")
                st.plotly_chart(fig_technician, use_container_width=True, config={"displayModeBar": False})

            # --------------------------------------------------------
            # MANAGEMENT SNAPSHOT
            # --------------------------------------------------------
            st.markdown("### 🧭 Management Snapshot")
            s1, s2, s3, s4 = st.columns(4)
            with s1:
                st.metric("Resolution Rate", f"{resolution_rate}%")
            with s2:
                st.metric("Medium Risk", medium_risk)
            with s3:
                st.metric("Low Risk", low_risk)
            with s4:
                unassigned = technicians.get("Unassigned", 0)
                st.metric("Unassigned", unassigned)

            # --------------------------------------------------------
            # COMPLAINT OVERVIEW
            # --------------------------------------------------------
            st.markdown("### 📊 Complaint Overview")
            overview_data = []
            for row in rows:
                overview_data.append({
                    "Complaint ID": safe_value(row.get("id"), "Unknown"),
                    "Category": safe_value(row.get("category"), "Unknown"),
                    "Risk": safe_value(row.get("risk"), "Unknown"),
                    "Priority": safe_value(row.get("priority"), "Unknown"),
                    "Status": safe_value(row.get("status"), "Unknown"),
                    "Technician": safe_value(row.get("technician_name"), "Unassigned"),
                })
            if overview_data:
                st.dataframe(overview_data, use_container_width=True, hide_index=True)

            # --------------------------------------------------------
            # LATEST COMPLAINTS
            # --------------------------------------------------------
            st.markdown("### 🛠️ Latest Complaints")
            for row in rows[:10]:
                complaint_card(row)
                with st.expander(f"View {safe_value(row.get('id'))}"):
                    st.write(f"**Technician:** {safe_value(row.get('technician_name'))}")
                    st.write(f"**Assigned:** {safe_value(row.get('assigned_at'))}")
                    if row.get("resolution_report"):
                        st.success(row["resolution_report"])

            # --------------------------------------------------------
            # CAMPUS RISK INTELLIGENCE SECTION
            # --------------------------------------------------------
            st.divider()
            st.markdown("### 📊 Campus Risk Intelligence")
            st.write("Advanced campus-level risk metrics, workload analysis, and resolution performance.")

            # Metrics row
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.metric("Total Complaints Registered", len(rows))
            with col_m2:
                st.metric("Active Work Orders", len([r for r in rows if r.get("status") != "Resolved"]))
            with col_m3:
                st.metric("Resolved Issues", len([r for r in rows if r.get("status") == "Resolved"]))
            with col_m4:
                high_critical_count = len([r for r in rows if str(r.get("risk", "")).strip().lower() in ("critical", "high")])
                st.metric("High/Critical Risk Alerts", high_critical_count)

            # Row 1: Risk by Location & Category Distribution
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.markdown("#### 📍 Risk Distribution by Location")
                loc_risks = {}
                for r in rows:
                    loc = safe_value(r.get("location"), "Unknown Location")
                    risk_lvl = safe_value(r.get("risk"), "Low")
                    if loc not in loc_risks:
                        loc_risks[loc] = {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}
                    if risk_lvl in loc_risks[loc]:
                        loc_risks[loc][risk_lvl] += 1
                
                locs = list(loc_risks.keys())
                low_y = [loc_risks[l]["Low"] for l in locs]
                med_y = [loc_risks[l]["Medium"] for l in locs]
                high_y = [loc_risks[l]["High"] for l in locs]
                crit_y = [loc_risks[l]["Critical"] for l in locs]
                
                fig_loc_risk = go.Figure()
                fig_loc_risk.add_trace(go.Bar(name="Low", x=locs, y=low_y, marker_color="#10B981"))
                fig_loc_risk.add_trace(go.Bar(name="Medium", x=locs, y=med_y, marker_color="#3B82F6"))
                fig_loc_risk.add_trace(go.Bar(name="High", x=locs, y=high_y, marker_color="#F59E0B"))
                fig_loc_risk.add_trace(go.Bar(name="Critical", x=locs, y=crit_y, marker_color="#EF4444"))
                fig_loc_risk.update_layout(
                    barmode='stack',
                    height=350,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=20, t=30, b=30),
                    legend=dict(orientation="h", y=-0.2)
                )
                st.plotly_chart(fig_loc_risk, use_container_width=True, config={"displayModeBar": False})

            with col_g2:
                st.markdown("#### 🛠️ Category Breakdown")
                fig_cat_dist = go.Figure(data=[go.Pie(
                    labels=list(categories.keys()),
                    values=list(categories.values()),
                    hole=0.5,
                    textinfo="label+percent"
                )])
                fig_cat_dist.update_layout(
                    height=350,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=20, t=30, b=30),
                    legend=dict(orientation="h", y=-0.2)
                )
                st.plotly_chart(fig_cat_dist, use_container_width=True, config={"displayModeBar": False})

            # Row 2: Technician Workload Comparison & Resolution Rate Gauge
            col_g3, col_g4 = st.columns(2)
            with col_g3:
                st.markdown("#### 👨‍🔧 Technician Workload Breakdown")
                users_list = get_users()
                all_techs = [u for u in users_list if u.get("role") == "Technician"]
                tech_data = {}
                for t in all_techs:
                    tname = t["name"]
                    tech_data[tname] = {"Assigned": 0, "Active": 0, "Resolved": 0}
                    
                for r in rows:
                    tname = r.get("technician_name")
                    status_lvl = str(r.get("status", "")).strip().lower()
                    if tname and tname in tech_data:
                        if status_lvl == "assigned":
                            tech_data[tname]["Assigned"] += 1
                        elif status_lvl == "accepted/in progress":
                            tech_data[tname]["Active"] += 1
                        elif status_lvl == "resolved":
                            tech_data[tname]["Resolved"] += 1
                            
                tech_names = list(tech_data.keys())
                tech_assigned = [tech_data[n]["Assigned"] for n in tech_names]
                tech_active = [tech_data[n]["Active"] for n in tech_names]
                tech_resolved = [tech_data[n]["Resolved"] for n in tech_names]
                
                fig_tech_workload = go.Figure()
                fig_tech_workload.add_trace(go.Bar(name="Assigned", y=tech_names, x=tech_assigned, orientation='h', marker_color="#F59E0B"))
                fig_tech_workload.add_trace(go.Bar(name="Active", x=tech_active, y=tech_names, orientation='h', marker_color="#EF4444"))
                fig_tech_workload.add_trace(go.Bar(name="Resolved", x=tech_resolved, y=tech_names, orientation='h', marker_color="#10B981"))
                fig_tech_workload.update_layout(
                    barmode='group',
                    height=350,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=20, t=30, b=30),
                    legend=dict(orientation="h", y=-0.2)
                )
                st.plotly_chart(fig_tech_workload, use_container_width=True, config={"displayModeBar": False})

            with col_g4:
                st.markdown("#### 🎯 Resolution Rate")
                fig_res_rate = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=resolution_rate,
                    number={"suffix": "%", "font": {"size": 36}},
                    gauge={
                        "axis": {"range": [0, 100], "ticksuffix": "%"},
                        "bar": {"thickness": 0.2, "color": "#10B981"},
                        "steps": [{"range": [0, 50], "color": "#131b2e"}, {"range": [50, 80], "color": "#131b2e"}, {"range": [80, 100], "color": "#131b2e"}]
                    }
                ))
                fig_res_rate.update_layout(
                    height=250,
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=20, t=35, b=20)
                )
                st.plotly_chart(fig_res_rate, use_container_width=True, config={"displayModeBar": False})

    with tab_reports:
        st.markdown("### 📋 Institutional Reports Control Panel")
        st.write("Generate and download detailed campus facility reports for the Principal.")

        # Helper to compute statistics
        def compute_stats(filtered):
            total = len(filtered)
            resolved = len([r for r in filtered if r.get("status") == "Resolved"])
            active = len([r for r in filtered if r.get("status") != "Resolved"])
            
            risk_breakdown = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
            priority_breakdown = {"Emergency": 0, "High": 0, "Medium": 0, "Low": 0}
            cat_breakdown = {}
            tech_load = {}
            
            res_times = []
            overdue_count = 0
            
            for r in filtered:
                rk = r.get("risk", "Low")
                risk_breakdown[rk] = risk_breakdown.get(rk, 0) + 1
                
                pr = r.get("priority", "Low")
                priority_breakdown[pr] = priority_breakdown.get(pr, 0) + 1
                
                cat = r.get("category", "Other")
                cat_breakdown[cat] = cat_breakdown.get(cat, 0) + 1
                
                tname = r.get("technician_name") or "Unassigned"
                tech_load[tname] = tech_load.get(tname, 0) + 1
                
                # Overdue check: active for more than 24h
                if r.get("status") != "Resolved":
                    created = r.get("created_at")
                    if created:
                        try:
                            c_dt = datetime.strptime(created, "%Y-%m-%d %H:%M:%S")
                            if (datetime.now() - c_dt).total_seconds() > 86400:
                                overdue_count += 1
                        except:
                            pass
                
                # Resolution time
                c_at = r.get("created_at")
                r_at = r.get("resolved_at")
                if c_at and r_at:
                    try:
                        c_dt = datetime.strptime(c_at, "%Y-%m-%d %H:%M:%S")
                        r_dt = datetime.strptime(r_at, "%Y-%m-%d %H:%M:%S")
                        res_times.append((r_dt - c_dt).total_seconds() / 3600.0)
                    except:
                        pass
                        
            avg_res = round(sum(res_times) / len(res_times), 1) if res_times else 0.0
            res_pct = round((resolved / total) * 100, 1) if total else 0.0
            
            return {
                "total": total,
                "resolved": resolved,
                "active": active,
                "risk": risk_breakdown,
                "priority": priority_breakdown,
                "category": cat_breakdown,
                "tech": tech_load,
                "avg_res_time": avg_res,
                "overdue": overdue_count,
                "res_pct": res_pct
            }

        # Date calculations
        now_dt = datetime.now()
        daily_list = []
        weekly_list = []
        monthly_list = []
        
        for r in rows:
            created = r.get("created_at")
            if created:
                try:
                    c_dt = datetime.strptime(created, "%Y-%m-%d %H:%M:%S")
                    diff_days = (now_dt - c_dt).days
                    if diff_days == 0:
                        daily_list.append(r)
                    if diff_days <= 7:
                        weekly_list.append(r)
                    if diff_days <= 30:
                        monthly_list.append(r)
                except:
                    pass

        def render_report_tab(filtered_list, name):
            stats = compute_stats(filtered_list)
            st.markdown(f"#### 📅 {name} Summary")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Submitted", stats["total"])
                st.metric("Resolved Percentage", f"{stats['res_pct']}%")
            with col2:
                st.metric("Active Work Orders", stats["active"])
                st.metric("Pending/Overdue (>24h)", stats["overdue"])
            with col3:
                st.metric("Avg Resolution Time", f"{stats['avg_res_time']} hrs")
                
            # Breakdown displays
            with st.expander("Show Category and Technician Breakdown"):
                st.write("**Category Breakdown:**")
                st.write(stats["category"])
                st.write("**Technician Workload:**")
                st.write(stats["tech"])
                
            # Formatted text report for the Principal
            report_txt = []
            report_txt.append("=============================================================")
            report_txt.append("DAYANANDA SAGAR ACADEMY OF TECHNOLOGY & MANAGEMENT (DSATM)")
            report_txt.append("CAMPUSFIX AI - FACILITIES INTELLIGENCE SYSTEM REPORT")
            report_txt.append(f"Reporting Period: {name.upper()}")
            report_txt.append(f"Generated On: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_txt.append("=============================================================\n")
            report_txt.append("SUMMARY STATISTICS:")
            report_txt.append(f"- Total Complaints Submitted: {stats['total']}")
            report_txt.append(f"- Resolved Complaints: {stats['resolved']} ({stats['res_pct']}%)")
            report_txt.append(f"- Active/Pending Complaints: {stats['active']}")
            report_txt.append(f"- Average Resolution Time: {stats['avg_res_time']} hours")
            report_txt.append(f"- Overdue Complaints: {stats['overdue']}\n")
            
            report_txt.append("RISK BREAKDOWN:")
            for k, v in stats['risk'].items():
                report_txt.append(f"- {k}: {v}")
                
            report_txt.append("\nPRIORITY BREAKDOWN:")
            for k, v in stats['priority'].items():
                report_txt.append(f"- {k}: {v}")
                
            report_txt.append("\nCATEGORY BREAKDOWN:")
            for k, v in stats['category'].items():
                report_txt.append(f"- {k}: {v}")
                
            report_txt.append("\nTECHNICIAN WORKLOAD:")
            for k, v in stats['tech'].items():
                report_txt.append(f"- {k}: {v} assigned")
                
            report_txt.append("\n" + "="*60)
            report_txt.append("DETAILED COMPLAINTS REPORT")
            report_txt.append("="*60 + "\n")
            
            for item in filtered_list:
                report_txt.append(f"Complaint ID: {item.get('id')}")
                report_txt.append(f"Location: {item.get('location')}")
                report_txt.append(f"Category: {item.get('category')}")
                report_txt.append(f"Risk: {item.get('risk')} | Priority: {item.get('priority')}")
                report_txt.append(f"Status: {item.get('status')}")
                report_txt.append(f"Technician: {item.get('technician_name')} (ID: {item.get('technician_id')})")
                report_txt.append(f"Created: {item.get('created_at')}")
                report_txt.append(f"Resolved: {item.get('resolved_at') or 'N/A'}")
                report_txt.append(f"Resolution Report: {item.get('resolution_report') or 'N/A'}")
                report_txt.append("-" * 40 + "\n")
                
            full_report_str = "\n".join(report_txt)
            
            st.download_button(
                label=f"📥 Download {name} Report (TXT/CSV)",
                data=full_report_str,
                file_name=f"campusfix_{name.lower().replace(' ', '_')}_report.txt",
                mime="text/plain",
                use_container_width=True
            )

        rep_t1, rep_t2, rep_t3 = st.tabs(["📅 Daily", "📅 Weekly", "📅 Monthly"])
        with rep_t1:
            render_report_tab(daily_list, "Daily Report")
        with rep_t2:
            render_report_tab(weekly_list, "Weekly Report")
        with rep_t3:
            render_report_tab(monthly_list, "Monthly Report")


# ============================================================
# FACILITY MANAGER - ALL COMPLAINTS
# ============================================================

def all_complaints_page():
    if st.button("← Back to Dashboard", key="all_complaints_back_btn"):
        st.session_state.page = "Dashboard"
        st.rerun()

    rows = get_all_complaints()

    st.markdown(
        '<div class="section-title">📋 All Facility Complaints</div>',
        unsafe_allow_html=True,
    )

    if not rows:
        st.info("No complaints recorded.")
        return

    # Add filter options
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        status_filter = st.selectbox("Filter by Status", ["All", "Assigned", "Accepted/In Progress", "Resolved"])
    with col_f2:
        risk_filter = st.selectbox("Filter by Risk Level", ["All", "Critical", "High", "Medium", "Low"])
    with col_f3:
        category_filter = st.selectbox("Filter by Category", ["All", "Electrical", "Plumbing", "HVAC", "IT / Network", "Civil / Building", "Cleaning / Housekeeping", "Furniture", "Other"])

    filtered_rows = []
    for r in rows:
        if status_filter != "All" and r.get("status") != status_filter:
            continue
        if risk_filter != "All" and r.get("risk") != risk_filter:
            continue
        if category_filter != "All" and r.get("category") != category_filter:
            continue
        filtered_rows.append(r)

    # Show count of filtered complaints
    st.write(f"Showing **{len(filtered_rows)}** complaints of {len(rows)} total.")

    for row in filtered_rows:
        complaint_card(row)

        with st.expander(f"View & Modify Details — {safe_value(row.get('id'))}"):
            st.markdown("### 📋 Complaint Information")
            st.write(f"**Description:** {safe_value(row.get('description'))}")
            st.write(f"**Location:** {safe_value(row.get('location'))}")
            st.write(f"**Category:** {safe_value(row.get('category'))}")
            st.write(f"**Risk Level:** {safe_value(row.get('risk'))}")
            st.write(f"**Priority:** {safe_value(row.get('priority'))}")
            st.write(f"**Status:** {safe_value(row.get('status'))}")
            st.write(f"**Created At:** {safe_value(row.get('created_at'))}")
            st.write(f"**Assigned At:** {safe_value(row.get('assigned_at'))}")
            st.write(f"**Accepted/Started At:** {safe_value(row.get('accepted_at'))}")
            st.write(f"**Resolution/Closed At:** {safe_value(row.get('resolved_at'))}")
            st.write(f"**Resolution Report:** {safe_value(row.get('resolution_report'))}")

            # Technician status
            tech_name = safe_value(row.get('technician_name'), 'Unassigned')
            tech_avail = safe_value(row.get('technician_availability'), 'N/A')
            st.write(f"**Assigned Technician:** {tech_name} (Availability: `{tech_avail}`)")

            st.divider()

            # Manager Edit & Reassignment
            st.markdown("### ✏️ Edit & Reassign Work Order")
            edit_desc = st.text_area("Complaint Description", value=row.get("description"), key=f"mgr_desc_{row['id']}")
            edit_loc = st.text_input("Location", value=row.get("location"), key=f"mgr_loc_{row['id']}")
            
            # Fetch tech list for manual override selection
            users_list = get_users()
            all_techs = [u for u in users_list if u.get("role") == "Technician"]
            tech_options = ["Automatic Assignment (AI)"] + [f"{t['name']} ({t['skill']} - {t['availability']})" for t in all_techs]
            
            # Find current technician option index
            current_tech_str = "Automatic Assignment (AI)"
            for opt in tech_options:
                if row.get("technician_name") and row.get("technician_name") in opt:
                    current_tech_str = opt
                    break

            selected_tech_opt = st.selectbox(
                "Assign Technician",
                tech_options,
                index=tech_options.index(current_tech_str),
                key=f"mgr_tech_{row['id']}"
            )

            # Manual Status override
            status_opts = ["Assigned", "Accepted/In Progress", "Resolved"]
            selected_status = st.selectbox(
                "Work Order Status",
                status_opts,
                index=status_opts.index(row.get("status")) if row.get("status") in status_opts else 0,
                key=f"mgr_status_{row['id']}"
            )

            manual_report = st.text_area(
                "Resolution Report (Only if Resolved)",
                value=safe_value(row.get("resolution_report"), ""),
                key=f"mgr_report_{row['id']}"
            )

            re_run_ai = st.checkbox("Re-run AI categorization and priority analysis based on description", value=False, key=f"mgr_rerun_{row['id']}")

            if st.button("💾 Apply Changes & Save", key=f"mgr_save_{row['id']}", use_container_width=True):
                if not edit_desc.strip() or not edit_loc.strip():
                    st.error("Description and Location cannot be empty.")
                else:
                    with st.spinner("Updating work order details..."):
                        if re_run_ai:
                            # Re-run AI
                            analysis = analyze_complaint(edit_desc, edit_loc, "Auto-detect")
                            new_category = analysis["category"]
                            new_risk = analysis["risk"]
                            new_priority = analysis["priority"]
                            # Look up AI tech
                            ai_tech = next((x for x in all_techs if x["name"] == analysis["technician"]), None)
                            new_tech_id = ai_tech["id"] if ai_tech else None
                        else:
                            # Manual / Keep current
                            new_category = row.get("category")
                            new_risk = row.get("risk")
                            new_priority = row.get("priority")
                            
                            # Lookup manual tech ID
                            if selected_tech_opt == "Automatic Assignment (AI)":
                                new_tech_id = None
                            else:
                                matched_tech = next((t for t in all_techs if f"{t['name']} ({t['skill']}" in selected_tech_opt), None)
                                new_tech_id = matched_tech["id"] if matched_tech else None

                        edit_complaint(
                            row["id"],
                            edit_desc,
                            edit_loc,
                            new_category,
                            new_risk,
                            new_priority,
                            new_tech_id,
                            status=selected_status
                        )

                        # If status was manually changed to Resolved, call update_work_order to trigger proper avail check
                        if selected_status == "Resolved":
                            update_work_order(row["id"], "Resolved", manual_report)

                    st.success("Work order updated successfully!")
                    st.rerun()

            st.divider()
            st.markdown("### 🗑️ Delete Complaint")
            mgr_del_confirm = st.checkbox("Confirm that you wish to delete this work order permanently.", key=f"mgr_del_conf_{row['id']}")
            if st.button("🗑️ Delete Work Order", key=f"mgr_del_btn_{row['id']}", use_container_width=True):
                if mgr_del_confirm:
                    delete_complaint(row["id"])
                    st.success("Work order deleted successfully!")
                    st.rerun()
                else:
                    st.warning("Please check the confirmation box before deleting.")


# ============================================================
# FACILITY MANAGER - TECHNICIANS
# ============================================================

def technicians_page():
    if st.button("← Back to Dashboard", key="techs_back_btn"):
        st.session_state.page = "Dashboard"
        st.rerun()

    users = get_users()

    techs = [
        u for u in users
        if u.get("role") == "Technician"
    ]

    st.markdown(
        '<div class="section-title">👨‍🔧 Technician Availability & Control</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-caption">Monitor current technician statuses and manually override availability.</div>',
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
                <b style="font-size:16px;">{safe_value(tech.get("name"))}</b><br>
                ID: {safe_value(tech.get("id"))}<br>
                Skill: {safe_value(tech.get("skill"))}<br>
                Availability status: <b>{availability} {"🟢" if availability == "Available" else "🔴" if availability == "Busy" else "🟡"}</b>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        # Override control
        col_ctl1, col_ctl2 = st.columns([2, 1])
        with col_ctl1:
            new_avail = st.selectbox(
                f"Override status for {tech['name']}",
                ["Available", "Busy"],
                index=["Available", "Busy"].index(availability) if availability in ["Available", "Busy"] else 0,
                key=f"avail_sel_{tech['id']}"
            )
        with col_ctl2:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            if st.button("Apply Status", key=f"avail_btn_{tech['id']}", use_container_width=True):
                update_user_availability(tech["id"], new_avail)
                st.success(f"Status for {tech['name']} updated to {new_avail}!")
                st.rerun()


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

# JYOTHIS K.P. , CSE, DSATM