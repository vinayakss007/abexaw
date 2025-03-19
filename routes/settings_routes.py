
from flask import Blueprint, jsonify, request, render_template
import pytz
from models import db, Integration

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
        return jsonify({'status': 'error', 'message': str(e)}), 500
