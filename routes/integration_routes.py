import logging
import os
from flask import Blueprint, request, jsonify, render_template
from services.integration_service import (
    send_email_notification, 
    get_integrations,
    get_integration,
    save_integration,
    delete_integration
)

logger = logging.getLogger(__name__)
integration_bp = Blueprint('integration', __name__)

@integration_bp.route('/api/integrations/email', methods=['POST'])
def email_integration():
    """
    Integration with email services
    """
    try:
        data = request.json
        recipient = data.get('recipient')
        subject = data.get('subject', 'New Webhook Notification')
        body = data.get('body', 'You have received new webhook data')
        
        # Send email notification
        result = send_email_notification(recipient, subject, body)
        
        return jsonify({"status": "success", "message": "Email notification sent", "result": result})
    
    except Exception as e:
        logger.error(f"Error with email integration: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@integration_bp.route('/api/integrations/stripe', methods=['POST'])
def stripe_integration():
    """Handle Stripe webhooks"""
    try:
        data = request.json
        result = integrate_with_stripe(data)
        return jsonify({"status": "success", "result": result})
    except Exception as e:
        logger.error(f"Error with Stripe integration: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@integration_bp.route('/api/integrations/paypal', methods=['POST'])
def paypal_integration():
    """Handle PayPal webhooks"""
    try:
        data = request.json
        result = integrate_with_paypal(data)
        return jsonify({"status": "success", "result": result})
    except Exception as e:
        logger.error(f"Error with PayPal integration: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@integration_bp.route('/api/integrations/google-analytics', methods=['POST'])
def google_analytics_integration():
    """Handle Google Analytics events"""
    try:
        data = request.json
        result = integrate_with_google_analytics(data)
        return jsonify({"status": "success", "result": result})
    except Exception as e:
        logger.error(f"Error with Google Analytics integration: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@integration_bp.route('/api/integrations/whatsapp', methods=['POST'])
def whatsapp_integration():
    """Handle WhatsApp Business API"""
    try:
        data = request.json
        result = integrate_with_whatsapp(data)
        return jsonify({"status": "success", "result": result})
    except Exception as e:
        logger.error(f"Error with WhatsApp integration: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@integration_bp.route('/api/integrations/facebook', methods=['POST'])
def facebook_integration():
    """Handle Facebook webhooks"""
    try:
        data = request.json
        result = integrate_with_facebook(data)
        return jsonify({"status": "success", "result": result})
    except Exception as e:
        logger.error(f"Error with Facebook integration: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@integration_bp.route('/api/integrations/crm', methods=['POST'])
def crm_integration():
    """
    Integration with CRM services
    """
    # This is a placeholder for CRM integration
    # In a real application, this would connect to a CRM API
    try:
        data = request.json
        
        # Simulate CRM integration
        logger.info(f"CRM integration called with data: {data}")
        
        return jsonify({
            "status": "success", 
            "message": "CRM integration successful (demonstration mode)",
            "data": data
        })
    
    except Exception as e:
        logger.error(f"Error with CRM integration: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@integration_bp.route('/api/integrations', methods=['GET'])
def list_integrations():
    """
    Get all configured integrations
    """
    try:
        integrations = get_integrations()
        return jsonify({
            "status": "success",
            "integrations": integrations
        })
    
    except Exception as e:
        logger.error(f"Error listing integrations: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@integration_bp.route('/api/integrations/<int:integration_id>', methods=['GET'])
def get_integration_by_id(integration_id):
    """
    Get a specific integration by ID
    """
    try:
        integration = get_integration(integration_id)
        if integration:
            return jsonify({
                "status": "success",
                "integration": integration
            })
        else:
            return jsonify({"status": "error", "message": "Integration not found"}), 404
    
    except Exception as e:
        logger.error(f"Error retrieving integration: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@integration_bp.route('/api/integrations', methods=['POST'])
def create_integration():
    """
    Create a new integration
    """
    try:
        data = request.json
        integration = save_integration(data)
        
        if integration:
            return jsonify({
                "status": "success",
                "message": "Integration created successfully",
                "integration": integration
            })
        else:
            return jsonify({"status": "error", "message": "Failed to create integration"}), 500
    
    except Exception as e:
        logger.error(f"Error creating integration: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@integration_bp.route('/api/integrations/<int:integration_id>', methods=['PUT'])
def update_integration(integration_id):
    """
    Update an existing integration
    """
    try:
        data = request.json
        data['id'] = integration_id
        
        integration = save_integration(data)
        
        if integration:
            return jsonify({
                "status": "success",
                "message": "Integration updated successfully",
                "integration": integration
            })
        else:
            return jsonify({"status": "error", "message": "Failed to update integration"}), 500
    
    except Exception as e:
        logger.error(f"Error updating integration: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@integration_bp.route('/api/integrations/<int:integration_id>', methods=['DELETE'])
def remove_integration(integration_id):
    """
    Delete an integration
    """
    try:
        result = delete_integration(integration_id)
        
        if result:
            return jsonify({
                "status": "success",
                "message": "Integration deleted successfully"
            })
        else:
            return jsonify({"status": "error", "message": "Integration not found or could not be deleted"}), 404
    
    except Exception as e:
        logger.error(f"Error deleting integration: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
