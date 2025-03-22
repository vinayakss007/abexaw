# Webhook Dashboard

A comprehensive webhook dashboard application for capturing, displaying, and managing webhook data with various service integrations.

## Features

- Capture and store webhook data from multiple sources
- Interactive dashboard with charts and statistics
- Export data in various formats (JSON, CSV, Excel)
- Document scanning integration
- Newsletter subscription tracking
- Support for various source types (Forms, CRM, Payment processors, etc.)
- Integration with external services

## Getting Started

### Prerequisites

- Python 3.8+
- Flask
- SQLAlchemy
- PostgreSQL (optional, can use SQLite for development)

### Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Initialize the database:

```bash
python migrations.py
```

4. Start the application:

```bash
python main.py
```

The application will be available at http://localhost:5000

## Usage

### Sending Webhooks

The application can receive webhook data from various sources. The primary webhook endpoint is:

```
POST /api/webhook
```

For testing, you can use the webhook test endpoint:

```
POST /api/webhook/test
```

The webhook endpoint accepts JSON data with various source types. See [WEBHOOK_INTEGRATION_GUIDE.md](WEBHOOK_INTEGRATION_GUIDE.md) for detailed information on payload formats.

### Testing Tools

#### Webhook Test Tool

The repository includes a command-line tool for testing webhook submissions:

```bash
python webhook_test_tool.py --help
```

Example commands:

```bash
# Send a form webhook
python webhook_test_tool.py form --type=contact

# Send a newsletter webhook
python webhook_test_tool.py newsletter

# Send a scanner webhook
python webhook_test_tool.py scanner

# Send a CRM webhook
python webhook_test_tool.py crm --event=lead_created

# Send a payment webhook
python webhook_test_tool.py payment --source=stripe

# Send a custom webhook from a JSON file
python webhook_test_tool.py custom newsletter_sample_data.json
```

#### Scanner API Client

For testing the scanner integration, you can use the Scanner API client:

```bash
python scanner_api_client.py --help
```

Example commands:

```bash
# Create a sample scan
python scanner_api_client.py sample

# Upload a file for scanning
python scanner_api_client.py upload --file=document.pdf

# View scan history
python scanner_api_client.py history

# View a specific scan
python scanner_api_client.py get --id=scan-id

# Send a webhook with scan data
python scanner_api_client.py webhook --data=scanner_sample_data.json
```

### Sample Data

The repository includes sample data files for testing:

- `scanner_sample_data.json`: Example scanner webhook payload
- `newsletter_sample_data.json`: Example newsletter webhook payload

### Web Interface

The web interface provides the following features:

- **Dashboard**: View charts and statistics for webhook data
- **Webhooks**: Browse and manage webhook data
- **Scanner**: Upload and process documents
- **Integrations**: Configure integrations with external services
- **Settings**: Configure application settings

## Documentation

- [WEBHOOK_INTEGRATION_GUIDE.md](WEBHOOK_INTEGRATION_GUIDE.md): Detailed guide for webhook integration
- [SCANNER_API_DOCS.md](SCANNER_API_DOCS.md): Documentation for the Scanner API
- [DATABASE.md](DATABASE.md): Database schema and design

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Flask](https://flask.palletsprojects.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Chart.js](https://www.chartjs.org/)
- [Bootstrap](https://getbootstrap.com/)