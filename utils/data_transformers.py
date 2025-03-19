import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def transform_for_charts(data):
    """
    Transform webhook data for chart visualization
    """
    try:
        # Get the dates for the last 7 days
        today = datetime.now().date()
        dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
        
        # Initialize source data
        sources = {}
        
        # Count data by date and source
        for item in data:
            # Extract timestamp and convert to date
            try:
                if isinstance(item.get('timestamp'), str):
                    timestamp = datetime.fromisoformat(item.get('timestamp', '')).date().strftime("%Y-%m-%d")
                elif isinstance(item.get('timestamp'), datetime):
                    timestamp = item.get('timestamp').date().strftime("%Y-%m-%d")
                else:
                    continue
            except (ValueError, TypeError):
                continue
                
            source = item.get('source', 'other')
            
            # Initialize source if not exists
            if source not in sources:
                sources[source] = {date: 0 for date in dates}
            
            # Increment count if timestamp is in the last 7 days
            if timestamp in dates:
                sources[source][timestamp] += 1
        
        # Format for Chart.js
        chart_data = {
            'labels': dates,
            'datasets': []
        }
        
        # Default colors for sources
        colors = {
            'crm': '#4CAF50',
            'form': '#2196F3',
            'email': '#F44336',
            'other': '#9C27B0'
        }
        
        # Create datasets for each source
        for source, date_counts in sources.items():
            dataset = {
                'label': source.capitalize(),
                'data': [date_counts[date] for date in dates],
                'backgroundColor': colors.get(source, '#888888'),
                'borderColor': colors.get(source, '#888888'),
                'fill': False
            }
            chart_data['datasets'].append(dataset)
        
        return chart_data
    
    except Exception as e:
        logger.error(f"Error transforming data for charts: {str(e)}")
        return {'labels': [], 'datasets': []}

def format_webhook_data_for_table(data, limit=None):
    """
    Format webhook data for table display
    """
    try:
        # Sort by timestamp (newest first)
        sorted_data = sorted(data, key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Apply limit if specified
        if limit:
            sorted_data = sorted_data[:limit]
        
        # Format the data for table display
        table_data = []
        for item in sorted_data:
            # Format timestamp
            try:
                if isinstance(item.get('timestamp'), str):
                    timestamp = datetime.fromisoformat(item.get('timestamp', ''))
                elif isinstance(item.get('timestamp'), datetime):
                    timestamp = item.get('timestamp')
                else:
                    raise ValueError("Invalid timestamp format")
                formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                formatted_time = "Unknown"
            
            # Extract key fields from payload
            payload = item.get('data', {})
            
            # Create table row
            table_row = {
                'id': item.get('id', 'Unknown'),
                'timestamp': formatted_time,
                'source': item.get('source', 'other'),
                'summary': get_payload_summary(payload)
            }
            
            table_data.append(table_row)
        
        return table_data
    
    except Exception as e:
        logger.error(f"Error formatting webhook data for table: {str(e)}")
        return []

def get_payload_summary(payload, max_length=100):
    """
    Generate a summary of the webhook payload
    """
    try:
        # Try to identify key fields like name, email, subject, etc.
        key_fields = ['name', 'email', 'subject', 'title', 'message', 'event']
        
        for field in key_fields:
            if field in payload and payload[field]:
                value = str(payload[field])
                if len(value) > max_length:
                    value = value[:max_length] + '...'
                return value
        
        # If no key fields found, return a generic summary
        payload_str = str(payload)
        if len(payload_str) > max_length:
            payload_str = payload_str[:max_length] + '...'
        
        return payload_str
    
    except Exception:
        return "Cannot display payload"
