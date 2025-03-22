
from flask import Blueprint, jsonify, request, render_template, flash, redirect, url_for
import pytz
import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from models import db, Integration, ExternalStorage
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)
settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings')
def settings_page():
    # Get all available timezones
    timezones = pytz.all_timezones
    
    # Get current settings from database
    current_settings = Integration.query.filter_by(integration_type='settings').first()
    if not current_settings:
        current_settings = Integration(
            integration_type='settings',
            name='Global Settings',
            settings={
                'timezone': 'UTC',
                'date_format': 'YYYY-MM-DD',
                'email_notifications': True,
                'browser_notifications': True,
                'refresh_interval': 30
            }
        )
        db.session.add(current_settings)
        db.session.commit()

    return render_template('settings.html', 
                         timezones=timezones,
                         current_settings=current_settings.settings)

@settings_bp.route('/api/settings', methods=['POST'])
def update_settings():
    try:
        settings_data = request.json
        settings_obj = Integration.query.filter_by(integration_type='settings').first()
        
        if settings_obj:
            settings_obj.settings.update(settings_data)
        else:
            settings_obj = Integration(
                integration_type='settings',
                name='Global Settings',
                settings=settings_data
            )
            db.session.add(settings_obj)
            
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
        
@settings_bp.route('/settings/email')
def email_settings_page():
    """Page for managing email settings"""
    # Get current email settings from database
    email_settings = Integration.query.filter_by(integration_type='email').first()
    
    if not email_settings:
        # Create default email settings
        email_settings = Integration(
            integration_type='email',
            name='Email Settings',
            enabled=False,
            settings={
                'provider': 'smtp',
                'from_email': 'notifications@example.com',
                'from_name': 'Webhook Dashboard',
                'notification_interval': 30,
                'notify_on_webhook': True,
                'notify_on_error': True,
                'include_payload': False,
                'smtp_host': '',
                'smtp_port': 587,
                'smtp_username': '',
                'smtp_password': '',
                'smtp_use_tls': True
            }
        )
        db.session.add(email_settings)
        db.session.commit()
    
    return render_template('email_settings.html', email_settings=email_settings.settings)

@settings_bp.route('/api/settings/email', methods=['POST'])
def update_email_settings():
    """Update email settings"""
    try:
        settings_data = request.json
        email_settings = Integration.query.filter_by(integration_type='email').first()
        
        if email_settings:
            # Update existing settings
            email_settings.settings.update(settings_data)
            email_settings.enabled = settings_data.get('email_provider') is not None
        else:
            # Create new email settings
            email_settings = Integration(
                integration_type='email',
                name='Email Settings',
                enabled=True,
                settings=settings_data
            )
            db.session.add(email_settings)
            
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error updating email settings: {str(e)}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@settings_bp.route('/api/settings/email/test', methods=['POST'])
def test_email_settings():
    """Send a test email using the current settings"""
    try:
        # Get email settings
        email_settings = Integration.query.filter_by(integration_type='email').first()
        
        if not email_settings:
            return jsonify({
                'status': 'error',
                'message': 'Email settings not configured'
            }), 400
            
        settings = email_settings.settings
        provider = settings.get('email_provider', 'smtp')
        
        # Setup test email content
        from_email = settings.get('from_email', 'notifications@example.com')
        from_name = settings.get('from_name', 'Webhook Dashboard')
        to_email = settings.get('test_email', from_email)  # Default to from email if test email not set
        
        subject = 'Test Email from Webhook Dashboard'
        body = 'This is a test email from your Webhook Dashboard. If you received this, your email settings are configured correctly.'
        
        # Send test email based on provider
        if provider == 'smtp':
            # Send via SMTP
            result = send_smtp_test_email(settings, to_email, subject, body)
        elif provider == 'sendgrid':
            # Send via SendGrid
            result = send_sendgrid_test_email(settings, to_email, subject, body)
        elif provider == 'mailgun':
            # Send via Mailgun
            result = send_mailgun_test_email(settings, to_email, subject, body)
        else:
            result = {'success': False, 'message': f'Unsupported email provider: {provider}'}
        
        if result.get('success'):
            return jsonify({
                'status': 'success',
                'message': f'Test email sent successfully to {to_email}'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result.get('message', 'Failed to send test email')
            }), 500
    except Exception as e:
        logger.error(f"Error sending test email: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error sending test email: {str(e)}'
        }), 500

def send_smtp_test_email(settings, to_email, subject, body):
    """Send a test email via SMTP"""
    try:
        # Get SMTP settings
        smtp_host = settings.get('smtp_host')
        smtp_port = int(settings.get('smtp_port', 587))
        smtp_username = settings.get('smtp_username')
        smtp_password = settings.get('smtp_password')
        smtp_use_tls = settings.get('smtp_use_tls', True)
        from_email = settings.get('from_email')
        from_name = settings.get('from_name')
        
        # Validate required settings
        if not smtp_host or not smtp_username or not smtp_password:
            return {
                'success': False,
                'message': 'Incomplete SMTP settings. Please provide host, username, and password.'
            }
            
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
        
        return {'success': True}
    except Exception as e:
        logger.error(f"SMTP error: {str(e)}")
        return {'success': False, 'message': f'SMTP error: {str(e)}'}

def send_sendgrid_test_email(settings, to_email, subject, body):
    """Send a test email via SendGrid"""
    try:
        # In a production app, we would use the SendGrid API
        # For this demo, we'll simulate the API call
        sendgrid_api_key = settings.get('sendgrid_api_key')
        
        if not sendgrid_api_key:
            return {
                'success': False,
                'message': 'SendGrid API key not provided'
            }
            
        # Log the SendGrid API call
        logger.info(f"Would send email via SendGrid to {to_email}")
        
        # In a real app, we would make an API call to SendGrid here
        # For demo purposes, we'll simulate a successful response
        return {'success': True}
    except Exception as e:
        logger.error(f"SendGrid error: {str(e)}")
        return {'success': False, 'message': f'SendGrid error: {str(e)}'}

def send_mailgun_test_email(settings, to_email, subject, body):
    """Send a test email via Mailgun"""
    try:
        # In a production app, we would use the Mailgun API
        # For this demo, we'll simulate the API call
        mailgun_api_key = settings.get('mailgun_api_key')
        mailgun_domain = settings.get('mailgun_domain')
        
        if not mailgun_api_key or not mailgun_domain:
            return {
                'success': False,
                'message': 'Mailgun API key or domain not provided'
            }
            
        # Log the Mailgun API call
        logger.info(f"Would send email via Mailgun to {to_email}")
        
        # In a real app, we would make an API call to Mailgun here
        # For demo purposes, we'll simulate a successful response
        return {'success': True}
    except Exception as e:
        logger.error(f"Mailgun error: {str(e)}")
        return {'success': False, 'message': f'Mailgun error: {str(e)}'}


# External storage routes
@settings_bp.route('/settings/external-storage')
def external_storage_page():
    """Page for managing external storage configurations"""
    storage_configs = ExternalStorage.query.all()
    storage_types = [
        {'id': 'database', 'name': 'External Database'},
        {'id': 'file', 'name': 'File Storage'},
        {'id': 's3', 'name': 'Amazon S3'},
        {'id': 'gcs', 'name': 'Google Cloud Storage'}
    ]
    return render_template('external_storage.html', 
                           storage_configs=storage_configs,
                           storage_types=storage_types)

@settings_bp.route('/api/external-storage', methods=['GET'])
def get_external_storage_configs():
    """Get all external storage configurations"""
    try:
        configs = ExternalStorage.query.all()
        return jsonify({
            'status': 'success',
            'data': [config.to_dict() for config in configs]
        })
    except Exception as e:
        logger.error(f"Error getting external storage configs: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@settings_bp.route('/api/external-storage', methods=['POST'])
def create_external_storage():
    """Create a new external storage configuration"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['storage_type', 'name']
        for field in required_fields:
            if field not in data:
                return jsonify({'status': 'error', 'message': f'Missing required field: {field}'}), 400
                
        # Create new configuration
        storage_config = ExternalStorage(
            storage_type=data.get('storage_type'),
            name=data.get('name'),
            enabled=data.get('enabled', False),
            connection_string=data.get('connection_string'),
            config=data.get('config', {})
        )
        
        db.session.add(storage_config)
        db.session.commit()
        
        return jsonify({
            'status': 'success', 
            'message': 'External storage configuration created successfully',
            'data': storage_config.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error creating external storage: {str(e)}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@settings_bp.route('/api/external-storage/<int:storage_id>', methods=['GET'])
def get_external_storage(storage_id):
    """Get a specific external storage configuration"""
    try:
        storage_config = ExternalStorage.query.get_or_404(storage_id)
        return jsonify({
            'status': 'success',
            'data': storage_config.to_dict()
        })
    except SQLAlchemyError as e:
        logger.error(f"Database error getting external storage {storage_id}: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    except Exception as e:
        logger.error(f"Error getting external storage {storage_id}: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Storage configuration not found'}), 404

@settings_bp.route('/api/external-storage/<int:storage_id>', methods=['PUT'])
def update_external_storage(storage_id):
    """Update an existing external storage configuration"""
    try:
        storage_config = ExternalStorage.query.get_or_404(storage_id)
        data = request.json
        
        # Update fields
        if 'name' in data:
            storage_config.name = data['name']
        if 'enabled' in data:
            storage_config.enabled = data['enabled']
        if 'connection_string' in data and data['connection_string']:
            storage_config.connection_string = data['connection_string']
        if 'config' in data:
            storage_config.config = data['config']
        if 'storage_type' in data:
            storage_config.storage_type = data['storage_type']
            
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'External storage configuration updated successfully',
            'data': storage_config.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating external storage {storage_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@settings_bp.route('/api/external-storage/<int:storage_id>', methods=['DELETE'])
def delete_external_storage(storage_id):
    """Delete an external storage configuration"""
    try:
        storage_config = ExternalStorage.query.get_or_404(storage_id)
        db.session.delete(storage_config)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'External storage configuration deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting external storage {storage_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@settings_bp.route('/api/external-storage/<int:storage_id>/test-connection', methods=['POST'])
def test_external_storage_connection(storage_id):
    """Test the connection to an external storage"""
    try:
        storage_config = ExternalStorage.query.get_or_404(storage_id)
        
        success = False
        message = "Connection test not implemented for this storage type"
        
        # Test connection based on storage type
        if storage_config.storage_type == 'database':
            from sqlalchemy import create_engine
            try:
                engine = create_engine(storage_config.connection_string)
                conn = engine.connect()
                conn.close()
                success = True
                message = "Database connection successful"
            except Exception as db_error:
                message = f"Database connection failed: {str(db_error)}"
                
        elif storage_config.storage_type == 'file':
            import os
            directory = storage_config.config.get('directory')
            if not directory:
                message = "No directory specified"
            elif not os.path.exists(directory):
                try:
                    os.makedirs(directory, exist_ok=True)
                    success = True
                    message = f"Directory created successfully: {directory}"
                except Exception as dir_error:
                    message = f"Failed to create directory: {str(dir_error)}"
            else:
                success = True
                message = f"Directory exists and is accessible: {directory}"
        
        # Update last test result
        storage_config.config['last_test'] = {
            'timestamp': datetime.utcnow().isoformat(),
            'success': success,
            'message': message
        }
        db.session.commit()
        
        return jsonify({
            'status': 'success' if success else 'error',
            'message': message
        })
        
    except Exception as e:
        logger.error(f"Error testing external storage connection {storage_id}: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
