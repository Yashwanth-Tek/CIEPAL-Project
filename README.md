# CIEPAL Submission Report Manager

A full-stack tool for pulling recruitment submission data out of CEIPAL ATS, browsing and editing it locally, and exporting it as CSV or JSON. It pairs a FastAPI backend that proxies the CEIPAL report API with a Streamlit dashboard for viewing, filtering, and managing records.

## What it does

- **One-click import** from CEIPAL into a local in-memory store.
- **Full CRUD** over submissions — create, read, update, and delete records through the UI or the API.
- **Interactive dashboard** with summary metrics, a column picker (choose which fields to show), and a chart builder (bar, horizontal bar, pie, donut, line) that reads whatever columns the data actually contains.
- **Live preview & export** of the raw CEIPAL report as CSV or JSON.
- **Resilient data handling** — normalizes CEIPAL's response whether rows arrive as named objects or positional arrays, so the table and charts populate correctly.

## Architecture

The project is two services that talk over HTTP on localhost:

```
┌─────────────────┐      HTTP      ┌──────────────────┐      HTTPS     ┌─────────────┐
│   Streamlit UI  │ ─────────────► │  FastAPI backend │ ─────────────► │  CEIPAL ATS │
│    (app.py)     │ ◄───────────── │   (backend.py)   │ ◄───────────── │   report API│
│  localhost:8501 │   JSON         │  localhost:8000  │   JSON         │             │
└─────────────────┘                └──────────────────┘                └─────────────┘
```

| File | Role |
| --- | --- |
| `app.py` | Streamlit frontend — dashboard, create/edit/delete forms, report download. |
| `backend.py` | FastAPI service — CRUD endpoints, CEIPAL proxy, CSV/JSON export. |
| `models.py` | Pydantic schemas (`SubmissionCreate`, `SubmissionUpdate`) shared by the backend. |
| `requirements.txt` | Python dependencies. |

The backend keeps submissions in an in-memory dictionary, so data resets whenever the server restarts. This keeps the project dependency-free (no database to set up), but it is not meant for persistent production use as-is.

## Tech stack

- **Backend:** FastAPI, Pydantic v2, Uvicorn
- **Frontend:** Streamlit, pandas, Plotly
- **HTTP:** requests

## Getting started

### Prerequisites

- Python 3.10 or newer
- A CEIPAL report URL and bearer token (see [Configuration](#configuration))

### Installation

```bash
# clone the repo
git clone https://github.com/Yashwanth-Tek/CIEPAL-Project.git
cd CIEPAL-Project

# (recommended) create and activate a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# install dependencies
pip install -r requirements.txt
```

### Running

The two services run in separate terminals.

**Terminal 1 — backend:**

```bash
uvicorn backend:app --reload --port 8000
```

Interactive API docs are then available at http://localhost:8000/docs.

**Terminal 2 — frontend:**

```bash
streamlit run app.py
```

The dashboard opens at http://localhost:8501. A status pill in the top bar shows whether the backend is reachable. Click **Import from CEIPAL** to load data.

## Configuration

The CEIPAL endpoint and token live near the top of `backend.py`:

```python
CIEPAL_URL   = "https://atsbi.ceipal.com/api/report-details/get-report-data/..."
CIEPAL_TOKEN = "..."
```

> **Security note:** the token is currently hardcoded. For anything beyond local use, move it to an environment variable (e.g. `os.getenv("CIEPAL_TOKEN")`) and keep it out of version control. If a token has already been committed, rotate it.

## Using the app

The UI has four sections, selectable from the top navigation bar:

- **Dashboard** — summary metrics (totals, average/max bill rate, status counts), optional filters, a column picker for the table, and a chart builder. Both the table and charts start empty so you choose exactly what to view.
- **Create Submission** — a grouped form covering all submission fields; only the Submission ID is required.
- **Edit / Delete** — pick an existing record to update its fields or remove it.
- **Download Report** — preview the live CEIPAL report and download it as CSV or JSON.

## API reference

All endpoints are served by the FastAPI backend on port 8000.

### Submissions (CRUD)

| Method | Path | Description |
| --- | --- | --- |
| GET | `/submissions` | List all submissions; supports `profile_status`, `pipeline_status`, `job_status`, and `recruiter_team` query filters. |
| GET | `/submissions/{sub_id}` | Fetch a single submission by ID. |
| POST | `/submissions` | Create a submission. |
| PUT | `/submissions/{sub_id}` | Update a submission. |
| DELETE | `/submissions/{sub_id}` | Delete a submission. |
| GET | `/submissions/summary/stats` | Aggregate stats — totals, rate averages, and counts by status, work auth, tax terms, and source. |

### CEIPAL proxy

| Method | Path | Description |
| --- | --- | --- |
| GET | `/ciepal/import` | Pull CEIPAL rows into the local store (skips duplicates by `Sub_ID`). |
| GET | `/ciepal/preview` | Return the first `limit` rows from CEIPAL (default 50, max 500). |
| GET | `/ciepal/report` | Download the full CEIPAL report; `format=csv` or `format=json`. |
| GET | `/ciepal/raw` | Debug endpoint — returns CEIPAL's unmodified response envelope and its top-level keys. |
| GET | `/` | Service info and endpoint index. |

## Project status & notes

- Submission storage is in-memory and resets on backend restart.
- The CEIPAL field mapping assumes columns arrive in a known order; if an import shows values under the wrong headers, use `/ciepal/raw` to inspect the real response shape.
- This is an internal tooling project; review the security note above before deploying anywhere shared.
