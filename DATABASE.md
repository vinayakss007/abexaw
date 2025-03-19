# ABEX Business Dashboard - Database Documentation

## Overview

ABEX Business Dashboard uses PostgreSQL as its primary database for storing webhook data, notifications, data sources, and integration configurations. This document describes the database setup, models, and how the application interacts with the database.

## Database Configuration

The application uses SQLAlchemy ORM to interact with the PostgreSQL database. The database connection is configured in `app.py` using environment variables:

```python
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
```

The PostgreSQL connection string is provided through the `DATABASE_URL` environment variable, which is automatically set up in the Replit environment.

## Environment Variables

The following environment variables are used for database configuration:

- `DATABASE_URL`: Full PostgreSQL connection string
- `PGHOST`: PostgreSQL server host
- `PGPORT`: PostgreSQL server port
- `PGUSER`: PostgreSQL username
- `PGPASSWORD`: PostgreSQL password
- `PGDATABASE`: PostgreSQL database name

## Data Models

The application defines the following data models in `models.py`:

### WebhookData

Stores incoming webhook data from external sources. The system supports multi-source webhooks with automatic source detection.

| Field      | Type      | Description                                   |
|------------|-----------|-----------------------------------------------|
| id         | String    | Primary key, unique ID for the webhook        |
| timestamp  | DateTime  | When the webhook was received                 |
| source     | String    | Source identifier (e.g., 'stripe', 'paypal', 'form', 'crm') |
| payload    | JSON      | The processed webhook payload data            |

#### Webhook Data Structure

The payload field stores normalized data based on the source type. Each processor transforms raw data into a standardized format:

**Common Fields (All Sources)**
- `source`: String identifying the data source
- `processed`: Boolean indicating successful processing
- `original_data`: The original webhook payload (for reference)

**Form Submissions Structure**
```json
{
  "source": "form",
  "form_type": "contact_form",
  "submission_data": {
    "message": "Hello, I'm interested in your service",
    "product": "Premium Plan"
  },
  "contact_info": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "555-1234"
  },
  "metadata": {
    "user_agent": "Mozilla/5.0...",
    "referer": "https://example.com/contact"
  }
}
```

**Payment Provider Structure (Stripe/PayPal)**
```json
{
  "source": "stripe",
  "event_type": "payment_intent_succeeded",
  "payment_status": "completed",
  "amount": 5999,
  "customer_email": "customer@example.com",
  "customer_name": "Jane Smith",
  "transaction_id": "pi_3O4mlkJH87d..."
}
```

**Google Analytics Structure**
```json
{
  "source": "google_analytics",
  "event_type": "page_view",
  "page_path": "/products",
  "user_type": "new",
  "session_id": "GA1.2.1234567890",
  "timestamp": "2024-03-16T10:30:00Z"
}
```

**Facebook Integration Structure**
```json
{
  "source": "facebook",
  "event_type": "page_interaction",
  "action": "like",
  "page_id": "123456789",
  "user_id": "fb_user_123",
  "timestamp": "2024-03-16T10:30:00Z"
}
```

**CRM Structure**
```json
{
  "source": "crm",
  "crm_type": "salesforce",
  "event_type": "lead_created",
  "entity_type": "lead",
  "entity_data": {
    "name": "Alice Johnson",
    "email": "alice@company.com",
    "status": "new",
    "value": 5000
  }
}
```

### DataSource

Defines available webhook data sources and their display properties.

| Field      | Type      | Description                                   |
|------------|-----------|-----------------------------------------------|
| id         | String    | Primary key, source identifier                |
| name       | String    | Display name for the source                   |
| color      | String    | Hex color code for UI display                 |

### Notification

Stores notifications about webhook events.

| Field      | Type      | Description                                   |
|------------|-----------|-----------------------------------------------|
| id         | Integer   | Primary key, auto-incrementing                |
| webhook_id | String    | Foreign key to WebhookData                    |
| timestamp  | DateTime  | When the notification was created             |
| type       | String    | Notification type                             |
| source     | String    | Data source identifier                        |
| message    | String    | Notification message                          |
| read       | Boolean   | Whether the notification has been read        |

### Integration

Stores integration settings for external services.

| Field           | Type      | Description                                   |
|-----------------|-----------|-----------------------------------------------|
| id              | Integer   | Primary key, auto-incrementing                |
| integration_type| String    | Type of integration (e.g., 'email', 'stripe', 'paypal', 'google_analytics', 'whatsapp', 'facebook') |
| name            | String    | Display name for the integration              |
| enabled         | Boolean   | Whether the integration is enabled            |
| settings        | JSON      | Integration-specific settings                 |

## Database Initialization

The database tables are automatically created when the application starts, using SQLAlchemy's `create_all()` method:

```python
with app.app_context():
    db.create_all()
    
    # Initialize default data sources if not exists
    from models import DataSource
    default_sources = [
        {"id": "stripe", "name": "Stripe Payments", "color": "#6772E5"},
        {"id": "paypal", "name": "PayPal", "color": "#003087"},
        {"id": "crm", "name": "CRM System", "color": "#4CAF50"},
        {"id": "form", "name": "Web Forms", "color": "#2196F3"},
        {"id": "email", "name": "Email Service", "color": "#F44336"},
        {"id": "cart", "name": "Shopping Cart", "color": "#FF9800"},
        {"id": "other", "name": "Other Sources", "color": "#9C27B0"}
    ]
    
    # Check if data sources exist before adding
    for source in default_sources:
        if not DataSource.query.filter_by(id=source["id"]).first():
            db.session.add(DataSource(**source))
    
    db.session.commit()
```

## API Endpoints

The application provides the following database-related API endpoints:

### Webhook Data

- `GET /api/webhook/data`: Retrieve webhook data with optional filtering
- `POST /api/webhook`: Submit new webhook data from any source (auto-detected)
- `POST /api/webhook/secure`: Submit webhook data with signature validation
- `GET /api/webhook/export`: Export webhook data in various formats (JSON, CSV, Excel)

### Dashboard

- `GET /api/dashboard/summary`: Get dashboard summary statistics

### Integrations

- `GET /api/integrations`: List all integrations
- `GET /api/integrations/<id>`: Get a specific integration
- `POST /api/integrations`: Create a new integration
- `PUT /api/integrations/<id>`: Update an existing integration
- `DELETE /api/integrations/<id>`: Delete an integration

## Database Services

The application includes several service modules for interacting with the database:

### data_service.py

Provides functions for working with webhook data and data sources:

- `save_webhook_data()`: Save new webhook data
- `get_webhook_data()`: Retrieve webhook data with filtering options
- `get_data_sources()`: Get the list of data sources
- `get_webhook_stats()`: Get statistics about webhooks

### notification_service.py

Manages webhook notifications:

- `notify_new_data()`: Create a notification for new webhook data
- `get_notifications()`: Get recent notifications
- `mark_notification_read()`: Mark notifications as read
- `mark_all_notifications_read()`: Mark all notifications as read
- `delete_old_notifications()`: Delete notifications older than specified days

### integration_service.py

Handles integration settings:

- `get_integrations()`: Get all configured integrations
- `get_integration()`: Get a specific integration
- `save_integration()`: Save integration settings
- `delete_integration()`: Delete an integration

### webhook_processor.py

Processes incoming webhooks from various sources:

- `process_webhook()`: Main entry point for webhook processing
- `determine_source()`: Automatically detect the webhook source
- `validate_webhook_signature()`: Validate webhook signatures for secure endpoints
- Source-specific processors:
  - `process_stripe_webhook()`: Process Stripe payment events
  - `process_paypal_webhook()`: Process PayPal payment notifications
  - `process_form_webhook()`: Process form submissions
  - `process_crm_webhook()`: Process CRM data updates
  - `generic_processor()`: Process webhooks from unknown sources

### export_service.py

Provides data export functionality:

- `export_data_as_json()`: Export webhook data as JSON
- `export_data_as_csv()`: Export webhook data as CSV
- `export_data_as_excel()`: Export webhook data as Excel spreadsheet
- `flatten_webhook_data()`: Transform webhook data for tabular formats

## Data Export Capabilities

The application provides robust data export capabilities through the `export_service.py` module. This allows users to export webhook data in various formats for analysis, reporting, and integration with other systems.

### Supported Export Formats

1. **JSON Export**
   - Configurable pretty-printing for readability
   - Complete webhook data with all nested structures preserved
   - Perfect for programmatic integration with other systems

2. **CSV Export**
   - Flattened data structure for tabular representation
   - Compatible with spreadsheet applications and data analysis tools
   - Includes headers for all available data fields

3. **Excel Export**
   - Full-featured Excel workbooks with formatted data
   - Auto-adjusted column widths for readability
   - Tabular data optimized for business reporting

### Data Transformation for Export

When exporting to tabular formats (CSV and Excel), the webhook data undergoes transformation via the `flatten_webhook_data()` function. This process:

1. Extracts top-level properties (id, timestamp, source)
2. Flattens nested structures with prefixed keys (e.g., `data_event_type`, `contact_email`)
3. Handles special data structures like contact information and entity data
4. Converts complex values to strings for compatibility

### Export Filtering

All export endpoints support the same filtering options as the data retrieval endpoint:

- Filter by source (e.g., only Stripe webhooks)
- Filter by date range (from/to)
- Custom formatting options (like pretty-printing for JSON)

## Best Practices

When working with the database in this application, follow these practices:

1. Use the service functions rather than direct database calls from routes
2. Handle database errors gracefully with try/except blocks
3. Always commit or rollback transactions to prevent connection leaks
4. Use proper filtering and limiting in queries to improve performance
5. Keep transaction scope as small as possible
6. Use the webhook processor system when adding new data sources
7. Leverage the export service for data integration with external systems