#!/usr/bin/env python3
"""
Scanner API Client

A sample client that demonstrates how to interact with the Document Scanner API
"""
import json
import os
import requests
import uuid
from datetime import datetime
import sys
import argparse


class ScannerAPIClient:
    """Client for interacting with the Document Scanner API"""
    
    def __init__(self, base_url="http://localhost:5000"):
        """
        Initialize the Scanner API client
        
        Args:
            base_url (str): Base URL of the scanner API
        """
        self.base_url = base_url
        self.api_key = os.environ.get("SCANNER_API_KEY", "demo-key")
        self.headers = {
            "X-API-Key": self.api_key,
            "Accept": "application/json"
        }
    
    def upload_file(self, file_path):
        """
        Upload a file for scanning and processing
        
        Args:
            file_path (str): Path to the file to upload
            
        Returns:
            dict: The processed scan data
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        upload_url = f"{self.base_url}/scanner/upload"
        
        with open(file_path, 'rb') as f:
            files = {"file": (os.path.basename(file_path), f)}
            response = requests.post(upload_url, headers=self.headers, files=files)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return {"success": False, "error": f"HTTP Error: {response.status_code}"}
    
    def get_scan_history(self):
        """
        Get a list of all processed scans (as JSON)
        
        Returns:
            list: List of processed scans
        """
        history_url = f"{self.base_url}/scanner/history"
        response = requests.get(history_url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return {"success": False, "error": f"HTTP Error: {response.status_code}"}
    
    def get_scan(self, scan_id):
        """
        Get details for a specific scan
        
        Args:
            scan_id (str): ID of the scan to retrieve
            
        Returns:
            dict: Scan details
        """
        scan_url = f"{self.base_url}/scanner/scan/{scan_id}"
        response = requests.get(scan_url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return {"success": False, "error": f"HTTP Error: {response.status_code}"}
    
    def create_sample_scan(self):
        """
        Create a sample scan for testing
        
        Returns:
            dict: Sample scan data
        """
        sample_url = f"{self.base_url}/scanner/sample"
        response = requests.get(sample_url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return {"success": False, "error": f"HTTP Error: {response.status_code}"}
    
    def send_scan_webhook(self, scan_data):
        """
        Manually send scan data to webhook endpoint
        
        Args:
            scan_data (dict): Scan data to send
            
        Returns:
            dict: Webhook response
        """
        webhook_url = f"{self.base_url}/api/webhook"
        
        # Ensure the data has the correct structure
        if not scan_data.get("source"):
            scan_data["source"] = "scanner"
        
        if not scan_data.get("scan_id"):
            scan_data["scan_id"] = str(uuid.uuid4())
        
        if not scan_data.get("timestamp"):
            scan_data["timestamp"] = datetime.utcnow().isoformat()
        
        response = requests.post(webhook_url, headers={
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }, json=scan_data)
        
        if response.status_code in (200, 201):
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return {"success": False, "error": f"HTTP Error: {response.status_code}"}


def main():
    """Main function to demonstrate the Scanner API client"""
    parser = argparse.ArgumentParser(description='Scanner API Client')
    parser.add_argument('--url', default='http://localhost:5000', help='Base URL of the scanner API')
    parser.add_argument('command', choices=['upload', 'history', 'get', 'sample', 'webhook'],
                        help='Command to execute')
    parser.add_argument('--file', help='File to upload (for upload command)')
    parser.add_argument('--id', help='Scan ID (for get command)')
    parser.add_argument('--data', help='JSON data file (for webhook command)')
    
    args = parser.parse_args()
    
    client = ScannerAPIClient(args.url)
    
    if args.command == 'upload':
        if not args.file:
            print("Error: --file is required for upload command")
            sys.exit(1)
        
        result = client.upload_file(args.file)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'history':
        history = client.get_scan_history()
        print(json.dumps(history, indent=2))
    
    elif args.command == 'get':
        if not args.id:
            print("Error: --id is required for get command")
            sys.exit(1)
        
        scan = client.get_scan(args.id)
        print(json.dumps(scan, indent=2))
    
    elif args.command == 'sample':
        sample = client.create_sample_scan()
        print(json.dumps(sample, indent=2))
    
    elif args.command == 'webhook':
        if not args.data:
            # Use a default sample payload
            data = {
                "source": "scanner",
                "scan_id": str(uuid.uuid4()),
                "scan_type": "pdf",
                "event_type": "scan_processed",
                "data": {
                    "file_name": "sample_document.pdf",
                    "timestamp": datetime.utcnow().isoformat(),
                    "extracted_text": "This is sample text extracted from a document.",
                    "structured_data": {
                        "invoice_number": "INV-12345",
                        "date": "2025-03-22",
                        "amount": "1,234.56"
                    }
                },
                "metadata": {
                    "file_size": 123456,
                    "file_type": "application/pdf",
                    "page_count": 1
                }
            }
        else:
            # Load data from file
            with open(args.data, 'r') as f:
                data = json.load(f)
        
        result = client.send_scan_webhook(data)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()