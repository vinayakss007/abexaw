import os
import logging
from pathlib import Path
from flask import Flask, send_file
from flask_cors import CORS
from db_config import db, logger

# Create data directory if it doesn't exist (for backward compatibility)
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

# Create app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
CORS(app)

# Add route for the simple HTML form
@app.route('/simple-form')
def simple_form():
    return send_file('simple_form.html')

# Configure SQLAlchemy
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'webhooks.db')
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", f"sqlite:///{db_path}")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "connect_args": {"check_same_thread": False} # Added for SQLite
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize SQLAlchemy
db.init_app(app)

# Import models (after db is defined but before create_all)
import models

# Create database tables
with app.app_context():
    db.create_all()

    # Initialize default data sources if not exists
    from models import DataSource
    default_sources = [
        {"id": "stripe", "name": "Stripe Payments", "color": "#6772E5"},
        {"id": "paypal", "name": "PayPal", "color": "#003087"},
        {"id": "crm", "name": "CRM System", "color": "#4CAF50"},
        {"id": "form", "name": "Web Forms", "color": "#2196F3"},
        {"id": "email", "name": "Email Service", "color": "#F44336"},
        {"id": "cart", "name": "Shopping Cart", "color": "#FF9800"},
        {"id": "google", "name": "Google Analytics", "color": "#EA4335"},
        {"id": "whatsapp", "name": "WhatsApp Business", "color": "#25D366"},
        {"id": "facebook", "name": "Facebook", "color": "#1877F2"},
        {"id": "newsletter", "name": "Newsletter", "color": "#00BCD4"}, # Added newsletter source
        {"id": "collection_form", "name": "Collection Form", "color": "#FF5722"}, # Added collection form source
        {"id": "scanner", "name": "Document Scanner", "color": "#795548"}, # Added scanner source
        {"id": "other", "name": "Other Sources", "color": "#9C27B0"}
    ]

    # Check if data sources exist before adding
    for source in default_sources:
        if not DataSource.query.filter_by(id=source["id"]).first():
            db.session.add(DataSource(**source))

    db.session.commit()
    
    # Run database migrations to update schema if needed
    from migrations import run_migrations
    run_migrations()

# Register blueprints
from routes.webhook_routes import webhook_bp
from routes.dashboard_routes import dashboard_bp
from routes.integration_routes import integration_bp
from routes.settings_routes import settings_bp
from routes.scanner_routes import scanner_bp


app.register_blueprint(webhook_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(integration_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(scanner_bp)

logger.info("Application initialized")