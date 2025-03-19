from datetime import datetime
import json
from app import db

class WebhookData(db.Model):
    """Model for storing webhook data"""
    __tablename__ = 'webhook_data'
    
    id = db.Column(db.String(36), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    source = db.Column(db.String(50), nullable=False, index=True)
    payload = db.Column(db.JSON)
    
    def __init__(self, id, timestamp, source, data):
        self.id = id
        self.timestamp = datetime.fromisoformat(timestamp) if isinstance(timestamp, str) else timestamp
        self.source = source
        self.payload = data
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
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