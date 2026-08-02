from flask import Blueprint, jsonify, request
from db.connection import get_connection

repayments_bp = Blueprint("repayments", __name__)

@repayments_bp.route("/<int:loan_id>", methods=["GET"])
def loan_repayments(loan_id):
    """Repayment history with running total (window function demo)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT repayment_id, loan_id, amount_paid, paid_on,
                       payment_method, penalty_applied,
                       SUM(amount_paid) OVER (
                           PARTITION BY loan_id ORDER BY paid_on
                       ) AS cumulative_repaid
                FROM repayment
                WHERE loan_id = %s
                ORDER BY paid_on
            """, (loan_id,))
            return jsonify(cur.fetchall())
    finally:
        conn.close()

@repayments_bp.route("/", methods=["POST"])
def record_repayment():
        data = request.get_json()
          conn = get_connection()
           try:
           with conn.cursor() as cur:
            cur.execute("""
       INSERT INTO repayment
           (loan_id, amount_paid, payment_method,
               transaction_ref, penalty_applied)
                VALUES (%s, %s, %s, %s, %s)
       RETURNING *
               """, (
             data["loan_id"], data["amount_paid"],
            data.get("payment_method"), data.get("transaction_ref"),
           data.get("penalty_applied", 0)
           ))
         # Update outstanding balance
      cur.execute("""
    UPDATE loan
    SET outstanding_balance = outstanding_balance - %s
   WHERE loan_id = %s
     """, (data["amount_paid"], data["loan_id"]))
     conn.commit()
return jsonify(cur.fetchone()), 201
    finally:
        conn.close()
