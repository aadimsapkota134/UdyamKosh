from flask import Blueprint, jsonify
from db.connection import get_connection

exemptions_bp = Blueprint("exemptions", __name__)

@exemptions_bp.route("/", methods=["GET"])
def list_exemptions():
    """All startups with active tax exemptions (turnover < 1 crore)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s.name, s.annual_turnover,
                       te.exemption_start, te.exemption_end,
                       te.fiscal_year, te.status
                FROM tax_exemption te
                JOIN loan l              ON te.loan_id = l.loan_id
                JOIN loan_application la ON l.application_id = la.application_id
                JOIN startup s           ON la.startup_id = s.startup_id
                WHERE s.annual_turnover < 10000000
                ORDER BY te.exemption_start DESC
            """)
            return jsonify(cur.fetchall())
    finally:
        conn.close()
