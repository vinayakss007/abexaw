import logging
from flask import Blueprint, render_template, jsonify
from services.data_service import get_webhook_data, get_data_sources, get_webhook_stats
from utils.data_transformers import transform_for_charts
from services.notification_service import get_notifications

logger = logging.getLogger(__name__)
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    """
    Main dashboard page
    """
    sources = get_data_sources()
    return render_template('dashboard.html', sources=sources)

@dashboard_bp.route('/webhooks')
def webhooks():
    """
    Webhook management page
    """
    return render_template('webhooks.html')

@dashboard_bp.route('/integrations')
def integrations():
    """
    Integrations management page
    """
    return render_template('integrations.html')

def get_dashboard_data():
    """Helper function to consolidate data fetching."""
    try:
        # Get webhook stats
        stats = get_webhook_stats()

        # Get latest webhooks
        latest_records = get_webhook_data(limit=5)

        # Get data sources for display
        sources = get_data_sources()

        # Get recent notifications
        recent_notifications = get_notifications(limit=5)

        # Get all webhook data for chart transformation
        all_webhooks = get_webhook_data()

        # Transform data for charts using chart-specific function
        chart_data = transform_for_charts(all_webhooks)

        # Source distribution for pie/doughnut chart
        source_counts = stats.get('by_source', {})

        return {
            "total_webhooks": stats.get('total', 0),
            "source_counts": source_counts,
            "chart_data": chart_data,
            "latest_records": latest_records,
            "notifications": recent_notifications,
            "sources": sources
        }
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {str(e)}")
        return None


@dashboard_bp.route('/api/dashboard/summary')
def dashboard_summary():
    """
    API endpoint to provide summary data for the dashboard
    """
    try:
        dashboard_data = get_dashboard_data()
        if not dashboard_data:
            return jsonify({
                "status": "success",
                "data": {
                    "total_webhooks": 0,
                    "source_counts": {},
                    "chart_data": {"labels": [], "datasets": []},
                    "latest_records": [],
                    "notifications": [],
                    "sources": get_data_sources() # Use existing function
                }
            })
        return jsonify({
            "status": "success",
            "data": dashboard_data
        })
    except Exception as e:
        logger.error(f"Error getting dashboard summary: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Failed to fetch dashboard data"
        }), 500