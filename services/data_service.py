import logging
import uuid
import json
import os
from datetime import datetime
import sqlalchemy
from sqlalchemy import create_engine, and_, func, MetaData
from app import db
from models import WebhookData, DataSource, ExternalStorage

logger = logging.getLogger(__name__)

def save_webhook_data(data, raw_data=None):
    """
    Save webhook data to the database with enhanced error handling and support for subtypes
    
    Args:
        data (dict): Processed webhook data including id, timestamp, source, etc.
        raw_data (str, optional): Raw request data for debugging/recovery
    
    Returns:
        bool: Success status
    """
    try:
        # Extract source subtype if present
        source_subtype = None
        status = 'processed'
        
        if data.get('data') and isinstance(data.get('data'), dict):
            # For form data, extract form_type as subtype
            if data.get('source') == 'form' and 'form_type' in data['data']:
                source_subtype = data['data']['form_type']
            
            # For newsletter data
            elif data.get('source') == 'form' and 'newsletter' in str(data['data']).lower():
                source_subtype = 'newsletter'
                
            # For CRM data, extract crm_type as subtype
            elif data.get('source') == 'crm' and 'crm_type' in data['data']:
                source_subtype = data['data']['crm_type']
                
            # For generic source detection
            elif 'source_subtype' in data['data']:
                source_subtype = data['data']['source_subtype']
                
            # Check if there was an error in processing
            if 'error' in data['data']:
                status = 'error'
        
        # Create a new WebhookData instance with enhanced fields
        webhook_data = WebhookData(
            id=data.get('id'),
            timestamp=data.get('timestamp'),
            source=data.get('source', 'other'),
            source_subtype=source_subtype,
            status=status,
            data=data.get('data', {}),
            raw_data=raw_data
        )
        
        # Save to database
        db.session.add(webhook_data)
        db.session.commit()
        
        logger.debug(f"Saved webhook data with ID: {data.get('id')}, source: {data.get('source')}, subtype: {source_subtype}")
        
        # Mirror to external storage if configured
        if status != 'error':
            try:
                mirror_to_external_storage(webhook_data)
            except Exception as mirror_error:
                logger.warning(f"Failed to mirror webhook data to external storage: {str(mirror_error)}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error saving webhook data: {str(e)}")
        db.session.rollback()
        
        # Attempt to save with minimal data if normal save fails
        try:
            minimal_data = WebhookData(
                id=data.get('id', str(uuid.uuid4())),
                timestamp=data.get('timestamp', datetime.utcnow()),
                source='error',
                status='save_failed',
                data={'error': str(e), 'original_source': data.get('source')},
                raw_data=raw_data or str(data)
            )
            db.session.add(minimal_data)
            db.session.commit()
            logger.info(f"Saved minimal error data after failure: {minimal_data.id}")
        except Exception as recovery_error:
            logger.error(f"Failed to save even minimal error data: {str(recovery_error)}")
            
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
        
        # Filter by source (case-insensitive)
        if source_filter:
            # Handle case-insensitive search by using SQLAlchemy's func.lower()
            query = query.filter(func.lower(WebhookData.source) == func.lower(source_filter))
        
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
            {"id": "newsletter", "name": "Newsletter Subscriptions", "color": "#888888"},
            {"id": "scanner", "name": "Document Scanner", "color": "#FF9800"},
            {"id": "other", "name": "Other Sources", "color": "#9C27B0"}
        ]

def mirror_to_external_storage(webhook_data):
    """
    Mirror webhook data to configured external storage systems
    
    Args:
        webhook_data (WebhookData): The webhook data to mirror
    
    Returns:
        bool: Success status
    """
    try:
        # Get enabled external storage configurations
        storage_configs = ExternalStorage.query.filter_by(enabled=True).all()
        
        if not storage_configs:
            # No external storage configured or enabled
            return True
            
        success = True
        webhook_dict = webhook_data.to_dict()
        
        for storage in storage_configs:
            try:
                if storage.storage_type == 'database':
                    success = success and mirror_to_external_database(webhook_dict, storage)
                elif storage.storage_type == 'file':
                    success = success and mirror_to_file_storage(webhook_dict, storage)
                # Add more storage types as needed
                
                if success:
                    # Update last sync time
                    storage.last_sync = datetime.utcnow()
                    storage.sync_status = 'success'
                    db.session.commit()
                    
            except Exception as e:
                storage.sync_status = 'error'
                db.session.commit()
                logger.error(f"Error mirroring to {storage.name} (ID: {storage.id}): {str(e)}")
                success = False
                
        return success
        
    except Exception as e:
        logger.error(f"Error in mirror_to_external_storage: {str(e)}")
        return False


def mirror_to_external_database(webhook_data, storage_config):
    """
    Mirror webhook data to an external database
    
    Args:
        webhook_data (dict): The webhook data dictionary
        storage_config (ExternalStorage): The external storage configuration
    
    Returns:
        bool: Success status
    """
    try:
        # Get connection details from storage configuration
        connection_string = storage_config.connection_string
        
        if not connection_string:
            logger.warning(f"No connection string for external storage {storage_config.name}")
            return False
            
        # Create database engine
        engine = create_engine(connection_string)
        
        # Define the table structure
        metadata = MetaData()
        webhook_table = sqlalchemy.Table(
            'external_webhooks', metadata,
            sqlalchemy.Column('id', sqlalchemy.String(36), primary_key=True),
            sqlalchemy.Column('timestamp', sqlalchemy.DateTime),
            sqlalchemy.Column('source', sqlalchemy.String(50)),
            sqlalchemy.Column('source_subtype', sqlalchemy.String(50)),
            sqlalchemy.Column('status', sqlalchemy.String(20)),
            sqlalchemy.Column('data', sqlalchemy.JSON),
            sqlalchemy.Column('synced_at', sqlalchemy.DateTime)
        )
        
        # Create table if it doesn't exist
        metadata.create_all(engine)
        
        # Insert or update data
        with engine.connect() as conn:
            # Check if record exists
            result = conn.execute(
                sqlalchemy.text("SELECT id FROM external_webhooks WHERE id = :id"),
                {"id": webhook_data['id']}
            )
            exists = result.fetchone() is not None
            
            if exists:
                # Update existing record
                conn.execute(
                    sqlalchemy.text("""
                        UPDATE external_webhooks
                        SET timestamp = :timestamp,
                            source = :source,
                            source_subtype = :source_subtype,
                            status = :status,
                            data = :data,
                            synced_at = :synced_at
                        WHERE id = :id
                    """),
                    {
                        "id": webhook_data['id'],
                        "timestamp": datetime.fromisoformat(webhook_data['timestamp']),
                        "source": webhook_data['source'],
                        "source_subtype": webhook_data.get('source_subtype'),
                        "status": webhook_data.get('status', 'processed'),
                        "data": json.dumps(webhook_data['data']),
                        "synced_at": datetime.utcnow()
                    }
                )
            else:
                # Insert new record
                conn.execute(
                    sqlalchemy.text("""
                        INSERT INTO external_webhooks
                        (id, timestamp, source, source_subtype, status, data, synced_at)
                        VALUES
                        (:id, :timestamp, :source, :source_subtype, :status, :data, :synced_at)
                    """),
                    {
                        "id": webhook_data['id'],
                        "timestamp": datetime.fromisoformat(webhook_data['timestamp']),
                        "source": webhook_data['source'],
                        "source_subtype": webhook_data.get('source_subtype'),
                        "status": webhook_data.get('status', 'processed'),
                        "data": json.dumps(webhook_data['data']),
                        "synced_at": datetime.utcnow()
                    }
                )
            
            # Commit the transaction
            conn.commit()
            
        return True
        
    except Exception as e:
        logger.error(f"Error mirroring to external database: {str(e)}")
        return False


def mirror_to_file_storage(webhook_data, storage_config):
    """
    Mirror webhook data to a file storage system
    
    Args:
        webhook_data (dict): The webhook data dictionary
        storage_config (ExternalStorage): The external storage configuration
    
    Returns:
        bool: Success status
    """
    try:
        # Get storage directory from configuration
        storage_dir = storage_config.config.get('directory')
        
        if not storage_dir:
            logger.warning(f"No directory specified for file storage {storage_config.name}")
            return False
            
        # Create directory if it doesn't exist
        os.makedirs(storage_dir, exist_ok=True)
        
        # Generate filename based on timestamp and ID
        timestamp = datetime.fromisoformat(webhook_data['timestamp'])
        filename = f"{timestamp.strftime('%Y%m%d%H%M%S')}_{webhook_data['source']}_{webhook_data['id']}.json"
        filepath = os.path.join(storage_dir, filename)
        
        # Write data to file
        with open(filepath, 'w') as f:
            json.dump(webhook_data, f, indent=2)
            
        return True
        
    except Exception as e:
        logger.error(f"Error mirroring to file storage: {str(e)}")
        return False


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
        
        # Count by source subtype
        subtype_counts = db.session.query(
            WebhookData.source,
            WebhookData.source_subtype,
            func.count(WebhookData.id)
        ).filter(WebhookData.source_subtype.isnot(None)).group_by(
            WebhookData.source, WebhookData.source_subtype
        ).all()
        
        stats['by_subtype'] = {}
        for source, subtype, count in subtype_counts:
            if source not in stats['by_subtype']:
                stats['by_subtype'][source] = {}
            stats['by_subtype'][source][subtype] = count
        
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
        
        # Add status statistics
        status_counts = db.session.query(
            WebhookData.status,
            func.count(WebhookData.id)
        ).group_by(WebhookData.status).all()
        
        stats['by_status'] = {status: count for status, count in status_counts}
        
        return stats
    
    except Exception as e:
        logger.error(f"Error retrieving webhook stats: {str(e)}")
        return {
            'total': 0,
            'by_source': {},
            'by_subtype': {},
            'by_status': {},
            'daily': {}
        }
