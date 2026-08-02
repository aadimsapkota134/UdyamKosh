-- ============================================================
--  RinSetu — Startup Loan Management System
--  Schema: tables, constraints, trigger, view, seed data
-- ============================================================

-- Drop in reverse dependency order (safe to re-run)
DROP VIEW  IF EXISTS v_loan_summary;
DROP TABLE IF EXISTS tax_exemption  CASCADE;
DROP TABLE IF EXISTS repayment      CASCADE;
DROP TABLE IF EXISTS loan           CASCADE;
DROP TABLE IF EXISTS loan_application CASCADE;
DROP TABLE IF EXISTS document       CASCADE;
DROP TABLE IF EXISTS startup        CASCADE;

-- ─────────────────────────────────────────────
-- 1. STARTUP
-- ─────────────────────────────────────────────
CREATE TABLE startup (
    startup_id      SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    registration_no VARCHAR(50)  UNIQUE NOT NULL,
    province        VARCHAR(50)  NOT NULL,
    sector          VARCHAR(100),
    annual_turnover DECIMAL(15,2),
    registered_on   DATE         NOT NULL,
    owner_name      VARCHAR(150),
    contact_email   VARCHAR(100) UNIQUE,
    status          VARCHAR(20)  DEFAULT 'active'
                    CHECK (status IN ('active','suspended','closed'))
);

-- ─────────────────────────────────────────────
-- 2. DOCUMENT
-- ─────────────────────────────────────────────
CREATE TABLE document (
    doc_id          SERIAL PRIMARY KEY,
    startup_id      INT          NOT NULL REFERENCES startup(startup_id) ON DELETE CASCADE,
    doc_type        VARCHAR(80)  NOT NULL,
    file_path       VARCHAR(300) NOT NULL,
    uploaded_on     DATE         DEFAULT CURRENT_DATE,
    verified_status VARCHAR(20)  DEFAULT 'pending'
                    CHECK (verified_status IN ('pending','verified','rejected'))
);

-- ─────────────────────────────────────────────
-- 3. LOAN_APPLICATION
-- ─────────────────────────────────────────────
CREATE TABLE loan_application (
application_id   SERIAL PRIMARY KEY,
startup_id       INT           NOT NULL REFERENCES startup(startup_id),
requested_amount DECIMAL(15,2) NOT NULL
CHECK (requested_amount > 0 AND requested_amount <= 10000000),
purpose          TEXT,
applied_on       DATE          DEFAULT CURRENT_DATE,
status           VARCHAR(20)   DEFAULT 'submitted'
CHECK (status IN ('submitted','under_review','approved',
'rejected','disbursed')),
reviewed_by      INT,
reviewed_on      DATE,
review_notes     TEXT
);
-- ─────────────────────────────────────────────
-- 4. LOAN
-- ─────────────────────────────────────────────
CREATE TABLE loan (
    loan_id             SERIAL PRIMARY KEY,
    application_id      INT           UNIQUE NOT NULL
                        REFERENCES loan_application(application_id),
    principal_amount    DECIMAL(15,2) NOT NULL,
    interest_rate       DECIMAL(5,2)  DEFAULT 3.00,
    tenure_months       INT           NOT NULL CHECK (tenure_months BETWEEN 6 AND 84),
    disbursed_on        DATE          NOT NULL,
    due_date            DATE          NOT NULL,
    status              VARCHAR(20)   DEFAULT 'active'
                        CHECK (status IN ('active','closed','defaulted')),
    outstanding_balance DECIMAL(15,2)
);

-- ─────────────────────────────────────────────
-- 5. REPAYMENT
-- ─────────────────────────────────────────────
CREATE TABLE repayment (
    repayment_id    SERIAL PRIMARY KEY,
    loan_id         INT           NOT NULL REFERENCES loan(loan_id),
    amount_paid     DECIMAL(15,2) NOT NULL CHECK (amount_paid > 0),
    paid_on         DATE          DEFAULT CURRENT_DATE,
    payment_method  VARCHAR(50),
    transaction_ref VARCHAR(100)  UNIQUE,
    penalty_applied DECIMAL(10,2) DEFAULT 0.00
);

-- ─────────────────────────────────────────────
-- 6. TAX_EXEMPTION

-- ─────────────────────────────────────────────
-- TRIGGER: auto-create tax exemption on loan insert
-- ─────────────────────────────────────────────
CREATE OR REPLACE FUNCTION create_tax_exemption()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO tax_exemption (loan_id, exemption_start, exemption_end, status)
    VALUES (
        NEW.loan_id,
        NEW.disbursed_on,
        NEW.disbursed_on + INTERVAL '5 years',
        'pending'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;



-- ─────────────────────────────────────────────
-- VIEW: v_loan_summary (replaces the heavy JOIN query)
-- ─────────────────────────────────────────────
CREATE VIEW v_loan_summary AS
SELECT
    l.loan_id,
    s.name                              AS startup_name,
    s.province,
    s.annual_turnover,
    l.principal_amount,
    l.interest_rate,
    l.tenure_months,
    l.disbursed_on,
    l.due_date,
    l.status,
    l.outstanding_balance,
    COALESCE(SUM(r.amount_paid), 0)     AS total_repaid,
    ROUND(
        COALESCE(SUM(r.amount_paid), 0)
        / NULLIF(l.principal_amount, 0) * 100, 2
    )                                   AS percent_repaid
FROM loan l
JOIN loan_application la ON l.application_id = la.application_id
JOIN startup s           ON la.startup_id    = s.startup_id
LEFT JOIN repayment r    ON r.loan_id        = l.loan_id
GROUP BY l.loan_id, s.name, s.province, s.annual_turnover;

-- ─────────────────────────────────────────────
-- SEED DATA (for development / demo)
-- ─────────────────────────────────────────────
INSERT INTO startup (name, registration_no, province, sector, annual_turnover, registered_on, owner_name, contact_email)
VALUES
  ('Sagarmatha Tech',  'REG-BAG-001', 'Bagmati', 'Technology',    8500000, '2080-04-12', 'Aarav Sharma',   'aarav@sagarmatha.com'),
  ('Himalayan Seeds',  'REG-GAN-002', 'Gandaki', 'Agriculture',   4200000, '2079-11-03', 'Sita Gurung',    'sita@hseeds.com'),
  ('Pokhara Crafts',   'REG-GAN-003', 'Gandaki', 'Handicrafts',   3100000, '2081-02-20', 'Bikash Thapa',   'bikash@pkrcrafts.com'),
  ('TechBridge Nepal', 'REG-BAG-004', 'Bagmati', 'EdTech',        9800000, '2080-07-15', 'Priya Shrestha', 'priya@techbridge.np'),
  ('Janakpur Dairy',   'REG-MAD-005', 'Madhesh', 'Agriculture',   6500000, '2078-09-10', 'Ramesh Yadav',   'ramesh@jkdairy.com');

INSERT INTO loan_application (startup_id, requested_amount, purpose, status)
VALUES
  (1, 800000,  'Purchase servers and cloud infrastructure',    'approved'),
  (2, 550000,  'Buy improved seed varieties and cold storage', 'approved'),
  (3, 320000,  'Expand workshop and export handicrafts',       'disbursed'),
  (4, 980000,  'Develop e-learning platform',                  'rejected'),
  (5, 700000,  'Expand dairy processing unit',                 'disbursed');
