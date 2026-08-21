# BlastScope

> Static code intelligence and change-impact analysis for Git repositories.

BlastScope analyzes a Git repository before a code change reaches production and identifies what could break, which components are affected, how far the impact can propagate, and which parts of the codebase deserve the most attention.

Instead of relying only on changed files, BlastScope builds a dependency graph of the repository and performs symbol-level analysis across functions, classes, API endpoints, imports, callers, tests, and architectural relationships.

The project includes a React dashboard, FastAPI backend, PostgreSQL persistence, Redis/RQ background processing, and an interactive dependency graph for exploring blast radius.

---

## Overview

A small code change can affect much more than the file being edited.

For example:

```text
Developer changes:
calculate_total()

        ↓

BlastScope detects:

calculate_total()
├── checkout()
├── create_order()
│   └── POST /orders
└── payment_service()
    └── retry_payment()

Blast Radius: 5 components
Risk: HIGH
```

BlastScope is designed to answer questions such as:

- What components depend on this function?
- What can break if a symbol is removed?
- Did a function signature change?
- Which API endpoints are indirectly affected?
- Which components are most critical?
- Which tests should run after a change?
- Does a change violate architecture boundaries?
- How large is the transitive blast radius?
- Is a refactor actually safe?
- Which areas of the repository have high coupling?

---

## Key Features

### Dependency Graph Analysis

BlastScope scans a repository and builds relationships between:

- Functions
- Methods
- Classes
- Modules
- Imports
- Function calls
- API endpoints

The resulting graph is used as the foundation for impact analysis.

---

### Blast Radius Analysis

Select a symbol and BlastScope determines the components that depend on it.

Blast radius analysis supports multiple dependency depths so developers can distinguish between direct and transitive impact.

```text
Target Symbol
     ↓
Direct Dependents
     ↓
Second-Level Dependents
     ↓
API / Application Impact
```

---

### Interactive Dependency Graph

The frontend provides an interactive graph visualization where users can:

- Select critical symbols
- View their blast radius
- Change the target symbol
- Search symbols
- Change dependency depth
- Filter calls and imports
- Filter functions, methods, classes, and API endpoints
- Inspect individual graph nodes

---

### Breaking Change Detection

BlastScope detects potentially dangerous changes including:

- Removed symbols
- Function signature changes
- Renamed symbols
- Caller incompatibility
- Missing dependencies
- Changes capable of producing runtime failures

Breaking changes can be connected directly to their affected callers and dependency graph.

---

### Symbol Change Analysis

BlastScope compares Git revisions and detects symbol-level changes instead of relying only on file-level diffs.

Examples include:

```text
calculate_total()
        ↓
compute_total()
```

and:

```text
process_payment(amount)
        ↓
process_payment(amount, currency)
```

This enables more precise change-impact analysis.

---

### Critical Component Detection

BlastScope calculates component criticality using factors such as:

- Direct dependents
- Transitive dependents
- Dependency depth
- API endpoint exposure
- Graph connectivity

A highly connected symbol receives a higher criticality score.

Example:

```text
src.error.Missing

Criticality Score: 95
Direct Dependents: 16
Transitive Dependents: 88
API Endpoints: 5
Dependency Depth: 4
```

---

### API Route Analysis

BlastScope identifies API endpoints and connects them to internal repository dependencies.

Supported analysis can identify relationships such as:

```text
POST /orders
      ↓
create_order()
      ↓
process_payment()
      ↓
payment_repository
```

This helps determine whether an internal change could affect a public API.

---

### Call Compatibility Analysis

Function changes are checked against existing callers.

BlastScope can identify situations where a modified function signature may no longer be compatible with existing calls.

---

### Removed Symbol Impact

When a symbol is deleted, BlastScope determines which components still depend on it.

This helps detect changes that may otherwise result in runtime failures.

---

### Refactor Validation

BlastScope analyzes structural changes to help determine whether a refactor preserved expected dependencies or introduced potentially unsafe changes.

---

### Architecture Analysis

Repository structure can be analyzed for architectural relationships and violations.

This helps identify unwanted dependencies between application layers.

Example:

```text
routes
  ↓
services
  ↓
repositories
  ↓
models
```

BlastScope can detect relationships that violate expected architectural boundaries.

---

### Cycle Detection

Dependency cycles are detected to identify tightly coupled components and potentially problematic architecture.

Example:

```text
payment
   ↓
order
   ↓
invoice
   ↓
payment
```

---

### Dead Code Analysis

BlastScope identifies symbols that appear to have no detected dependents and can flag potential dead or unused code for further review.

---

### Test Impact Analysis

BlastScope maps application components to tests and helps identify which tests are relevant to a code change.

This can eventually be used to reduce unnecessary CI execution by prioritizing impacted tests.

---

### Git History Analysis

Git history is used to provide additional repository intelligence such as historical change information and coupling between components.

---

### Change Severity Analysis

Changes can be categorized based on their potential impact rather than treating every modified file equally.

---

## SaaS Architecture

```text
┌───────────────────────────────┐
│        React + Vite UI        │
│                               │
│ Dashboard                     │
│ New Analysis                  │
│ Analysis Report               │
│ Dependency Graph              │
│ Analysis History              │
└───────────────┬───────────────┘
                │
                │ HTTP / REST
                ▼
┌───────────────────────────────┐
│          FastAPI API          │
│                               │
│ POST /api/jobs                │
│ GET  /api/jobs                │
│ GET  /api/jobs/{id}           │
└───────────────┬───────────────┘
                │
        ┌───────┴────────┐
        │                │
        ▼                ▼
┌──────────────┐  ┌──────────────┐
│ PostgreSQL   │  │ Redis / RQ   │
│              │  │    Queue     │
│ Jobs         │  └───────┬──────┘
│ Results      │          │
│ History      │          ▼
└──────────────┘  ┌──────────────┐
                  │  RQ Worker   │
                  └───────┬──────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ Clone Git Repo  │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ BlastScope Core │
                 │ Analysis Engine │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ Dependency      │
                 │ Graph + Reports │
                 └─────────────────┘
```

---

## Background Job Architecture

Repository analysis can be CPU-intensive and should not block the API process.

BlastScope therefore uses Redis and RQ.

```text
POST /api/jobs
      ↓
Create PostgreSQL job
      ↓
Push job to Redis
      ↓
Return job ID immediately
      ↓
RQ Worker receives job
      ↓
Clone repository
      ↓
Run analysis
      ↓
Store result
      ↓
Frontend polls job status
```

Typical lifecycle:

```text
queued
   ↓
running
   ↓
cloning
   ↓
analyzing
   ↓
finalizing
   ↓
completed
```

If processing fails, the job is marked as failed and the error can be stored with the analysis record.

---

## Technology Stack

### Backend

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis
- RQ
- GitPython
- Pydantic
- Python AST

### Frontend

- React
- TypeScript
- Vite
- React Router
- Axios
- React Flow
- Lucide React

### Infrastructure

- Git
- GitHub
- Render
- PostgreSQL
- Redis-compatible Key Value storage
- RQ workers

---

## Project Structure

```text
blastscope/
├── backend/
│   ├── app/
│   │   ├── analyzers/
│   │   │   ├── api_route_analyzer.py
│   │   │   ├── architecture_analyzer.py
│   │   │   ├── base_revision_analyzer.py
│   │   │   ├── breaking_change_analyzer.py
│   │   │   ├── call_compatibility_analyzer.py
│   │   │   ├── change_impact_analyzer.py
│   │   │   ├── criticality_analyzer.py
│   │   │   ├── cycle_analyzer.py
│   │   │   ├── dead_code_analyzer.py
│   │   │   ├── refactor_validation_analyzer.py
│   │   │   ├── removed_symbol_impact_analyzer.py
│   │   │   ├── repository_analyzer.py
│   │   │   ├── signature_analyzer.py
│   │   │   └── symbol_change_analyzer.py
│   │   │
│   │   ├── api/
│   │   │   ├── graph.py
│   │   │   ├── jobs.py
│   │   │   ├── main.py
│   │   │   ├── repositories.py
│   │   │   └── schemas.py
│   │   │
│   │   ├── core/
│   │   ├── db/
│   │   ├── git/
│   │   ├── graph/
│   │   ├── impact/
│   │   ├── models/
│   │   ├── queue/
│   │   ├── risk/
│   │   ├── services/
│   │   ├── symbols/
│   │   ├── tests/
│   │   ├── workers/
│   │   └── workspace/
│   │
│   ├── samples/
│   ├── requirements.txt
│   └── worker.py
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   └── DependencyGraph.tsx
│   │   ├── layouts/
│   │   │   └── AppLayout.tsx
│   │   ├── pages/
│   │   │   ├── AnalysisDetail.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── History.tsx
│   │   │   └── NewAnalysis.tsx
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── types/
│   │   ├── App.tsx
│   │   ├── index.css
│   │   └── main.tsx
│   │
│   ├── package.json
│   └── vite.config.ts
│
├── render.yaml
├── .gitignore
└── README.md
```

---

## Local Development

### Prerequisites

Install:

- Python 3.11+
- Node.js
- npm
- PostgreSQL
- Redis
- Git

---

## 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/BlastScope.git
cd BlastScope
```

---

## 2. Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Create:

```text
backend/.env
```

Example:

```env
DATABASE_URL=postgresql://YOUR_USER@localhost:5432/blastscope
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=http://localhost:5173
ENVIRONMENT=development
```

Do not commit the real `.env` file.

---

## 3. PostgreSQL Setup

Create the local database:

```bash
createdb blastscope
```

Initialize the tables:

```bash
python -m app.db.init_db
```

Verify:

```bash
psql blastscope -c "\dt"
```

---

## 4. Redis Setup

On macOS with Homebrew:

```bash
brew install redis
brew services start redis
```

Verify:

```bash
redis-cli ping
```

Expected:

```text
PONG
```

---

## 5. Start the Backend

From `backend/`:

```bash
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will run locally on port `8000`.

---

## 6. Start the Analysis Worker

Open another terminal:

```bash
cd backend
source .venv/bin/activate
python worker.py
```

For local macOS development, BlastScope uses an RQ `SimpleWorker` to avoid Objective-C runtime issues caused by process forking.

Production Linux environments can use the standard RQ worker.

---

## 7. Frontend Setup

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend will normally run on port `5173`.

---

## Running an Analysis

Open the BlastScope frontend and select **New Analysis**.

Provide:

```text
Repository URL:
https://github.com/OWNER/REPOSITORY.git

Base Reference:
main

Target Reference:
HEAD
```

Submit the analysis.

BlastScope will:

```text
Create job
   ↓
Queue analysis
   ↓
Clone repository
   ↓
Build symbol table
   ↓
Build dependency graph
   ↓
Analyze changes
   ↓
Calculate impact
   ↓
Calculate risk
   ↓
Store result
   ↓
Display report
```

---

## API

### Create Analysis Job

```http
POST /api/jobs
```

Example request:

```json
{
  "repository_url": "https://github.com/OWNER/REPOSITORY.git",
  "base_ref": "main",
  "target_ref": "HEAD"
}
```

Example initial response:

```json
{
  "id": "analysis-job-id",
  "status": "queued",
  "progress": 0,
  "current_stage": "queued"
}
```

---

### Get Analysis Job

```http
GET /api/jobs/{job_id}
```

The frontend polls this endpoint while an analysis is running.

---

### List Analysis Jobs

```http
GET /api/jobs
```

Supports analysis history and pagination.

---

### Delete Analysis Job

```http
DELETE /api/jobs/{job_id}
```

---

## Example Analysis Output

BlastScope can produce information such as:

```json
{
  "name": "src.fake.creature.check_missing",
  "node_type": "function",
  "criticality_score": 99,
  "direct_dependents": 3,
  "transitive_dependents": 11,
  "api_endpoints": 3,
  "dependency_depth": 3
}
```

This indicates that changing the component could affect multiple downstream components and public API endpoints.

---

## Dependency Graph

The dependency graph stores nodes such as:

```json
{
  "id": "src.payment.process_payment",
  "name": "src.payment.process_payment",
  "node_type": "function",
  "direct_dependents": 4,
  "direct_dependencies": 2
}
```

and relationships such as:

```json
{
  "source": "src.checkout.create_order",
  "target": "src.payment.process_payment",
  "edge_type": "calls"
}
```

The frontend uses this data to visualize the blast radius interactively.

---

## Repository Analysis Pipeline

BlastScope's analysis pipeline combines multiple analyzers:

```text
Repository
    ↓
Repository Analyzer
    ↓
Symbol Table
    ↓
Dependency Graph
    ↓
Git Change Mapping
    ↓
Symbol Change Analysis
    ↓
Signature Analysis
    ↓
Call Compatibility
    ↓
Breaking Change Detection
    ↓
Removed Symbol Impact
    ↓
API Impact
    ↓
Criticality Analysis
    ↓
Architecture Analysis
    ↓
Cycle Detection
    ↓
Test Impact
    ↓
Risk Analysis
    ↓
Final Report
```

---

## Deployment

BlastScope is structured as a monorepo and prepared for deployment using Render.

The deployment architecture consists of:

```text
blastscope-frontend
        │
        ▼
blastscope-api
        │
   ┌────┴────┐
   ▼         ▼
PostgreSQL  Redis
              │
              ▼
      blastscope-worker
```

The root `render.yaml` defines the deployment services.

Production environment variables include:

```text
DATABASE_URL
REDIS_URL
CORS_ORIGINS
VITE_API_URL
ENVIRONMENT
```

Secrets and local `.env` files must never be committed.

---

## Production Build

Frontend:

```bash
cd frontend
npm ci
npm run build
```

Backend dependency installation:

```bash
cd backend
python -m pip install -r requirements.txt
```

Backend validation:

```bash
python -m py_compile app/api/main.py
python -m py_compile app/workers/analysis_worker.py
python -m py_compile worker.py
```

---

## Current Status

BlastScope currently supports an end-to-end workflow:

```text
Git Repository
      ↓
React Frontend
      ↓
FastAPI
      ↓
PostgreSQL Job
      ↓
Redis / RQ
      ↓
Background Worker
      ↓
Repository Analysis
      ↓
Persisted Results
      ↓
Interactive Report
```

The complete local pipeline has been tested using public Git repositories.

---

## Roadmap

Planned improvements include:

- GitHub authentication
- Private repository support
- GitHub pull request integration
- Automatic PR risk reports
- Improved dependency graph layouts
- Repository size and resource limits
- Analysis cancellation
- Retry support
- More language support
- CI/CD integration
- GitHub Checks integration
- Team workspaces
- Authentication and authorization
- Historical risk trends
- Repository dashboards
- Improved test selection
- Analysis caching
- Webhook-triggered analysis

---

## Use Cases

BlastScope can be useful for:

- Pull request risk analysis
- Refactor validation
- Breaking-change detection
- Legacy codebase exploration
- Dependency visualization
- API impact analysis
- Test selection
- Architecture review
- Codebase onboarding
- Change-risk assessment

---

## Why BlastScope?

Traditional Git diffs answer:

> What lines changed?

BlastScope aims to answer:

> What does this change affect?

That distinction is the core idea behind the project.

---

## Security

BlastScope clones external repositories into temporary workspaces for analysis.

Production deployments should enforce:

- Repository URL validation
- Clone timeouts
- Repository size limits
- Worker execution limits
- Temporary workspace cleanup
- Restricted network access where appropriate
- Secret isolation
- Private repository credential protection

Never commit `.env` files, database passwords, Redis credentials, GitHub tokens, or other secrets.

---

## Contributing

Contributions, bug reports, and feature suggestions are welcome.

To contribute:

```bash
git checkout -b feature/your-feature
git add .
git commit -m "feat: add your feature"
git push origin feature/your-feature
```

Then open a pull request.

---

## License

No license has been added yet.

Until a license is explicitly added, the source code remains under the repository owner's default copyright protections.

---

## Author

**Rahul Bansal**

GitHub: `rahulbansalcs`

---

## Project Goal

The long-term goal of BlastScope is to become a developer intelligence platform capable of understanding the consequences of a code change before that change reaches production.

```text
Change Code
    ↓
Understand Dependencies
    ↓
Calculate Blast Radius
    ↓
Detect Breaking Changes
    ↓
Estimate Risk
    ↓
Run Relevant Tests
    ↓
Ship With Confidence
```
