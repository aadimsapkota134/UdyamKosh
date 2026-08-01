from flask import Blueprint, jsonify, request
from db.connection import get_connection

applications_bp = Blueprint("applications", __name__)

@applications_bp.route("/", methods=["GET"])
def list_applications():
    status = request.args.get("status")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if status:
                cur.execute("""
                    SELECT la.*, s.name AS startup_name, s.province
                    FROM loan_application la
                    JOIN startup s ON la.startup_id = s.startup_id
                    WHERE la.status = %s
                    ORDER BY la.applied_on DESC
                """, (status,))
            else:
                cur.execute("""
                    SELECT la.*, s.name AS startup_name, s.province
                    FROM loan_application la
                    JOIN startup s ON la.startup_id = s.startup_id
                    ORDER BY la.applied_on DESC
                """)
            return jsonify(cur.fetchall())
    finally:
        conn.close()

@applications_bp.route("/", methods=["POST"])


@applications_bp.route("/<int:app_id>/review", methods=["PATCH"])
def review_application(app_id):
    """Officer approves or rejects an application."""
    data = request.get_json()
    status = data.get("status")  # 'approved' or 'rejected'
    if status not in ("approved", "rejected"):
        return jsonify({"error": "status must be approved or rejected"}), 400
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE loan_application
                SET status      = %s,
                    reviewed_by = %s,
                    reviewed_on = CURRENT_DATE,
                    review_notes = %s
                WHERE application_id = %s
                RETURNING *
            """, (status, data.get("reviewed_by"), data.get("review_notes"), app_id))
            conn.commit()
            return jsonify(cur.fetchone())
    finally:
        conn.close()
