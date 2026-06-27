from flask import Blueprint, jsonify, request
from db.connection import get_connection

loans_bp = Blueprint("loans", __name__)

@loans_bp.route("/", methods=["GET"])
def list_loans():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT l.*, s.name AS startup_name, s.province,
                       s.annual_turnover,
                       COALESCE(SUM(r.amount_paid), 0) AS total_repaid
                FROM loan l
                JOIN loan_application la ON l.application_id = la.application_id
                JOIN startup s           ON la.startup_id = s.startup_id
                LEFT JOIN repayment r    ON r.loan_id = l.loan_id
                GROUP BY l.loan_id, s.name, s.province, s.annual_turnover
                ORDER BY l.disbursed_on DESC
            """)
            return jsonify(cur.fetchall())
    finally:
        conn.close()

@loans_bp.route("/overdue", methods=["GET"])
def overdue_loans():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s.name, s.contact_email,
                       l.loan_id, l.outstanding_balance,
                       CURRENT_DATE - l.due_date AS days_overdue
                FROM loan l
                JOIN loan_application la ON l.application_id = la.application_id
                JOIN startup s           ON la.startup_id = s.startup_id
                WHERE l.status = 'active' AND l.due_date < CURRENT_DATE
            """)
            return jsonify(cur.fetchall())
    finally:
        conn.close()

@loans_bp.route("/summary", methods=["GET"])
def province_summary():
    """Province-wise disbursement summary — GROUP BY demo."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s.province,
                       COUNT(l.loan_id)           AS total_loans,
                       SUM(l.principal_amount)    AS total_disbursed,
                       AVG(l.outstanding_balance) AS avg_outstanding
                FROM loan l
                JOIN loan_application la ON l.application_id = la.application_id
                JOIN startup s           ON la.startup_id = s.startup_id
                GROUP BY s.province
                ORDER BY total_disbursed DESC
            """)
            return jsonify(cur.fetchall())
    finally:
        conn.close()

@loans_bp.route("/<int:app_id>/disburse", methods=["POST"])
def disburse_loan(app_id):
    """
    Disburse a loan for an approved application.
    Wrapped in a single transaction — if tax_exemption insert fails,
    the loan insert also rolls back (ACID demo).
    """
    data = request.get_json()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Verify application is approved
            cur.execute(
                "SELECT * FROM loan_application WHERE application_id = %s",
                (app_id,)
            )
            appl = cur.fetchone()
            if not appl:
                return jsonify({"error": "Application not found"}), 404
            if appl["status"] != "approved":
                return jsonify({"error": "Application is not in approved state"}), 400

            # BEGIN transaction (psycopg2 is always in a transaction)
            cur.execute("""
                INSERT INTO loan
                    (application_id, principal_amount, interest_rate,
                     tenure_months, disbursed_on, due_date, outstanding_balance)
                VALUES (%s, %s, 3.00, %s,
                        CURRENT_DATE,
                        CURRENT_DATE + (%s || ' months')::interval,
                        %s)
                RETURNING *
            """, (
                app_id,
                appl["requested_amount"],
                data["tenure_months"],
                data["tenure_months"],
                appl["requested_amount"]
            ))
            loan = cur.fetchone()

            # Tax exemption auto-insert (mirrors the trigger — shown explicitly here
            # for the ACID transaction demo; the DB trigger also handles this)
            cur.execute("""
                INSERT INTO tax_exemption
                    (loan_id, exemption_start, exemption_end, fiscal_year)
                VALUES (%s, CURRENT_DATE, CURRENT_DATE + INTERVAL '5 years', %s)
            """, (loan["loan_id"], data.get("fiscal_year", "2082/83")))

            # Mark application as disbursed
            cur.execute("""
                UPDATE loan_application SET status = 'disbursed'
                WHERE application_id = %s
            """, (app_id,))

            conn.commit()   # COMMIT — all three writes land together
            return jsonify(loan), 201

    except Exception as e:
        conn.rollback()     # ROLLBACK — none of them land on error
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
