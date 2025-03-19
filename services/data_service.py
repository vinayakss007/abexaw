import logging
from datetime import datetime
from app import db
from models import WebhookData, DataSource
from sqlalchemy import and_, func

logger = logging.getLogger(__name__)

def save_webhook_data(data):
    """
    Save webhook data to the database
    """
    try:
        # Create a new WebhookData instance
        webhook_data = WebhookData(
            id=data.get('id'),
            timestamp=data.get('timestamp'),
            source=data.get('source', 'other'),
            data=data.get('data', {})
        )
        
        # Save to database
        db.session.add(webhook_data)
        db.session.commit()
        
        logger.debug(f"Saved webhook data with ID: {data.get('id')}")
        return True
    
    except Exception as e:
        logger.error(f"Error saving webhook data: {str(e)}")
        db.session.rollback()
        return False

def get_webhook_data(source_filter=None, date_from=None, date_to=None, limit=None):
    """
    Get webhook data with optional filtering
    
    Args:
        source_filter (str, optional): Filter by source
        date_from (str, optional): ISO format date string for start date
        date_to (str, optional): ISO format date string for end date
        limit (int, optional): Max number of records to return
        
    Returns:
        list: List of webhook data dictionaries
    """
    try:
        # Build query with filters
        query = WebhookData.query
        
        # Filter by source
        if source_filter:
            query = query.filter(WebhookData.source == source_filter)
        
        # Filter by date range
        if date_from:
            try:
                date_from_obj = datetime.fromisoformat(date_from)
                query = query.filter(WebhookData.timestamp >= date_from_obj)
            except ValueError:
                logger.warning(f"Invalid date_from format: {date_from}")
        
        if date_to:
            try:
                date_to_obj = datetime.fromisoformat(date_to)
                query = query.filter(WebhookData.timestamp <= date_to_obj)
            except ValueError:
                logger.warning(f"Invalid date_to format: {date_to}")
        
        # Order by timestamp descending (most recent first)
        query = query.order_by(WebhookData.timestamp.desc())
        
        # Apply limit if provided
        if limit is not None:
            query = query.limit(limit)
        
        # Convert to list of dictionaries
        result = [item.to_dict() for item in query.all()]
        return result
    
    except Exception as e:
        logger.error(f"Error retrieving webhook data: {str(e)}")
        return []

def get_data_sources():
    """
    Get the list of data sources from the database
    """
    try:
        sources = DataSource.query.all()
        return [source.to_dict() for source in sources]
    
    except Exception as e:
        logger.error(f"Error retrieving data sources: {str(e)}")
        # Return default sources on error
        return [
            {"id": "crm", "name": "CRM System", "color": "#4CAF50"},
            {"id": "form", "name": "Web Forms", "color": "#2196F3"},
            {"id": "email", "name": "Email Service", "color": "#F44336"},
            {"id": "other", "name": "Other Sources", "color": "#9C27B0"}
        ]

def get_webhook_stats():
    """
    Get statistics about webhooks
    """
    try:
        stats = {}
        
        # Total count
        stats['total'] = WebhookData.query.count()
        
        # Count by source
        source_counts = db.session.query(
            WebhookData.source, 
            func.count(WebhookData.id)
        ).group_by(WebhookData.source).all()
        
        stats['by_source'] = {source: count for source, count in source_counts}
        
        # Recent activity - last 7 days
        seven_days_ago = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        seven_days_ago = seven_days_ago.replace(day=seven_days_ago.day - 7)
        
        daily_counts = db.session.query(
            func.date(WebhookData.timestamp),
            func.count(WebhookData.id)
        ).filter(WebhookData.timestamp >= seven_days_ago).group_by(
            func.date(WebhookData.timestamp)
        ).all()
        
        stats['daily'] = {str(date): count for date, count in daily_counts}
        
        return stats
    
    except Exception as e:
        logger.error(f"Error retrieving webhook stats: {str(e)}")
        return {
            'total': 0,
            'by_source': {},
            'daily': {}
        }
