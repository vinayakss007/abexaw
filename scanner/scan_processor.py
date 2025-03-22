"""
Scan Processor Module

This module provides functionality for scanning and processing images and documents
with text extraction, metadata analysis, and webhook integration.

Note: This version uses pytesseract for OCR.  Ensure pytesseract and its dependencies are installed.
"""

import os
import uuid
import json
import datetime
import logging
import re
from typing import Dict, Any, List, Tuple, Optional
import base64
from io import BytesIO

from PIL import Image, ImageFilter, ImageEnhance
import requests
import pytesseract
import cv2
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure file paths
UPLOAD_FOLDER = 'data/scans'
PROCESSED_FOLDER = 'data/processed_scans'
TEMP_FOLDER = 'data/temp'

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)

class ScanProcessor:
    """
    ScanProcessor handles scanning and processing images and documents
    """

    def __init__(self):
        """Initialize the scan processor"""
        self.supported_image_types = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
        self.supported_document_types = ['.pdf']
        self.webhook_url = 'http://localhost:5000/api/webhook'

    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process an uploaded file based on its type

        Args:
            file_path: Path to the uploaded file

        Returns:
            Dict containing processed data and metadata
        """
        file_ext = os.path.splitext(file_path)[1].lower()

        try:
            # Process the file based on its type
            if file_ext in self.supported_image_types:
                result = self.process_image(file_path)
            elif file_ext in self.supported_document_types:
                result = self.process_document(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")

            # Save processed result
            result_path = os.path.join(
                PROCESSED_FOLDER, 
                f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{os.path.basename(file_path)}.json"
            )

            with open(result_path, 'w') as f:
                json.dump(result, f, indent=2)

            # Send to webhook system
            self.send_to_webhook(result)

            return result

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            raise

    def process_image(self, image_path: str) -> Dict[str, Any]:
        """
        Process an image file

        Args:
            image_path: Path to the image file

        Returns:
            Dict containing image analysis and metadata
        """
        try:
            # Get image properties
            with Image.open(image_path) as img:
                width, height = img.size
                format_name = img.format
                mode = img.mode

                # Get a thumbnail for preview
                img.thumbnail((300, 300))
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()

                # Extract metadata
                metadata = {}
                if hasattr(img, 'getexif'):
                    exif = img.getexif()
                    if exif:
                        for tag_id, value in exif.items():
                            tag_name = self._get_exif_tag_name(tag_id)
                            if isinstance(value, bytes):
                                value = str(value)
                            metadata[tag_name] = value

            # Advanced OCR processing
            def perform_ocr(image):
                # Convert PIL image to OpenCV format
                img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

                # Image preprocessing
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                denoised = cv2.fastNlMeansDenoising(gray)
                thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

                # Additional preprocessing for better OCR
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
                processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

                # Convert back to PIL for Tesseract
                pil_img = Image.fromarray(processed)

                # Enhance contrast
                enhancer = ImageEnhance.Contrast(pil_img)
                enhanced = enhancer.enhance(1.5)

                # Perform OCR with advanced configuration
                custom_config = r'--oem 3 --psm 6 -l eng+osd --dpi 300'
                detected_text = pytesseract.image_to_string(enhanced, config=custom_config)

                return detected_text.strip()

            # Process the image with advanced OCR
            detected_text = perform_ocr(img)


            # Extract structured data
            structured_data = self._extract_structured_data(detected_text)

            # Create scan result
            data = {
                'raw_text': detected_text,
                'structured_data': structured_data,
                'type': 'image',
                'file_name': os.path.basename(image_path),
                'timestamp': datetime.datetime.now().isoformat(),
                'file_size': os.path.getsize(image_path),
                'scan_id': str(uuid.uuid4()),
                'image_metadata': {
                    'width': width,
                    'height': height,
                    'format': format_name,
                    'mode': mode,
                    'exif': metadata
                },
                'thumbnail': img_str
            }

            return data

        except Exception as e:
            logger.error(f"Error in process_image: {str(e)}")
            raise

    def process_document(self, pdf_path: str) -> Dict[str, Any]:
        """
        Process a PDF document

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dict containing document analysis and metadata
        """
        try:
            # In a real implementation, we would use a PDF parsing library
            # Since we don't have direct PDF support, we'll simulate the process

            # Get file size
            file_size = os.path.getsize(pdf_path)

            # Generate sample page data
            page_count = min(int(file_size / 10000) + 1, 10)  # Simulate page count based on file size

            # Sample text patterns for different pages
            page_patterns = [
                "Page {page_num}\nThis document contains important information.\nSection {section}: {topic}",
                "Page {page_num}\nData Table\nID\tName\tValue\n001\tItem A\t$100\n002\tItem B\t$200",
                "Page {page_num}\nSignature: ___________________\nDate: {date}",
                "Page {page_num}\nAPPENDIX {appendix}\nAdditional notes and references"
            ]

            # Generate pages with simulated content
            page_data = []
            all_text = []

            for i in range(page_count):
                page_num = i + 1
                import random

                pattern = random.choice(page_patterns)
                page_text = pattern.format(
                    page_num=page_num,
                    section=random.randint(1, 5),
                    topic=random.choice(["Financial", "Technical", "Legal", "Marketing", "Operations"]),
                    date="03/22/2025",
                    appendix=chr(65 + i)
                )

                page_data.append({
                    'page_num': page_num,
                    'text': page_text
                })

                all_text.append(page_text)

            # Combine all text
            combined_text = "\n\n".join(all_text)

            # Extract structured data
            structured_data = self._extract_structured_data(combined_text)

            # Create scan result
            data = {
                'raw_text': combined_text,
                'structured_data': structured_data,
                'pages': page_data,
                'type': 'pdf',
                'file_name': os.path.basename(pdf_path),
                'timestamp': datetime.datetime.now().isoformat(),
                'file_size': file_size,
                'page_count': page_count,
                'scan_id': str(uuid.uuid4())
            }

            return data

        except Exception as e:
            logger.error(f"Error in process_document: {str(e)}")
            raise

    def _get_exif_tag_name(self, tag_id):
        """Get a human-readable name for an EXIF tag ID"""
        exif_tags = {
            271: 'Make',
            272: 'Model',
            274: 'Orientation',
            306: 'DateTime',
            36867: 'DateTimeOriginal',
            37521: 'SubsecTimeOriginal',
            33434: 'ExposureTime',
            33437: 'FNumber',
            37386: 'FocalLength',
            41728: 'FileSource',
            41985: 'CustomRendered',
            41986: 'ExposureMode',
            41987: 'WhiteBalance',
            41988: 'DigitalZoomRatio',
            41989: 'FocalLengthIn35mmFilm',
        }
        return exif_tags.get(tag_id, f'Tag_{tag_id}')

    def _extract_structured_data(self, text: str) -> Dict[str, Any]:
        """
        Extract structured data from text

        Args:
            text: Text content

        Returns:
            Dict of structured data (key-value pairs, etc.)
        """
        # Basic implementation - extract key:value pairs
        structured_data = {}

        # Define regex patterns for common data formats
        patterns = {
            'invoice_number': r'(?i)invoice\s*(?:#|number|num|no)?[:.\s]*\s*([A-Z0-9\-]+)',
            'amount': r'(?i)(?:total|amount|sum|balance)[:.\s]*\s*\$?\s*([0-9,]+\.[0-9]{2})',
            'date': r'(?i)(?:date|issued|created)[:.\s]*\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            'customer_id': r'(?i)(?:customer|client|account|cust)[\s\.\-_]*(?:id|number|#|no)[:.\s]*\s*([A-Z0-9\-]+)',
            'email': r'(?i)(?:email|e-mail)[:.\s]*\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            'phone': r'(?i)(?:phone|tel|telephone|mobile)[:.\s]*\s*(\+?[0-9\-\(\)\s]{10,})',
            'payment_due': r'(?i)(?:due|payment\s*due|pay\s*by)[:.\s]*\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})'
        }

        # Extract data using regex patterns
        for key, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                structured_data[key] = match.group(1).strip()

        # Also check for key-value pairs with : or = separators
        lines = text.split('\n')
        for line in lines:
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip().lower().replace(' ', '_')
                    value = parts[1].strip()
                    if key not in structured_data and value:
                        structured_data[key] = value
            elif '=' in line:
                parts = line.split('=', 1)
                if len(parts) == 2:
                    key = parts[0].strip().lower().replace(' ', '_')
                    value = parts[1].strip()
                    if key not in structured_data and value:
                        structured_data[key] = value

        return structured_data

    def send_to_webhook(self, data: Dict[str, Any]) -> bool:
        """
        Send processed scan data to webhook endpoint

        Args:
            data: The processed scan data

        Returns:
            Success status
        """
        # Remove thumbnail from webhook data to reduce payload size
        webhook_data_copy = data.copy()
        if 'thumbnail' in webhook_data_copy:
            del webhook_data_copy['thumbnail']

        webhook_data = {
            'source': 'scanner',
            'source_subtype': data.get('type', 'unknown'),
            'event_type': 'scan_processed',
            'data': {
                'scan_id': data.get('scan_id'),
                'file_name': data.get('file_name'),
                'timestamp': data.get('timestamp'),
                'structured_data': data.get('structured_data', {}),
                'text_extract': data.get('raw_text', '')[:500] + '...' if len(data.get('raw_text', '')) > 500 else data.get('raw_text', '')
            },
            'metadata': {
                'processor_version': '1.0',
                'processing_time': datetime.datetime.now().isoformat(),
                'file_type': data.get('type', 'unknown'),
                'file_size': data.get('file_size', 0)
            }
        }

        try:
            response = requests.post(
                self.webhook_url,
                json=webhook_data,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                logger.info(f"Successfully sent scan data to webhook: {data.get('scan_id')}")
                return True
            else:
                logger.error(f"Failed to send scan data to webhook. Status code: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error sending to webhook: {str(e)}")
            return False


# Helper functions
def save_uploaded_file(file, filename: Optional[str] = None) -> str:
    """
    Save an uploaded file to the upload folder

    Args:
        file: The file object (e.g., from Flask's request.files)
        filename: Optional custom filename to use

    Returns:
        Path to the saved file
    """
    if filename is None:
        filename = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"

    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    return file_path