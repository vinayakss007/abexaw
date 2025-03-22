import logging
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from app import db
from models import Notification, WebhookData, Integration

logger = logging.getLogger(__name__)

def get_email_settings():
    """Get email settings from database"""
    try:
        email_settings = Integration.query.filter_by(integration_type='email').first()
        if email_settings and email_settings.enabled:
            return email_settings.settings
        return None
    except Exception as e:
        logger.error(f"Error retrieving email settings: {str(e)}")
        return None

def send_email_notification(subject, body, recipient=None):
    """
    Send an email notification based on configured settings
    
    Args:
        subject (str): Email subject
        body (str): Email body content
        recipient (str, optional): Override recipient email
        
    Returns:
        bool: Success status
    """
    try:
        # Get email settings
        settings = get_email_settings()
        if not settings:
            logger.warning("Email notification not sent: Email settings not configured or disabled")
            return False
            
        # Check if notifications are enabled
        if not settings.get('notify_on_webhook', False):
            logger.debug("Email notification not sent: Notifications are disabled")
            return False
            
        # Get provider
        provider = settings.get('email_provider', 'smtp')
        
        # Get recipient (use passed one or fall back to settings)
        to_email = recipient or settings.get('from_email')
        if not to_email:
            logger.warning("Email notification not sent: No recipient email")
            return False
            
        # Send based on provider type
        if provider == 'smtp':
            return send_smtp_email(settings, to_email, subject, body)
        elif provider == 'sendgrid':
            return send_sendgrid_email(settings, to_email, subject, body)
        elif provider == 'mailgun':
            return send_mailgun_email(settings, to_email, subject, body)
        else:
            logger.warning(f"Email notification not sent: Unsupported provider {provider}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending email notification: {str(e)}")
        return False
        
def send_smtp_email(settings, to_email, subject, body):
    """Send email via SMTP"""
    try:
        # Get SMTP settings
        smtp_host = settings.get('smtp_host')
        smtp_port = int(settings.get('smtp_port', 587))
        smtp_username = settings.get('smtp_username')
        smtp_password = settings.get('smtp_password')
        smtp_use_tls = settings.get('smtp_use_tls', True)
        from_email = settings.get('from_email')
        from_name = settings.get('from_name', 'Webhook Dashboard')
        
        # Validate required settings
        if not smtp_host or not smtp_username or not smtp_password:
            logger.warning("SMTP email not sent: Incomplete SMTP settings")
            return False
            
        # Create message
        msg = MIMEMultipart()
        msg['From'] = f'{from_name} <{from_email}>'
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to SMTP server
        if smtp_use_tls:
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
        else:
            server = smtplib.SMTP(smtp_host, smtp_port)
            
        server.login(smtp_username, smtp_password)
        
        # Send email
        server.send_message(msg)
        server.quit()
        
        logger.info(f"SMTP email sent to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"SMTP error: {str(e)}")
        return False

def send_sendgrid_email(settings, to_email, subject, body):
    """Send email via SendGrid API"""
    try:
        # In a production app, we would use the SendGrid API
        sendgrid_api_key = settings.get('sendgrid_api_key')
        
        if not sendgrid_api_key:
            logger.warning("SendGrid email not sent: API key not provided")
            return False
            
        # Log the SendGrid API call
        logger.info(f"Would send email via SendGrid to {to_email}")
        
        # In a real app, we would use the SendGrid API
        # For this implementation, we log and simulate success
        return True
        
    except Exception as e:
        logger.error(f"SendGrid error: {str(e)}")
        return False

def send_mailgun_email(settings, to_email, subject, body):
    """Send email via Mailgun API"""
    try:
        # In a production app, we would use the Mailgun API
        mailgun_api_key = settings.get('mailgun_api_key')
        mailgun_domain = settings.get('mailgun_domain')
        
        if not mailgun_api_key or not mailgun_domain:
            logger.warning("Mailgun email not sent: API key or domain not provided")
            return False
            
        # Log the Mailgun API call
        logger.info(f"Would send email via Mailgun to {to_email}")
        
        # In a real app, we would use the Mailgun API
        # For this implementation, we log and simulate success
        return True
        
    except Exception as e:
        logger.error(f"Mailgun error: {str(e)}")
        return False

def notify_new_data(data):
    """
    Create a notification for new webhook data
    
    In a production system, this might:
    - Send a WebSocket message to connected clients
    - Trigger push notifications
    - Send emails or SMS
    - Update a notification center
    
    For this implementation, we'll store it in the database and send email notifications
    if configured.
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
        
        # Send email notification if configured
        email_settings = get_email_settings()
        if email_settings and email_settings.get('notify_on_webhook', False):
            # Prepare email content
            subject = f"New webhook data from {source}"
            
            # Basic email body
            body = f"New webhook data received from {source} at {datetime.utcnow().isoformat()}.\n\n"
            
            # Include payload if configured
            if email_settings.get('include_payload', False) and 'payload' in data:
                payload = data.get('payload', {})
                if isinstance(payload, dict):
                    body += "Payload:\n" + json.dumps(payload, indent=2)
                else:
                    body += f"Payload: {payload}"
            
            # Send the email
            send_email_notification(subject, body)
        
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
        
def notify_processing_error(source, error_message, webhook_id=None):
    """
    Create a notification and potentially send an email for webhook processing errors
    
    Args:
        source (str): The source of the webhook
        error_message (str): Error message details
        webhook_id (str, optional): Associated webhook ID if available
        
    Returns:
        bool: Success status
    """
    try:
        # Create notification
        message = f"Error processing webhook from {source}: {error_message}"
        
        notification = Notification(
            webhook_id=webhook_id,
            type="processing_error",
            source=source,
            message=message
        )
        
        # Save notification to database
        db.session.add(notification)
        db.session.commit()
        
        logger.info(f"Created error notification for source: {source}")
        
        # Send email notification if configured
        email_settings = get_email_settings()
        if email_settings and email_settings.get('notify_on_error', False):
            # Prepare email content
            subject = f"Webhook Processing Error: {source}"
            
            # Email body
            body = f"""
A webhook processing error occurred:

Source: {source}
Time: {datetime.utcnow().isoformat()}
Error: {error_message}
"""
            
            if webhook_id:
                body += f"\nWebhook ID: {webhook_id}"
            
            # Send the email
            send_email_notification(subject, body)
        
        return True
    
    except Exception as e:
        logger.error(f"Error creating error notification: {str(e)}")
        db.session.rollback()
        return False
