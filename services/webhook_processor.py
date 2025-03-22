"""
Webhook processor service

This module handles the processing of webhook data from different sources.
It contains processors for different webhook types and utilities for routing
webhooks to the appropriate processor.
"""
import json
import logging
import re
import hashlib
import hmac
import base64
import uuid
from functools import wraps
from typing import Dict, Any, Callable, List
from services.notification_service import notify_processing_error

logger = logging.getLogger(__name__)

# Registry to store webhook processors by source type
_PROCESSOR_REGISTRY = {}

def register_processor(source_type: str):
    """
    Decorator to register a webhook processor function for a specific source type
    
    Usage:
        @register_processor('stripe')
        def process_stripe_webhook(data):
            # Process stripe webhook data
            return processed_data
    """
    def decorator(func: Callable):
        _PROCESSOR_REGISTRY[source_type] = func
        logger.debug(f"Registered webhook processor for source: {source_type}")
        
        @wraps(func)
        def wrapper(data):
            return func(data)
        
        return wrapper
    
    return decorator

def process_webhook(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for webhook processing
    
    Args:
        data (dict): The raw webhook data
    
    Returns:
        dict: Processed webhook data
    """
    try:
        # Determine the source type of the webhook
        source_type = determine_source(data)
        
        # Find the registered processor for this source type
        processor = _PROCESSOR_REGISTRY.get(source_type)
        
        # If no specific processor is found, use the generic processor
        if not processor:
            logger.info(f"No specific processor found for {source_type}, using generic processor")
            return generic_processor(data)
        
        # Otherwise, use the registered processor
        logger.info(f"Processing webhook with {source_type} processor")
        processed_data = processor(data)
        
        # Check if the processor returned an error
        if 'error' in processed_data:
            # Generate webhook_id if not present
            webhook_id = data.get('id') or processed_data.get('id')
            if not webhook_id:
                webhook_id = str(uuid.uuid4())
                processed_data['id'] = webhook_id
                
            # Send an error notification
            error_message = processed_data.get('error', 'Unknown processing error')
            notify_processing_error(source_type, error_message, webhook_id)
            
            # Set error status
            processed_data['status'] = 'error'
        
        return processed_data
        
    except Exception as e:
        # Handle unexpected errors during processing
        logger.error(f"Unexpected error in webhook processing: {str(e)}")
        
        # Determine source type safely
        try:
            source_type = determine_source(data)
        except:
            source_type = 'unknown'
        
        # Generate webhook_id
        webhook_id = data.get('id', str(uuid.uuid4()))
        
        # Send error notification
        notify_processing_error(source_type, str(e), webhook_id)
        
        # Return error information
        return {
            'id': webhook_id,
            'source': source_type,
            'status': 'error',
            'error': str(e),
            'original_data': data
        }

def determine_source(data: Dict[str, Any]) -> str:
    """
    Determine the source of a webhook based on its content
    
    Args:
        data (dict): The webhook data
    
    Returns:
        str: The determined source type
    """
    # First check if the source is explicitly set
    if 'source' in data:
        return data['source']
    
    # Check for Stripe-specific fields
    if 'type' in data and data.get('object') == 'event' and 'api_version' in data:
        return 'stripe'
    
    # Check for PayPal-specific fields
    if 'event_type' in data and 'resource_type' in data and data.get('resource_type') == 'sale':
        return 'paypal'
    
    # Check for Google Analytics webhooks
    if any(field in data for field in ['tracking_id', 'client_id', 'page_view', 'event_action']):
        return 'google'
    
    # Check for WhatsApp Business API webhooks
    if 'entry' in data and 'changes' in data.get('entry', [{}])[0] and 'messaging_product' in data.get('entry', [{}])[0].get('changes', [{}])[0]:
        return 'whatsapp'
    
    # Check for Facebook webhooks
    if 'entry' in data and 'changes' in data.get('entry', [{}])[0] and 'id' in data.get('entry', [{}])[0]:
        return 'facebook'
    
    # Check for Newsletter webhooks - check first to avoid misclassifying as form
    if any(keyword in str(data).lower() for keyword in ['newsletter', 'subscribe', 'mailing list']):
        return 'newsletter'
    
    # Check for form submission patterns
    if any(field in data for field in ['name', 'email', 'message', 'phone']):
        return 'form'
    
    # Check for CRM webhooks
    if any(field in data for field in ['customer', 'lead', 'opportunity', 'contact']):
        return 'crm'
    
    # Check for Shopping Cart webhooks
    if any(field in data for field in ['cart', 'product', 'order', 'checkout']):
        return 'cart'
    
    # Check for Scanner webhooks
    if any(field in data for field in ['scan_id', 'extracted_text', 'scan_type', 'scan_data']):
        return 'scanner'
    
    # Default source type
    return 'other'

def validate_webhook_signature(request, secret: str) -> bool:
    """
    Validate webhook signature for authenticity
    
    Args:
        request: The Flask request object
        secret (str): The secret used to sign the webhook
        
    Returns:
        bool: True if signature is valid, False otherwise
    """
    try:
        # Get the signature from headers
        signature_header = request.headers.get('X-Webhook-Signature')
        
        if not signature_header:
            # Stripe style signature
            signature_header = request.headers.get('Stripe-Signature')
            
        if not signature_header:
            # GitHub style signature
            signature_header = request.headers.get('X-Hub-Signature')
            
        if not signature_header:
            logger.warning("No signature header found in request")
            return False
        
        # Get the request body
        payload_body = request.data
        
        # Compute the signature
        computed_signature = hmac.new(
            secret.encode('utf-8'),
            payload_body,
            hashlib.sha256
        ).hexdigest()
        
        # GitHub style uses sha1
        if request.headers.get('X-Hub-Signature'):
            computed_signature = 'sha1=' + hmac.new(
                secret.encode('utf-8'),
                payload_body,
                hashlib.sha1
            ).hexdigest()
        
        # Compare the signatures
        return hmac.compare_digest(computed_signature, signature_header)
    
    except Exception as e:
        logger.error(f"Error validating webhook signature: {str(e)}")
        return False

# Register processors for different webhook types

@register_processor('stripe')
def process_stripe_webhook(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process Stripe webhooks"""
    try:
        # Extract the event type
        event_type = data.get('type', '').replace('.', '_')
        
        # Add metadata to the processed data
        processed_data = {
            'source': 'stripe',
            'event_type': event_type,
            'payment_status': None,
            'amount': None,
            'customer_email': None,
            'customer_name': None,
            'original_data': data
        }
        
        # Extract common useful information based on event type
        if 'data' in data and 'object' in data['data']:
            obj = data['data']['object']
            
            # Handle different object types
            if obj.get('object') == 'charge':
                processed_data['payment_status'] = obj.get('status')
                processed_data['amount'] = obj.get('amount')
                if 'billing_details' in obj:
                    processed_data['customer_email'] = obj['billing_details'].get('email')
                    processed_data['customer_name'] = obj['billing_details'].get('name')
            
            elif obj.get('object') == 'payment_intent':
                processed_data['payment_status'] = obj.get('status')
                processed_data['amount'] = obj.get('amount')
                if 'receipt_email' in obj:
                    processed_data['customer_email'] = obj.get('receipt_email')
            
            elif obj.get('object') == 'subscription':
                processed_data['payment_status'] = obj.get('status')
                processed_data['amount'] = obj.get('plan', {}).get('amount')
                processed_data['customer_id'] = obj.get('customer')
        
        return processed_data
    
    except Exception as e:
        logger.error(f"Error processing Stripe webhook: {str(e)}")
        return {
            'source': 'stripe',
            'error': str(e),
            'original_data': data
        }

@register_processor('form')
def process_form_webhook(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process form submission webhooks with enhanced source type detection"""
    try:
        # Create a standardized structure
        processed_data = {
            'source': 'form',
            'form_type': data.get('form_type', 'generic'),
            'submission_data': {},
            'contact_info': {},
            'metadata': {},
            'original_data': data
        }
        
        # Detect newsletter forms based on common patterns
        is_newsletter = False
        if any(keyword in str(data).lower() for keyword in ['newsletter', 'subscribe', 'mailing list']):
            processed_data['form_type'] = 'newsletter'
            is_newsletter = True
        
        # Check for specific newsletter fields
        if any(key in data for key in ['subscribe', 'newsletter_email', 'signup', 'subscription']):
            processed_data['form_type'] = 'newsletter'
            is_newsletter = True
            
        # Detect collection forms based on common patterns
        if any(keyword in str(data).lower() for keyword in ['collection', 'product_id', 'category', 'product collection']):
            processed_data['form_type'] = 'collection_form'
        
        # Check for specific collection form fields
        if any(key in data for key in ['product_id', 'collection_id', 'item_category', 'shopping_category']):
            processed_data['form_type'] = 'collection_form'
            
        # Set source subtype for better categorization in database
        processed_data['source_subtype'] = processed_data['form_type']
        
        # Process common form fields
        if 'name' in data:
            processed_data['contact_info']['name'] = data['name']
        
        if 'email' in data:
            processed_data['contact_info']['email'] = data['email']
        
        if 'phone' in data:
            processed_data['contact_info']['phone'] = data['phone']
        
        if 'message' in data:
            processed_data['submission_data']['message'] = data['message']
        
        # Extract all other fields that are not in the special categories
        special_fields = ['source', 'form_type', 'name', 'email', 'phone', 'message', '_headers']
        
        for key, value in data.items():
            if key not in special_fields:
                processed_data['submission_data'][key] = value
        
        # Enhanced newsletter processing - ensure newsletter content is captured
        if is_newsletter:
            # Look for newsletter content in various possible fields
            for key in ['content', 'newsletter_content', 'email_content', 'template']:
                if key in data:
                    processed_data['submission_data']['newsletter_content'] = data[key]
                    break
            
            # Look for preferences
            for key in ['preferences', 'frequency', 'email_preferences', 'subscription_preferences']:
                if key in data:
                    processed_data['submission_data'][key] = data[key]
            
            # Set subscription status
            processed_data['submission_data']['subscribed'] = True
            processed_data['submission_data']['subscription_date'] = data.get('timestamp', '')
        
        # Add metadata
        if '_headers' in data and isinstance(data['_headers'], dict):
            if 'user_agent' in data['_headers']:
                processed_data['metadata']['user_agent'] = data['_headers']['user_agent']
            
            if 'referer' in data['_headers']:
                processed_data['metadata']['referer'] = data['_headers']['referer']
        
        return processed_data
    
    except Exception as e:
        logger.error(f"Error processing form webhook: {str(e)}")
        return {
            'source': 'form',
            'source_subtype': 'error',
            'error': str(e),
            'original_data': data
        }

@register_processor('crm')
def process_crm_webhook(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process CRM webhooks with enhanced subtype detection"""
    try:
        # Create a standardized structure
        processed_data = {
            'source': 'crm',
            'crm_type': data.get('crm_type', 'generic'),
            'event_type': data.get('event_type', 'update'),
            'entity_type': None,
            'entity_data': {},
            'original_data': data
        }
        
        # Determine entity type
        for entity_type in ['customer', 'lead', 'opportunity', 'contact', 'deal']:
            if entity_type in data:
                processed_data['entity_type'] = entity_type
                processed_data['entity_data'] = data[entity_type]
                break
        
        # If entity_type is still None, look for common CRM fields
        if processed_data['entity_type'] is None:
            entity_data = {}
            
            # Common field mappings
            for field in ['name', 'email', 'phone', 'company', 'status', 'value', 'stage']:
                if field in data:
                    entity_data[field] = data[field]
            
            if entity_data:
                processed_data['entity_type'] = 'generic'
                processed_data['entity_data'] = entity_data
                
        # Set source subtype for better categorization - use either crm_type or entity_type
        if processed_data['crm_type'] != 'generic':
            processed_data['source_subtype'] = processed_data['crm_type']
        elif processed_data['entity_type']:
            processed_data['source_subtype'] = processed_data['entity_type']
        else:
            processed_data['source_subtype'] = 'unknown'
            
        # Look for specific CRM systems in the data
        crm_systems = {
            'salesforce': ['salesforce', 'sf_', 'sfdc'],
            'hubspot': ['hubspot', 'hs_'],
            'zoho': ['zoho', 'zcrm'],
            'pipedrive': ['pipedrive', 'pd_deal'],
            'dynamics': ['dynamics', 'ms_crm', 'mscrm']
        }
        
        data_str = str(data).lower()
        for system, keywords in crm_systems.items():
            if any(keyword in data_str for keyword in keywords):
                processed_data['crm_type'] = system
                processed_data['source_subtype'] = system
                break
        
        return processed_data
    
    except Exception as e:
        logger.error(f"Error processing CRM webhook: {str(e)}")
        return {
            'source': 'crm',
            'source_subtype': 'error',
            'error': str(e),
            'original_data': data
        }

@register_processor('paypal')
def process_paypal_webhook(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process PayPal webhooks"""
    try:
        # Create a standardized structure
        processed_data = {
            'source': 'paypal',
            'event_type': data.get('event_type', ''),
            'payment_status': None,
            'amount': None,
            'customer_email': None,
            'transaction_id': None,
            'original_data': data
        }
        
        # Extract information from resource
        if 'resource' in data:
            resource = data['resource']
            
            if 'state' in resource:
                processed_data['payment_status'] = resource['state']
            
            if 'amount' in resource:
                if isinstance(resource['amount'], dict) and 'total' in resource['amount']:
                    processed_data['amount'] = resource['amount']['total']
                else:
                    processed_data['amount'] = resource['amount']
            
            if 'payer' in resource and 'email_address' in resource['payer']:
                processed_data['customer_email'] = resource['payer']['email_address']
            
            if 'id' in resource:
                processed_data['transaction_id'] = resource['id']
        
        return processed_data
    
    except Exception as e:
        logger.error(f"Error processing PayPal webhook: {str(e)}")
        return {
            'source': 'paypal',
            'error': str(e),
            'original_data': data
        }

def generic_processor(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generic processor for unknown webhook types
    
    This is used when no specific processor is found for a source type.
    """
    source = determine_source(data)
    
    # Create a standardized output structure
    processed_data = {
        'source': source,
        'source_subtype': data.get('type', 'generic'),
        'contact_info': {},
        'submission_data': {},
        'metadata': {},
        'processed': True,
        'original_data': data
    }
    
    # Process common fields if they exist
    if 'email' in data:
        processed_data['contact_info']['email'] = data['email']
    if 'name' in data:
        processed_data['contact_info']['name'] = data['name']
    if 'message' in data:
        processed_data['submission_data']['message'] = data['message']
    
    # Handle subscription data
    if source.lower() in ['subscribed', 'newsletter', 'subscription']:
        processed_data['subscribed'] = True
        processed_data['subscription_date'] = data.get('timestamp', '')
    
    # Try to extract useful information
    for key in ['id', 'event', 'type', 'action', 'status', 'timestamp']:
        if key in data:
            processed_data['submission_data'][key] = data[key]
    
    return processed_data
@register_processor('newsletter')
def process_newsletter_webhook(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process newsletter webhooks
    
    Newsletter webhooks contain data from newsletter subscriptions, including
    email, name, and preferences.
    """
    try:
        # Create a standardized structure
        processed_data = {
            'source': 'newsletter',
            'contact_info': {},
            'preferences': {},
            'metadata': {},
            'original_data': data
        }
        
        # Process common fields
        if 'name' in data:
            processed_data['contact_info']['name'] = data['name']
        
        if 'email' in data:
            processed_data['contact_info']['email'] = data['email']
        
        if 'phone' in data:
            processed_data['contact_info']['phone'] = data['phone']
        
        if 'message' in data:
            processed_data['message'] = data['message']
        
        # Extract newsletter-specific fields
        for key in ['frequency', 'preferences', 'interests', 'topics']:
            if key in data:
                processed_data['preferences'][key] = data[key]
        
        # Set subscription status
        processed_data['subscribed'] = True
        processed_data['subscription_date'] = data.get('timestamp', '')
        
        # Add metadata
        if '_headers' in data and isinstance(data['_headers'], dict):
            if 'user_agent' in data['_headers']:
                processed_data['metadata']['user_agent'] = data['_headers']['user_agent']
            
            if 'referer' in data['_headers']:
                processed_data['metadata']['referer'] = data['_headers']['referer']
        
        return processed_data
    
    except Exception as e:
        logger.error(f"Error processing newsletter webhook: {str(e)}")
        return {
            'source': 'newsletter',
            'error': str(e),
            'original_data': data
        }

@register_processor('scanner')
def process_scanner_webhook(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process scanner webhooks
    
    Scanner webhooks contain data from processed document scans, including
    extracted text, structured data, and metadata about the scanned document.
    """
    try:
        # Generate ID if not provided
        webhook_id = data.get('scan_id') or str(uuid.uuid4())
        
        # Get event type from data or default to 'scan_processed'
        event_type = data.get('event_type', 'scan_processed')
        
        # Extract source subtype (image, pdf, etc.)
        source_subtype = data.get('source_subtype', 'unknown')
        
        # Get scan data
        scan_data = data.get('data', {})
        
        # Create structured payload for database
        processed_data = {
            'id': webhook_id,
            'source': 'scanner',
            'source_subtype': source_subtype,
            'event_type': event_type,
            'status': 'processed',
            'data': scan_data,
            'metadata': data.get('metadata', {})
        }
        
        logger.info(f"Processed scanner webhook: {webhook_id} - Document type: {source_subtype}")
        
        return processed_data
    
    except Exception as e:
        logger.error(f"Error processing scanner webhook: {str(e)}")
        return {
            'source': 'scanner',
            'source_subtype': 'error',
            'error': str(e),
            'original_data': data
        }
