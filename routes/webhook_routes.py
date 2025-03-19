import json
import logging
import uuid
import time
from datetime import datetime
from flask import Blueprint, request, jsonify, Response, make_response, send_file
from pathlib import Path
import io
import os

from services.data_service import save_webhook_data, get_webhook_data
from services.notification_service import notify_new_data
from services.webhook_processor import process_webhook, validate_webhook_signature, determine_source
from services.export_service import export_data_as_json, export_data_as_csv, export_data_as_excel

logger = logging.getLogger(__name__)
webhook_bp = Blueprint('webhook', __name__)

# Maximum number of retry attempts for webhook processing
MAX_RETRIES = 3

@webhook_bp.route('/api/webhook', methods=['POST'])
def receive_webhook():
    """
    Endpoint to receive webhook data from external sources
    
    This is the main webhook endpoint that can handle multiple types of incoming data.
    It identifies the source based on the payload and routes it accordingly.
    """
    start_time = time.time()
    retry_count = 0
    
    try:
        # Get HTTP headers for later use in signature validation
        headers = {k: v for k, v in request.headers.items()}
        
        # Get data from request with retries for robustness
        while retry_count < MAX_RETRIES:
            try:
                # Try JSON first as it's most common
                if request.is_json:
                    data = request.json
                # Then try form data
                elif request.form:
                    data = request.form.to_dict()
                # Then try raw data as JSON
                else:
                    try:
                        data = json.loads(request.data.decode('utf-8'))
                    except json.JSONDecodeError:
                        # As a last resort, store as raw content
                        data = {"raw_content": request.data.decode('utf-8')}
                
                # Break out of retry loop if we successfully got data
                break
            
            except Exception as e:
                retry_count += 1
                if retry_count >= MAX_RETRIES:
                    logger.error(f"Failed to parse webhook data after {MAX_RETRIES} attempts: {str(e)}")
                    raise
                time.sleep(0.1)  # Short delay before retry
        
        # Add HTTP headers to data for processing
        data['_headers'] = headers
        
        # Process the webhook data through our processor pipeline
        processed_data = process_webhook(data)
        
        # Create webhook data record
        webhook_data = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "source": processed_data.get("source", determine_source(data)),
            "data": processed_data
        }
        
        # Save the data
        save_webhook_data(webhook_data)
        
        # Notify about new data
        notify_new_data(webhook_data)
        
        # Log successful processing
        processing_time = time.time() - start_time
        logger.info(f"Processed webhook from {webhook_data['source']} in {processing_time:.2f}s")
        
        # Return success response
        return jsonify({
            "status": "success", 
            "message": f"Webhook data from {webhook_data['source']} received and processed",
            "id": webhook_data["id"]
        }), 200
    
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error processing webhook after {processing_time:.2f}s: {str(e)}")
        
        # Always return 200 OK to the webhook sender even on error
        # This prevents endless retries from webhook senders
        return jsonify({
            "status": "error", 
            "message": "Webhook received, but there was an error processing it. It has been logged for investigation."
        }), 200

@webhook_bp.route('/api/webhook/secure', methods=['POST'])
def receive_secure_webhook():
    """
    Secure endpoint for webhooks that require signature validation
    """
    try:
        # Get the webhook secret from environment or config
        webhook_secret = os.environ.get('WEBHOOK_SECRET', 'your-webhook-secret-key')
        
        # Validate webhook signature
        if not validate_webhook_signature(request, webhook_secret):
            logger.warning("Invalid webhook signature received")
            return jsonify({
                "status": "error", 
                "message": "Invalid webhook signature"
            }), 401
        
        # If signature is valid, process like a normal webhook
        return receive_webhook()
    
    except Exception as e:
        logger.error(f"Error processing secure webhook: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@webhook_bp.route('/api/webhook/test', methods=['GET'])
def test_webhook():
    """
    Test endpoint to verify webhook functionality
    """
    return jsonify({
        "status": "success", 
        "message": "Webhook endpoint is working. Send a POST request to /api/webhook with your data."
    })

@webhook_bp.route('/api/webhook/data', methods=['GET'])
def get_data():
    """
    Endpoint to retrieve webhook data
    """
    try:
        source_filter = request.args.get('source')
        date_from = request.args.get('from')
        date_to = request.args.get('to')
        limit = request.args.get('limit')
        
        # Convert limit to integer if provided
        if limit:
            try:
                limit = int(limit)
            except ValueError:
                limit = None
        
        data = get_webhook_data(source_filter, date_from, date_to, limit)
        return jsonify({"status": "success", "data": data})
    
    except Exception as e:
        logger.error(f"Error retrieving webhook data: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@webhook_bp.route('/api/webhook/export', methods=['GET'])
def export_data():
    """
    Export webhook data in various formats
    
    Query parameters:
    - format: json, csv, or excel (default: json)
    - source: filter by source
    - from: start date in ISO format
    - to: end date in ISO format
    - pretty: true/false for pretty JSON (default: false)
    """
    try:
        # Get export parameters
        export_format = request.args.get('format', 'json').lower()
        source_filter = request.args.get('source')
        date_from = request.args.get('from')
        date_to = request.args.get('to')
        pretty = request.args.get('pretty', 'false').lower() == 'true'
        
        # Export data in requested format
        if export_format == 'json':
            data, filename = export_data_as_json(source_filter, date_from, date_to, pretty)
            response = make_response(data)
            response.headers['Content-Type'] = 'application/json'
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        
        elif export_format == 'csv':
            data, filename = export_data_as_csv(source_filter, date_from, date_to)
            response = make_response(data)
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        
        elif export_format == 'excel':
            data, filename = export_data_as_excel(source_filter, date_from, date_to)
            if data is None:
                return jsonify({
                    "status": "error", 
                    "message": "Excel export is not available. Pandas library is required."
                }), 400
                
            return send_file(
                io.BytesIO(data),
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=filename
            )
        
        else:
            return jsonify({
                "status": "error", 
                "message": f"Unsupported export format: {export_format}. Supported formats are: json, csv, excel"
            }), 400
    
    except Exception as e:
        logger.error(f"Error exporting webhook data: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
