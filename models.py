from datetime import datetime
import json
from db_config import db

class WebhookData(db.Model):
    """Model for storing webhook data"""
    __tablename__ = 'webhook_data'
    
    id = db.Column(db.String(36), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    source = db.Column(db.String(50), nullable=False, index=True)
    # Separate column for the sub-type of the source (e.g., newsletter, collection_form within 'form' source)
    source_subtype = db.Column(db.String(50), nullable=True, index=True)
    status = db.Column(db.String(20), nullable=True, index=True, default='processed')
    payload = db.Column(db.JSON)
    # Store raw data in case of parsing issues
    raw_data = db.Column(db.Text, nullable=True)
    
    def __init__(self, id, timestamp, source, data, source_subtype=None, status='processed', raw_data=None):
        self.id = id
        self.timestamp = datetime.fromisoformat(timestamp) if isinstance(timestamp, str) else timestamp
        self.source = source
        self.source_subtype = source_subtype
        self.status = status
        self.payload = data
        self.raw_data = raw_data
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'source_subtype': self.source_subtype,
            'status': self.status,
            'data': self.payload
        }

class DataSource(db.Model):
    """Model for webhook data sources"""
    __tablename__ = 'data_sources'
    
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(20), nullable=False)
    
    def __init__(self, id, name, color):
        self.id = id
        self.name = name
        self.color = color
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color
        }

class Notification(db.Model):
    """Model for storing notifications"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    webhook_id = db.Column(db.String(36), db.ForeignKey('webhook_data.id', ondelete='CASCADE'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.Column(db.String(50), nullable=False)
    source = db.Column(db.String(50), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    read = db.Column(db.Boolean, default=False)
    
    def __init__(self, webhook_id, type, source, message, read=False):
        self.webhook_id = webhook_id
        self.timestamp = datetime.utcnow()
        self.type = type
        self.source = source
        self.message = message
        self.read = read
    
    def to_dict(self):
        return {
            'id': self.id,
            'webhook_id': self.webhook_id,
            'timestamp': self.timestamp.isoformat(),
            'type': self.type,
            'source': self.source,
            'message': self.message,
            'read': self.read
        }

class Integration(db.Model):
    """Model for storing integration settings"""
    __tablename__ = 'integrations'
    
    id = db.Column(db.Integer, primary_key=True)
    integration_type = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    enabled = db.Column(db.Boolean, default=False)
    settings = db.Column(db.JSON)
    
    def __init__(self, integration_type, name, enabled=False, settings=None):
        self.integration_type = integration_type
        self.name = name
        self.enabled = enabled
        self.settings = settings or {}
    
    def to_dict(self):
        return {
            'id': self.id,
            'integration_type': self.integration_type,
            'name': self.name,
            'enabled': self.enabled,
            'settings': self.settings
        }

class ExternalStorage(db.Model):
    """Model for storing external storage configurations"""
    __tablename__ = 'external_storage'
    
    id = db.Column(db.Integer, primary_key=True)
    storage_type = db.Column(db.String(50), nullable=False)  # 'database', 's3', 'gcs', etc.
    name = db.Column(db.String(100), nullable=False)
    enabled = db.Column(db.Boolean, default=False)
    connection_string = db.Column(db.String(500), nullable=True)  # Encrypted or masked in responses
    config = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_sync = db.Column(db.DateTime, nullable=True)
    sync_status = db.Column(db.String(20), default='pending')
    
    def __init__(self, storage_type, name, enabled=False, connection_string=None, config=None):
        self.storage_type = storage_type
        self.name = name
        self.enabled = enabled
        self.connection_string = connection_string
        self.config = config or {}
        self.created_at = datetime.utcnow()
    
    def to_dict(self, mask_connection=True):
        result = {
            'id': self.id,
            'storage_type': self.storage_type,
            'name': self.name,
            'enabled': self.enabled,
            'config': self.config,
            'created_at': self.created_at.isoformat(),
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'sync_status': self.sync_status
        }
        
        # Mask connection string in responses for security
        if mask_connection and self.connection_string:
            result['connection_string'] = '******'
        elif not mask_connection:
            result['connection_string'] = self.connection_string
            
        return result