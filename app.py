"""
app.py — Streamlit UI for CIEPAL Submission Report CRUD.
Run: streamlit run app.py
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime
import time

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="CIEPAL Submissions",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Global styles ───────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ---- base ---- */
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(1200px 600px at 12% -8%, rgba(124,58,237,.20), transparent 55%),
        radial-gradient(1000px 520px at 105% 0%, rgba(14,165,233,.16), transparent 50%),
        #0a0e1a;
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { display: none; }
.block-container { padding-top: 1.4rem; max-width: 1500px; }

/* hide the default collapsed-sidebar arrow */
[data-testid="collapsedControl"] { display: none; }

* { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }

/* ---- top app bar ---- */
.topbar {
    display:flex; align-items:center; justify-content:space-between;
    padding:16px 22px; margin-bottom:18px;
    background: linear-gradient(135deg, rgba(30,27,55,.92), rgba(17,21,38,.92));
    border:1px solid rgba(124,92,255,.22);
    border-radius:18px;
    box-shadow: 0 10px 40px -12px rgba(99,52,237,.45), inset 0 1px 0 rgba(255,255,255,.04);
}
.brand { display:flex; align-items:center; gap:14px; }
.brand-logo {
    width:46px; height:46px; border-radius:13px;
    background: linear-gradient(135deg,#7c3aed,#4f46e5 55%,#06b6d4);
    display:flex; align-items:center; justify-content:center;
    font-size:24px; box-shadow:0 6px 20px -4px rgba(124,58,237,.7);
}
.brand-title {
    font-size:1.42rem; font-weight:800; letter-spacing:-.02em;
    background:linear-gradient(90deg,#c4b5fd,#a5b4fc 45%,#67e8f9);
    -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent;
    line-height:1.05;
}
.brand-sub { font-size:.72rem; color:#8b93b8; letter-spacing:.04em; margin-top:1px; }

.pill {
    display:inline-flex; align-items:center; gap:7px;
    font-size:.72rem; font-weight:600; padding:7px 14px; border-radius:999px;
}
.pill-on  { background:rgba(16,185,129,.13); color:#34d399; border:1px solid rgba(16,185,129,.35); }
.pill-off { background:rgba(244,63,94,.13);  color:#fb7185; border:1px solid rgba(244,63,94,.35); }
.dot { width:8px; height:8px; border-radius:50%; box-shadow:0 0 8px currentColor; background:currentColor; }

/* ---- headings ---- */
.page-h {
    font-size:2.05rem; font-weight:800; letter-spacing:-.025em; margin:6px 0 2px;
    background:linear-gradient(90deg,#e9e4ff,#c7d2fe 50%,#a5f3fc);
    -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent;
}
.page-sub { color:#8b93b8; font-size:.9rem; margin-bottom:6px; }

.sh { font-size:.66rem; font-weight:700; letter-spacing:.16em; text-transform:uppercase;
      color:#a78bfa; margin:4px 0 12px; padding-bottom:6px;
      border-bottom:1px solid rgba(124,92,255,.18); }

/* ---- metric cards ---- */
[data-testid="stMetric"] {
    background: linear-gradient(160deg, rgba(36,33,66,.85), rgba(20,24,43,.85));
    border:1px solid rgba(124,92,255,.18);
    border-radius:16px; padding:16px 20px;
    box-shadow: 0 8px 28px -16px rgba(99,52,237,.5);
    transition: transform .15s ease, border-color .15s ease;
}
[data-testid="stMetric"]:hover { transform: translateY(-2px); border-color: rgba(124,92,255,.45); }
[data-testid="stMetricLabel"] p { color:#8b93b8 !important; font-size:.66rem !important;
    letter-spacing:.12em; text-transform:uppercase; font-weight:600; }
[data-testid="stMetricValue"] {
    font-size:1.7rem !important; font-weight:800 !important;
    background:linear-gradient(90deg,#ede9fe,#bfdbfe);
    -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent;
}

/* ---- nav buttons (horizontal) ---- */
div[data-testid="column"] .stButton > button {
    background: rgba(30,33,60,.55);
    border:1px solid rgba(124,92,255,.16);
    color:#c7cce6; font-weight:600; font-size:.9rem;
    border-radius:12px; padding:11px 8px; width:100%;
    transition: all .15s ease;
}
div[data-testid="column"] .stButton > button:hover {
    border-color: rgba(124,92,255,.55); color:#fff;
    background: rgba(60,52,120,.45);
    transform: translateY(-1px);
}
/* active nav button */
.nav-active div[data-testid="column"] .stButton > button,
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg,#7c3aed,#4f46e5 60%,#06b6d4) !important;
    border:none !important; color:#fff !important;
    box-shadow: 0 8px 22px -6px rgba(124,58,237,.7) !important;
}

/* generic primary / form-submit / download buttons */
.stForm .stButton > button,
.stDownloadButton > button {
    background: linear-gradient(135deg,#7c3aed,#4f46e5 60%,#06b6d4) !important;
    color:#fff !important; font-weight:700 !important; border:none !important;
    border-radius:12px !important; font-size:.95rem !important;
    box-shadow: 0 8px 22px -8px rgba(124,58,237,.7) !important;
}
.stForm .stButton > button:hover,
.stDownloadButton > button:hover { filter:brightness(1.08); transform:translateY(-1px); }

.dl-btn > button {
    background: linear-gradient(135deg,#7c3aed,#4f46e5 60%,#06b6d4) !important;
    color:#fff !important; font-weight:700 !important; border:none !important;
    border-radius:12px !important; font-size:.95rem !important; width:100%;
    box-shadow: 0 8px 22px -8px rgba(124,58,237,.7) !important;
}
.dl-btn > button:hover { filter:brightness(1.08); }

/* import button (give it its own glow) */
.import-btn > button {
    background: linear-gradient(135deg,#06b6d4,#3b82f6 60%,#7c3aed) !important;
    color:#fff !important; font-weight:700 !important; border:none !important;
    border-radius:12px !important; box-shadow:0 8px 22px -8px rgba(6,182,212,.7) !important;
}
.import-btn > button:hover { filter:brightness(1.08); transform:translateY(-1px); }

/* ---- alerts ---- */
.ok   { background:rgba(16,185,129,.1);  border-left:4px solid #10b981; color:#a7f3d0;
        padding:11px 16px; border-radius:10px; font-size:.86rem; margin:8px 0; }
.err  { background:rgba(244,63,94,.1);   border-left:4px solid #f43f5e; color:#fecdd3;
        padding:11px 16px; border-radius:10px; font-size:.86rem; margin:8px 0; }
.warn { background:rgba(245,158,11,.1);  border-left:4px solid #f59e0b; color:#fde68a;
        padding:11px 16px; border-radius:10px; font-size:.86rem; margin:8px 0; }

/* ---- inputs ---- */
[data-testid="stTextInput"] > div > div > input,
[data-testid="stNumberInput"] input,
[data-testid="stSelectbox"] > div,
textarea {
    background:rgba(20,24,43,.85) !important; border:1px solid rgba(124,92,255,.2) !important;
    color:#e6e8f2 !important; border-radius:10px !important;
}
[data-testid="stTextInput"] > div > div > input:focus,
[data-testid="stNumberInput"] input:focus {
    border-color: rgba(124,92,255,.6) !important;
    box-shadow: 0 0 0 2px rgba(124,92,255,.18) !important;
}
div[data-testid="stDataFrame"] {
    border:1px solid rgba(124,92,255,.2); border-radius:14px; overflow:hidden;
}
hr { border-color: rgba(124,92,255,.14) !important; }

/* info card */
.info-card {
    background: linear-gradient(160deg, rgba(36,33,66,.6), rgba(20,24,43,.6));
    border:1px solid rgba(124,92,255,.18); border-radius:16px;
    padding:20px 22px; color:#aab1d6; font-size:.92rem;
}
</style>
""", unsafe_allow_html=True)

# ─── Animations ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ===== keyframes ===== */
@keyframes fadeUp {
    from { opacity:0; transform: translateY(14px); }
    to   { opacity:1; transform: translateY(0); }
}
@keyframes fadeIn {
    from { opacity:0; } to { opacity:1; }
}
@keyframes barIn {
    from { opacity:0; transform: translateY(-10px) scale(.98); }
    to   { opacity:1; transform: translateY(0) scale(1); }
}
@keyframes activePulse {
    0%,100% { box-shadow: 0 8px 22px -6px rgba(124,58,237,.55); }
    50%     { box-shadow: 0 8px 30px -4px rgba(124,58,237,.95); }
}
@keyframes sheen {
    0%   { left:-140%; }
    100% { left:140%; }
}

/* ===== page entrance: stagger the main blocks on each load/route change ===== */
.block-container > div > div > div > [data-testid="stVerticalBlock"] > div {
    animation: fadeUp .45s cubic-bezier(.22,.61,.36,1) both;
}
.block-container > div > div > div > [data-testid="stVerticalBlock"] > div:nth-child(1) { animation-delay:.02s; }
.block-container > div > div > div > [data-testid="stVerticalBlock"] > div:nth-child(2) { animation-delay:.06s; }
.block-container > div > div > div > [data-testid="stVerticalBlock"] > div:nth-child(3) { animation-delay:.10s; }
.block-container > div > div > div > [data-testid="stVerticalBlock"] > div:nth-child(4) { animation-delay:.14s; }
.block-container > div > div > div > [data-testid="stVerticalBlock"] > div:nth-child(5) { animation-delay:.18s; }
.block-container > div > div > div > [data-testid="stVerticalBlock"] > div:nth-child(n+6) { animation-delay:.22s; }

/* top bar drops in */
.topbar { animation: barIn .5s cubic-bezier(.22,.61,.36,1) both; }

/* page headings + section labels fade up */
.page-h   { animation: fadeUp .5s cubic-bezier(.22,.61,.36,1) both; }
.page-sub { animation: fadeUp .5s cubic-bezier(.22,.61,.36,1) .05s both; }
.sh       { animation: fadeIn .6s ease both; }

/* dataframe + charts ease in */
div[data-testid="stDataFrame"],
div[data-testid="stArrowVegaLiteChart"],
.info-card { animation: fadeUp .5s cubic-bezier(.22,.61,.36,1) both; }

/* ===== buttons: smooth transition + hover/press + shine sweep ===== */
.stButton > button,
.stDownloadButton > button,
.stForm button {
    position: relative;
    overflow: hidden;
    transition: transform .18s cubic-bezier(.22,.61,.36,1),
                box-shadow .18s ease, filter .18s ease, border-color .18s ease !important;
    will-change: transform;
}
.stButton > button:hover,
.stDownloadButton > button:hover,
.stForm button:hover { transform: translateY(-2px); }

.stButton > button:active,
.stDownloadButton > button:active,
.stForm button:active { transform: translateY(0) scale(.97); transition-duration:.05s !important; }

/* light sweep across buttons on hover */
.stButton > button::after,
.stDownloadButton > button::after,
.stForm button::after {
    content:""; position:absolute; top:0; left:-140%;
    width:60%; height:100%;
    background: linear-gradient(120deg, transparent, rgba(255,255,255,.28), transparent);
    transform: skewX(-20deg); pointer-events:none;
}
.stButton > button:hover::after,
.stDownloadButton > button:hover::after,
.stForm button:hover::after { animation: sheen .7s ease; }

/* active nav button keeps a gentle glow pulse */
.nav-active .stButton > button,
.stButton > button[kind="primary"] { animation: activePulse 2.6s ease-in-out infinite; }

/* spinner-friendly: respect reduced-motion preference */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { animation: none !important; transition: none !important; }
}

/* ===== group cards on the Create / Edit forms ===== */
.group-card {
    background: linear-gradient(160deg, rgba(36,33,66,.55), rgba(20,24,43,.55));
    border:1px solid rgba(124,92,255,.16);
    border-radius:16px; padding:18px 20px 6px; margin-bottom:18px;
    box-shadow: 0 8px 28px -18px rgba(99,52,237,.5);
    animation: fadeUp .5s cubic-bezier(.22,.61,.36,1) both;
    transition: border-color .18s ease, transform .18s ease;
}
.group-card:hover { border-color: rgba(124,92,255,.4); }

/* ===== dynamic page transition (re-stamped on every page toggle) ===== */
@keyframes pageEnter {
    from { opacity:0; transform: translateY(20px) scale(.985); filter: blur(2px); }
    to   { opacity:1; transform: translateY(0) scale(1); filter: blur(0); }
}
.page-wrap { animation: pageEnter .42s cubic-bezier(.22,.61,.36,1) both; }

/* The main content column re-mounts on every rerun (each page toggle),
   so animating it here replays a smooth transition whenever you switch pages.
   The top bar/nav live above this and are excluded so they stay steady. */
section.main .block-container { animation: pageEnter .44s cubic-bezier(.22,.61,.36,1) both; }
</style>
""", unsafe_allow_html=True)


# ─── Helpers ───────────────────────────────────────────────────────────────────
def api(method, path, **kw):
    try:
        r = getattr(requests, method)(f"{API_BASE}{path}", timeout=30, **kw)
        r.raise_for_status()
        return r
    except requests.exceptions.ConnectionError:
        st.error("⚠️  Backend offline — run: uvicorn backend:app --reload")
        st.stop()
    except requests.exceptions.HTTPError as e:
        detail = ""
        try:   detail = e.response.json().get("detail", "")
        except Exception: pass
        raise RuntimeError(detail or str(e))

def ok(m):   st.markdown(f"<div class='ok'>✅ {m}</div>",   unsafe_allow_html=True)
def err(m):  st.markdown(f"<div class='err'>❌ {m}</div>",  unsafe_allow_html=True)
def warn(m): st.markdown(f"<div class='warn'>⚠️ {m}</div>", unsafe_allow_html=True)

# ─── Data normalization ────────────────────────────────────────────────────────
# CEIPAL can return rows as positional arrays (or numeric-string-keyed objects)
# instead of named dicts. Map them onto these field names by position so the
# dashboard sees real columns instead of 0,1,2… (which showed as empty/"Unknown").
CIEPAL_FIELDS = [
    "Sub_ID","Job_Code","Client_Manager","MSP","End_Client","Job_Type","Job_Status",
    "Job_Applied","Job_Location","States","Applicant_Location","Profile_Status",
    "Client_Interview_Scheduled_Date","Priority","Submission_Bill_Rate","Submission_Pay_Rate",
    "Submission_Tax_Terms","Job_Client_Bill_Rate","Work_Authorization","Pipeline_Status",
    "Job_Created_On","Applicant_Created_On","Submitted_On","Status_Changed_On","Modified_On",
    "Max_Number_of_Submissions","Applicant_Current_Employer","Experience","Client_Rejection_On",
    "Applicant_Status","Job_Created_By","Submission_Rating","Current_Company",
    "Recruiter_Team_Name","Assigned_To_Email_ID","Sales_Manager","Submitted_By_Email_ID",
    "Status_Changed_By","Applicant_Created_By","Account_Manager","Recruitment_Manager",
    "Applicant_ID","Email_Address","Number_of_Positions","Client_Category","Linkedin_URL",
    "Number_of_Interviews","Source","Submission_Source","Ownership","RowAdded","Client_Job_ID",
]
_INTERNAL_KEYS = {"_local_id", "_created_at", "_updated_at"}

def normalize_rows(rows):
    """Return rows as clean named-dict records regardless of incoming shape."""
    out = []
    for r in rows or []:
        if isinstance(r, dict):
            if r and all(str(k).isdigit() for k in r.keys()):     # numeric-keyed → positional
                vals = [r[k] for k in sorted(r.keys(), key=lambda x: int(x))]
                rec = {CIEPAL_FIELDS[i]: v for i, v in enumerate(vals) if i < len(CIEPAL_FIELDS)}
            else:
                rec = {k: v for k, v in r.items() if k not in _INTERNAL_KEYS}
            out.append(rec)
        elif isinstance(r, (list, tuple)):                         # bare array → positional
            out.append({CIEPAL_FIELDS[i]: v for i, v in enumerate(r) if i < len(CIEPAL_FIELDS)})
    return out

# Theme colors for charts
CHART_SEQ = ["#7c3aed","#06b6d4","#a78bfa","#3b82f6","#f59e0b","#10b981",
             "#f43f5e","#67e8f9","#c4b5fd","#fb7185","#34d399","#fbbf24"]

# ─── Field config ──────────────────────────────────────────────────────────────
GROUPS = {
    "🔖 Identifiers":       ["Sub_ID","Applicant_ID","Client_Job_ID","Job_Code"],
    "💼 Job Info":          ["Job_Type","Job_Status","Job_Location","States",
                              "Number_of_Positions","Max_Number_of_Submissions",
                              "Priority","Client_Category","End_Client","MSP","Client_Manager"],
    "👤 Applicant":         ["Email_Address","Applicant_Location","Applicant_Current_Employer",
                              "Current_Company","Experience","Work_Authorization",
                              "Linkedin_URL","Source","Submission_Source","Ownership"],
    "💰 Rates":             ["Submission_Bill_Rate","Submission_Pay_Rate",
                              "Submission_Tax_Terms","Job_Client_Bill_Rate"],
    "📊 Status / Pipeline": ["Profile_Status","Pipeline_Status","Applicant_Status",
                              "Submission_Rating","Number_of_Interviews"],
    "👥 Team":              ["Recruiter_Team_Name","Assigned_To_Email_ID","Sales_Manager",
                              "Submitted_By_Email_ID","Status_Changed_By","Applicant_Created_By",
                              "Account_Manager","Recruitment_Manager","Job_Created_By"],
    "📅 Dates":             ["Job_Applied","Client_Interview_Scheduled_Date","Job_Created_On",
                              "Applicant_Created_On","Submitted_On","Status_Changed_On",
                              "Modified_On","Client_Rejection_On","RowAdded"],
}

FLOAT_FIELDS = {"Submission_Bill_Rate","Submission_Pay_Rate","Job_Client_Bill_Rate"}
INT_FIELDS   = {"Number_of_Positions","Max_Number_of_Submissions","Number_of_Interviews"}
PROFILE_STATUS_OPTS  = ["","Available","On Project","Not Available","Do Not Contact","Blacklisted"]
PIPELINE_STATUS_OPTS = ["","New","Submitted","Shortlisted","Interview","Offered","Hired","Rejected","On Hold"]
JOB_STATUS_OPTS      = ["","Active","Closed","On Hold","Cancelled","Filled"]
TAX_OPTS             = ["","W2","C2C","1099","W2 with Benefits"]
WA_OPTS              = ["","US Citizen","Green Card","H1B","EAD","TN Visa","OPT","CPT","Other"]

# Human-friendly labels (fallback: derive from the field name)
LABELS = {
    "Sub_ID":"Submission ID","Applicant_ID":"Applicant ID","Client_Job_ID":"Client Job ID",
    "Job_Code":"Job Code","Job_Type":"Job Type","Job_Status":"Job Status","Job_Location":"Job Location",
    "Number_of_Positions":"No. of Positions","Max_Number_of_Submissions":"Max Submissions",
    "Client_Category":"Client Category","Email_Address":"Email Address",
    "Applicant_Location":"Applicant Location","Applicant_Current_Employer":"Current Employer",
    "Current_Company":"Current Company","Work_Authorization":"Work Authorization",
    "Linkedin_URL":"LinkedIn URL","Submission_Source":"Submission Source",
    "Submission_Bill_Rate":"Bill Rate ($/hr)","Submission_Pay_Rate":"Pay Rate ($/hr)",
    "Submission_Tax_Terms":"Tax Terms","Job_Client_Bill_Rate":"Client Bill Rate ($/hr)",
    "Profile_Status":"Profile Status","Pipeline_Status":"Pipeline Status",
    "Applicant_Status":"Applicant Status","Submission_Rating":"Submission Rating",
    "Number_of_Interviews":"No. of Interviews","Recruiter_Team_Name":"Recruiter Team",
    "Assigned_To_Email_ID":"Assigned To (email)","Sales_Manager":"Sales Manager",
    "Submitted_By_Email_ID":"Submitted By (email)","Status_Changed_By":"Status Changed By",
    "Applicant_Created_By":"Applicant Created By","Account_Manager":"Account Manager",
    "Recruitment_Manager":"Recruitment Manager","Job_Created_By":"Job Created By",
    "Job_Applied":"Job Applied On","Client_Interview_Scheduled_Date":"Interview Scheduled",
    "Job_Created_On":"Job Created On","Applicant_Created_On":"Applicant Created On",
    "Submitted_On":"Submitted On","Status_Changed_On":"Status Changed On",
    "Modified_On":"Modified On","Client_Rejection_On":"Client Rejection On","RowAdded":"Row Added",
    "End_Client":"End Client","Client_Manager":"Client Manager",
}
PLACEHOLDERS = {
    "Sub_ID":"e.g. SUB-100245","Applicant_ID":"e.g. APP-58821","Client_Job_ID":"e.g. CJ-3391",
    "Job_Code":"e.g. JAVA-SR-01","Job_Type":"e.g. Contract / Full-Time","Job_Location":"e.g. Austin, TX",
    "States":"e.g. TX","Email_Address":"e.g. jane.doe@company.com",
    "Applicant_Location":"e.g. Dallas, TX","Applicant_Current_Employer":"e.g. Acme Corp",
    "Current_Company":"e.g. Acme Corp","Experience":"e.g. 8 years","Linkedin_URL":"https://linkedin.com/in/…",
    "Source":"e.g. LinkedIn / Referral","Submission_Source":"e.g. Internal","Ownership":"e.g. John Smith",
    "Priority":"e.g. High","Client_Category":"e.g. Direct Client","End_Client":"e.g. Global Bank Inc.",
    "Client_Manager":"e.g. Sarah Lee","Recruiter_Team_Name":"e.g. Team Alpha",
    "Assigned_To_Email_ID":"name@company.com","Submitted_By_Email_ID":"name@company.com",
    "MSP":"e.g. Beeline","Submission_Rating":"e.g. A / B / C",
}
HELP = {
    "Sub_ID":"Unique identifier for this submission. Required.",
    "Submission_Bill_Rate":"Hourly rate billed to the client.",
    "Submission_Pay_Rate":"Hourly rate paid to the candidate.",
    "Job_Client_Bill_Rate":"Approved client bill rate for the job.",
    "Work_Authorization":"Candidate's current work authorization status.",
    "Pipeline_Status":"Where the candidate sits in the hiring pipeline.",
}

def pretty(label):
    return LABELS.get(label, label.replace("_", " "))

def field_input(label, default=None, key=None, required=False):
    disp = pretty(label) + (" *" if required else "")
    help_txt = HELP.get(label)
    ph = PLACEHOLDERS.get(label, "")
    if label == "Profile_Status":
        v = default or ""; idx = PROFILE_STATUS_OPTS.index(v) if v in PROFILE_STATUS_OPTS else 0
        return st.selectbox(disp, PROFILE_STATUS_OPTS, index=idx, key=key, help=help_txt)
    if label == "Pipeline_Status":
        v = default or ""; idx = PIPELINE_STATUS_OPTS.index(v) if v in PIPELINE_STATUS_OPTS else 0
        return st.selectbox(disp, PIPELINE_STATUS_OPTS, index=idx, key=key, help=help_txt)
    if label == "Job_Status":
        v = default or ""; idx = JOB_STATUS_OPTS.index(v) if v in JOB_STATUS_OPTS else 0
        return st.selectbox(disp, JOB_STATUS_OPTS, index=idx, key=key, help=help_txt)
    if label == "Submission_Tax_Terms":
        v = default or ""; idx = TAX_OPTS.index(v) if v in TAX_OPTS else 0
        return st.selectbox(disp, TAX_OPTS, index=idx, key=key, help=help_txt)
    if label == "Work_Authorization":
        v = default or ""; idx = WA_OPTS.index(v) if v in WA_OPTS else 0
        return st.selectbox(disp, WA_OPTS, index=idx, key=key, help=help_txt)
    if label in FLOAT_FIELDS:
        return st.number_input(disp, value=float(default or 0), step=1.0, format="%.2f", key=key, help=help_txt)
    if label in INT_FIELDS:
        return st.number_input(disp, value=int(default or 0), step=1, key=key, help=help_txt)
    return st.text_input(disp, value=str(default or ""), key=key, placeholder=ph, help=help_txt)

# ─── Session state ─────────────────────────────────────────────────────────────
if "preview_df"    not in st.session_state: st.session_state.preview_df    = None
if "preview_total" not in st.session_state: st.session_state.preview_total = 0
if "page"          not in st.session_state: st.session_state.page          = "Dashboard"

# ─── Backend health check ──────────────────────────────────────────────────────
try:
    hc = requests.get(f"{API_BASE}/", timeout=3)
    backend_ok = hc.status_code == 200
except Exception:
    backend_ok = False

# ═══════════════════════════════════════════════════════════════════════════════
# TOP BAR  (brand + status + import)   — replaces the old sidebar
# ═══════════════════════════════════════════════════════════════════════════════
status_html = (
    "<span class='pill pill-on'><span class='dot'></span>Backend online</span>"
    if backend_ok else
    "<span class='pill pill-off'><span class='dot'></span>Backend offline</span>"
)
st.markdown(f"""
<div class="topbar">
  <div class="brand">
    <div class="brand-logo">📋</div>
    <div>
      <div class="brand-title">CIEPAL</div>
      <div class="brand-sub">Submission Report Manager</div>
    </div>
  </div>
  <div>{status_html}</div>
</div>
""", unsafe_allow_html=True)

# ─── Horizontal nav + import row ───────────────────────────────────────────────
NAV = ["Dashboard", "Create Submission", "Edit / Delete", "Download Report"]

nav_cols = st.columns([1, 1, 1, 1, 0.25, 1.15])
for i, name in enumerate(NAV):
    is_active = st.session_state.page == name
    wrapper = "nav-active" if is_active else ""
    with nav_cols[i]:
        st.markdown(f"<div class='{wrapper}'>", unsafe_allow_html=True)
        if st.button(name, key=f"nav_{name}",
                     use_container_width=True,
                     type="primary" if is_active else "secondary"):
            st.session_state.page = name
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

with nav_cols[5]:
    st.markdown("<div class='import-btn'>", unsafe_allow_html=True)
    if st.button("Import from CIEPAL", key="import_btn",
                 use_container_width=True, disabled=not backend_ok):
        with st.spinner("Importing from CIEPAL…"):
            try:
                res = api("get", "/ciepal/import").json()
                ok(f"Imported <b>{res['imported']}</b> rows. "
                   f"{res['skipped_duplicates']} duplicates skipped. "
                   f"Total in store: <b>{res['total_in_store']}</b>")
                time.sleep(0.6)
                st.rerun()
            except RuntimeError as e:
                err(str(e))
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<hr/>", unsafe_allow_html=True)

page = st.session_state.page

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "Dashboard":
    st.markdown("<div class='page-h'>Submission Dashboard</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Live overview of all submissions in the local store.</div>",
                unsafe_allow_html=True)

    try:
        stats = api("get", "/submissions/summary/stats").json()
        rows  = normalize_rows(api("get", "/submissions").json())
    except Exception as e:
        st.error(str(e)); st.stop()

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Total Submissions",  stats.get("total", len(rows)))
    c2.metric("Avg Bill Rate",      f"${stats.get('avg_bill_rate', 0):,.0f}")
    c3.metric("Max Bill Rate",      f"${stats.get('max_bill_rate', 0):,.0f}")
    c4.metric("Profile Statuses",   len(stats.get("by_profile_status", {})))
    c5.metric("Pipeline Stages",    len(stats.get("by_pipeline_status", {})))

    st.divider()

    if not rows:
        st.markdown(
            "<div class='info-card'>No submissions yet. Click "
            "<b>Import from CIEPAL</b> in the top bar to load data.</div>",
            unsafe_allow_html=True,
        )
    else:
        df = pd.DataFrame(rows)
        # Coerce obvious numeric columns so charts/aggregations behave.
        # (pandas >=2.2 removed errors="ignore", so convert and keep original on failure.)
        for c in df.columns:
            if any(t in c for t in ("Rate","Number_of","Positions","Interviews","Experience")):
                converted = pd.to_numeric(df[c], errors="coerce")
                if converted.notna().any():        # only adopt if at least some values parsed
                    df[c] = converted
        all_cols = list(df.columns)

        # ── Optional quick filters (only for columns that actually exist) ──────
        filterable = [c for c in ["Profile_Status","Pipeline_Status","Job_Status"] if c in df.columns]
        if filterable:
            st.markdown("<div class='sh'>Filters</div>", unsafe_allow_html=True)
            fcols = st.columns(len(filterable))
            for fcol, name in zip(fcols, filterable):
                opts = ["All"] + sorted([str(x) for x in df[name].dropna().unique()])
                choice = fcol.selectbox(pretty(name), opts, key=f"dash_filt_{name}")
                if choice != "All":
                    df = df[df[name].astype(str) == choice]
            st.divider()

        # ── Table: user picks columns, starts empty ───────────────────────────
        st.markdown("<div class='sh'>Table — choose columns to display</div>", unsafe_allow_html=True)
        chosen_cols = st.multiselect(
            "Columns", all_cols, default=[],
            placeholder="Pick one or more columns to show the table…",
            label_visibility="collapsed", key="dash_table_cols",
        )
        if chosen_cols:
            st.markdown(f"<div class='page-sub' style='margin:2px 0 8px'>{len(df)} rows · "
                        f"{len(chosen_cols)} of {len(all_cols)} columns</div>", unsafe_allow_html=True)
            st.dataframe(df[chosen_cols], use_container_width=True, hide_index=True)
        else:
            st.markdown(
                "<div class='info-card'>No columns selected yet. Use the box above to choose "
                "which columns appear in the table.</div>", unsafe_allow_html=True,
            )

        st.divider()

        # ── Chart builder: user picks column + chart type, starts empty ───────
        st.markdown("<div class='sh'>Chart builder — pick a column and a chart type</div>",
                    unsafe_allow_html=True)
        bc1, bc2, bc3 = st.columns([2, 1.4, 1])
        chart_col = bc1.selectbox(
            "Column to chart", ["— select a column —"] + all_cols,
            key="dash_chart_col",
        )
        chart_kind = bc2.selectbox(
            "Chart type", ["Bar", "Horizontal bar", "Pie", "Donut", "Line"],
            key="dash_chart_kind",
        )
        top_n = bc3.number_input("Top N", 3, 50, 12, 1, key="dash_chart_topn",
                                 help="Limit to the N most frequent / most recent values.")

        if chart_col == "— select a column —":
            st.markdown(
                "<div class='info-card'>No chart yet. Choose a column above and a chart type to "
                "render it. Categorical columns work well as Bar/Pie; numeric columns as Line.</div>",
                unsafe_allow_html=True,
            )
        else:
            series = df[chart_col].dropna()
            is_numeric = pd.api.types.is_numeric_dtype(series)

            try:
                if chart_kind == "Line":
                    if is_numeric:
                        plot_df = series.reset_index(drop=True).rename("value").to_frame()
                        plot_df["row"] = range(1, len(plot_df) + 1)
                        fig = px.line(plot_df, x="row", y="value", markers=True,
                                      color_discrete_sequence=CHART_SEQ)
                    else:  # line over value counts (ordered) for categorical
                        vc = series.astype(str).value_counts().head(int(top_n)).sort_index()
                        fig = px.line(x=vc.index, y=vc.values, markers=True,
                                      color_discrete_sequence=CHART_SEQ,
                                      labels={"x": pretty(chart_col), "y": "Count"})
                else:
                    # count-based charts
                    vc = series.astype(str).value_counts().head(int(top_n))
                    cat_df = pd.DataFrame({pretty(chart_col): vc.index, "Count": vc.values})
                    if chart_kind == "Bar":
                        fig = px.bar(cat_df, x=pretty(chart_col), y="Count",
                                     color=pretty(chart_col), color_discrete_sequence=CHART_SEQ)
                    elif chart_kind == "Horizontal bar":
                        fig = px.bar(cat_df, x="Count", y=pretty(chart_col), orientation="h",
                                     color=pretty(chart_col), color_discrete_sequence=CHART_SEQ)
                    elif chart_kind == "Pie":
                        fig = px.pie(cat_df, names=pretty(chart_col), values="Count",
                                     color_discrete_sequence=CHART_SEQ)
                    else:  # Donut
                        fig = px.pie(cat_df, names=pretty(chart_col), values="Count", hole=0.55,
                                     color_discrete_sequence=CHART_SEQ)

                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#c7cce6", size=12),
                    margin=dict(l=10, r=10, t=30, b=10), height=440,
                    legend=dict(font=dict(color="#aab1d6")),
                    title=dict(text=f"{pretty(chart_col)} — {chart_kind}", font=dict(color="#e6e8f2")),
                )
                fig.update_xaxes(gridcolor="rgba(124,92,255,.12)", zeroline=False)
                fig.update_yaxes(gridcolor="rgba(124,92,255,.12)", zeroline=False)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                warn(f"Couldn't render that combination: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# CREATE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Create Submission":
    st.markdown("<div class='page-h'>Create Submission</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Add a new submission to the store. "
                "Fields marked <span style='color:#fb7185'>*</span> are required — "
                "everything else is optional.</div>", unsafe_allow_html=True)

    with st.form("create_form", clear_on_submit=True):
        form_data = {}
        for group, fields in GROUPS.items():
            # group header as a card-like band
            st.markdown(f"<div class='group-card'><div class='sh' style='border:none;margin:0 0 14px'>"
                        f"{group}</div>", unsafe_allow_html=True)
            cols = st.columns(3)
            for i, field in enumerate(fields):
                with cols[i % 3]:
                    is_req = (field == "Sub_ID")
                    form_data[field] = field_input(field, key=f"c_{field}", required=is_req)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        cbtn1, cbtn2 = st.columns([3, 1])
        with cbtn1:
            submitted = st.form_submit_button("Create Submission", use_container_width=True)
        with cbtn2:
            st.form_submit_button("Reset", use_container_width=True, type="secondary")

    if submitted:
        if not form_data.get("Sub_ID","").strip():
            err("<b>Submission ID</b> is required to create a record.")
        else:
            payload = {k: v for k, v in form_data.items() if v not in (None,"",0,0.0)}
            try:
                rec = api("post", "/submissions", json=payload).json()
                st.balloons()
                ok(f"Submission <b>{rec['Sub_ID']}</b> created successfully "
                   f"with <b>{len(payload)}</b> field(s) populated.")
                # quick read-back summary of the key fields
                summary = {pretty(k): rec.get(k) for k in
                           ["Sub_ID","Job_Code","End_Client","Pipeline_Status","Submission_Bill_Rate"]
                           if rec.get(k) not in (None, "")}
                if summary:
                    st.markdown("<div class='sh' style='margin-top:14px'>Created Record</div>",
                                unsafe_allow_html=True)
                    st.dataframe(pd.DataFrame([summary]), use_container_width=True, hide_index=True)
            except RuntimeError as e:
                err(str(e))


# ══════════════════════════════════════════════════════════════════════════════
# EDIT / DELETE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Edit / Delete":
    st.markdown("<div class='page-h'>Edit / Delete Submission</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Update or remove an existing submission.</div>",
                unsafe_allow_html=True)
    rows = api("get", "/submissions").json()

    if not rows:
        st.markdown(
            "<div class='info-card'>No submissions in store. Click "
            "<b>Import from CIEPAL</b> in the top bar first.</div>",
            unsafe_allow_html=True,
        )
    else:
        opts = {f"{r.get('Sub_ID','?')} — {r.get('End_Client','') or r.get('Job_Code','?')}": r["Sub_ID"]
                for r in rows if r.get("Sub_ID")}
        chosen = st.selectbox("Select Submission", list(opts.keys()))
        sub_id = opts[chosen]
        rec    = api("get", f"/submissions/{sub_id}").json()

        st.divider()
        tab_e, tab_d = st.tabs(["Edit", "Delete"])

        with tab_e:
            with st.form("edit_form"):
                form_data = {}
                for group, fields in GROUPS.items():
                    if group == "🔖 Identifiers": continue
                    st.markdown(f"<div class='sh'>{group}</div>", unsafe_allow_html=True)
                    cols = st.columns(3)
                    for i, field in enumerate(fields):
                        with cols[i % 3]:
                            form_data[field] = field_input(field, default=rec.get(field), key=f"e_{field}")
                    st.markdown("")

                if st.form_submit_button("Save Changes", use_container_width=True):
                    payload = {k: v for k, v in form_data.items() if v not in (None,"")}
                    try:
                        api("put", f"/submissions/{sub_id}", json=payload)
                        ok("Submission updated.")
                        time.sleep(0.4); st.rerun()
                    except RuntimeError as e:
                        err(str(e))

            with st.expander("🔖 Identifiers (read-only)"):
                ic1,ic2,ic3,ic4 = st.columns(4)
                for col, field in zip([ic1,ic2,ic3,ic4],["Sub_ID","Applicant_ID","Client_Job_ID","Job_Code"]):
                    col.text_input(field, value=rec.get(field,""), disabled=True)

        with tab_d:
            st.warning(f"Permanently delete **{rec.get('Sub_ID')}** "
                       f"({rec.get('End_Client') or rec.get('Job_Code','')})? Cannot be undone.")
            if st.button("Delete Submission", type="primary", use_container_width=True):
                try:
                    api("delete", f"/submissions/{sub_id}")
                    ok(f"Submission {sub_id} deleted.")
                    time.sleep(0.5); st.rerun()
                except RuntimeError as e:
                    err(str(e))


# ══════════════════════════════════════════════════════════════════════════════
# DOWNLOAD REPORT
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Download Report":
    st.markdown("<div class='page-h'>Download CIEPAL Report</div>", unsafe_allow_html=True)
    st.markdown("<div class='sh'>Live from atsbi.ceipal.com</div>", unsafe_allow_html=True)

    c1, c2 = st.columns([2,2])
    fmt   = c1.radio("Format", ["CSV","JSON"], horizontal=True)
    limit = c2.number_input("Preview rows", 5, 500, 50, 10)

    st.divider()
    left, right = st.columns([3,1])

    with left:
        st.markdown("<div class='sh'>Live Preview</div>", unsafe_allow_html=True)
        if st.button("Load Preview", use_container_width=True):
            with st.spinner("Fetching from CIEPAL…"):
                try:
                    data = api("get", "/ciepal/preview", params={"limit": limit}).json()
                    rows = data.get("rows", [])
                    if rows:
                        st.session_state.preview_df    = pd.DataFrame(rows)
                        st.session_state.preview_total = data.get("total", 0)
                        ok(f"Showing {len(rows)} of {data.get('total',0)} rows.")
                    else:
                        warn("CIEPAL returned 0 rows.")
                except RuntimeError as e:
                    err(str(e))

        if st.session_state.preview_df is not None:
            df = st.session_state.preview_df
            PRIORITY = ["Sub_ID","Job_Code","End_Client","Client_Manager","Profile_Status",
                        "Pipeline_Status","Job_Status","Applicant_Status","Submission_Bill_Rate",
                        "Submission_Pay_Rate","Submission_Tax_Terms","Work_Authorization",
                        "Recruiter_Team_Name","Submitted_On","Source"]
            ordered = [c for c in PRIORITY if c in df.columns] + \
                      [c for c in df.columns if c not in PRIORITY]
            st.dataframe(df[ordered], use_container_width=True, hide_index=True)

    with right:
        st.markdown("<div class='sh'>Export</div>", unsafe_allow_html=True)
        st.markdown(
            "<p style='font-size:.68rem;color:#8b93b8;word-break:break-all;margin-bottom:14px'>"
            "atsbi.ceipal.com/api/report-details/get-report-data/W4DKw9QX…</p>",
            unsafe_allow_html=True,
        )

        st.markdown("<div class='dl-btn'>", unsafe_allow_html=True)
        if st.button(f"Download {fmt}", use_container_width=True):
            with st.spinner(f"Downloading {fmt}…"):
                try:
                    resp = api("get", "/ciepal/report", params={"format": fmt.lower()})
                    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
                    ext  = fmt.lower()
                    mime = "text/csv" if fmt == "CSV" else "application/json"
                    st.download_button(
                        label=f"Save ciepal_{ts}.{ext}",
                        data=resp.content,
                        file_name=f"ciepal_{ts}.{ext}",
                        mime=mime,
                        use_container_width=True,
                    )
                    ok(f"Ready — {len(resp.content):,} bytes.")
                except RuntimeError as e:
                    err(str(e))
        st.markdown("</div>", unsafe_allow_html=True)
