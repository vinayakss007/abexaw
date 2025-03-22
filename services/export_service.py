"""
Export service for webhook data

This module provides functionality to export webhook data in various formats
such as CSV, Excel, and JSON.
"""
import json
import logging
import csv
from datetime import datetime
from io import StringIO, BytesIO
from typing import Tuple, Dict, List, Optional, Any, Union

from services.data_service import get_webhook_data

logger = logging.getLogger(__name__)

# Try to import pandas for Excel export
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("Pandas not available. Excel export functionality will be limited.")

def export_data_as_json(
    source_filter: Optional[str] = None, 
    date_from: Optional[str] = None, 
    date_to: Optional[str] = None, 
    pretty: bool = False
) -> Tuple[str, str]:
    """
    Export webhook data as JSON
    
    Args:
        source_filter (str, optional): Filter by source
        date_from (str, optional): ISO format date string for start date
        date_to (str, optional): ISO format date string for end date
        pretty (bool, optional): Whether to format JSON for readability
    
    Returns:
        tuple: (data, filename)
            - data: string containing the JSON data
            - filename: suggested filename for the export
    """
    try:
        # Get data from database
        data = get_webhook_data(source_filter, date_from, date_to)
        
        # Generate a filename
        filename = generate_export_filename("json", source_filter)
        
        # Convert to JSON
        if pretty:
            json_data = json.dumps(data, indent=2, sort_keys=True)
        else:
            json_data = json.dumps(data)
        
        return json_data, filename
    
    except Exception as e:
        logger.error(f"Error exporting JSON data: {str(e)}")
        return json.dumps({"error": str(e)}), "export_error.json"

def export_data_as_csv(
    source_filter: Optional[str] = None, 
    date_from: Optional[str] = None, 
    date_to: Optional[str] = None
) -> Tuple[str, str]:
    """
    Export webhook data as CSV
    
    Args:
        source_filter (str, optional): Filter by source
        date_from (str, optional): ISO format date string for start date
        date_to (str, optional): ISO format date string for end date
    
    Returns:
        tuple: (data, filename)
            - data: string containing the CSV data
            - filename: suggested filename for the export
    """
    try:
        # Get data from database
        data = get_webhook_data(source_filter, date_from, date_to)
        
        # Generate a filename
        filename = generate_export_filename("csv", source_filter)
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header row
        flattened_data = flatten_webhook_data(data)
        if flattened_data:
            # Get all unique keys from all items
            all_keys = set()
            for item in flattened_data:
                all_keys.update(item.keys())
            
            # Sort the keys for consistent output
            sorted_keys = sorted(all_keys)
            
            # Write header
            writer.writerow(sorted_keys)
            
            # Write data rows
            for item in flattened_data:
                row = [item.get(key, "") for key in sorted_keys]
                writer.writerow(row)
        else:
            # Write an empty result with a header
            writer.writerow(["id", "timestamp", "source", "data"])
        
        return output.getvalue(), filename
    
    except Exception as e:
        logger.error(f"Error exporting CSV data: {str(e)}")
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Error"])
        writer.writerow([str(e)])
        return output.getvalue(), "export_error.csv"

def export_data_as_excel(
    source_filter: Optional[str] = None, 
    date_from: Optional[str] = None, 
    date_to: Optional[str] = None
) -> Tuple[Optional[bytes], str]:
    """
    Export webhook data as Excel
    
    Args:
        source_filter (str, optional): Filter by source
        date_from (str, optional): ISO format date string for start date
        date_to (str, optional): ISO format date string for end date
    
    Returns:
        tuple: (data, filename)
            - data: bytes containing the Excel data, or None if pandas is not available
            - filename: suggested filename for the export
    """
    if not PANDAS_AVAILABLE:
        logger.warning("Excel export requested but pandas is not available")
        return None, "export_error.xlsx"
    
    try:
        # Get data from database
        data = get_webhook_data(source_filter, date_from, date_to)
        
        # Generate a filename
        filename = generate_export_filename("xlsx", source_filter)
        
        # Flatten the webhook data
        flattened_data = flatten_webhook_data(data)
        
        # Convert to DataFrame
        df = pd.DataFrame(flattened_data)
        
        # Convert to Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Webhook Data', index=False)
            
            # Auto-adjust columns' width
            worksheet = writer.sheets['Webhook Data']
            for i, col in enumerate(df.columns):
                column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, column_width)
        
        return output.getvalue(), filename
    
    except Exception as e:
        logger.error(f"Error exporting Excel data: {str(e)}")
        if PANDAS_AVAILABLE:
            # Create an error DataFrame
            df = pd.DataFrame([{"Error": str(e)}])
            output = BytesIO()
            df.to_excel(output, index=False)
            return output.getvalue(), "export_error.xlsx"
        return None, "export_error.xlsx"

def generate_export_filename(extension: str, source_filter: Optional[str] = None) -> str:
    """
    Generate a filename for an export file
    
    Args:
        extension (str): The file extension (without dot)
        source_filter (str, optional): Source filter used for the export
    
    Returns:
        str: A filename for the export
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if source_filter:
        # Normalize source filter to lowercase to ensure consistent filenames
        source_name = source_filter.lower()
        return f"webhook_data_{source_name}_{timestamp}.{extension}"
    else:
        return f"webhook_data_{timestamp}.{extension}"

def flatten_webhook_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Flatten the webhook data for export
    
    This function creates a flattened view of webhook data suitable for 
    export to tabular formats like CSV and Excel.
    
    Args:
        data (list): List of webhook data dictionaries
    
    Returns:
        list: List of flattened webhook data dictionaries
    """
    flattened = []
    
    for item in data:
        flat_item = {
            "id": item.get("id", ""),
            "timestamp": item.get("timestamp", ""),
            "source": item.get("source", "")
        }
        
        # Add first-level keys from the payload
        payload = item.get("data", {})
        
        if isinstance(payload, dict):
            # For each key in the payload, add it to the flattened item
            # Skip 'original_data' to avoid duplication and deeply nested structures
            for key, value in payload.items():
                if key != 'original_data' and not isinstance(value, (dict, list)):
                    flat_key = f"data_{key}"
                    flat_item[flat_key] = str(value) if value is not None else ""
            
            # Special handling for common nested structures
            # Contact info
            if "contact_info" in payload and isinstance(payload["contact_info"], dict):
                for key, value in payload["contact_info"].items():
                    flat_item[f"contact_{key}"] = str(value) if value is not None else ""
            
            # Entity data (for CRM)
            if "entity_data" in payload and isinstance(payload["entity_data"], dict):
                for key, value in payload["entity_data"].items():
                    if not isinstance(value, (dict, list)):
                        flat_item[f"entity_{key}"] = str(value) if value is not None else ""
            
            # Submission data (for forms)
            if "submission_data" in payload and isinstance(payload["submission_data"], dict):
                for key, value in payload["submission_data"].items():
                    if not isinstance(value, (dict, list)):
                        flat_item[f"submission_{key}"] = str(value) if value is not None else ""
        
        flattened.append(flat_item)
    
    return flattened