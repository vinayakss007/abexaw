"""
Scanner routes module

This module provides routes for the scanning functionality of the application.
"""

import os
import json
import datetime
import traceback
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename

from scanner.scan_processor import ScanProcessor, save_uploaded_file

# Create blueprint
scanner_bp = Blueprint('scanner', __name__, url_prefix='/scanner')

# Initialize scan processor
scan_processor = ScanProcessor()

@scanner_bp.route('/')
def scanner_page():
    """
    Scanner main page
    """
    return render_template('scanner.html')

@scanner_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    Handle file upload and scanning
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    # Check file extension
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf', '.tiff', '.tif', '.bmp']
    file_ext = os.path.splitext(file.filename.lower())[1]
    
    if file_ext not in allowed_extensions:
        return jsonify({
            'error': 'File type not supported',
            'message': f'Supported formats: {", ".join(allowed_extensions)}'
        }), 400
        
    try:
        # Save the uploaded file
        file_path = save_uploaded_file(file)
        
        # Process the file
        result = scan_processor.process_file(file_path)
        
        # Return the results
        return jsonify({
            'success': True,
            'message': 'File processed successfully',
            'scan_id': result.get('scan_id', ''),
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Processing error',
            'message': str(e)
        }), 500

@scanner_bp.route('/history')
def scan_history():
    """
    View scan history
    """
    processed_files = []
    
    # List processed JSON files
    processed_folder = 'data/processed_scans'
    
    if os.path.exists(processed_folder):
        for filename in os.listdir(processed_folder):
            if filename.endswith('.json'):
                file_path = os.path.join(processed_folder, filename)
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        processed_files.append(data)
                except Exception as e:
                    print(f"Error reading {file_path}: {str(e)}")
    
    # Sort by timestamp (newest first)
    processed_files.sort(
        key=lambda x: x.get('timestamp', ''), 
        reverse=True
    )
    
    return render_template(
        'scan_history.html', 
        scans=processed_files
    )

@scanner_bp.route('/view/<scan_id>')
def view_scan(scan_id):
    """
    View a specific scan
    """
    processed_folder = 'data/processed_scans'
    
    for filename in os.listdir(processed_folder):
        if filename.endswith('.json'):
            file_path = os.path.join(processed_folder, filename)
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if data.get('scan_id') == scan_id:
                        return render_template('scan_view.html', scan=data)
            except Exception as e:
                print(f"Error reading {file_path}: {str(e)}")
    
    return render_template('error.html', message=f"Scan with ID {scan_id} not found"), 404

@scanner_bp.route('/uploads/<path:filename>')
def serve_uploaded_file(filename):
    """
    Serve uploaded files
    """
    return send_from_directory('data/scans', filename)

@scanner_bp.route('/sample')
def sample_scan():
    """
    Create a sample scan for testing
    """
    try:
        # Load sample image
        sample_file_path = 'static/img/aBETwORLKS.png'
        
        if not os.path.exists(sample_file_path):
            return jsonify({
                'error': 'Sample file not found',
                'message': 'The sample image file does not exist.'
            }), 404
            
        # Copy the file to the uploads folder with a timestamp
        filename = f"sample_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        upload_path = os.path.join('data/scans', filename)
        
        # Make a copy of the file
        with open(sample_file_path, 'rb') as src, open(upload_path, 'wb') as dst:
            dst.write(src.read())
        
        # Process the file
        result = scan_processor.process_file(upload_path)
        
        # Redirect to the scan view page
        return redirect(url_for('scanner.view_scan', scan_id=result['scan_id']))
        
    except Exception as e:
        error_details = traceback.format_exc()
        return render_template('error.html', 
                             message=f"Error creating sample scan: {str(e)}",
                             details=error_details)