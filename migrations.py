import logging
import sqlite3
from app import app, db
from models import WebhookData, DataSource, Notification, Integration, ExternalStorage

logger = logging.getLogger(__name__)

def run_migrations():
    """
    Run database migrations to update schema
    """
    logger.info("Running database migrations...")
    
    with app.app_context():
        # Start with a clean connection
        db.session.close()
        
        # Execute independent statements to avoid transaction issues
        connection = db.engine.raw_connection()
        try:
            cursor = connection.cursor()
            
            # Check if we need to add columns to WebhookData table
            logger.info("Checking webhook_data table structure")
            
            # Get column names from SQLite pragma (SQLite-specific approach)
            cursor.execute("PRAGMA table_info(webhook_data)")
            columns = {row[1]: True for row in cursor.fetchall()}
            
            # Check for required columns
            has_source_subtype = 'source_subtype' in columns
            has_status = 'status' in columns
            has_raw_data = 'raw_data' in columns
            
            # Add missing columns if needed
            if not has_source_subtype:
                logger.info("Adding source_subtype column to webhook_data table")
                cursor.execute("ALTER TABLE webhook_data ADD COLUMN source_subtype VARCHAR(50)")
                cursor.execute("CREATE INDEX idx_webhook_data_source_subtype ON webhook_data (source_subtype)")
                connection.commit()
                
            if not has_status:
                logger.info("Adding status column to webhook_data table")
                cursor.execute("ALTER TABLE webhook_data ADD COLUMN status VARCHAR(20) DEFAULT 'processed'")
                cursor.execute("CREATE INDEX idx_webhook_data_status ON webhook_data (status)")
                connection.commit()
                
            if not has_raw_data:
                logger.info("Adding raw_data column to webhook_data table")
                cursor.execute("ALTER TABLE webhook_data ADD COLUMN raw_data TEXT")
                connection.commit()
            
            # Check if external_storage table exists (SQLite approach)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='external_storage'")
            has_external_storage = cursor.fetchone() is not None
            
            if not has_external_storage:
                logger.info("Creating external_storage table")
                cursor.execute("""
                    CREATE TABLE external_storage (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        storage_type VARCHAR(50) NOT NULL,
                        name VARCHAR(100) NOT NULL,
                        enabled BOOLEAN DEFAULT 0,
                        connection_string VARCHAR(500),
                        config JSON,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_sync TIMESTAMP,
                        sync_status VARCHAR(20) DEFAULT 'pending'
                    )
                """)
                connection.commit()
                logger.info("Successfully created external_storage table")
                
            logger.info("Database migrations completed successfully")
            cursor.close()
            return True
            
        except Exception as e:
            logger.error(f"Error during database migrations: {str(e)}")
            if hasattr(connection, 'rollback'):
                connection.rollback()
            return False
        finally:
            connection.close()

if __name__ == "__main__":
    run_migrations()