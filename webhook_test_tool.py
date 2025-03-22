#!/usr/bin/env python3
"""
Webhook Test Tool

A command-line tool for testing webhook submissions to the webhook dashboard
"""
import argparse
import json
import requests
import sys
import uuid
from datetime import datetime
import os


class WebhookTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.webhook_url = f"{base_url}/api/webhook"
        self.test_webhook_url = f"{base_url}/api/webhook/test"
        self.api_key = os.environ.get("WEBHOOK_API_KEY", "demo-key")
        
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
    
    def send_webhook(self, data, test_mode=False):
        """Send data to the webhook endpoint"""
        url = self.test_webhook_url if test_mode else self.webhook_url
        
        response = requests.post(url, headers=self.headers, json=data)
        
        if response.status_code in (200, 201):
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return {"success": False, "error": f"HTTP Error: {response.status_code}"}
    
    def send_form_webhook(self, form_type="contact", test_mode=False):
        """Send a form webhook"""
        data = {
            "source": "form",
            "form_type": form_type,
            "name": "John Smith",
            "email": "john.smith@example.com",
            "message": "This is a test message from the webhook test tool",
            "phone": "123-456-7890",
            "company": "Test Company",
            "submit_date": datetime.utcnow().isoformat(),
            "metadata": {
                "form_id": "contact-form-main",
                "page_url": "https://example.com/contact",
                "user_agent": "Mozilla/5.0"
            }
        }
        
        return self.send_webhook(data, test_mode)
    
    def send_newsletter_webhook(self, test_mode=False):
        """Send a newsletter webhook"""
        data = {
            "source": "newsletter",
            "name": "Jane Doe",
            "email": "jane.doe@example.com",
            "frequency": "weekly",
            "interests": ["technology", "marketing", "business"],
            "subscribe_date": datetime.utcnow().isoformat(),
            "gdpr_consent": True,
            "marketing_consent": True,
            "metadata": {
                "source_page": "blog-signup",
                "utm_source": "website",
                "utm_medium": "blog",
                "utm_campaign": "spring-newsletter"
            }
        }
        
        return self.send_webhook(data, test_mode)
    
    def send_scanner_webhook(self, test_mode=False):
        """Send a scanner webhook"""
        data = {
            "source": "scanner",
            "scan_id": str(uuid.uuid4()),
            "scan_type": "document",
            "event_type": "scan_processed",
            "data": {
                "file_name": "test_document.pdf",
                "timestamp": datetime.utcnow().isoformat(),
                "extracted_text": "This is test text extracted from a scanned document.",
                "structured_data": {
                    "title": "Test Document",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "keywords": ["test", "document", "webhook"]
                }
            },
            "metadata": {
                "file_size": 123456,
                "file_type": "application/pdf",
                "page_count": 2
            }
        }
        
        return self.send_webhook(data, test_mode)
    
    def send_crm_webhook(self, event_type="lead_created", test_mode=False):
        """Send a CRM webhook"""
        data = {
            "source": "crm",
            "crm_type": "generic",
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "lead": {
                "id": f"LEAD-{uuid.uuid4().hex[:8].upper()}",
                "name": "Robert Johnson",
                "email": "robert.johnson@example.com",
                "phone": "987-654-3210",
                "company": "ABC Industries",
                "status": "new",
                "score": 85,
                "created_at": datetime.utcnow().isoformat(),
                "owner": "sales-rep-1234"
            },
            "metadata": {
                "source": "website-form",
                "campaign": "google-ads",
                "reference": "REF-12345"
            }
        }
        
        return self.send_webhook(data, test_mode)
    
    def send_payment_webhook(self, source="stripe", test_mode=False):
        """Send a payment webhook (Stripe or PayPal)"""
        if source == "stripe":
            data = {
                "source": "stripe",
                "type": "payment_intent.succeeded",
                "object": "event",
                "api_version": "2023-10-16",
                "data": {
                    "object": {
                        "id": f"pi_{uuid.uuid4().hex[:24]}",
                        "object": "payment_intent",
                        "amount": 5000,
                        "currency": "usd",
                        "status": "succeeded",
                        "customer": f"cus_{uuid.uuid4().hex[:16]}",
                        "receipt_email": "customer@example.com",
                        "payment_method": f"pm_{uuid.uuid4().hex[:16]}"
                    }
                }
            }
        else:  # paypal
            data = {
                "source": "paypal",
                "event_type": "PAYMENT.SALE.COMPLETED",
                "resource_type": "sale",
                "summary": "Payment completed for $50.00 USD",
                "resource": {
                    "id": f"{uuid.uuid4().hex[:8].upper()}",
                    "state": "completed",
                    "amount": {
                        "total": "50.00",
                        "currency": "USD"
                    },
                    "payment_mode": "INSTANT_TRANSFER",
                    "create_time": datetime.utcnow().isoformat(),
                    "update_time": datetime.utcnow().isoformat(),
                    "payer": {
                        "email_address": "customer@example.com"
                    }
                }
            }
        
        return self.send_webhook(data, test_mode)
    
    def send_custom_webhook(self, data_file, test_mode=False):
        """Send a custom webhook from a JSON file"""
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
            
            return self.send_webhook(data, test_mode)
        except FileNotFoundError:
            print(f"Error: File not found: {data_file}")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in file: {data_file}")
            sys.exit(1)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Webhook Test Tool')
    parser.add_argument('--url', default='http://localhost:5000',
                        help='Base URL of the webhook API')
    parser.add_argument('--test', action='store_true',
                        help='Use test mode (data not stored)')
    
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # Form webhook
    form_parser = subparsers.add_parser('form', help='Send a form webhook')
    form_parser.add_argument('--type', default='contact',
                           choices=['contact', 'feedback', 'registration', 'support'],
                           help='Form type')
    
    # Newsletter webhook
    subparsers.add_parser('newsletter', help='Send a newsletter webhook')
    
    # Scanner webhook
    subparsers.add_parser('scanner', help='Send a scanner webhook')
    
    # CRM webhook
    crm_parser = subparsers.add_parser('crm', help='Send a CRM webhook')
    crm_parser.add_argument('--event', default='lead_created',
                          choices=['lead_created', 'lead_updated', 'deal_created', 'deal_updated', 'contact_created'],
                          help='CRM event type')
    
    # Payment webhook
    payment_parser = subparsers.add_parser('payment', help='Send a payment webhook')
    payment_parser.add_argument('--source', default='stripe',
                              choices=['stripe', 'paypal'],
                              help='Payment source')
    
    # Custom webhook
    custom_parser = subparsers.add_parser('custom', help='Send a custom webhook from a JSON file')
    custom_parser.add_argument('file', help='JSON file containing webhook data')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    tester = WebhookTester(args.url)
    
    if args.command == 'form':
        result = tester.send_form_webhook(args.type, args.test)
    elif args.command == 'newsletter':
        result = tester.send_newsletter_webhook(args.test)
    elif args.command == 'scanner':
        result = tester.send_scanner_webhook(args.test)
    elif args.command == 'crm':
        result = tester.send_crm_webhook(args.event, args.test)
    elif args.command == 'payment':
        result = tester.send_payment_webhook(args.source, args.test)
    elif args.command == 'custom':
        result = tester.send_custom_webhook(args.file, args.test)
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()