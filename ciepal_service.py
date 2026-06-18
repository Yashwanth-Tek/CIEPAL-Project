"""
ciepal_service.py — FastAPI read endpoints + CIEPAL proxy
Run: uvicorn ciepal_service:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import csv, io, json, uuid, os
from datetime import datetime
import requests as ext_requests
from dotenv import load_dotenv

load_dotenv()  # read .env into environment (no-op if the file is absent)

app = FastAPI(title="CIEPAL Submission Report API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── CIEPAL sources (credentials loaded from .env) ─────────────────────────────
# Each source has a URL + bearer token. The UI lists these and the user picks one;
# the chosen source name is passed as the `source` query param on CIEPAL calls.
# To add a source: add <NAME>_URL and <NAME>_TOKEN to .env and a line here.
SOURCES: dict[str, dict] = {
    "tekninjas": {
        "label": "Tekninjas",
        "url":   os.getenv("TEKNINJAS_URL", ""),
        "token": os.getenv("TEKNINJAS_TOKEN", ""),
    },
    "medninjas": {
        "label": "MedNinjas",
        "url":   os.getenv("MEDNINJAS_URL", ""),
        "token": os.getenv("MEDNINJAS_TOKEN", ""),
    },
}

DEFAULT_SOURCE = "tekninjas"


def _resolve_source(source: Optional[str]) -> dict:
    """Validate a source name and return its config, with clear errors."""
    name = (source or DEFAULT_SOURCE).lower()
    cfg = SOURCES.get(name)
    if not cfg:
        raise HTTPException(
            400, f"Unknown source '{source}'. Available: {', '.join(SOURCES)}"
        )
    if not cfg.get("url") or not cfg.get("token"):
        raise HTTPException(
            500,
            f"Source '{name}' is missing its URL or token. "
            f"Set {name.upper()}_URL and {name.upper()}_TOKEN in your .env file."
        )
    return cfg

# ─── In-memory store ───────────────────────────────────────────────────────────
submissions: dict[str, dict] = {}

# ─── Root ──────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "message": "CIEPAL Submission Report API",
        "version": "3.0.0",
        "docs": "/docs",
        "endpoints": {
            "submissions":       "/submissions",
            "ciepal_preview":    "/ciepal/preview",
            "ciepal_report":     "/ciepal/report",
            "ciepal_import":     "/ciepal/import",
            "stats":             "/submissions/summary/stats",
        }
    }


@app.get("/sources")
def list_sources():
    """List the CIEPAL sources the UI can choose from. Only sources that have
    both a URL and token configured are returned as `configured: true`."""
    return {
        "sources": [
            {
                "name":       name,
                "label":      cfg["label"],
                "configured": bool(cfg.get("url") and cfg.get("token")),
            }
            for name, cfg in SOURCES.items()
        ],
        "default": DEFAULT_SOURCE,
    }

# ─── Read endpoints ─────────────────────────────────────────────────────────────
@app.get("/submissions", response_model=List[dict])
def list_submissions(
    profile_status: Optional[str] = None,
    pipeline_status: Optional[str] = None,
    job_status: Optional[str] = None,
    recruiter_team: Optional[str] = None,
):
    rows = list(submissions.values())
    if profile_status:
        rows = [r for r in rows if r.get("Profile_Status","").lower() == profile_status.lower()]
    if pipeline_status:
        rows = [r for r in rows if r.get("Pipeline_Status","").lower() == pipeline_status.lower()]
    if job_status:
        rows = [r for r in rows if r.get("Job_Status","").lower() == job_status.lower()]
    if recruiter_team:
        rows = [r for r in rows if r.get("Recruiter_Team_Name","").lower() == recruiter_team.lower()]
    return rows


@app.get("/submissions/summary/stats")
def submission_stats():
    rows = list(submissions.values())
    if not rows:
        return {"total": 0, "by_profile_status": {}, "by_pipeline_status": {},
                "by_job_status": {}, "by_work_auth": {}, "by_tax_terms": {},
                "by_source": {}, "avg_bill_rate": 0, "max_bill_rate": 0}

    def freq(field):
        out: dict = {}
        for r in rows:
            v = r.get(field) or "Unknown"
            out[v] = out.get(v, 0) + 1
        return out

    rates = [r["Submission_Bill_Rate"] for r in rows if r.get("Submission_Bill_Rate")]
    return {
        "total":             len(rows),
        "by_profile_status": freq("Profile_Status"),
        "by_pipeline_status":freq("Pipeline_Status"),
        "by_job_status":     freq("Job_Status"),
        "by_work_auth":      freq("Work_Authorization"),
        "by_tax_terms":      freq("Submission_Tax_Terms"),
        "by_source":         freq("Source"),
        "avg_bill_rate":     round(sum(rates)/len(rates), 2) if rates else 0,
        "max_bill_rate":     max(rates) if rates else 0,
    }


@app.get("/submissions/{sub_id}", response_model=dict)
def get_submission(sub_id: str):
    if sub_id not in submissions:
        raise HTTPException(404, "Submission not found")
    return submissions[sub_id]


# ─── CIEPAL proxy — uses hardcoded URL + token, NO query params ────────────────
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

def _normalize_ciepal_rows(rows: list) -> list:
    """CEIPAL may return rows as named dicts, numeric-keyed dicts, or bare arrays.
    Map them all to {field_name: value} dicts using CIEPAL_FIELDS positional order,
    so fields like Pipeline_Status can be read by name."""
    out = []
    for r in rows or []:
        if isinstance(r, dict):
            if r and all(str(k).isdigit() for k in r.keys()):      # numeric-keyed -> positional
                vals = [r[k] for k in sorted(r.keys(), key=lambda x: int(x))]
                rec = {CIEPAL_FIELDS[i]: v for i, v in enumerate(vals) if i < len(CIEPAL_FIELDS)}
            else:
                rec = dict(r)
            out.append(rec)
        elif isinstance(r, (list, tuple)):                          # bare array -> positional
            out.append({CIEPAL_FIELDS[i]: v for i, v in enumerate(r) if i < len(CIEPAL_FIELDS)})
    return out


def _fetch_ciepal(source: Optional[str] = None) -> list:
    """Call CIEPAL for the given source, using that source's URL and token."""
    cfg = _resolve_source(source)
    headers = {
        "Authorization": f"Bearer {cfg['token']}",
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }
    try:
        resp = ext_requests.get(cfg["url"], headers=headers, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
    except ext_requests.exceptions.HTTPError:
        raise HTTPException(
            resp.status_code,
            f"CIEPAL returned {resp.status_code}: {resp.text[:300]}"
        )
    except Exception as e:
        raise HTTPException(502, f"Cannot reach CIEPAL: {e}")

    # CEIPAL wraps its response like:
    #   {"success": 0/1, "message": "...", "data": {"aaData": [...], "iTotalRecords": N, ...}}
    # The actual rows live at data -> aaData. We dig down to find them, and we
    # surface CEIPAL's own message when it reports no data / an error.
    if isinstance(payload, dict):
        inner = payload.get("data", payload)

        # If CEIPAL explicitly signals failure or "Records Not Found", report it clearly.
        if payload.get("success") in (0, "0", False) or payload.get("message") == "Records Not Found":
            msg = payload.get("message", "CEIPAL returned no data")
            total = inner.get("iTotalRecords") if isinstance(inner, dict) else None
            raise HTTPException(404, f"CEIPAL: {msg} (iTotalRecords={total})")

        # Normal case: pull the DataTables row array from the nested envelope.
        if isinstance(inner, dict):
            for key in ("aaData", "data", "result", "records", "report", "rows", "submissions"):
                if key in inner and isinstance(inner[key], list):
                    return inner[key]
        # Fallback: maybe rows sit at the top level under one of these keys.
        for key in ("aaData", "data", "result", "records", "report", "rows", "submissions"):
            if isinstance(payload.get(key), list):
                return payload[key]

    return payload if isinstance(payload, list) else [payload]


@app.get("/ciepal/preview")
def preview_ciepal(limit: int = Query(50, le=500), source: Optional[str] = None):
    rows = _fetch_ciepal(source)
    return {"rows": rows[:limit], "total": len(rows), "source": (source or DEFAULT_SOURCE).lower()}


@app.get("/ciepal/stats")
def ciepal_stats(source: Optional[str] = None):
    """Dashboard metrics computed from the LIVE CIEPAL feed (same source as the
    report), so the totals always match what CIEPAL actually returns.

    - total              : every submission CIEPAL returns
    - submitted_to_client: rows whose pipeline status indicates a client submission
    - placements         : rows whose pipeline status indicates a placement

    Status wording varies between CEIPAL configurations, so matching is done by
    keyword rather than an exact string. The distinct values actually seen are
    returned under `pipeline_values` so the thresholds can be tuned to your data.
    """
    rows = _normalize_ciepal_rows(_fetch_ciepal(source))

    SUBMITTED_KEYS = ("submit", "submiss")    # "Submitted to Client", "Submitted", "Client Submission"
    PLACEMENT_KEYS = ("place", "joined", "offer accepted")  # "Placed", "Placement"

    submitted = placements = 0
    seen: dict = {}
    for r in rows:
        status = str(r.get("Pipeline_Status") or "").strip()
        seen[status or "(blank)"] = seen.get(status or "(blank)", 0) + 1
        low = status.lower()
        if any(k in low for k in PLACEMENT_KEYS):
            placements += 1
        elif any(k in low for k in SUBMITTED_KEYS):
            submitted += 1

    return {
        "total":               len(rows),
        "submitted_to_client": submitted,
        "placements":          placements,
        "pipeline_values":     seen,   # distinct Pipeline_Status values + counts, for tuning
        "source":              (source or DEFAULT_SOURCE).lower(),
    }


@app.get("/ciepal/raw")
def raw_ciepal(source: Optional[str] = None):
    """Debug: return CEIPAL's unmodified response envelope and its top-level keys,
    so you can see exactly what the API is sending (e.g. aaData contents,
    iTotalRecords, error messages)."""
    cfg = _resolve_source(source)
    headers = {
        "Authorization": f"Bearer {cfg['token']}",
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }
    resp = ext_requests.get(cfg["url"], headers=headers, timeout=30)
    try:
        payload = resp.json()
    except Exception:
        return {"status_code": resp.status_code, "text": resp.text[:2000]}
    return {
        "status_code": resp.status_code,
        "top_level_keys": list(payload.keys()) if isinstance(payload, dict) else "(not a dict)",
        "aaData_length": len(payload["aaData"]) if isinstance(payload, dict) and isinstance(payload.get("aaData"), list) else None,
        "payload": payload,
    }


@app.get("/ciepal/report")
def download_ciepal_report(format: str = Query("csv", enum=["csv", "json"]),
                           source: Optional[str] = None):
    # Normalize so positional/numeric-keyed CEIPAL rows become named-field dicts
    # (otherwise CSV headers come out as 0,1,2,... instead of Sub_ID, Job_Code, ...).
    rows = _normalize_ciepal_rows(_fetch_ciepal(source))
    src  = (source or DEFAULT_SOURCE).lower()
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")

    if format == "json":
        content = json.dumps(rows, indent=2, default=str)
        return StreamingResponse(
            io.BytesIO(content.encode()), media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={src}_report_{ts}.json"},
        )

    keys = CIEPAL_FIELDS if (rows and isinstance(rows[0], dict) and "Sub_ID" in rows[0]) \
           else (list(rows[0].keys()) if rows and isinstance(rows[0], dict) else CIEPAL_FIELDS)

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=keys, extrasaction="ignore", restval="")
    writer.writeheader()
    writer.writerows(rows)

    return StreamingResponse(
        io.BytesIO(buf.getvalue().encode()), media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={src}_report_{ts}.csv"},
    )


@app.get("/ciepal/import")
def import_from_ciepal(source: Optional[str] = None):
    """Pull CIEPAL data into the local in-memory store."""
    rows  = _normalize_ciepal_rows(_fetch_ciepal(source))
    added, skipped = 0, 0
    now   = datetime.now().isoformat()
    for row in rows:
        # Use Sub_ID when present and non-empty; otherwise mint a stable id so
        # rows with blank Sub_ID don't all collide on the same "" key.
        sub_id = str(row.get("Sub_ID") or "").strip()
        key = sub_id or str(uuid.uuid4())[:8]
        if key in submissions:
            skipped += 1
            continue
        row["_local_id"]   = key
        row["_created_at"] = now
        row["_updated_at"] = now
        submissions[key]   = row
        added += 1
    return {"imported": added, "skipped_duplicates": skipped, "total_in_store": len(submissions)}