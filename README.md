# AICTE Integrated Institution Complaint Monitoring & Cross-Bureau Coordination System
### Smart India Hackathon (SIH) — Problem Statement ID: 26264

An enterprise-grade, offline-capable complaint monitoring, duplicate detection, and cross-bureau coordination platform engineered for the **All India Council for Technical Education (AICTE)**.

Built with **React + Vite + TypeScript**, **Django REST Framework**, **PostgreSQL 17 + pgvector**, **Django Q2 Worker**, and local **all-MiniLM-L6-v2** neural embeddings.

---

## 🏛️ Executive Overview

AICTE oversees thousands of technical institutions across India through multiple specialized bureaus—notably the **Approval Bureau (Regional Offices / RB)** and the **Public Grievance Redressal Cell (PGRC)**. 

Prior to this system, complaints filed across distinct bureaus were siloed in isolated channels. This caused:
- **Redundant investigations**: Parallel proceedings initiated by different bureaus for the same underlying institution or incident.
- **Fragmented institution visibility**: Lack of a single institutional view showing all historical and active complaints across bureaus.
- **Accountability gaps**: Lack of formal cross-bureau action tracking, officer acknowledgment, and SLA escalation policies.

### Core Capabilities
1. **Institution Command Centre (Milestone 3)**:
   - Authoritative operational KPIs computed from permission-scoped database queries.
   - Non-overlapping ageing bands (`0–7 days`, `8–15 days`, `16–30 days`, and `>30 days`).
   - Current bureau workload tracking (ownership reflecting active transfers).
   - Traceable disposal share metric calculated over selected receipt cohorts.
   - Real-time overdue vs. approaching deadline tracking.
2. **AI-Powered Overlap & Semantic Duplicate Detection**:
   - Local CPU-optimized `all-MiniLM-L6-v2` embeddings (384-dimensional vectors).
   - Fast cosine-similarity search powered by `pgvector` indexing.
   - Human-in-the-loop candidate comparison with audit-logged determinations (`Same Incident`, `Related Issue`, `Unrelated`).
3. **Accountable Cross-Bureau Coordination**:
   - Institutional cross-bureau notices automatically triggered when an institution has active complaints in multiple bureaus.
   - Joint coordination actions with officer assignment, two-way acknowledgment, and milestone outcome logging.
4. **Strict Role-Based Access Control (RBAC)**:
   - **Coordinator**: Full multi-bureau visibility, overlap review, case transfers, coordination action assignment.
   - **Auditor**: Read-only oversight, independent verification access, complete audit log inspection.
   - **Bureau Officers (`officer_rb`, `officer_pgrc`)**: Scoped strictly to cases owned by their assigned bureau; cross-bureau actions gated.
5. **100% Offline-Capable & Sovereign**:
   - Runs completely offline on local hardware or air-gapped government infrastructure without external API dependencies.

---

## 🏗️ System Architecture

```
                                 +-------------------------------------+
                                 |         React + Vite + TS           |
                                 |  (Government Enterprise Theme)      |
                                 |        http://localhost:5173        |
                                 +------------------+------------------+
                                                    |
                                    REST API / JSON | (Django Session + CSRF)
                                                    v
                                 +-------------------------------------+
                                 |      Django REST Framework API      |
                                 |       (Python 3.12 / Gunicorn)      |
                                 |        http://localhost:8000        |
                                 +---------+-----------------+---------+
                                           |                 |
                   SQL & Vector Queries    |                 | Task Enqueue
                                           v                 v
                 +--------------------------------+   +-------------------+
                 |     PostgreSQL 17 + pgvector   |   |  Django Q2 Worker |
                 |  - Tabular relational data     |   |  - Async ML match |
                 |  - 384-dim vector cosine index |   |  - Reminders/SLAs |
                 |  - Append-only audit histories |   |  - File intake    |
                 +--------------------------------+   +---------+---------+
                                                                |
                                        Local Inference         v
                                 +-------------------------------------+
                                 |    Local HuggingFace MiniLM Model   |
                                 |      (CPU Sentence-Transformers)    |
                                 |           models/minilm/            |
                                 +-------------------------------------+
```

---

## ⚡ Quick Start Guide (Windows)

### Prerequisites
- **Docker Desktop** (with Linux container support enabled)
- **Node.js 18+** and **npm**

### Method 1: One-Click Startup (Recommended for Windows)

1. Clone or extract the repository:
   ```cmd
   git clone https://github.com/SanjaiS12a/SIH-AICTE.git
   cd SIH-AICTE
   ```

2. Run the startup script:
   ```cmd
   start.bat
   ```
   *What `start.bat` does automatically:*
   - Verifies Docker and Node.js installation.
   - Prepares `.env` from `.env.example`.
   - Starts PostgreSQL 17 (`pgvector`), Django API, and Django Q2 worker containers.
   - Applies database migrations.
   - Installs frontend dependencies (if not already installed).
   - Starts the Vite frontend dev server in a new window.

3. To cleanly stop all services:
   ```cmd
   stop.bat
   ```

---

### Method 2: Manual Docker Compose (Linux / macOS / Windows)

```bash
# 1. Prepare environment configuration
cp .env.example .env

# 2. Build and launch backend services
docker compose up -d

# 3. Apply database migrations
docker compose exec api python manage.py migrate

# 4. (Optional) Seed demo data if database is fresh
docker compose exec api python manage.py seed_demo

# 5. Launch frontend dev server
cd frontend
npm install
npm run dev
```

The portal is now accessible at:
- **Web Application**: `http://localhost:5173`
- **Backend API**: `http://localhost:8000/api/`
- **Django Admin**: `http://localhost:8000/admin/`

---

## 🔐 Default Demonstration Accounts

All demo accounts are pre-seeded with the password `Demo-only-26264!` (configured via `DEMO_PASSWORD` in `.env`).

| Role | Username | Initial Password | Scope & Permissions |
| :--- | :--- | :--- | :--- |
| **Portal Coordinator** | `coordinator` | `Demo-only-26264!` | Multi-Bureau access, Command Centre, Overlap review, Case transfers, Joint coordination assignments. |
| **Vigilance Auditor** | `auditor` | `Demo-only-26264!` | System-wide read-only visibility, immutable audit log verification, compliance inspection. |
| **Approval Bureau Officer** | `officer_rb` | `Demo-only-26264!` | Scoped strictly to Approval Bureau cases; manages investigation notes, hearing schedules, and actions. |
| **PGRC Bureau Officer** | `officer_pgrc` | `Demo-only-26264!` | Scoped strictly to Grievance Redressal cases; acknowledges joint coordination notices, logs outcomes. |
| **System Administrator** | `admin` | `Demo-only-26264!` | Infrastructure maintenance and Django administration at `/admin/`. |

---

## 📊 Management Command Centre (Milestone 3 Features)

The redesigned AICTE Management Command Centre provides leadership with actionable, authoritative intelligence:

- **Authoritative Operational KPIs**:
  - **Total Complaints**: Exact count of complaints received within the selected date cohort.
  - **Open Pending Workload**: Non-disposed active complaints.
  - **Under Process**: Quantified cases undergoing active investigation or multi-bureau review.
  - **Disposed Share**: Clear percentage of the cohort resolved (`Disposed / Total * 100`).
  - **Overdue Workload**: Cases exceeding the configurable SLA timeline (`status != disposed AND due_at < now`).
  - **Approaching Deadlines**: Active cases with deadlines expiring within 7 days.
- **Pending Case Ageing Analysis**:
  - Non-overlapping cohorts: `0–7 Days`, `8–15 Days`, `16–30 Days`, and `>30 Days`.
  - Age derived from actual received timestamps, decoupled from escalation counts.
- **Current Bureau Ownership**:
  - Workload metrics reflect active, current bureau custodianship after transfers, preventing historical misattribution.
- **Interactive Traceability & Drill-Downs**:
  - Every chart segment, KPI card, and summary metric links directly to a pre-filtered case registry.

---

## 🧪 Testing & Quality Assurance

The system undergoes rigorous regression testing across backend APIs, concurrency locks, and end-to-end browser flows.

### 1. Backend Automated Regression Suite
139 unit and integration tests covering models, serializers, permissions, optimistic locking, and analytics:
```bash
docker compose exec api python manage.py test cases --verbosity 2
```
*Current Status: **139 Passed** (0 Failures, 0 Errors).*

### 2. End-to-End Browser Suite (Playwright)
45 comprehensive end-to-end browser tests verifying user journeys across all roles and viewports:
```bash
cd frontend
npx playwright test
```
*Current Status: **45 Passed** (100% Passing).*

### 3. Production Frontend Build
TypeScript compilation and Vite asset bundling:
```bash
cd frontend
npm run build
```
*Current Status: **0 Type Errors, Production Build Successful**.*

---

## 📁 Repository Structure

```
SIH-AICTE/
├── backend/                  # Django REST Framework application
│   ├── cases/                # Core domain: cases, analytics, coordination, models
│   │   ├── access.py         # Permission checks and cohort filtering
│   │   ├── analytics.py      # Authoritative KPI & management aggregations
│   │   ├── api.py            # DRF viewsets and API endpoints
│   │   ├── matching.py       # MiniLM vector embeddings & pgvector matching
│   │   ├── models.py         # Relational schema (Cases, Institutions, History)
│   │   └── serializers.py    # Request validation & response schemas
│   ├── config/               # Django project settings and WSGI/ASGI entrypoints
│   ├── Dockerfile            # Container definition for API and Worker
│   └── requirements.txt      # Python dependencies
├── frontend/                 # React + Vite + TypeScript application
│   ├── src/
│   │   ├── api.ts            # Typed API client and contract definitions
│   │   ├── dashboard.tsx     # Case registry, filters, and detail drawer
│   │   ├── management.tsx    # Management Command Centre & analytics charts
│   │   ├── institutions.tsx  # Institution-centric profiles & cross-bureau views
│   │   ├── coordination.tsx  # Multi-bureau coordination queue & review
│   │   ├── main.tsx          # Navigation, authentication, and routing
│   │   └── style.css         # Enterprise Government design system styles
│   ├── package.json          # Node dependencies & build scripts
│   └── vite.config.ts        # Vite configuration & proxy definitions
├── models/
│   └── minilm/               # Sentence-Transformers all-MiniLM-L6-v2 model weights
├── backups/                  # Authoritative demonstration database dumps
│   ├── verified-demo.dump    # Standard demonstration fixture
│   └── source-intake-*.dump  # Complete multi-bureau historical intake snapshot
├── scripts/                  # Operational maintenance utilities
│   ├── start.ps1             # PowerShell startup script
│   ├── backup.ps1            # Database backup utility
│   ├── verify_delivery.py    # Delivery verification runner
│   └── verify_source_restore.py # Database restore verification
├── tests/                    # Test suites and fixtures
│   ├── backend/              # Django test cases (139 tests)
│   ├── browser/              # Playwright test specs (45 tests)
│   ├── fixtures/             # Mock files and test spreadsheets
│   └── results/              # Verified test execution evidence & screenshots
├── compose.yaml              # Docker Compose multi-service specification
├── start.bat                 # One-click Windows startup script
├── stop.bat                  # One-click Windows shutdown script
├── .env.example              # Environment variable template
└── README.md                 # Project documentation & setup guide
```

---

## 🛡️ Security, Privacy & Integrity Guarantees

- **Immutable Audit Trails**: Original complaint texts, initial bureau assignments, and citizen details are permanent. All subsequent transfers, escalations, and decisions are captured as append-only records with user stamps and ISO timestamps.
- **Optimistic Concurrency Control**: All state transitions enforce version checks (`409 Conflict` returned upon stale updates) to prevent race conditions during concurrent officer workflows.
- **No Speculative Automation**: The AI system acts exclusively as an assist tool for human officers—it identifies potential overlaps and flags multi-bureau activity, but never merges or closes cases without explicit officer review and logged justification.
- **Zero Third-Party Cloud Leaks**: In accordance with government data protection standards, all natural language processing and vector search operations occur 100% locally on CPU without external API transmission.

---

## 📜 Problem Statement & Compliance Note
Developed for **Smart India Hackathon (SIH)** under Problem Statement **26264** (*AICTE Integrated Institution Complaint Monitoring and Cross-Bureau Coordination System*). All institution names, complaint texts, and citizen identifiers included in test fixtures are fictional and generated strictly for demonstration and verification purposes.
