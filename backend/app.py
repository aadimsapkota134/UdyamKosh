from flask import Flask
from flask_cors import CORS
from db.connection import init_db

from routes.startups import startups_bp
from routes.applications import applications_bp
from routes.loans import loans_bp
from routes.repayments import repayments_bp
from routes.exemptions import exemptions_bp

app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(startups_bp,    url_prefix="/api/startups")
app.register_blueprint(applications_bp, url_prefix="/api/applications")
app.register_blueprint(loans_bp,       url_prefix="/api/loans")
app.register_blueprint(repayments_bp,  url_prefix="/api/repayments")
app.register_blueprint(exemptions_bp,  url_prefix="/api/exemptions")

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
