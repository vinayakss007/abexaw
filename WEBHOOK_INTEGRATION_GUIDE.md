# Webhook Integration Guide

This document provides detailed information on how to integrate with our webhook system. It includes sample payloads for different types of data sources, allowing you to design web forms and applications that properly send data to the webhook dashboard.

## Table of Contents

1. [Overview](#overview)
2. [Endpoint Information](#endpoint-information)
3. [Source Types](#source-types)
4. [Sample Payloads](#sample-payloads)
   - [Form Submissions](#form-submissions)
   - [Newsletter Subscriptions](#newsletter-subscriptions)
   - [Scanner Data](#scanner-data)
   - [CRM Data](#crm-data)
   - [Payment Data](#payment-data)
5. [Headers and Authentication](#headers-and-authentication)
6. [Response Format](#response-format)
7. [Error Handling](#error-handling)
8. [Best Practices](#best-practices)
9. [Webhook Testing](#webhook-testing)

## Overview

Our webhook system accepts HTTP POST requests with JSON data and processes them based on the source type. The system automatically detects the source type based on the payload content and routes it to the appropriate processor.

The processed data is stored in the database and displayed in the dashboard, allowing you to view and analyze the data in real-time.

## Endpoint Information

### Main Webhook Endpoint

```
POST /api/webhook
```

This endpoint accepts webhook data from any source. The source type is automatically detected based on the payload content.

### Secure Webhook Endpoint

```
POST /api/webhook/secure
```

This endpoint requires a signature for validation. The signature should be included in the headers as `X-Webhook-Signature`.

## Source Types

The webhook system supports the following source types:

| Source Type | Description | Auto-detection |
|-------------|-------------|----------------|
| `form` | Web form submissions | Detects fields like `name`, `email`, `message`, `phone` |
| `newsletter` | Newsletter subscriptions | Detects keywords like `newsletter`, `subscribe`, `mailing list` |
| `scanner` | Document scanner data | Detects fields like `scan_id`, `extracted_text`, `scan_type` |
| `crm` | CRM system data | Detects fields like `customer`, `lead`, `opportunity`, `contact` |
| `stripe` | Stripe payment data | Detects fields like `type`, `object: event`, `api_version` |
| `paypal` | PayPal payment data | Detects fields like `event_type`, `resource_type: sale` |

## Sample Payloads

### Form Submissions

Standard web form submission:

```json
{
  "source": "form",
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "123-456-7890",
  "message": "This is a test message",
  "form_type": "contact"
}
```

Contact form with additional fields:

```json
{
  "source": "form",
  "name": "Jane Smith",
  "email": "jane@example.com",
  "phone": "987-654-3210",
  "message": "Please contact me about your services",
  "form_type": "contact",
  "company": "Acme Inc.",
  "budget": "10000-20000",
  "preferred_contact_method": "email"
}
```

Registration form:

```json
{
  "source": "form",
  "form_type": "registration",
  "name": "Alice Johnson",
  "email": "alice@example.com",
  "company": "Tech Solutions",
  "job_title": "Product Manager",
  "industry": "Technology",
  "employees": "50-100"
}
```

Feedback form:

```json
{
  "source": "form",
  "form_type": "feedback",
  "name": "Bob Williams",
  "email": "bob@example.com",
  "rating": 4,
  "feedback_type": "product",
  "comments": "Great product, but could use more features",
  "would_recommend": true
}
```

### Newsletter Subscriptions

Basic newsletter subscription:

```json
{
  "source": "newsletter",
  "name": "Carol Miller",
  "email": "carol@example.com"
}
```

Newsletter with preferences:

```json
{
  "source": "newsletter",
  "name": "David Wilson",
  "email": "david@example.com",
  "frequency": "weekly",
  "interests": ["technology", "business", "marketing"],
  "subscribe_date": "2025-03-22T10:00:00Z",
  "referral_source": "website"
}
```

Advanced newsletter subscription:

```json
{
  "source": "newsletter",
  "name": "Eve Brown",
  "email": "eve@example.com",
  "preferences": {
    "frequency": "monthly",
    "format": "html",
    "categories": ["product updates", "industry news", "webinars"]
  },
  "gdpr_consent": true,
  "marketing_consent": true,
  "subscription_source": "landing_page",
  "utm_source": "google",
  "utm_medium": "cpc",
  "utm_campaign": "newsletter_signup"
}
```

### Scanner Data

Basic document scan:

```json
{
  "source": "scanner",
  "scan_id": "2f9a4b5c-6d7e-8f9a-0b1c-2d3e4f5a6b7c",
  "scan_type": "image",
  "event_type": "scan_processed",
  "data": {
    "file_name": "document.jpg",
    "timestamp": "2025-03-22T10:15:00Z",
    "extracted_text": "This is the text extracted from the document...",
    "structured_data": {
      "invoice_number": "INV-12345",
      "date": "2025-03-15",
      "amount": "1,234.56"
    }
  },
  "metadata": {
    "file_size": 256789,
    "file_type": "image/jpeg",
    "page_count": 1
  }
}
```

PDF document scan:

```json
{
  "source": "scanner",
  "scan_id": "3a4b5c6d-7e8f-9a0b-1c2d-3e4f5a6b7c8d",
  "scan_type": "pdf",
  "event_type": "scan_processed",
  "data": {
    "file_name": "contract.pdf",
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

### CRM Data

Lead creation:

```json
{
  "source": "crm",
  "crm_type": "salesforce",
  "event_type": "lead_created",
  "lead": {
    "id": "LD-789012",
    "name": "Frank Thomas",
    "email": "frank@example.com",
    "phone": "123-789-4560",
    "company": "Global Industries",
    "status": "new",
    "source": "website",
    "created_at": "2025-03-22T10:45:00Z",
    "score": 85,
    "notes": "Interested in enterprise plan",
    "owner": "sales-rep-1234"
  }
}
```

Deal update:

```json
{
  "source": "crm",
  "crm_type": "hubspot",
  "event_type": "deal_updated",
  "deal": {
    "id": "DEAL-345678",
    "name": "SaaS Platform Renewal",
    "stage": "negotiation",
    "amount": 25000,
    "currency": "USD",
    "probability": 80,
    "close_date": "2025-04-30",
    "contact_id": "CONT-123456",
    "contact_name": "Grace Lee",
    "company_id": "COMP-789012",
    "company_name": "Tech Innovations Inc.",
    "updated_at": "2025-03-22T11:00:00Z",
    "previous_stage": "proposal",
    "products": [
      {
        "id": "PROD-123",
        "name": "Enterprise License",
        "quantity": 5,
        "price": 5000
      }
    ]
  }
}
```

Customer update:

```json
{
  "source": "crm",
  "crm_type": "zoho",
  "event_type": "customer_updated",
  "customer": {
    "id": "CUST-456789",
    "name": "Henry Adams",
    "email": "henry@example.com",
    "phone": "456-789-0123",
    "company": "Adams Consulting",
    "address": {
      "street": "123 Business Ave",
      "city": "San Francisco",
      "state": "CA",
      "postal_code": "94107",
      "country": "US"
    },
    "segment": "enterprise",
    "lifetime_value": 75000,
    "updated_at": "2025-03-22T11:15:00Z",
    "subscriptions": [
      {
        "id": "SUB-123",
        "plan": "Enterprise",
        "status": "active",
        "start_date": "2024-01-01",
        "end_date": "2025-12-31"
      }
    ]
  }
}
```

### Payment Data

Stripe payment success:

```json
{
  "source": "stripe",
  "type": "payment_intent.succeeded",
  "object": "event",
  "api_version": "2023-10-16",
  "data": {
    "object": {
      "id": "pi_1N2OivJsNj8JnNj8gGFq1XY2",
      "object": "payment_intent",
      "amount": 5000,
      "currency": "usd",
      "status": "succeeded",
      "customer": "cus_1N2OivJsNj8JnNj8",
      "receipt_email": "customer@example.com",
      "payment_method": "pm_1N2OivJsNj8JnNj8"
    }
  }
}
```

PayPal payment completed:

```json
{
  "source": "paypal",
  "event_type": "PAYMENT.SALE.COMPLETED",
  "resource_type": "sale",
  "summary": "Payment completed for $50.00 USD",
  "resource": {
    "id": "7DH23894TK130282P",
    "state": "completed",
    "amount": {
      "total": "50.00",
      "currency": "USD"
    },
    "payment_mode": "INSTANT_TRANSFER",
    "create_time": "2025-03-22T11:30:00Z",
    "update_time": "2025-03-22T11:31:00Z",
    "payer": {
      "email_address": "customer@example.com"
    }
  }
}
```

## Headers and Authentication

The webhook system supports the following authentication methods:

### Basic Authentication

Include the source and API key in the headers:

```
X-Webhook-Source: form
X-API-Key: your-api-key
```

### Signature Authentication

Include a signature in the headers:

```
X-Webhook-Signature: computed-signature
```

The signature should be a HMAC-SHA256 hash of the request body, using your webhook secret as the key.

Example in JavaScript:
```javascript
const crypto = require('crypto');
const payload = JSON.stringify(data);
const signature = crypto
  .createHmac('sha256', 'your-webhook-secret')
  .update(payload)
  .digest('hex');
```

Example in Python:
```python
import hmac
import hashlib
import json

payload = json.dumps(data)
signature = hmac.new(
    'your-webhook-secret'.encode('utf-8'),
    payload.encode('utf-8'),
    hashlib.sha256
).hexdigest()
```

## Response Format

The webhook endpoint returns a JSON response with the following structure:

### Success Response

```json
{
  "success": true,
  "message": "Webhook received and processed",
  "webhook_id": "f4a5b6c7-d8e9-f0a1-b2c3-d4e5f6a7b8c9"
}
```

### Error Response

```json
{
  "success": false,
  "error": "INVALID_PAYLOAD",
  "message": "The payload is invalid"
}
```

## Error Handling

The webhook system returns the following error codes:

| Error Code | Description |
|------------|-------------|
| `INVALID_PAYLOAD` | The payload is invalid or missing required fields |
| `INVALID_SIGNATURE` | The signature is invalid or missing |
| `INVALID_SOURCE` | The source is invalid or not supported |
| `PROCESSING_ERROR` | An error occurred while processing the webhook |
| `RATE_LIMIT_EXCEEDED` | Rate limit exceeded |

## Best Practices

1. **Always include a source**
   - Explicitly set the `source` field in your payload to ensure proper processing
   - If no source is provided, the system will attempt to detect it automatically

2. **Include timestamps**
   - Add a `timestamp` field to your payload to track when events occurred
   - Use ISO 8601 format (e.g., `2025-03-22T12:00:00Z`)

3. **Use structured data**
   - Organize your data in a logical structure
   - Group related fields together (e.g., contact information, preferences)

4. **Handle errors properly**
   - Check for error responses and handle them appropriately
   - Implement retry logic for failed webhook submissions

5. **Test before production**
   - Use the testing endpoint to verify your integration works correctly
   - Test all edge cases and error scenarios

## Webhook Testing

You can use the test endpoint to verify your webhook integration:

```
POST /api/webhook/test
```

This endpoint processes the webhook but doesn't store the data in the database, making it safe for testing.

Example curl command to test a form webhook:

```bash
curl -X POST -H "Content-Type: application/json" -d '{
  "source": "form",
  "name": "Test User",
  "email": "test@example.com",
  "message": "This is a test"
}' https://yourdomain.com/api/webhook/test
```

## Example HTML Forms

### Standard Form

```html
<form id="contactForm">
  <input type="text" name="name" placeholder="Name" required>
  <input type="email" name="email" placeholder="Email" required>
  <textarea name="message" placeholder="Message" required></textarea>
  <button type="submit">Submit</button>
</form>

<script>
document.getElementById('contactForm').addEventListener('submit', function(e) {
  e.preventDefault();
  
  const formData = {
    source: 'form',
    name: this.elements.name.value,
    email: this.elements.email.value,
    message: this.elements.message.value
  };
  
  fetch('/api/webhook', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(formData)
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      alert('Form submitted successfully!');
      this.reset();
    } else {
      alert('Error: ' + data.message);
    }
  })
  .catch(error => {
    console.error('Error:', error);
    alert('An error occurred. Please try again.');
  });
});
</script>
```

### Newsletter Form

```html
<form id="newsletterForm">
  <input type="text" name="name" placeholder="Name" required>
  <input type="email" name="email" placeholder="Email" required>
  <div class="preferences">
    <h4>Interests:</h4>
    <label><input type="checkbox" name="interests[]" value="technology"> Technology</label>
    <label><input type="checkbox" name="interests[]" value="business"> Business</label>
    <label><input type="checkbox" name="interests[]" value="marketing"> Marketing</label>
  </div>
  <div class="frequency">
    <h4>Frequency:</h4>
    <label><input type="radio" name="frequency" value="daily"> Daily</label>
    <label><input type="radio" name="frequency" value="weekly" checked> Weekly</label>
    <label><input type="radio" name="frequency" value="monthly"> Monthly</label>
  </div>
  <button type="submit">Subscribe</button>
</form>

<script>
document.getElementById('newsletterForm').addEventListener('submit', function(e) {
  e.preventDefault();
  
  // Get selected interests
  const interests = [];
  this.querySelectorAll('input[name="interests[]"]:checked').forEach(checkbox => {
    interests.push(checkbox.value);
  });
  
  const formData = {
    source: 'newsletter',
    name: this.elements.name.value,
    email: this.elements.email.value,
    interests: interests,
    frequency: this.elements.frequency.value,
    subscribe_date: new Date().toISOString()
  };
  
  fetch('/api/webhook', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(formData)
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      alert('Subscribed successfully!');
      this.reset();
    } else {
      alert('Error: ' + data.message);
    }
  })
  .catch(error => {
    console.error('Error:', error);
    alert('An error occurred. Please try again.');
  });
});
</script>
```

---

For more information or assistance, please contact the support team or refer to the API documentation.