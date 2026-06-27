# RinSetu — Startup Loan Management System
*A DBMS course mini-project | Nepal Budget FY 2082/83*

---

## Tech stack

| Layer    | Choice                  |
|----------|-------------------------|
| Database | PostgreSQL               |
| Backend  | Python 3.11 + Flask      |
| Frontend | Plain HTML + Vanilla JS  |

---

## Project structure

```
rinsetu/
├── backend/
│   ├── app.py                  # Flask entry point
│   ├── requirements.txt
│   ├── .env.example
│   ├── db/
│   │   └── connection.py       # psycopg2 connection + init_db()
│   └── routes/
│       ├── startups.py         # GET /, GET /:id, POST /
│       ├── applications.py     # GET /, POST /, PATCH /:id/review
│       ├── loans.py            # GET /, GET /overdue, GET /summary, POST /:id/disburse
│       ├── repayments.py       # GET /:loan_id, POST /
│       └── exemptions.py       # GET /
├── frontend/
│   ├── css/style.css
│   ├── js/api.js               # shared fetch helpers, badge, formatters
│   └── pages/
│       ├── dashboard.html      # stats + recent applications
│       ├── startups.html       # register + list startups
│       ├── applications.html   # submit + review + disburse
│       └── loans.html          # active loans, province summary, overdue
└── sql/
    └── schema.sql              # tables, constraints, trigger, view, seed data
```

---

## Setup

### 1. PostgreSQL

```bash
psql -U postgres
CREATE DATABASE rinsetu;
\q
```

### 2. Backend

```bash
cd backend
cp .env.example .env          # fill in your DB password
pip install -r requirements.txt
python app.py                 # starts on http://localhost:5000
```

On first run, `init_db()` reads `sql/schema.sql` and creates all tables, the trigger, the view, and seed data automatically.

### 3. Frontend

Open `frontend/pages/dashboard.html` directly in your browser, or serve with:

```bash
cd frontend
python -m http.server 8080
# then visit http://localhost:8080/pages/dashboard.html
```

---

## DBMS concepts demonstrated

| Concept                | Where                                                  |
|------------------------|--------------------------------------------------------|
| Normalization (3NF)    | All 6 tables — no transitive dependencies              |
| Primary / foreign keys | Every table; ON DELETE CASCADE on document             |
| CHECK constraints      | `requested_amount`, `tenure_months`, `status` enums   |
| UNIQUE constraints     | `registration_no`, `contact_email`, `transaction_ref` |
| Trigger                | `trg_tax_exemption_on_disburse` in schema.sql          |
| View                   | `v_loan_summary` — pre-joins loan + startup + repayment|
| GROUP BY / HAVING      | Province summary endpoint (`/loans/summary`)           |
| Window function        | `SUM OVER PARTITION BY` in repayments route            |
| ACID transaction       | `disburse_loan()` — 3 writes in one commit/rollback    |

---

## API endpoints

| Method | Endpoint                        | Description                    |
|--------|---------------------------------|--------------------------------|
| GET    | /api/startups/                  | List all startups              |
| POST   | /api/startups/                  | Register a startup             |
| GET    | /api/applications/              | List applications (filterable) |
| POST   | /api/applications/              | Submit application             |
| PATCH  | /api/applications/:id/review    | Approve / reject               |
| POST   | /api/loans/:app_id/disburse     | Disburse + create tax exemption|
| GET    | /api/loans/                     | All loans (via view)           |
| GET    | /api/loans/summary              | Province-wise GROUP BY         |
| GET    | /api/loans/overdue              | Overdue loans                  |
| GET    | /api/repayments/:loan_id        | Repayments with window function|
| POST   | /api/repayments/                | Record a repayment             |
| GET    | /api/exemptions/                | Tax-exempt startups            |
