"""
app.py — Streamlit UI for CIEPAL Submission Report CRUD
Run: streamlit run app.py
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="CIEPAL Submissions",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #0d1117; }
[data-testid="stSidebar"] { background: #161b27; border-right: 1px solid #21293d; }

[data-testid="metric-container"] {
    background: #1a2236; border: 1px solid #21293d;
    border-radius: 10px; padding: 14px 20px;
}
[data-testid="stMetricLabel"] { color:#7c8fa6 !important; font-size:.68rem !important;
    letter-spacing:.1em; text-transform:uppercase; }
[data-testid="stMetricValue"] { color:#e2e8f0 !important; font-size:1.5rem !important; }

.sh { font-size:.65rem; font-weight:700; letter-spacing:.14em; text-transform:uppercase;
      color:#4a90d9; margin-bottom:10px; padding-bottom:5px; border-bottom:1px solid #21293d; }

.dl-btn > button {
    background: linear-gradient(135deg,#1a6fd4,#0e4fa3) !important;
    color:#fff !important; font-weight:700 !important; border:none !important;
    border-radius:8px !important; font-size:.95rem !important; width:100%;
}
.dl-btn > button:hover { opacity:.85 !important; }

.ok   { background:#1a3a2a; border-left:4px solid #48bb78; color:#c6f6d5;
        padding:9px 14px; border-radius:6px; font-size:.85rem; margin:6px 0; }
.err  { background:#2d1a1a; border-left:4px solid #f56565; color:#fed7d7;
        padding:9px 14px; border-radius:6px; font-size:.85rem; margin:6px 0; }
.warn { background:#2d2510; border-left:4px solid #f6ad55; color:#feebc8;
        padding:9px 14px; border-radius:6px; font-size:.85rem; margin:6px 0; }

[data-testid="stTextInput"] > div > div > input,
[data-testid="stNumberInput"] input,
[data-testid="stSelectbox"] > div,
textarea {
    background:#1a2236 !important; border:1px solid #21293d !important;
    color:#e2e8f0 !important; border-radius:6px !important;
}
div[data-testid="stDataFrame"] { border:1px solid #21293d; border-radius:10px; overflow:hidden; }
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

def field_input(label, default=None, key=None):
    if label == "Profile_Status":
        v = default or ""; idx = PROFILE_STATUS_OPTS.index(v) if v in PROFILE_STATUS_OPTS else 0
        return st.selectbox(label, PROFILE_STATUS_OPTS, index=idx, key=key)
    if label == "Pipeline_Status":
        v = default or ""; idx = PIPELINE_STATUS_OPTS.index(v) if v in PIPELINE_STATUS_OPTS else 0
        return st.selectbox(label, PIPELINE_STATUS_OPTS, index=idx, key=key)
    if label == "Job_Status":
        v = default or ""; idx = JOB_STATUS_OPTS.index(v) if v in JOB_STATUS_OPTS else 0
        return st.selectbox(label, JOB_STATUS_OPTS, index=idx, key=key)
    if label == "Submission_Tax_Terms":
        v = default or ""; idx = TAX_OPTS.index(v) if v in TAX_OPTS else 0
        return st.selectbox(label, TAX_OPTS, index=idx, key=key)
    if label == "Work_Authorization":
        v = default or ""; idx = WA_OPTS.index(v) if v in WA_OPTS else 0
        return st.selectbox(label, WA_OPTS, index=idx, key=key)
    if label in FLOAT_FIELDS:
        return st.number_input(label, value=float(default or 0), step=1.0, format="%.2f", key=key)
    if label in INT_FIELDS:
        return st.number_input(label, value=int(default or 0), step=1, key=key)
    return st.text_input(label, value=str(default or ""), key=key)

# ─── Session state ─────────────────────────────────────────────────────────────
if "preview_df"    not in st.session_state: st.session_state.preview_df    = None
if "preview_total" not in st.session_state: st.session_state.preview_total = 0

# ─── Backend health check ──────────────────────────────────────────────────────
try:
    hc = requests.get(f"{API_BASE}/", timeout=3)
    backend_ok = hc.status_code == 200
except Exception:
    backend_ok = False

# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📋 CIEPAL")
    st.markdown("<p style='color:#7c8fa6;font-size:.76rem;margin-top:-10px'>Submission Report Manager</p>",
                unsafe_allow_html=True)

    if backend_ok:
        st.markdown("<p style='font-size:.7rem;color:#48bb78'>● Backend online</p>", unsafe_allow_html=True)
    else:
        st.markdown("<p style='font-size:.7rem;color:#f56565'>● Backend offline — run uvicorn</p>", unsafe_allow_html=True)

    st.divider()
    page = st.radio("", ["Dashboard","Create Submission","Edit / Delete","Download Report"],
                    label_visibility="collapsed")

    st.divider()
    # Simple one-click import — no token/URL fields needed
    st.markdown("<div class='sh'>CIEPAL Sync</div>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:.7rem;color:#7c8fa6'>Endpoint & token are pre-configured.</p>",
                unsafe_allow_html=True)

    if st.button("🔄  Import from CIEPAL", use_container_width=True, disabled=not backend_ok):
        with st.spinner("Importing from CIEPAL…"):
            try:
                res = api("get", "/ciepal/import").json()
                ok(f"✅ Imported **{res['imported']}** rows. "
                   f"{res['skipped_duplicates']} duplicates skipped. "
                   f"Total in store: **{res['total_in_store']}**")
                time.sleep(0.6)
                st.rerun()
            except RuntimeError as e:
                err(str(e))


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "Dashboard":
    st.markdown("# Submission Dashboard")

    try:
        stats = api("get", "/submissions/summary/stats").json()
        rows  = api("get", "/submissions").json()
    except Exception as e:
        st.error(str(e)); st.stop()

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Total Submissions",  stats.get("total", 0))
    c2.metric("Avg Bill Rate",      f"${stats.get('avg_bill_rate', 0):,.0f}")
    c3.metric("Max Bill Rate",      f"${stats.get('max_bill_rate', 0):,.0f}")
    c4.metric("Profile Statuses",   len(stats.get("by_profile_status", {})))
    c5.metric("Pipeline Stages",    len(stats.get("by_pipeline_status", {})))

    st.divider()

    if rows:
        df = pd.DataFrame(rows)

        st.markdown("<div class='sh'>Filters</div>", unsafe_allow_html=True)
        fc1, fc2, fc3 = st.columns(3)
        def filter_opts(col):
            return ["All"] + sorted(df[col].dropna().unique().tolist()) if col in df else ["All"]

        filt_ps  = fc1.selectbox("Profile Status",  filter_opts("Profile_Status"))
        filt_pip = fc2.selectbox("Pipeline Status", filter_opts("Pipeline_Status"))
        filt_js  = fc3.selectbox("Job Status",      filter_opts("Job_Status"))

        if filt_ps  != "All": df = df[df["Profile_Status"]  == filt_ps]
        if filt_pip != "All": df = df[df["Pipeline_Status"] == filt_pip]
        if filt_js  != "All": df = df[df["Job_Status"]      == filt_js]

        st.divider()
        SHOW = [c for c in ["Sub_ID","Applicant_ID","Job_Code","End_Client","Profile_Status",
                             "Pipeline_Status","Job_Status","Submission_Bill_Rate",
                             "Submission_Pay_Rate","Work_Authorization","Submission_Tax_Terms",
                             "Recruiter_Team_Name","Submitted_On","Applicant_Status"]
                if c in df.columns]
        st.markdown(f"<div class='sh'>Submissions ({len(df)} rows)</div>", unsafe_allow_html=True)
        st.dataframe(df[SHOW], use_container_width=True, hide_index=True)

        st.divider()
        ch1, ch2, ch3 = st.columns(3)
        for col, title, key in [
            (ch1, "Profile Status",  "by_profile_status"),
            (ch2, "Pipeline Status", "by_pipeline_status"),
            (ch3, "Work Auth",       "by_work_auth"),
        ]:
            d = stats.get(key, {})
            if d:
                col.markdown(f"<div class='sh'>{title}</div>", unsafe_allow_html=True)
                col.bar_chart(pd.DataFrame(list(d.items()), columns=["Label","Count"]).set_index("Label"))
    else:
        st.info("No submissions yet. Click **🔄 Import from CIEPAL** in the sidebar to load data.")


# ══════════════════════════════════════════════════════════════════════════════
# CREATE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Create Submission":
    st.markdown("# Create Submission")
    st.caption("All CIEPAL fields. Only Sub_ID is required.")

    with st.form("create_form", clear_on_submit=True):
        form_data = {}
        for group, fields in GROUPS.items():
            st.markdown(f"<div class='sh'>{group}</div>", unsafe_allow_html=True)
            cols = st.columns(3)
            for i, field in enumerate(fields):
                with cols[i % 3]:
                    form_data[field] = field_input(field, key=f"c_{field}")
            st.markdown("")
        submitted = st.form_submit_button("➕  Create Submission", use_container_width=True)

    if submitted:
        if not form_data.get("Sub_ID","").strip():
            err("Sub_ID is required.")
        else:
            payload = {k: v for k, v in form_data.items() if v not in (None,"",0,0.0)}
            try:
                rec = api("post", "/submissions", json=payload).json()
                ok(f"Submission <b>{rec['Sub_ID']}</b> created.")
            except RuntimeError as e:
                err(str(e))


# ══════════════════════════════════════════════════════════════════════════════
# EDIT / DELETE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Edit / Delete":
    st.markdown("# Edit / Delete Submission")
    rows = api("get", "/submissions").json()

    if not rows:
        st.info("No submissions in store. Click **🔄 Import from CIEPAL** in the sidebar first.")
    else:
        opts = {f"{r.get('Sub_ID','?')} — {r.get('End_Client','') or r.get('Job_Code','?')}": r["Sub_ID"]
                for r in rows if r.get("Sub_ID")}
        chosen = st.selectbox("Select Submission", list(opts.keys()))
        sub_id = opts[chosen]
        rec    = api("get", f"/submissions/{sub_id}").json()

        st.divider()
        tab_e, tab_d = st.tabs(["✏️  Edit", "🗑️  Delete"])

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

                if st.form_submit_button("💾  Save Changes", use_container_width=True):
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
            if st.button("🗑️  Delete Submission", type="primary", use_container_width=True):
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
    st.markdown("# Download CIEPAL Report")
    st.markdown("<div class='sh'>Live from atsbi.ceipal.com</div>", unsafe_allow_html=True)

    c1, c2 = st.columns([2,2])
    fmt   = c1.radio("Format", ["CSV","JSON"], horizontal=True)
    limit = c2.number_input("Preview rows", 5, 500, 50, 10)

    st.divider()
    left, right = st.columns([3,1])

    with left:
        st.markdown("<div class='sh'>Live Preview</div>", unsafe_allow_html=True)
        if st.button("🔍  Load Preview", use_container_width=True):
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
            "<p style='font-size:.68rem;color:#7c8fa6;word-break:break-all;margin-bottom:14px'>"
            "atsbi.ceipal.com/api/report-details/get-report-data/W4DKw9QX…</p>",
            unsafe_allow_html=True,
        )

        st.markdown("<div class='dl-btn'>", unsafe_allow_html=True)
        if st.button(f"⬇️  Download {fmt}", use_container_width=True):
            with st.spinner(f"Downloading {fmt}…"):
                try:
                    resp = api("get", "/ciepal/report", params={"format": fmt.lower()})
                    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
                    ext  = fmt.lower()
                    mime = "text/csv" if fmt == "CSV" else "application/json"
                    st.download_button(
                        label=f"📥  Save ciepal_{ts}.{ext}",
                        data=resp.content,
                        file_name=f"ciepal_{ts}.{ext}",
                        mime=mime,
                        use_container_width=True,
                    )
                    ok(f"Ready — {len(resp.content):,} bytes.")
                except RuntimeError as e:
                    err(str(e))
        st.markdown("</div>", unsafe_allow_html=True)