from flask import Blueprint, jsonify, request
from db.connection import get_connection

startups_bp = Blueprint("startups", __name__)

@startups_bp.route("/", methods=["GET"])
def list_startups():
    province = request.args.get("province")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if province:
                cur.execute(
                    "SELECT * FROM startup WHERE province = %s ORDER BY registered_on DESC",
                    (province,)
                )
            else:
                cur.execute("SELECT * FROM startup ORDER BY registered_on DESC")
            return jsonify(cur.fetchall())
    finally:
        conn.close()

@startups_bp.route("/<int:startup_id>", methods=["GET"])
def get_startup(startup_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM startup WHERE startup_id = %s", (startup_id,))
            row = cur.fetchone()
            if not row:
                return jsonify({"error": "Not found"}), 404
            return jsonify(row)
    finally:
        conn.close()

@startups_bp.route("/", methods=["POST"])
..... // delete it later 
            return jsonify(cur.fetchone()), 201
    finally:
        conn.close()
