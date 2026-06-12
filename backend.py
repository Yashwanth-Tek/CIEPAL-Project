"""
backend.py — FastAPI CRUD + CIEPAL proxy
Run: uvicorn backend:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import csv, io, json, uuid, os
from datetime import datetime
import requests as ext_requests

app = FastAPI(title="CIEPAL Submission Report API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── CIEPAL Config (hardcoded — no env vars needed) ────────────────────────────
CIEPAL_URL   = "https://atsbi.ceipal.com/api/report-details/get-report-data/W4DKw9QXpzus8xvoxmX2Gq_BkoWnE6CR1LCTLCEwZsw?response_type=1"
CIEPAL_TOKEN = "Ied0oOCTsUzHnmmmSp6hYa/gCgCpzkRr/yTvtZsXcapXHZqJbfHYofOrBqAE7nuShk1YhRqCImStOA3nbnigUJU+XpJsYJ6LV/pwmU7QFm8rrO10QDN6xakU0N4VHWG+AM8qKJH6BCrjd8sVp0RnhIjUOn6eBaf7zQyuT+/2pXcZe32HhlEQKiC1/ClpWv1irSOGdUdnqlHsH5Ezth/pQefMFAEFOavUq9LiW3pqa39fwl/3ql3Pm4LcF2XeQN9oHF9tIptymO08GMWRxHP83Tzvqt+F9Ec8Hv9uyNW2bHDKb8ZepRmDxzaigmMbHHVZ9CfkFTY4IyJ270yB9tJ/yA=="

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

# ─── Schemas ───────────────────────────────────────────────────────────────────
class SubmissionCreate(BaseModel):
    Sub_ID:                             str
    Applicant_ID:                       Optional[str] = None
    Client_Job_ID:                      Optional[str] = None
    Job_Code:                           Optional[str] = None
    Job_Type:                           Optional[str] = None
    Job_Status:                         Optional[str] = None
    Job_Location:                       Optional[str] = None
    States:                             Optional[str] = None
    Number_of_Positions:                Optional[int] = None
    Max_Number_of_Submissions:          Optional[int] = None
    Priority:                           Optional[str] = None
    Client_Category:                    Optional[str] = None
    Email_Address:                      Optional[str] = None
    Applicant_Location:                 Optional[str] = None
    Applicant_Current_Employer:         Optional[str] = None
    Current_Company:                    Optional[str] = None
    Experience:                         Optional[str] = None
    Work_Authorization:                 Optional[str] = None
    Linkedin_URL:                       Optional[str] = None
    Source:                             Optional[str] = None
    Submission_Source:                  Optional[str] = None
    Ownership:                          Optional[str] = None
    Submission_Bill_Rate:               Optional[float] = None
    Submission_Pay_Rate:                Optional[float] = None
    Submission_Tax_Terms:               Optional[str] = None
    Job_Client_Bill_Rate:               Optional[float] = None
    Profile_Status:                     Optional[str] = None
    Pipeline_Status:                    Optional[str] = None
    Applicant_Status:                   Optional[str] = None
    Submission_Rating:                  Optional[str] = None
    Number_of_Interviews:               Optional[int] = None
    Client_Manager:                     Optional[str] = None
    MSP:                                Optional[str] = None
    End_Client:                         Optional[str] = None
    Recruiter_Team_Name:                Optional[str] = None
    Assigned_To_Email_ID:               Optional[str] = None
    Sales_Manager:                      Optional[str] = None
    Submitted_By_Email_ID:              Optional[str] = None
    Status_Changed_By:                  Optional[str] = None
    Applicant_Created_By:               Optional[str] = None
    Account_Manager:                    Optional[str] = None
    Recruitment_Manager:                Optional[str] = None
    Job_Created_By:                     Optional[str] = None
    Job_Applied:                        Optional[str] = None
    Client_Interview_Scheduled_Date:    Optional[str] = None
    Job_Created_On:                     Optional[str] = None
    Applicant_Created_On:               Optional[str] = None
    Submitted_On:                       Optional[str] = None
    Status_Changed_On:                  Optional[str] = None
    Modified_On:                        Optional[str] = None
    Client_Rejection_On:                Optional[str] = None
    RowAdded:                           Optional[str] = None


class SubmissionUpdate(BaseModel):
    Job_Code:                           Optional[str] = None
    Job_Type:                           Optional[str] = None
    Job_Status:                         Optional[str] = None
    Job_Location:                       Optional[str] = None
    States:                             Optional[str] = None
    Number_of_Positions:                Optional[int] = None
    Max_Number_of_Submissions:          Optional[int] = None
    Priority:                           Optional[str] = None
    Client_Category:                    Optional[str] = None
    Email_Address:                      Optional[str] = None
    Applicant_Location:                 Optional[str] = None
    Applicant_Current_Employer:         Optional[str] = None
    Current_Company:                    Optional[str] = None
    Experience:                         Optional[str] = None
    Work_Authorization:                 Optional[str] = None
    Linkedin_URL:                       Optional[str] = None
    Source:                             Optional[str] = None
    Submission_Source:                  Optional[str] = None
    Ownership:                          Optional[str] = None
    Submission_Bill_Rate:               Optional[float] = None
    Submission_Pay_Rate:                Optional[float] = None
    Submission_Tax_Terms:               Optional[str] = None
    Job_Client_Bill_Rate:               Optional[float] = None
    Profile_Status:                     Optional[str] = None
    Pipeline_Status:                    Optional[str] = None
    Applicant_Status:                   Optional[str] = None
    Submission_Rating:                  Optional[str] = None
    Number_of_Interviews:               Optional[int] = None
    Client_Manager:                     Optional[str] = None
    MSP:                                Optional[str] = None
    End_Client:                         Optional[str] = None
    Recruiter_Team_Name:                Optional[str] = None
    Assigned_To_Email_ID:               Optional[str] = None
    Sales_Manager:                      Optional[str] = None
    Submitted_By_Email_ID:              Optional[str] = None
    Status_Changed_By:                  Optional[str] = None
    Applicant_Created_By:               Optional[str] = None
    Account_Manager:                    Optional[str] = None
    Recruitment_Manager:                Optional[str] = None
    Job_Created_By:                     Optional[str] = None
    Client_Interview_Scheduled_Date:    Optional[str] = None
    Client_Rejection_On:                Optional[str] = None
    Applicant_Created_On:               Optional[str] = None
    Submitted_On:                       Optional[str] = None
    Status_Changed_On:                  Optional[str] = None
    Modified_On:                        Optional[str] = None


# ─── CRUD ──────────────────────────────────────────────────────────────────────
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


@app.post("/submissions", status_code=201)
def create_submission(body: SubmissionCreate):
    key = body.Sub_ID or str(uuid.uuid4())[:8]
    if key in submissions:
        raise HTTPException(409, f"Sub_ID {key} already exists")
    now = datetime.now().isoformat()
    rec = body.model_dump()
    rec["_local_id"] = key
    rec["_created_at"] = now
    rec["_updated_at"] = now
    submissions[key] = rec
    return rec


@app.put("/submissions/{sub_id}")
def update_submission(sub_id: str, body: SubmissionUpdate):
    if sub_id not in submissions:
        raise HTTPException(404, "Submission not found")
    rec = submissions[sub_id]
    rec.update({k: v for k, v in body.model_dump(exclude_none=True).items()})
    rec["_updated_at"] = datetime.now().isoformat()
    submissions[sub_id] = rec
    return rec


@app.delete("/submissions/{sub_id}")
def delete_submission(sub_id: str):
    if sub_id not in submissions:
        raise HTTPException(404, "Submission not found")
    del submissions[sub_id]
    return {"message": f"Submission {sub_id} deleted"}


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

def _fetch_ciepal() -> list:
    """Call CIEPAL directly using hardcoded URL and token."""
    headers = {
        "Authorization": f"Bearer {CIEPAL_TOKEN}",
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }
    try:
        resp = ext_requests.get(CIEPAL_URL, headers=headers, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
    except ext_requests.exceptions.HTTPError:
        raise HTTPException(
            resp.status_code,
            f"CIEPAL returned {resp.status_code}: {resp.text[:300]}"
        )
    except Exception as e:
        raise HTTPException(502, f"Cannot reach CIEPAL: {e}")

    # Unwrap common wrapper keys
    rows = payload
    for key in ("data", "result", "records", "report", "rows", "submissions"):
        if isinstance(payload, dict) and key in payload:
            rows = payload[key]
            break
    return rows if isinstance(rows, list) else [rows]


@app.get("/ciepal/preview")
def preview_ciepal(limit: int = Query(50, le=500)):
    rows = _fetch_ciepal()
    return {"rows": rows[:limit], "total": len(rows)}


@app.get("/ciepal/report")
def download_ciepal_report(format: str = Query("csv", enum=["csv", "json"])):
    rows = _fetch_ciepal()
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")

    if format == "json":
        content = json.dumps(rows, indent=2, default=str)
        return StreamingResponse(
            io.BytesIO(content.encode()), media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=ciepal_report_{ts}.json"},
        )

    keys = CIEPAL_FIELDS if (rows and isinstance(rows[0], dict) and "Sub_ID" in rows[0]) \
           else (list(rows[0].keys()) if rows and isinstance(rows[0], dict) else CIEPAL_FIELDS)

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=keys, extrasaction="ignore", restval="")
    writer.writeheader()
    writer.writerows(rows)

    return StreamingResponse(
        io.BytesIO(buf.getvalue().encode()), media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=ciepal_report_{ts}.csv"},
    )


@app.get("/ciepal/import")
def import_from_ciepal():
    """Pull CIEPAL data into the local in-memory store."""
    rows  = _fetch_ciepal()
    added, skipped = 0, 0
    now   = datetime.now().isoformat()
    for row in rows:
        key = str(row.get("Sub_ID", uuid.uuid4()))
        if key in submissions:
            skipped += 1
            continue
        row["_local_id"]   = key
        row["_created_at"] = now
        row["_updated_at"] = now
        submissions[key]   = row
        added += 1
    return {"imported": added, "skipped_duplicates": skipped, "total_in_store": len(submissions)}