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

            # Insert loan – the trigger will create the tax_exemption record
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

            # Mark application as disbursed
            cur.execute("""
                UPDATE loan_application SET status = 'disbursed'
                WHERE application_id = %s
            """, (app_id,))

            conn.commit()
            return jsonify(loan), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
