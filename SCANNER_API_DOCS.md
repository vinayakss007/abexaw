# Scanner API Documentation

This document provides detailed information on how to integrate with the Document Scanner API. It includes endpoints, request/response formats, and examples for scanning and processing documents.

## Table of Contents

1. [Overview](#overview)
2. [API Endpoints](#api-endpoints)
3. [Authentication](#authentication)
4. [File Upload](#file-upload)
5. [Scan Processing](#scan-processing)
6. [Webhook Integration](#webhook-integration)
7. [Response Formats](#response-formats)
8. [Error Handling](#error-handling)
9. [Sample Code](#sample-code)
10. [Best Practices](#best-practices)

## Overview

The Document Scanner API allows you to upload images and documents, process them for text extraction and metadata analysis, and receive the processed data via webhooks. 

The API supports various file formats including:
- Images: JPG, PNG, TIFF, BMP
- Documents: PDF, DOCX, TXT

## API Endpoints

Base URL: `https://your-domain.com`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/scanner` | GET | Scanner main page |
| `/scanner/upload` | POST | Upload files for processing |
| `/scanner/history` | GET | View scan history |
| `/scanner/scan/:id` | GET | View a specific scan |
| `/scanner/files/:filename` | GET | Serve uploaded files |
| `/scanner/sample` | GET | Create a sample scan for testing |

## Authentication

All API requests require authentication. You can authenticate using:

1. **API Key**: Include your API key in the headers:
   ```
   X-API-Key: your-api-key
   ```

2. **Bearer Token**: Include a bearer token in the Authorization header:
   ```
   Authorization: Bearer your-token
   ```

## File Upload

### Endpoint

```
POST /scanner/upload
```

### Request Format

Use multipart/form-data to upload files:

```
Content-Type: multipart/form-data
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | The file to upload |
| `scan_type` | String | No | Custom scan type (default: auto-detect) |
| `process_immediately` | Boolean | No | Whether to process immediately (default: true) |
| `webhook_url` | String | No | Custom webhook URL to receive results |

### Response Format

```json
{
  "success": true,
  "scan_id": "f4a5b6c7-d8e9-f0a1-b2c3-d4e5f6a7b8c9",
  "message": "File uploaded and processing started",
  "file_info": {
    "name": "document.pdf",
    "size": 1024567,
    "type": "application/pdf"
  },
  "status": "processing"
}
```

## Scan Processing

The scanner processes files in several steps:

1. **File Analysis**: Determines file type and extracts basic metadata
2. **Text Extraction**: Extracts text from the document using OCR (for images) or direct extraction (for documents)
3. **Content Analysis**: Analyzes the content to identify structured data
4. **Metadata Extraction**: Extracts additional metadata like EXIF data, creation date, etc.
5. **Result Generation**: Compiles all extracted data into a structured format
6. **Webhook Notification**: Sends the processed data to the webhook endpoint

## Webhook Integration

When a scan is completed, the scanner sends the processed data to the webhook endpoint. The default webhook endpoint is `/api/webhook`, but you can specify a custom endpoint using the `webhook_url` parameter during upload.

### Webhook Payload

The webhook payload includes the processed scan data in the following format:

```json
{
  "source": "scanner",
  "scan_id": "f4a5b6c7-d8e9-f0a1-b2c3-d4e5f6a7b8c9",
  "scan_type": "pdf",
  "event_type": "scan_processed",
  "data": {
    "file_name": "document.pdf",
    "timestamp": "2025-03-22T10:30:00Z",
    "extracted_text": "This is the text extracted from the PDF...",
    "structured_data": {
      "contract_number": "CTR-789012",
      "effective_date": "2025-04-01",
      "expiration_date": "2026-03-31",
      "parties": ["Company A", "Company B"]
    },
    "pages": [
      {
        "page_number": 1,
        "text": "First page content...",
        "form_fields": [{"name": "signature", "location": "bottom"}]
      },
      {
        "page_number": 2,
        "text": "Second page content...",
        "form_fields": []
      }
    ]
  },
  "metadata": {
    "file_size": 1024567,
    "file_type": "application/pdf",
    "page_count": 2,
    "author": "Legal Department"
  }
}
```

## Response Formats

### Scan History

```json
{
  "success": true,
  "scans": [
    {
      "scan_id": "f4a5b6c7-d8e9-f0a1-b2c3-d4e5f6a7b8c9",
      "file_name": "document.pdf",
      "scan_type": "pdf",
      "timestamp": "2025-03-22T10:30:00Z",
      "status": "completed",
      "extracted_text_snippet": "This is the text extracted from the PDF..."
    },
    {
      "scan_id": "9c8b7a6f-5e4d-3c2b-1a0f-e9d8c7b6a5f4",
      "file_name": "image.jpg",
      "scan_type": "image",
      "timestamp": "2025-03-22T10:15:00Z",
      "status": "completed",
      "extracted_text_snippet": "This is the text extracted from the image..."
    }
  ]
}
```

### Single Scan View

```json
{
  "success": true,
  "scan": {
    "scan_id": "f4a5b6c7-d8e9-f0a1-b2c3-d4e5f6a7b8c9",
    "file_name": "document.pdf",
    "scan_type": "pdf",
    "timestamp": "2025-03-22T10:30:00Z",
    "status": "completed",
    "extracted_text": "This is the text extracted from the PDF...",
    "structured_data": {
      "contract_number": "CTR-789012",
      "effective_date": "2025-04-01",
      "expiration_date": "2026-03-31",
      "parties": ["Company A", "Company B"]
    },
    "metadata": {
      "file_size": 1024567,
      "file_type": "application/pdf",
      "page_count": 2,
      "author": "Legal Department"
    }
  }
}
```

## Error Handling

### Error Response Format

```json
{
  "success": false,
  "error": "ERROR_CODE",
  "message": "Detailed error message",
  "details": {
    "field": "Additional information about the error"
  }
}
```

### Common Error Codes

| Error Code | Description |
|------------|-------------|
| `INVALID_FILE` | The uploaded file is invalid or corrupt |
| `UNSUPPORTED_FILE_TYPE` | The file type is not supported |
| `FILE_TOO_LARGE` | The file exceeds the maximum size limit |
| `PROCESSING_ERROR` | An error occurred during processing |
| `NOT_FOUND` | The requested scan was not found |
| `UNAUTHORIZED` | Authentication failed |

## Sample Code

### Python Client

```python
import requests
import json

class ScannerClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {
            'X-API-Key': api_key
        }
    
    def upload_file(self, file_path, scan_type=None, process_immediately=True, webhook_url=None):
        """Upload a file for scanning"""
        url = f"{self.base_url}/scanner/upload"
        
        files = {
            'file': open(file_path, 'rb')
        }
        
        data = {}
        if scan_type:
            data['scan_type'] = scan_type
        if webhook_url:
            data['webhook_url'] = webhook_url
        if not process_immediately:
            data['process_immediately'] = 'false'
        
        response = requests.post(url, headers=self.headers, files=files, data=data)
        return response.json()
    
    def get_scan_history(self):
        """Get scan history"""
        url = f"{self.base_url}/scanner/history"
        response = requests.get(url, headers=self.headers)
        return response.json()
    
    def get_scan(self, scan_id):
        """Get a specific scan"""
        url = f"{self.base_url}/scanner/scan/{scan_id}"
        response = requests.get(url, headers=self.headers)
        return response.json()
    
    def create_sample_scan(self):
        """Create a sample scan for testing"""
        url = f"{self.base_url}/scanner/sample"
        response = requests.get(url, headers=self.headers)
        return response.json()

# Example usage
client = ScannerClient('https://your-domain.com', 'your-api-key')

# Upload a file
result = client.upload_file('path/to/document.pdf')
print(f"Scan ID: {result['scan_id']}")

# Get scan history
history = client.get_scan_history()
for scan in history['scans']:
    print(f"{scan['file_name']} - {scan['status']}")

# Get a specific scan
scan = client.get_scan(result['scan_id'])
print(f"Extracted text: {scan['scan']['extracted_text'][:100]}...")

# Create a sample scan
sample = client.create_sample_scan()
print(f"Sample scan created with ID: {sample['scan_id']}")
```

### JavaScript Client

```javascript
class ScannerClient {
  constructor(baseUrl, apiKey) {
    this.baseUrl = baseUrl;
    this.headers = {
      'X-API-Key': apiKey
    };
  }
  
  async uploadFile(file, scanType = null, processImmediately = true, webhookUrl = null) {
    const url = `${this.baseUrl}/scanner/upload`;
    const formData = new FormData();
    
    formData.append('file', file);
    
    if (scanType) {
      formData.append('scan_type', scanType);
    }
    
    if (webhookUrl) {
      formData.append('webhook_url', webhookUrl);
    }
    
    if (!processImmediately) {
      formData.append('process_immediately', 'false');
    }
    
    const response = await fetch(url, {
      method: 'POST',
      headers: this.headers,
      body: formData
    });
    
    return response.json();
  }
  
  async getScanHistory() {
    const url = `${this.baseUrl}/scanner/history`;
    const response = await fetch(url, {
      headers: this.headers
    });
    
    return response.json();
  }
  
  async getScan(scanId) {
    const url = `${this.baseUrl}/scanner/scan/${scanId}`;
    const response = await fetch(url, {
      headers: this.headers
    });
    
    return response.json();
  }
  
  async createSampleScan() {
    const url = `${this.baseUrl}/scanner/sample`;
    const response = await fetch(url, {
      headers: this.headers
    });
    
    return response.json();
  }
}

// Example usage
const client = new ScannerClient('https://your-domain.com', 'your-api-key');

// Upload a file
const fileInput = document.getElementById('fileInput');
const file = fileInput.files[0];

client.uploadFile(file)
  .then(result => {
    console.log(`Scan ID: ${result.scan_id}`);
  })
  .catch(error => {
    console.error('Error:', error);
  });

// Get scan history
client.getScanHistory()
  .then(history => {
    history.scans.forEach(scan => {
      console.log(`${scan.file_name} - ${scan.status}`);
    });
  })
  .catch(error => {
    console.error('Error:', error);
  });

// Get a specific scan
const scanId = 'f4a5b6c7-d8e9-f0a1-b2c3-d4e5f6a7b8c9';
client.getScan(scanId)
  .then(scan => {
    console.log(`Extracted text: ${scan.scan.extracted_text.substring(0, 100)}...`);
  })
  .catch(error => {
    console.error('Error:', error);
  });

// Create a sample scan
client.createSampleScan()
  .then(sample => {
    console.log(`Sample scan created with ID: ${sample.scan_id}`);
  })
  .catch(error => {
    console.error('Error:', error);
  });
```

## Best Practices

1. **File Size**: Keep file sizes under 10MB for optimal performance
2. **File Types**: Use PDF for multi-page documents and JPG/PNG for images
3. **Resolution**: Ensure images have sufficient resolution for OCR (at least 300 DPI)
4. **Error Handling**: Implement proper error handling to manage failed scans
5. **Webhooks**: Use webhooks for asynchronous processing of large files
6. **Polling**: For critical applications, implement polling to check scan status
7. **Rate Limiting**: Respect API rate limits to avoid throttling
8. **Authentication**: Secure your API key and rotate it periodically
9. **Testing**: Use the sample scan endpoint to test your integration
10. **Logging**: Log all API responses for debugging and auditing

For more information or assistance, please contact the support team.