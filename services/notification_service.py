import logging
from datetime import datetime
from app import db
from models import Notification, WebhookData

logger = logging.getLogger(__name__)

def notify_new_data(data):
    """
    Create a notification for new webhook data
    
    In a production system, this might:
    - Send a WebSocket message to connected clients
    - Trigger push notifications
    - Send emails or SMS
    - Update a notification center
    
    For this implementation, we'll store it in the database
    """
    try:
        # Create notification
        webhook_id = data.get("id")
        source = data.get("source", "other")
        message = f"New data received from {source}"
        
        notification = Notification(
            webhook_id=webhook_id,
            type="new_webhook",
            source=source,
            message=message
        )
        
        # Save notification to database
        db.session.add(notification)
        db.session.commit()
        
        logger.info(f"Created notification for webhook data: {webhook_id}")
        return True
    
    except Exception as e:
        logger.error(f"Error creating notification: {str(e)}")
        db.session.rollback()
        return False

def get_notifications(limit=10, unread_only=False):
    """
    Get the latest notifications from the database
    """
    try:
        # Build query
        query = Notification.query
        
        # Filter to unread if requested
        if unread_only:
            query = query.filter(Notification.read == False)
        
        # Order by timestamp (newest first) and limit
        notifications = query.order_by(Notification.timestamp.desc()).limit(limit).all()
        
        # Convert to dictionaries
        return [notification.to_dict() for notification in notifications]
    
    except Exception as e:
        logger.error(f"Error retrieving notifications: {str(e)}")
        return []

def mark_notification_read(notification_id):
    """
    Mark a notification as read in the database
    """
    try:
        # Find the notification
        notification = Notification.query.get(notification_id)
        
        if notification:
            # Update the read status
            notification.read = True
            db.session.commit()
            return True
        
        return False
    
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        db.session.rollback()
        return False

def mark_all_notifications_read():
    """
    Mark all notifications as read
    """
    try:
        # Update all unread notifications
        Notification.query.filter_by(read=False).update({Notification.read: True})
        db.session.commit()
        return True
    
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {str(e)}")
        db.session.rollback()
        return False

def delete_old_notifications(days=30):
    """
    Delete notifications older than the specified number of days
    """
    try:
        # Calculate cutoff date
        cutoff_date = datetime.utcnow().replace(day=datetime.utcnow().day - days)
        
        # Delete old notifications
        Notification.query.filter(Notification.timestamp < cutoff_date).delete()
        db.session.commit()
        return True
    
    except Exception as e:
        logger.error(f"Error deleting old notifications: {str(e)}")
        db.session.rollback()
        return False
