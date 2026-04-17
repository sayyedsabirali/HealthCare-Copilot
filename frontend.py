import streamlit as st
import requests
import json
from datetime import datetime
from streamlit_option_menu import option_menu
import pandas as pd
import plotly.express as px
import time
from typing import Dict, Optional

# -------------------- CONFIGURATION --------------------
BASE_URL = "http://127.0.0.1:8000"
API_TIMEOUT = 30

st.set_page_config(
    page_title="DischargeCare AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- CUSTOM CSS --------------------
def load_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    .stApp {
        background: #0f172a !important;
        color: #e2e8f0 !important;
    }

    [data-testid="stSidebar"] {
        background: #1e293b !important;
        border-right: 1px solid #334155;
    }
    [data-testid="stSidebar"] * { color: #e2e8f0 !important; }

    .sidebar-welcome {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        padding: 1.2rem 1rem;
        border-radius: 14px;
        text-align: center;
        color: white !important;
        margin-bottom: 1rem;
    }
    .sidebar-welcome h2 { font-size: 1.4rem; font-weight: 800; margin: 0 0 4px 0; }
    .sidebar-welcome p  { font-size: 0.8rem; opacity: 0.85; margin: 0; }

    .stMarkdown, .stMarkdown p, .stMarkdown li,
    h1, h2, h3, h4, h5, h6, label, .stTextInput label,
    .stTextArea label, .stSelectbox label { color: #e2e8f0 !important; }

    .main-header {
        background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 60%, #3b82f6 100%);
        padding: 1.8rem 2rem;
        border-radius: 18px;
        color: white !important;
        margin-bottom: 1.8rem;
        box-shadow: 0 8px 32px rgba(37,99,235,0.35);
        border: 1px solid rgba(255,255,255,0.1);
    }
    .main-header h1 { font-size: 2rem; font-weight: 800; margin: 0 0 6px 0; color: white !important; }
    .main-header p  { font-size: 0.95rem; opacity: 0.9; margin: 0; color: rgba(255,255,255,0.9) !important; }

    .card {
        background: #1e293b;
        padding: 1.4rem;
        border-radius: 16px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.3);
        margin-bottom: 1.2rem;
        border: 1px solid #334155;
    }
    .card h3, .card h4, .card strong, .card p, .card span { color: #e2e8f0 !important; }

    .stat-card {
        background: #1e293b;
        padding: 1.2rem;
        border-radius: 14px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.25);
        border: 1px solid #334155;
        margin-bottom: 1rem;
    }
    .stat-number { font-size: 2.2rem; font-weight: 800; color: #60a5fa !important; line-height: 1; }
    .stat-label  { color: #94a3b8 !important; font-size: 0.85rem; font-weight: 600; margin-top: 4px; }

    .diagnosis-tag {
        background: #dc2626; color: #fff !important;
        padding: 0.35rem 0.9rem; border-radius: 30px;
        display: inline-block; margin: 0.2rem; font-size: 0.82rem; font-weight: 600;
    }
    .medication-tag {
        background: #2563eb; color: #fff !important;
        padding: 0.25rem 0.75rem; border-radius: 20px;
        display: inline-block; margin: 0.2rem; font-size: 0.78rem; font-weight: 500;
    }
    .symptom-tag {
        background: #16a34a; color: #fff !important;
        padding: 0.25rem 0.75rem; border-radius: 20px;
        display: inline-block; margin: 0.2rem; font-size: 0.78rem; font-weight: 500;
    }
    .instruction-badge {
        background: #d97706; color: #fff !important;
        padding: 0.35rem 0.9rem; border-radius: 8px;
        display: inline-block; margin: 0.2rem; font-size: 0.82rem; font-weight: 600;
    }
    .diet-tag {
        background: #ea580c; color: #fff !important;
        padding: 0.25rem 0.75rem; border-radius: 20px;
        display: inline-block; margin: 0.2rem; font-size: 0.78rem;
    }
    .restriction-tag {
        background: #475569; color: #cbd5e1 !important;
        padding: 0.25rem 0.75rem; border-radius: 20px;
        display: inline-block; margin: 0.2rem; font-size: 0.78rem;
        text-decoration: line-through;
    }
    .risk-tag {
        background: #7c3aed; color: #fff !important;
        padding: 0.25rem 0.75rem; border-radius: 20px;
        display: inline-block; margin: 0.2rem; font-size: 0.78rem; font-weight: 500;
    }
    .procedure-tag {
        background: #0891b2; color: #fff !important;
        padding: 0.25rem 0.75rem; border-radius: 20px;
        display: inline-block; margin: 0.2rem; font-size: 0.78rem; font-weight: 500;
    }

    .chat-wrapper { display: flex; flex-direction: column; gap: 0.8rem; padding: 0.5rem 0; }
    .chat-user-row  { display: flex; justify-content: flex-end; }
    .chat-agent-row { display: flex; justify-content: flex-start; }
    .chat-user {
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
        color: #fff !important;
        padding: 0.85rem 1.1rem;
        border-radius: 18px 18px 4px 18px;
        max-width: 72%;
        box-shadow: 0 4px 16px rgba(37,99,235,0.3);
        font-size: 0.92rem; line-height: 1.55;
    }
    .chat-user .sender { font-weight: 700; font-size: 0.78rem; opacity: 0.85; margin-bottom: 4px; }
    .chat-agent {
        background: #1e293b; color: #e2e8f0 !important;
        padding: 0.85rem 1.1rem;
        border-radius: 18px 18px 18px 4px;
        max-width: 78%;
        box-shadow: 0 4px 16px rgba(0,0,0,0.2);
        border-left: 4px solid #2563eb;
        font-size: 0.92rem; line-height: 1.55;
    }
    .chat-agent .sender { font-weight: 700; font-size: 0.78rem; color: #60a5fa !important; margin-bottom: 4px; }
    .chat-agent p, .chat-agent li, .chat-agent span { color: #e2e8f0 !important; }
    .chat-scroll-area {
        background: #0f172a; border-radius: 14px;
        border: 1px solid #334155; padding: 1rem;
        min-height: 320px; max-height: 480px; overflow-y: auto;
    }
    .chat-empty { text-align: center; color: #475569 !important; padding: 3rem 1rem; font-size: 0.9rem; }

    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: #1e293b !important; color: #e2e8f0 !important;
        border: 2px solid #334155 !important; border-radius: 10px !important; font-size: 0.95rem !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 3px rgba(37,99,235,0.25) !important;
    }
    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder { color: #64748b !important; }

    .stSelectbox > div > div {
        background: #1e293b !important; color: #e2e8f0 !important;
        border: 2px solid #334155 !important; border-radius: 10px !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
        color: #ffffff !important; border: none !important;
        padding: 0.6rem 1.4rem !important; border-radius: 10px !important;
        font-weight: 700 !important; font-size: 0.9rem !important;
        letter-spacing: 0.3px; transition: all 0.2s ease !important; width: 100%;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(37,99,235,0.4) !important;
        background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
    }
    .stButton > button:active { transform: translateY(0) !important; }

    .stTabs [data-baseweb="tab-list"] {
        background: #1e293b !important; border-radius: 10px;
        gap: 4px; padding: 4px; border: 1px solid #334155;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important; color: #94a3b8 !important;
        border-radius: 8px !important; font-weight: 600 !important; font-size: 0.85rem !important;
    }
    .stTabs [aria-selected="true"] { background: #2563eb !important; color: #ffffff !important; }

    [data-testid="stDataFrame"] {
        background: #1e293b !important; border-radius: 10px; border: 1px solid #334155;
    }
    [data-testid="stDataFrame"] * { color: #e2e8f0 !important; }

    .success-box {
        background: #14532d; color: #86efac !important;
        padding: 0.85rem 1rem; border-radius: 10px;
        border-left: 4px solid #22c55e; font-weight: 600; margin: 0.5rem 0;
    }
    .error-box {
        background: #450a0a; color: #fca5a5 !important;
        padding: 0.85rem 1rem; border-radius: 10px;
        border-left: 4px solid #ef4444; font-weight: 600; margin: 0.5rem 0;
    }

    [data-testid="stFileUploader"] {
        background: #1e293b !important; border: 2px dashed #334155 !important;
        border-radius: 14px !important; padding: 1rem !important;
    }
    [data-testid="stFileUploader"] * { color: #94a3b8 !important; }

    .stSpinner > div { border-top-color: #2563eb !important; }
    .stProgress > div > div { background: #2563eb !important; }
    .stCheckbox > label > span { color: #e2e8f0 !important; }
    .stAlert { background: #1e293b !important; border-color: #334155 !important; color: #94a3b8 !important; }
    hr { border-color: #334155 !important; }
    .js-plotly-plot .plotly .bg { fill: #1e293b !important; }

    .section-title {
        font-size: 0.75rem; font-weight: 700; letter-spacing: 1px;
        text-transform: uppercase; color: #64748b !important; margin-bottom: 0.6rem;
    }
    .profile-row { display: flex; gap: 1rem; align-items: center; flex-wrap: wrap; }
    .profile-badge {
        background: #0f172a; color: #94a3b8 !important;
        padding: 0.3rem 0.75rem; border-radius: 8px;
        font-size: 0.82rem; font-weight: 600; border: 1px solid #334155;
    }
    .profile-name { font-size: 1.4rem; font-weight: 800; color: #f1f5f9 !important; }
    .vitals-grid {
        display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
        gap: 0.7rem; margin-top: 0.5rem;
    }
    .vital-item {
        background: #0f172a; border: 1px solid #334155; border-radius: 10px;
        padding: 0.6rem 0.8rem;
    }
    .vital-label { font-size: 0.72rem; color: #64748b !important; font-weight: 600; text-transform: uppercase; }
    .vital-value { font-size: 1rem; color: #60a5fa !important; font-weight: 700; margin-top: 2px; }
    </style>
    """, unsafe_allow_html=True)

load_css()

# -------------------- SESSION STATE --------------------
defaults = {
    'token': None,
    'patient_data': None,
    'patient_id': None,
    'chat_history': [],
    'login_time': None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# -------------------- API HELPERS --------------------
def login(email: str, password: str) -> Dict:
    try:
        r = requests.post(f"{BASE_URL}/auth/login",
                          json={"email": email, "password": password}, timeout=API_TIMEOUT)
        return r.json()
    except:
        return {"error": "Connection error"}

def register(email: str, password: str) -> Dict:
    try:
        r = requests.post(f"{BASE_URL}/auth/register",
                          json={"email": email, "password": password}, timeout=API_TIMEOUT)
        res = r.json()
        res["status_code"] = r.status_code
        return res
    except:
        return {"error": "Connection error"}

def fetch_patient_data(patient_id: str, token: str) -> Optional[Dict]:
    try:
        if not token:
            return None
        r = requests.get(
            f"{BASE_URL}/patients/{patient_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=API_TIMEOUT,
        )
        if r.status_code == 200:
            return r.json()
        print(f"❌ fetch_patient_data → {r.status_code}")
        return None
    except Exception as e:
        print("🔥 fetch_patient_data exception:", e)
        return None

def add_symptom(patient_id: str, symptom: str, token: str) -> bool:
    try:
        r = requests.post(
            f"{BASE_URL}/patients/{patient_id}/symptoms",
            json={"symptom": symptom},
            headers={"Authorization": f"Bearer {token}"},
            timeout=API_TIMEOUT,
        )
        return r.status_code == 200
    except:
        return False

def send_chat_message(question: str, token: str) -> Dict:
    try:
        r = requests.post(
            f"{BASE_URL}/chat",
            json={"question": question},
            headers={"Authorization": f"Bearer {token}"},
            timeout=API_TIMEOUT,
        )
        return r.json()
    except:
        return {"response": "Connection error. Please try again."}

def get_upload_counts(token: str) -> Dict:
    try:
        r = requests.get(
            f"{BASE_URL}/upload/counts",
            headers={"Authorization": f"Bearer {token}"},
            timeout=API_TIMEOUT,
        )
        return r.json() if r.status_code == 200 else {"text": 0, "documents": 0, "images": 0}
    except:
        return {"text": 0, "documents": 0, "images": 0}

# ── Helper: resolve patient data from API response ──────────────────────────
def resolve_data(raw) -> dict:
    """
    The /patients/{id} endpoint may return the flat patient dict directly,
    or wrap it as {"data": {...}}.  Always return the inner flat dict.
    """
    if not raw:
        return {}
    if isinstance(raw, dict):
        # If there's a "data" wrapper, unwrap it
        if "data" in raw and isinstance(raw["data"], dict):
            return raw["data"]
        return raw
    return {}

def format_value(v):
    if isinstance(v, list):
        return ", ".join([format_value(item) for item in v])
    elif isinstance(v, dict):
        if "name" in v:
            parts = [str(v["name"])]
            if v.get("dose"):      parts.append(v["dose"])
            if v.get("frequency"): parts.append(v["frequency"])
            return " · ".join(parts)
        values = [str(val) for val in v.values() if val]
        return ", ".join(values) if values else "N/A"
    return str(v) if v else "N/A"

def safe_str(item) -> str:
    """
    Convert any list item to a plain display string.
    Handles: plain str, dict with common text keys, or any other dict.
    Prevents '[object Object]' / raw dict repr showing in tags.
    """
    if isinstance(item, str):
        return item.strip()
    if isinstance(item, dict):
        # Try common text-holding keys in priority order
        for key in ("name", "symptom", "description", "text", "value", "title", "label"):
            if item.get(key):
                return str(item[key]).strip()
        # Fallback: join all non-empty string values
        parts = [str(v) for v in item.values() if v and isinstance(v, str)]
        return ", ".join(parts) if parts else str(item)
    return str(item) if item else ""

# ── Structured table renderer (used in Upload page) ─────────────────────────
def _render_structured_table(structured: dict):
    """Render structured_data returned from /upload/* endpoints as a clean table."""
    rows = []
    skip = {"patient_info", "vitals", "lab_results", "medications"}
    for k, v in structured.items():
        if k in skip:
            continue
        rows.append({"Field": k.replace('_', ' ').title(), "Value": format_value(v)})
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Patient info mini-block
    pi = structured.get("patient_info") or {}
    if any(pi.values()):
        age_s = str(pi.get("age")) if pi.get("age") is not None else "N/A"
        st.markdown(
            f'<div style="margin-top:0.5rem;padding:0.6rem 1rem;background:#0f172a;'
            f'border-radius:8px;border:1px solid #334155">'
            f'<b style="color:#f1f5f9">Patient:</b> '
            f'<span style="color:#94a3b8">{pi.get("name","—")} · '
            f'Age {age_s} · {pi.get("gender","—")}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
    # Medications table
    meds = structured.get("medications") or []
    if meds:
        med_rows = []
        for m in meds:
            if isinstance(m, dict):
                med_rows.append({
                    "Name":      m.get("name", ""),
                    "Dose":      m.get("dose", ""),
                    "Frequency": m.get("frequency", ""),
                    "Duration":  m.get("duration", ""),
                    "Purpose":   m.get("purpose", ""),
                })
        if med_rows:
            st.markdown('<p class="section-title" style="margin-top:0.8rem">💊 Medications</p>',
                        unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(med_rows), use_container_width=True, hide_index=True)


# -------------------- TAG DISPLAY --------------------
def display_tags(data: Dict):
    """Compact tag summary used in Dashboard and Chat sidebar."""
    if not data:
        return
    if data.get('diagnosis'):
        st.markdown('<p class="section-title">🏷️ Diagnoses</p>', unsafe_allow_html=True)
        st.markdown(
            "<div>" + "".join([f'<span class="diagnosis-tag">{safe_str(d)}</span>'
                                for d in data['diagnosis'] if safe_str(d)]) + "</div>",
            unsafe_allow_html=True
        )
    if data.get('medications'):
        st.markdown('<p class="section-title">💊 Medications</p>', unsafe_allow_html=True)
        for med in data['medications']:
            if isinstance(med, dict):
                name = med.get('name', 'Unknown')
                dose = med.get('dose', '')
                freq = med.get('frequency', '')
                parts = " ".join(filter(None, [dose, freq]))
                st.markdown(
                    f'<b style="color:#e2e8f0">{safe_str(name)}</b>'
                    + (f' <span class="medication-tag">{parts}</span>' if parts else ""),
                    unsafe_allow_html=True
                )
            else:
                st.markdown(f'<span class="medication-tag">{safe_str(med)}</span>', unsafe_allow_html=True)
    if data.get('symptoms'):
        st.markdown('<p class="section-title">🤒 Symptoms</p>', unsafe_allow_html=True)
        st.markdown(
            "<div>" + "".join([f'<span class="symptom-tag">{safe_str(s)}</span>'
                                for s in data['symptoms'] if safe_str(s)]) + "</div>",
            unsafe_allow_html=True
        )
    if data.get('doctor_instructions'):
        st.markdown('<p class="section-title">📋 Instructions</p>', unsafe_allow_html=True)
        for inst in data['doctor_instructions']:
            if safe_str(inst):
                st.markdown(f'<span class="instruction-badge">{safe_str(inst)}</span>', unsafe_allow_html=True)
    if data.get('diet_recommendations'):
        st.markdown('<p class="section-title">🥗 Diet</p>', unsafe_allow_html=True)
        st.markdown(
            "<div>" + "".join([f'<span class="diet-tag">{safe_str(d)}</span>'
                                for d in data['diet_recommendations'] if safe_str(d)]) + "</div>",
            unsafe_allow_html=True
        )
    if data.get('activity_restrictions'):
        st.markdown('<p class="section-title">⚠️ Restrictions</p>', unsafe_allow_html=True)
        st.markdown(
            "<div>" + "".join([f'<span class="restriction-tag">{safe_str(r)}</span>'
                                for r in data['activity_restrictions'] if safe_str(r)]) + "</div>",
            unsafe_allow_html=True
        )

# -------------------- AGENT LABEL MAP --------------------
# -------------------- AGENT LABEL MAP --------------------
AGENT_MAP = {
    "RiskAgent":            "🚨 Risk Assessment",
    "DrugAgent":            "💊 Medication Expert",
    "DietAgent":            "🍎 Dietitian",
    "MedicalResearchAgent": "📚 Research",
    "GuardrailAgent":       "🛡️ Safety",
    "ReflectionAgent":      "🔄 Verification",
    "AssistantAgent":       "🤖 Assistant",  # 🔥 ADD THIS
}

# -------------------- SIDEBAR --------------------
with st.sidebar:
    st.markdown(
        '<div class="sidebar-welcome"><h2>🏥 DischargeCare</h2>'
        '<p>Post-discharge AI assistant</p></div>',
        unsafe_allow_html=True
    )

    if st.session_state.token and st.session_state.patient_data:
        data = resolve_data(st.session_state.patient_data)
        p    = data.get('patient_info') or {}
        name   = p.get("name") or "Patient"
        age    = p.get("age")
        gender = p.get("gender") or "—"
        age_str = str(age) if age is not None else "N/A"
        st.markdown(
            f'<div style="padding:0.8rem;background:#0f172a;border-radius:10px;'
            f'border:1px solid #334155;margin-bottom:0.8rem">'
            f'<b style="color:#f1f5f9">👤 {name}</b><br>'
            f'<span style="color:#94a3b8;font-size:0.82rem">'
            f'Age: {age_str} · {gender}</span><br>'
            f'<span style="color:#64748b;font-size:0.75rem">'
            f'🕐 {st.session_state.login_time}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

    menu = option_menu(
        menu_title=None,
        options=["Dashboard", "Chat", "Track Symptoms",
                 "Upload Medical Data", "Medical Profile", "Settings"],
        icons=["house-fill", "chat-dots-fill", "activity",
               "cloud-upload-fill", "file-medical-fill", "gear-fill"],
        default_index=0,
        styles={
            "container":        {"padding": "0!important", "background-color": "transparent"},
            "icon":             {"color": "#60a5fa", "font-size": "16px"},
            "nav-link": {
                "color": "#cbd5e1", "font-size": "14px", "font-weight": "600",
                "text-align": "left", "margin": "2px 0", "padding": "0.55rem 0.8rem",
                "border-radius": "8px", "--hover-color": "rgba(37,99,235,0.2)"
            },
            "nav-link-selected": {"background-color": "rgba(37,99,235,0.35)", "color": "#ffffff"},
        }
    )

    if st.session_state.token:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪 Logout"):
            for k in defaults:
                st.session_state[k] = defaults[k]
            st.rerun()

# ============================== MAIN ==============================
if not st.session_state.token:
    # ---- LOGIN / REGISTER ----
    st.markdown(
        '<div class="main-header">'
        '<h1>🏥 Welcome to DischargeCare AI</h1>'
        '<p>Your intelligent post-discharge companion</p>'
        '</div>',
        unsafe_allow_html=True
    )
    _, col, _ = st.columns([1, 2, 1])
    with col:
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])

        with tab1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            email = st.text_input("Email", placeholder="doctor@hospital.com", key="login_email")
            pwd   = st.text_input("Password", type="password", key="login_pwd")
            if st.button("Login →", use_container_width=True):
                if email and pwd:
                    with st.spinner("Logging in..."):
                        res = login(email, pwd)
                    if "access_token" in res:
                        st.session_state.token      = res["access_token"]
                        patient_id                  = res.get("patient_id")
                        if not patient_id:
                            st.error("❌ No patient_id returned from backend")
                            st.stop()
                        st.session_state.patient_id  = patient_id
                        st.session_state.login_time  = datetime.now().strftime("%d %b %Y %H:%M")
                        pd_data = fetch_patient_data(patient_id, st.session_state.token)
                        if pd_data:
                            st.session_state.patient_data = pd_data
                        st.markdown('<div class="success-box">✅ Login successful!</div>',
                                    unsafe_allow_html=True)
                        time.sleep(0.8)
                        st.rerun()
                    else:
                        st.markdown(
                            f'<div class="error-box">❌ {res.get("detail", "Login failed")}</div>',
                            unsafe_allow_html=True
                        )
                else:
                    st.markdown('<div class="error-box">❌ Please fill all fields</div>',
                                unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with tab2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            new_email   = st.text_input("Email",            placeholder="you@example.com", key="reg_email")
            new_pwd     = st.text_input("Password",         type="password",               key="reg_pwd")
            confirm_pwd = st.text_input("Confirm Password", type="password",               key="reg_confirm")
            if st.button("Create Account →", use_container_width=True):
                if new_email and new_pwd and confirm_pwd:
                    if new_pwd != confirm_pwd:
                        st.markdown('<div class="error-box">❌ Passwords do not match</div>',
                                    unsafe_allow_html=True)
                    elif len(new_pwd) < 6:
                        st.markdown('<div class="error-box">❌ Password must be at least 6 characters</div>',
                                    unsafe_allow_html=True)
                    else:
                        with st.spinner("Creating account..."):
                            res = register(new_email, new_pwd)
                        if res.get("status_code") == 200:
                            st.markdown('<div class="success-box">✅ Account created! Please login.</div>',
                                        unsafe_allow_html=True)
                        elif "already exists" in res.get("detail", "").lower():
                            st.markdown('<div class="error-box">❌ Email already registered</div>',
                                        unsafe_allow_html=True)
                        else:
                            st.markdown(
                                f'<div class="error-box">❌ {res.get("detail","Registration failed")}</div>',
                                unsafe_allow_html=True
                            )
                else:
                    st.markdown('<div class="error-box">❌ Please fill all fields</div>',
                                unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

else:
    # ============================== DASHBOARD ==============================
    if menu == "Dashboard":
        st.markdown(
            '<div class="main-header"><h1>📊 Dashboard</h1>'
            '<p>Your health overview at a glance</p></div>',
            unsafe_allow_html=True
        )

        if st.session_state.patient_data:
            data   = resolve_data(st.session_state.patient_data)
            p      = data.get('patient_info') or {}
            counts = get_upload_counts(st.session_state.token)

            # ── Stat cards ───────────────────────────────────────────────────
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(
                    f'<div class="stat-card">'
                    f'<div class="stat-number">{len(data.get("diagnosis", []))}</div>'
                    f'<div class="stat-label">Diagnoses</div></div>',
                    unsafe_allow_html=True
                )
            with c2:
                st.markdown(
                    f'<div class="stat-card">'
                    f'<div class="stat-number">{len(data.get("medications", []))}</div>'
                    f'<div class="stat-label">Medications</div></div>',
                    unsafe_allow_html=True
                )
            with c3:
                st.markdown(
                    f'<div class="stat-card">'
                    f'<div class="stat-number">{len(data.get("symptoms", []))}</div>'
                    f'<div class="stat-label">Symptoms</div></div>',
                    unsafe_allow_html=True
                )
            with c4:
                total = counts["text"] + counts["documents"] + counts["images"]
                st.markdown(
                    f'<div class="stat-card">'
                    f'<div class="stat-number">{total}</div>'
                    f'<div class="stat-label">Uploads</div></div>',
                    unsafe_allow_html=True
                )

            # ── Patient card ─────────────────────────────────────────────────
            name   = p.get("name")   or "Unknown Patient"
            age    = p.get("age")
            gender = p.get("gender") or "—"
            age_str = str(age) if age is not None else "N/A"

            st.markdown('<div class="card">', unsafe_allow_html=True)
            left, right = st.columns([1, 2])
            with left:
                st.markdown(f'<div class="profile-name">👤 {name}</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="profile-row" style="margin-top:0.5rem">'
                    f'<span class="profile-badge">Age: {age_str}</span>'
                    f'<span class="profile-badge">{gender}</span>'
                    f'<span class="profile-badge">ID: {st.session_state.patient_id}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                # Vitals mini-display
                vitals = data.get("vitals") or {}
                vital_labels = {
                    "blood_pressure":   "BP",
                    "heart_rate":       "HR",
                    "oxygen_saturation":"SpO₂",
                    "temperature":      "Temp",
                }
                vital_html = ""
                for key, label in vital_labels.items():
                    val = vitals.get(key)
                    if val:
                        vital_html += (
                            f'<div class="vital-item">'
                            f'<div class="vital-label">{label}</div>'
                            f'<div class="vital-value">{val}</div>'
                            f'</div>'
                        )
                if vital_html:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown('<p class="section-title">🩺 Vitals</p>', unsafe_allow_html=True)
                    st.markdown(f'<div class="vitals-grid">{vital_html}</div>', unsafe_allow_html=True)

            with right:
                display_tags(data)
            st.markdown('</div>', unsafe_allow_html=True)

            # ── Follow-up ────────────────────────────────────────────────────
            if data.get("follow_up"):
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<p class="section-title">📅 Follow-up</p>', unsafe_allow_html=True)
                st.markdown(
                    f'<span style="color:#e2e8f0">{data["follow_up"]}</span>',
                    unsafe_allow_html=True
                )
                st.markdown('</div>', unsafe_allow_html=True)

            # ── Recent chat preview ───────────────────────────────────────────
            if st.session_state.chat_history:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<p class="section-title">💬 Recent Conversation</p>', unsafe_allow_html=True)
                for msg in st.session_state.chat_history[-4:]:
                    icon = "👤" if msg["role"] == "user" else "🤖"
                    role = "You" if msg["role"] == "user" else "AI"
                    text = msg['content'][:80] + ("…" if len(msg['content']) > 80 else "")
                    st.markdown(
                        f'<span style="color:#94a3b8;font-size:0.82rem">'
                        f'{icon} <b>{role}:</b> {text}</span><br>',
                        unsafe_allow_html=True
                    )
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No patient data found. Please upload your medical records or contact support.")

    # ============================== CHAT ==============================
    elif menu == "Chat":
        st.markdown(
            '<div class="main-header"><h1>💬 AI Health Assistant</h1>'
            '<p>Ask about medications, symptoms, diet, and more</p></div>',
            unsafe_allow_html=True
        )

        # Simple, ChatGPT-like interface – no sidebar clutter, only conversation
        # Chat history container
        st.markdown('<div class="chat-scroll-area"><div class="chat-wrapper">', unsafe_allow_html=True)

        if not st.session_state.chat_history:
            st.markdown(
                '<div class="chat-empty">'
                '🤖<br><br>Hello! I\'m your DischargeCare AI assistant.<br>'
                'Ask me anything about your medications, diet, symptoms, or recovery.'
                '</div>',
                unsafe_allow_html=True
            )
        else:
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    st.markdown(
                        f'<div class="chat-user-row">'
                        f'<div class="chat-user"><div class="sender">👤 You</div>'
                        f'{msg["content"]}</div></div>',
                        unsafe_allow_html=True
                    )
                else:
                    agents_list = msg.get("agents", [])
                    if agents_list:
                        # Map each agent to its label
                        labels = []
                        for a in agents_list:
                            if a in AGENT_MAP:
                                labels.append(AGENT_MAP[a])
                            elif a == "AssistantAgent":
                                labels.append("🤖 Assistant")
                            else:
                                labels.append(a)
                        agent_label = " · ".join(labels)
                    else:
                        agent_label = "🤖 AI Assistant"
                    
                    st.markdown(
                        f'<div class="chat-agent-row">'
                        f'<div class="chat-agent"><div class="sender">{agent_label}</div>'
                        f'{msg["content"]}</div></div>',
                        unsafe_allow_html=True
                    )
        st.markdown('</div></div>', unsafe_allow_html=True)

        # Input and clear button row
        col_input, col_clear = st.columns([5, 1])
        with col_input:
            prompt = st.chat_input("Ask me anything... (press Enter to send)")
        with col_clear:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()

        if prompt:
            st.session_state.chat_history.append({"role": "user", "content": prompt.strip()})
            with st.spinner("AI is thinking..."):
                res = send_chat_message(prompt.strip(), st.session_state.token)
            st.session_state.chat_history.append({
                "role":    "assistant",
                "content": res.get("response", "No response received."),
                "agents":  res.get("agents", []),
            })
            st.rerun()

    # ============================== TRACK SYMPTOMS ==============================
    elif menu == "Track Symptoms":
        st.markdown(
            '<div class="main-header"><h1>🤒 Track Symptoms</h1>'
            '<p>Log and monitor your symptoms over time</p></div>',
            unsafe_allow_html=True
        )

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<p class="section-title">📝 Log New Symptom</p>', unsafe_allow_html=True)
            sym = st.text_input("Symptom name", placeholder="e.g., headache, chest pain")
            sev = st.select_slider("Severity", options=["Mild", "Moderate", "Severe"])
            dur = st.text_input("Duration",     placeholder="e.g., 2 days, since morning")
            if st.button("➕ Add Symptom", use_container_width=True):
                if sym:
                    entry = f"{sym} ({sev}, {dur})" if dur else f"{sym} ({sev})"
                    if add_symptom(st.session_state.patient_id, entry, st.session_state.token):
                        st.markdown('<div class="success-box">✅ Symptom added successfully</div>',
                                    unsafe_allow_html=True)
                        st.session_state.patient_data = fetch_patient_data(
                            st.session_state.patient_id, st.session_state.token
                        )
                        time.sleep(0.8)
                        st.rerun()
                    else:
                        st.markdown('<div class="error-box">❌ Failed to add symptom</div>',
                                    unsafe_allow_html=True)
                else:
                    st.markdown('<div class="error-box">❌ Please enter a symptom name</div>',
                                unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<p class="section-title">📋 Current Symptoms</p>', unsafe_allow_html=True)
            syms_raw = resolve_data(st.session_state.patient_data or {}).get('symptoms', [])
            syms = [safe_str(s) for s in syms_raw if safe_str(s)]
            if syms:
                df = pd.DataFrame({"Symptom": syms, "Count": [1] * len(syms)})
                fig = px.bar(df, x="Symptom", y="Count",
                             color_discrete_sequence=["#2563eb"], template="plotly_dark")
                fig.update_layout(
                    showlegend=False, plot_bgcolor='#1e293b', paper_bgcolor='#1e293b',
                    font_color='#e2e8f0', margin=dict(l=0, r=0, t=10, b=0),
                    xaxis=dict(tickfont=dict(size=10))
                )
                fig.update_traces(marker_line_width=0)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown(
                    "<div>" + "".join([f'<span class="symptom-tag">{s}</span>' for s in syms]) + "</div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    '<div style="text-align:center;color:#475569;padding:2rem">No symptoms logged yet</div>',
                    unsafe_allow_html=True
                )
            st.markdown('</div>', unsafe_allow_html=True)

    # ============================== UPLOAD ==============================
    elif menu == "Upload Medical Data":
        st.markdown(
            '<div class="main-header"><h1>📤 Upload Medical Data</h1>'
            '<p>Upload and analyze your medical records</p></div>',
            unsafe_allow_html=True
        )

        counts = get_upload_counts(st.session_state.token)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                f'<div class="stat-card"><div class="stat-number">{counts["text"]}</div>'
                f'<div class="stat-label">Text Reports</div></div>',
                unsafe_allow_html=True
            )
        with c2:
            st.markdown(
                f'<div class="stat-card"><div class="stat-number">{counts["documents"]}</div>'
                f'<div class="stat-label">Documents</div></div>',
                unsafe_allow_html=True
            )
        with c3:
            st.markdown(
                f'<div class="stat-card"><div class="stat-number">{counts["images"]}</div>'
                f'<div class="stat-label">Images</div></div>',
                unsafe_allow_html=True
            )

        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        tab1, tab2, tab3 = st.tabs(["📝 Text Report", "📄 PDF / Image", "📁 Multiple Files"])

        with tab1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            text_data = st.text_area(
                "Paste medical text:", height=160,
                placeholder="e.g., BP 140/90, glucose 180, patient discharged on metformin 500mg..."
            )
            if st.button("🔍 Analyze & Save", key="text_btn", use_container_width=True):
                if text_data.strip():
                    with st.spinner("Analyzing with AI..."):
                        r = requests.post(f"{BASE_URL}/upload/text",
                                          json={"text": text_data},
                                          headers=headers, timeout=30)
                    if r.status_code == 200:
                        resp = r.json()
                        st.markdown('<div class="success-box">✅ Data saved to your profile</div>',
                                    unsafe_allow_html=True)
                        structured = resp.get('structured_data') or {}
                        if structured:
                            _render_structured_table(structured)
                        with st.expander("📝 Original Text"):
                            st.text(resp.get("raw_text", ""))
                        st.markdown(
                            f'<span style="color:#64748b;font-size:0.8rem">'
                            f'Document ID: {resp.get("document_id","N/A")} · '
                            f'Collection: {resp.get("collection","medical_texts")}</span>',
                            unsafe_allow_html=True
                        )
                        st.session_state.patient_data = fetch_patient_data(
                            st.session_state.patient_id, st.session_state.token
                        )
                    else:
                        st.markdown(f'<div class="error-box">❌ Upload failed: {r.text}</div>',
                                    unsafe_allow_html=True)
                else:
                    st.markdown('<div class="error-box">❌ Please enter some text</div>',
                                unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with tab2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            uploaded = st.file_uploader("Choose a PDF or image file", type=["pdf", "png", "jpg", "jpeg"])
            if uploaded:
                st.markdown(
                    f'<span style="color:#94a3b8">📎 <b>{uploaded.name}</b> · '
                    f'{uploaded.size/1024:.1f} KB</span>',
                    unsafe_allow_html=True
                )
                if uploaded.type.startswith("image"):
                    st.image(uploaded, width=220)
                if st.button("📤 Upload & Analyze", key="file_btn", use_container_width=True):
                    with st.spinner("Extracting and analyzing..."):
                        uploaded.seek(0)
                        files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type)}
                        r = requests.post(f"{BASE_URL}/upload/medical-report",
                                          files=files, headers=headers, timeout=60)
                    if r.status_code == 200:
                        resp = r.json()
                        st.markdown('<div class="success-box">✅ File analyzed and saved</div>',
                                    unsafe_allow_html=True)
                        structured = resp.get('structured_data') or {}
                        if structured:
                            _render_structured_table(structured)
                        with st.expander("📝 Extracted Text"):
                            st.text(resp.get("extracted_text", ""))
                        st.session_state.patient_data = fetch_patient_data(
                            st.session_state.patient_id, st.session_state.token
                        )
                    else:
                        st.markdown(f'<div class="error-box">❌ {r.text}</div>',
                                    unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with tab3:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            multi_files = st.file_uploader(
                "Select multiple files", accept_multiple_files=True,
                type=["pdf", "png", "jpg", "jpeg", "txt"]
            )
            if multi_files:
                st.markdown(
                    f'<span style="color:#94a3b8">{len(multi_files)} file(s) selected</span>',
                    unsafe_allow_html=True
                )
                df_show = pd.DataFrame([{"File": f.name, "Size": f"{f.size/1024:.1f} KB"}
                                         for f in multi_files])
                st.dataframe(df_show, use_container_width=True, hide_index=True)
                if st.button("📤 Upload All", key="multi_btn", use_container_width=True):
                    progress = st.progress(0)
                    for i, f in enumerate(multi_files):
                        f.seek(0)
                        file_data = {"files": (f.name, f.getvalue(), f.type)}
                        r = requests.post(f"{BASE_URL}/upload/multiple",
                                          files=file_data, headers=headers, timeout=30)
                        if r.status_code == 200:
                            st.markdown(f'<div class="success-box">✅ {f.name}</div>',
                                        unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="error-box">❌ {f.name} failed</div>',
                                        unsafe_allow_html=True)
                        progress.progress((i + 1) / len(multi_files))
                    st.session_state.patient_data = fetch_patient_data(
                        st.session_state.patient_id, st.session_state.token
                    )
            st.markdown('</div>', unsafe_allow_html=True)

    # ============================== MEDICAL PROFILE ==============================
    elif menu == "Medical Profile":
        st.markdown(
            '<div class="main-header"><h1>📋 Medical Profile</h1>'
            '<p>Your complete health record</p></div>',
            unsafe_allow_html=True
        )

        if st.button("🔄 Refresh Data", use_container_width=False):
            with st.spinner("Refreshing..."):
                fresh = fetch_patient_data(st.session_state.patient_id, st.session_state.token)
                if fresh:
                    st.session_state.patient_data = fresh
            st.rerun()

        if st.session_state.patient_data is None:
            with st.spinner("Loading profile..."):
                fresh = fetch_patient_data(st.session_state.patient_id, st.session_state.token)
                if fresh:
                    st.session_state.patient_data = fresh

        if not st.session_state.patient_data:
            st.warning("No data fetched yet. Upload your medical records to get started.")
            st.stop()

        # ── Resolve into a flat dict regardless of API wrapper ─────────────
        data = resolve_data(st.session_state.patient_data)
        p    = data.get('patient_info') or {}

        name   = p.get("name")   or "Unknown Patient"
        age    = p.get("age")
        gender = p.get("gender") or "—"
        age_str = str(age) if age is not None else "N/A"

        # ── Patient header ──────────────────────────────────────────────────
        st.markdown(
            f'<div class="card">'
            f'<div class="profile-name">👤 {name}</div>'
            f'<div class="profile-row" style="margin-top:0.6rem">'
            f'<span class="profile-badge">Age: {age_str}</span>'
            f'<span class="profile-badge">Gender: {gender}</span>'
            f'<span class="profile-badge">ID: {st.session_state.patient_id}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
        # History
        history = p.get("history") or []
        if history:
            st.markdown(
                '<p class="section-title" style="margin-top:0.8rem">Past Medical History</p>',
                unsafe_allow_html=True
            )
            st.markdown(
                "<div>" + "".join([f'<span class="risk-tag">{safe_str(h)}</span>'
                                   for h in history if safe_str(h)]) + "</div>",
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

        # ── Summary ─────────────────────────────────────────────────────────
        if data.get("summary"):
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<p class="section-title">🧾 Clinical Summary</p>', unsafe_allow_html=True)
            st.write(data["summary"])
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Vitals ──────────────────────────────────────────────────────────
        vitals = data.get("vitals") or {}
        vital_non_empty = {k: v for k, v in vitals.items() if v}
        if vital_non_empty:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<p class="section-title">🩺 Vitals</p>', unsafe_allow_html=True)
            vital_display_names = {
                "blood_pressure":    "Blood Pressure",
                "heart_rate":        "Heart Rate",
                "oxygen_saturation": "SpO₂",
                "temperature":       "Temperature",
                "respiratory_rate":  "Resp. Rate",
                "weight":            "Weight",
                "height":            "Height",
            }
            html = '<div class="vitals-grid">'
            for k, v in vital_non_empty.items():
                label = vital_display_names.get(k, k.replace("_", " ").title())
                html += (
                    f'<div class="vital-item">'
                    f'<div class="vital-label">{label}</div>'
                    f'<div class="vital-value">{v}</div>'
                    f'</div>'
                )
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Lab Results ─────────────────────────────────────────────────────
        labs = data.get("lab_results") or {}
        lab_non_empty = {k: v for k, v in labs.items() if v}
        if lab_non_empty:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<p class="section-title">🔬 Lab Results</p>', unsafe_allow_html=True)
            rows = []
            for k, v in lab_non_empty.items():
                rows.append({"Test": k.replace("_", " ").title(), "Result": format_value(v)})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Overview stat numbers ────────────────────────────────────────────
        c1, c2, c3, c4, c5 = st.columns(5)
        for col, key, label in [
            (c1, "diagnosis",         "Diagnoses"),
            (c2, "medications",       "Medications"),
            (c3, "symptoms",          "Symptoms"),
            (c4, "doctor_instructions","Instructions"),
            (c5, "diet_recommendations","Diet Tips"),
        ]:
            with col:
                st.markdown(
                    f'<div class="stat-card">'
                    f'<div class="stat-number">{len(data.get(key, []))}</div>'
                    f'<div class="stat-label">{label}</div></div>',
                    unsafe_allow_html=True
                )

        # ── Profile tabs ─────────────────────────────────────────────────────
        tabs = st.tabs([
            "🏷️ Diagnoses", "💊 Medications", "🤒 Symptoms",
            "📋 Instructions", "🥗 Diet & Activity",
            "🚨 Risk & Procedures"
        ])

        with tabs[0]:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            diagnoses = list(dict.fromkeys([safe_str(d) for d in (data.get('diagnosis') or []) if safe_str(d)]))
            if diagnoses:
                for d in diagnoses:
                    st.markdown(f'<span class="diagnosis-tag">{d}</span>', unsafe_allow_html=True)
            else:
                st.markdown(
                    '<span style="color:#64748b">No diagnoses recorded. '
                    'Upload your discharge summary to populate this.</span>',
                    unsafe_allow_html=True
                )
            st.markdown('</div>', unsafe_allow_html=True)

        with tabs[1]:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            meds = data.get('medications') or []
            if meds:
                for m in meds:
                    if isinstance(m, dict):
                        name_m   = m.get('name', 'Unknown')
                        dose     = m.get('dose', '')         # ← correct key
                        freq     = m.get('frequency', '')
                        duration = m.get('duration', '')
                        purpose  = m.get('purpose', '')
                        st.markdown(
                            f'<div style="padding:0.8rem;background:#0f172a;border-radius:10px;'
                            f'margin-bottom:0.5rem;border:1px solid #334155">'
                            f'<b style="color:#f1f5f9;font-size:1rem">{name_m}</b><br>'
                            + (f'<span class="medication-tag">{dose}</span>' if dose else '')
                            + (f'<span class="medication-tag">{freq}</span>' if freq else '')
                            + (f'<span class="medication-tag">{duration}</span>' if duration else '')
                            + (f'<br><span style="color:#94a3b8;font-size:0.8rem">Purpose: {purpose}</span>'
                               if purpose else '')
                            + '</div>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(f'<span class="medication-tag">{safe_str(m)}</span>', unsafe_allow_html=True)
            else:
                st.markdown(
                    '<span style="color:#64748b">No medications recorded. '
                    'Upload your prescription or discharge summary.</span>',
                    unsafe_allow_html=True
                )
            st.markdown('</div>', unsafe_allow_html=True)

        with tabs[2]:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            syms = [safe_str(s) for s in (data.get('symptoms') or []) if safe_str(s)]
            if syms:
                st.markdown(
                    "<div>" + "".join([f'<span class="symptom-tag">{s}</span>' for s in syms]) + "</div>",
                    unsafe_allow_html=True
                )
                st.markdown("<br>", unsafe_allow_html=True)
                df_sym = pd.DataFrame({"Symptom": syms, "Count": [1]*len(syms)})
                fig = px.bar(df_sym, x="Symptom", y="Count",
                             color_discrete_sequence=["#16a34a"], template="plotly_dark")
                fig.update_layout(
                    showlegend=False, plot_bgcolor='#0f172a', paper_bgcolor='#1e293b',
                    font_color='#e2e8f0', margin=dict(l=0, r=0, t=10, b=0)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.markdown(
                    '<span style="color:#64748b">No symptoms recorded yet. '
                    'Use "Track Symptoms" to log them.</span>',
                    unsafe_allow_html=True
                )
            st.markdown('</div>', unsafe_allow_html=True)

        with tabs[3]:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            instructions = data.get('doctor_instructions') or []
            if instructions:
                for inst in instructions:
                    txt = safe_str(inst)
                    if txt:
                        st.markdown(
                            f'<div style="display:flex;align-items:flex-start;gap:0.6rem;margin-bottom:0.5rem">'
                            f'<span style="color:#d97706;font-size:1.1rem">📌</span>'
                            f'<span style="color:#e2e8f0">{txt}</span>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
            else:
                st.markdown(
                    '<span style="color:#64748b">No doctor instructions recorded. '
                    'Upload your discharge summary.</span>',
                    unsafe_allow_html=True
                )
            # Follow-up
            if data.get("follow_up"):
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown('<p class="section-title">📅 Follow-up Appointment</p>', unsafe_allow_html=True)
                st.markdown(
                    f'<span style="color:#60a5fa;font-weight:600">{data["follow_up"]}</span>',
                    unsafe_allow_html=True
                )
            st.markdown('</div>', unsafe_allow_html=True)

        with tabs[4]:
            left, right = st.columns(2)
            with left:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<p class="section-title">🥗 Diet Recommendations</p>', unsafe_allow_html=True)
                diet = data.get('diet_recommendations') or []
                if diet:
                    for d in diet:
                        if safe_str(d):
                            st.markdown(f'<span class="diet-tag">{safe_str(d)}</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span style="color:#64748b">None recorded</span>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            with right:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<p class="section-title">⚠️ Activity Restrictions</p>', unsafe_allow_html=True)
                restrictions = data.get('activity_restrictions') or []
                if restrictions:
                    for r_item in restrictions:
                        if safe_str(r_item):
                            st.markdown(f'<span class="restriction-tag">{safe_str(r_item)}</span>',
                                        unsafe_allow_html=True)
                else:
                    st.markdown('<span style="color:#64748b">None recorded</span>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

        with tabs[5]:
            left, right = st.columns(2)
            with left:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<p class="section-title">🚨 Risk Factors</p>', unsafe_allow_html=True)
                risks = data.get('risk_factors') or []
                if risks:
                    for r in risks:
                        if safe_str(r):
                            st.markdown(f'<span class="risk-tag">{safe_str(r)}</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span style="color:#64748b">None recorded</span>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            with right:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<p class="section-title">🔬 Procedures Performed</p>', unsafe_allow_html=True)
                procs = data.get('procedures') or []
                if procs:
                    for proc in procs:
                        if safe_str(proc):
                            st.markdown(f'<span class="procedure-tag">{safe_str(proc)}</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span style="color:#64748b">None recorded</span>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # Hospital course
            course = data.get('hospital_course') or []
            if course:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<p class="section-title">🏥 Hospital Course</p>', unsafe_allow_html=True)
                for event in course:
                    txt = safe_str(event)
                    if txt:
                        st.markdown(
                            f'<div style="display:flex;gap:0.6rem;margin-bottom:0.4rem">'
                            f'<span style="color:#60a5fa">▸</span>'
                            f'<span style="color:#e2e8f0">{txt}</span></div>',
                            unsafe_allow_html=True
                        )
                st.markdown('</div>', unsafe_allow_html=True)

        with st.expander("🔧 Raw Profile Data (debug)"):
            st.json(data)

    # ============================== SETTINGS ==============================
    elif menu == "Settings":
        st.markdown(
            '<div class="main-header"><h1>⚙️ Settings</h1>'
            '<p>Preferences and account options</p></div>',
            unsafe_allow_html=True
        )

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<p class="section-title">🔔 Notifications</p>', unsafe_allow_html=True)
            st.checkbox("Medication reminders",  value=True)
            st.checkbox("Appointment reminders", value=True)
            st.checkbox("Daily health tips",     value=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<p class="section-title">🎨 Display</p>', unsafe_allow_html=True)
            st.selectbox("Theme", ["Dark (Default)", "Light"])
            st.checkbox("Show agent names in chat", value=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<p class="section-title">🔐 Account</p>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔑 Change Password", use_container_width=True):
                st.info("Coming soon")
        with c2:
            if st.button("📥 Export My Data", use_container_width=True):
                if st.session_state.patient_data:
                    data_export = resolve_data(st.session_state.patient_data)
                    st.download_button(
                        "⬇️ Download JSON",
                        data=json.dumps(data_export, indent=2, default=str),
                        file_name="my_health_data.json",
                        mime="application/json",
                    )
                else:
                    st.info("No data to export")
        st.markdown('</div>', unsafe_allow_html=True)


# ---- Footer ----
st.markdown("---")
st.markdown(
    '<div style="text-align:center;color:#475569;padding:0.8rem;font-size:0.8rem">'
    '© 2025 DischargeCare AI · Not a substitute for professional medical advice'
    '</div>',
    unsafe_allow_html=True
)