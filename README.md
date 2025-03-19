# ABEX Business Dashboard

![ABEX Logo](./aBETwORLKS.png)

A Flask-based custom business dashboard with multi-source webhook data capture capabilities and service integrations for real-time data visualization.

## Features

- **Advanced Webhook System**: Capture, process, and store data from multiple sources with automatic source detection
- **Multi-source Support**: Process webhooks from various sources including payment providers (Stripe, PayPal), forms, CRMs, and more
- **Data Export**: Export webhook data in JSON, CSV, and Excel formats
- **Secure Webhooks**: Validate webhook signatures for enhanced security
- **PostgreSQL Database**: Persistent storage using PostgreSQL for all application data
- **Real-time Dashboard**: Visualize webhook data with charts and statistics
- **Service Integrations**: Connect with Google Analytics, Facebook, WhatsApp, Stripe, PayPal, and CRM services
- **Notification System**: Get notified when new webhook data arrives
- **Advanced Filtering**: Filter and search webhook data by source, date range, and more
- **Customizable Settings**: Configure timezone and display preferences for better user experience

## Architecture

The application is built on a modular architecture:

- **Routes**: Handle HTTP requests and responses
- **Services**: Business logic and data access
- **Models**: Database structure and relationships
- **Utils**: Helper functions and utilities
- **Templates**: HTML templates for the web interface
- **Static**: CSS, JavaScript, and other static assets

## Database

The application uses PostgreSQL for data storage. See [DATABASE.md](DATABASE.md) for detailed database documentation.

## API Endpoints

### Webhook Endpoints

- `POST /api/webhook`: Receive webhook data from any source (auto-detected)
- `POST /api/webhook/secure`: Receive webhook data with signature validation
- `GET /api/webhook/test`: Test webhook endpoint
- `GET /api/webhook/data`: Get webhook data with optional filtering
- `GET /api/webhook/export`: Export webhook data (JSON, CSV, Excel)

### Dashboard Endpoints

- `GET /api/dashboard/summary`: Get dashboard summary data

### Integration Endpoints

- `POST /api/integrations/email`: Send email notification
- `POST /api/integrations/stripe`: Handle Stripe webhooks
- `POST /api/integrations/paypal`: Handle PayPal webhooks
- `POST /api/integrations/google-analytics`: Handle Google Analytics events
- `POST /api/integrations/whatsapp`: Handle WhatsApp Business API
- `POST /api/integrations/facebook`: Handle Facebook webhooks
- `POST /api/integrations/crm`: Integration with CRM
- `GET /api/integrations`: List all integrations
- `GET /api/integrations/<id>`: Get a specific integration
- `POST /api/integrations`: Create a new integration
- `PUT /api/integrations/<id>`: Update an existing integration
- `DELETE /api/integrations/<id>`: Delete an integration

## Webhook Integration Guide

### Sending Data to the Webhook Endpoint

The webhook system supports multiple data sources and formats. You can send data to the webhook endpoint using any of the following methods:

### 1. Direct HTTP Request

```bash
# Basic webhook with source detection
curl -X POST https://yourdomain.com/api/webhook \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com","message":"Hello from the form"}'

# With explicit source
curl -X POST https://yourdomain.com/api/webhook \
  -H "Content-Type: application/json" \
  -d '{"source":"custom_app","event_type":"user_action","user_id":"123"}'
  
# Secure webhook with signature validation
curl -X POST https://yourdomain.com/api/webhook/secure \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: your-computed-signature" \
  -d '{"source":"secure_app","event":"data_update","data":{"id":123}}'
```

### 2. Form Submissions

HTML forms can post directly to the webhook endpoint:

```html
<form action="https://yourdomain.com/api/webhook" method="post">
  <input type="hidden" name="source" value="contact_form">
  <input type="text" name="name" placeholder="Your Name">
  <input type="email" name="email" placeholder="Your Email">
  <textarea name="message" placeholder="Your Message"></textarea>
  <button type="submit">Send</button>
</form>
```

### 3. Third-Party Integration

#### Stripe Webhooks

1. Go to Stripe Dashboard > Developers > Webhooks
2. Add an endpoint: `https://yourdomain.com/api/webhook`
3. Select events to send (e.g., `payment_intent.succeeded`, `checkout.session.completed`)

#### PayPal Webhooks

1. Go to PayPal Developer Dashboard > Webhooks
2. Add a webhook with URL: `https://yourdomain.com/api/webhook`
3. Choose event types to receive

#### Zapier Integration

1. Create a Zap with any trigger
2. Add a "Webhook" action
3. Set the webhook URL to `https://yourdomain.com/api/webhook`
4. Configure the payload to include a `source` field

### 4. Custom Application Integration

For Node.js applications:

```javascript
fetch('https://yourdomain.com/api/webhook', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    source: 'node_app',
    event_type: 'user_signup',
    user: {
      id: 123,
      name: 'John Doe',
      email: 'john@example.com'
    }
  })
})
```

For Python applications:

```python
import requests
import json

data = {
    'source': 'python_app',
    'event_type': 'data_processed',
    'items_processed': 150,
    'status': 'completed'
}

response = requests.post(
    'https://yourdomain.com/api/webhook',
    headers={'Content-Type': 'application/json'},
    data=json.dumps(data)
)
```

### Supported Webhook Data Sources

The system automatically detects and processes data from these sources:

1. **Stripe**: Payment events, customer events, subscription events
2. **PayPal**: Payment notifications, refunds, disputes
3. **Forms**: Contact forms, registration forms, survey submissions
4. **CRM Systems**: Customer updates, lead creation, opportunity changes
5. **Custom Applications**: Any custom data source with a valid JSON payload

## Setup

### Prerequisites

- Python 3.8 or higher
- PostgreSQL database
- Required Python packages (see requirements.txt)

### Environment Variables

The application requires the following environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `SESSION_SECRET`: Secret key for session management
- Other database connection variables (`PGHOST`, `PGUSER`, etc.)

### Installation

1. Clone the repository
2. Install dependencies with `pip install -r requirements.txt`
3. Set up the required environment variables
4. Run the application with `python main.py` or using Gunicorn:
   ```
   gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
   ```

## Development

### Project Structure

```
├── app.py              # Flask app configuration
├── main.py             # Entry point
├── models.py           # Database models
├── routes/             # Route definitions
│   ├── dashboard_routes.py
│   ├── integration_routes.py
│   └── webhook_routes.py
├── services/           # Business logic
│   ├── data_service.py
│   ├── integration_service.py
│   └── notification_service.py
├── static/             # Static assets
│   ├── css/
│   ├── js/
│   └── img/
├── templates/          # HTML templates
├── utils/              # Utility functions
└── data/               # Data directory (legacy)
```

### Adding New Features

To add new features:

1. Define models in `models.py` if needed
2. Create or update services in the `services/` directory
3. Add routes in the `routes/` directory
4. Create templates in the `templates/` directory if needed
5. Update static assets in the `static/` directory

## Testing

You can test the webhook functionality by sending POST requests to the `/api/webhook` endpoint. For example:

```bash
curl -X POST http://localhost:5000/api/webhook \
  -H "Content-Type: application/json" \
  -d '{"source":"test","message":"Test webhook data"}'
```

## License

This project is proprietary and confidential.