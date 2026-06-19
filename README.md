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
│    (app.py)     │ ◄───────────── │ (ciepal_service) │ ◄───────────── │   report API│
│  localhost:8501 │   JSON         │  localhost:8000  │   JSON         │             │
└─────────────────┘                └──────────────────┘                └─────────────┘
```

| File | Role |
| --- | --- |
| `app.py` | Streamlit frontend — dashboard, create/edit/delete forms, report download. |
| `ciepal_service.py` | FastAPI service — CRUD endpoints, CEIPAL proxy, CSV/JSON export. |
| `models.py` | Pydantic schemas (`SubmissionCreate`, `SubmissionUpdate`) shared by the backend. |
| `requirements.txt` | Python dependencies (pip). |
| `pyproject.toml` | Python dependencies (uv / modern tooling) — same set as `requirements.txt`. |

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
```

Dependencies are declared in **both** `requirements.txt` (for pip) and `pyproject.toml` (for [uv](https://docs.astral.sh/uv/) and other modern tooling). They list the same packages — use whichever workflow you prefer.

**Option A — uv (recommended):**

```bash
# creates the virtual environment and installs everything into it
uv sync
```

`uv sync` reads `pyproject.toml`, builds a `.venv`, and installs the dependencies there — so the packages always land in the environment uv runs commands against. Prefix run commands with `uv run` (shown below), or activate `.venv` manually.

**Option B — pip + virtualenv:**

```bash
# create and activate a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# install dependencies
pip install -r requirements.txt
```

> **Tip (Windows / uv users):** if `pip install` reports packages as "already satisfied" but the app then can't find them, your `pip` and your run command are pointing at different Python installs. Install into the venv explicitly with `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`, or just use `uv sync` (Option A), which avoids the problem entirely.

Then set up credentials (see [Configuration](#configuration)):

```bash
cp .env.example .env
# then edit .env and fill in your CEIPAL URLs and tokens
```

### Running

The two services run in separate terminals. If you installed with **uv**, prefix each command with `uv run` (e.g. `uv run uvicorn ...`); if you activated a venv with pip, run the commands as-is.

**Terminal 1 — backend:**

```bash
uvicorn ciepal_service:app --reload --port 8000
```

Interactive API docs are then available at http://localhost:8000/docs.

**Terminal 2 — frontend:**

```bash
streamlit run app.py
```

The dashboard opens at http://localhost:8501. A status pill in the top bar shows whether the backend is reachable. Click **Import from CEIPAL** to load data.

## Configuration

Credentials and the frontend's backend URL live in a `.env` file (loaded automatically at startup). Copy the template and fill in your values:

```bash
cp .env.example .env
```

The app supports multiple CEIPAL data sources. Each needs a `_URL` and a `_TOKEN`:

```bash
TEKNINJAS_URL=https://atsbi.ceipal.com/api/report-details/get-report-data/...
TEKNINJAS_TOKEN=...

MEDNINJAS_URL=https://atsbi.ceipal.com/api/report-details/get-report-data/...
MEDNINJAS_TOKEN=...

API_BASE=http://localhost:8000
```

In the UI, a **Data source** selector (Tekninjas / MedNinjas) appears below the top navigation. The chosen source drives the dashboard metrics, the live preview, and the report download — so you can switch between accounts without editing any code. Downloaded files are named with the source (e.g. `medninjas_report_<timestamp>.csv`).

To add another source: add `<NAME>_URL` and `<NAME>_TOKEN` to `.env`, then add a matching entry to the `SOURCES` dict near the top of `ciepal_service.py`. Only sources with both a URL and token configured appear in the selector.

> **Security note:** `.env` is git-ignored so secrets stay out of version control. If a token was ever committed previously, rotate it.

## Using the app

A **Data source** selector (Tekninjas / MedNinjas) sits below the top navigation and applies across the app. The UI has two sections:

- **Dashboard** — live metrics for the selected source (total submissions, submitted to client, placements), optional filters, a column picker for the table, and a chart builder. The table and charts start empty so you choose exactly what to view.
- **Download Report** — preview the live CEIPAL report for the selected source and download it as CSV or JSON.

The top bar also has an **Import from CEIPAL** button (loads the selected source's rows into the local store) and a status pill showing whether the backend is reachable.

## API reference

All endpoints are served by the FastAPI backend on port 8000.

### Submissions (read-only local store)

| Method | Path | Description |
| --- | --- | --- |
| GET | `/submissions` | List submissions in the local store; supports `profile_status`, `pipeline_status`, `job_status`, and `recruiter_team` query filters. |
| GET | `/submissions/{sub_id}` | Fetch a single submission by ID. |
| GET | `/submissions/summary/stats` | Aggregate stats over the local store. |
| GET | `/sources` | List the configured CEIPAL data sources (name, label, whether credentials are present). |

### CEIPAL proxy

All proxy endpoints accept an optional `source` query param (`tekninjas` or `medninjas`); it defaults to `tekninjas`.

| Method | Path | Description |
| --- | --- | --- |
| GET | `/ciepal/import` | Pull CEIPAL rows into the local store (skips duplicates by `Sub_ID`). |
| GET | `/ciepal/preview` | Return the first `limit` rows from CEIPAL (default 50, max 500). |
| GET | `/ciepal/stats` | Live dashboard metrics — total, submitted-to-client, and placements — computed from the selected source. |
| GET | `/ciepal/report` | Download the full CEIPAL report; `format=csv` or `format=json`. |
| GET | `/ciepal/raw` | Debug endpoint — returns CEIPAL's unmodified response envelope and its top-level keys. |
| GET | `/` | Service info and endpoint index. |

## Project status & notes

- Submission storage is in-memory and resets on backend restart.
- The CEIPAL field mapping assumes columns arrive in a known order; if an import shows values under the wrong headers, use `/ciepal/raw` to inspect the real response shape.
- This is an internal tooling project; review the security note above before deploying anywhere shared.