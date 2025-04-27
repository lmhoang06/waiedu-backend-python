"""
R2 Storage Service Module

This module provides a wrapper around the Cloudflare R2 client to simplify storage operations.
It handles file uploads, URL generation, and other R2-related operations.
"""
from flask import current_app
import os
import logging
from io import BytesIO
import uuid
import time
from werkzeug.utils import secure_filename
from botocore.exceptions import ClientError
from typing import Optional, Tuple, BinaryIO, Dict, Any

def get_r2_client():
    """
    Get the R2 client from the current Flask application.
    
    Returns:
        boto3.client: The configured R2 client
    """
    return current_app.r2_storage

def get_bucket_name() -> str:
    """
    Get the configured R2 bucket name from environment variables.
    
    Returns:
        str: The name of the R2 bucket
    """
    return os.environ.get('R2_BUCKET_NAME', 'course-image')

def get_r2_endpoint() -> str:
    """
    Get the configured R2 endpoint URL from environment variables.
    
    Returns:
        str: The R2 endpoint URL
    """
    endpoint = os.environ.get('R2_ENDPOINT_URL', '')
    # Remove trailing slash if present
    if endpoint.endswith('/'):
        endpoint = endpoint[:-1]
    return endpoint

def upload_file(
    file_obj: BinaryIO, 
    filename: str, 
    content_type: str = 'application/octet-stream',
    extra_args: Dict[str, Any] = None
) -> Tuple[bool, str, Optional[str]]:
    """
    Upload a file to R2 storage.
    
    Args:
        file_obj: File-like object containing the file data
        filename: Name to use for the stored file
        content_type: MIME type of the file
        extra_args: Additional arguments to pass to the upload_fileobj method
        
    Returns:
        Tuple containing:
        - Boolean indicating success or failure
        - URL of the uploaded file if successful, error message if failed
        - Error details if failed, None if successful
    """
    try:
        # Get R2 client and bucket name
        r2_client = get_r2_client()
        bucket_name = get_bucket_name()
        
        # Set default extra args if not provided
        if extra_args is None:
            extra_args = {}
        
        # Ensure content type is set
        if 'ContentType' not in extra_args:
            extra_args['ContentType'] = content_type
        
        # Upload the file
        r2_client.upload_fileobj(
            file_obj,
            bucket_name,
            filename,
            ExtraArgs=extra_args
        )
        
        # Generate URL for the uploaded file
        file_url = f"{get_r2_endpoint()}/{bucket_name}/{filename}"
        
        return True, file_url, None
        
    except ClientError as e:
        error_msg = f"R2 client error: {str(e)}"
        logging.error(error_msg)
        return False, error_msg, str(e)
    except Exception as e:
        error_msg = f"Error uploading file to R2: {str(e)}"
        logging.error(error_msg)
        return False, error_msg, str(e)

def upload_image(
    image_data: BinaryIO, 
    filename_base: str, 
    content_type: str = 'image/webp'
) -> Tuple[bool, str, Optional[str]]:
    """
    Upload an image to R2 storage with a unique filename.
    
    Args:
        image_data: File-like object containing the image data
        filename_base: Base name to use for the image (will be sanitized and made unique)
        content_type: MIME type of the image
        
    Returns:
        Tuple containing:
        - Boolean indicating success or failure
        - URL of the uploaded image if successful, error message if failed
        - Error details if failed, None if successful
    """
    # Generate a unique filename
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4())[:8]
    safe_filename = secure_filename(filename_base)
    
    # Create filename with extension based on content type
    extension = content_type.split('/')[-1] if '/' in content_type else 'webp'
    unique_filename = f"{safe_filename}-{timestamp}-{unique_id}.{extension}"
    
    # Upload the file
    return upload_file(
        image_data, 
        unique_filename, 
        content_type=content_type
    )

def delete_file(filename: str) -> Tuple[bool, Optional[str]]:
    """
    Delete a file from R2 storage.
    
    Args:
        filename: Name of the file to delete
        
    Returns:
        Tuple containing:
        - Boolean indicating success or failure
        - Error message if failed, None if successful
    """
    try:
        # Get R2 client and bucket name
        r2_client = get_r2_client()
        bucket_name = get_bucket_name()
        
        # Delete the file
        r2_client.delete_object(
            Bucket=bucket_name,
            Key=filename
        )
        
        return True, None
        
    except ClientError as e:
        error_msg = f"R2 client error: {str(e)}"
        logging.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Error deleting file from R2: {str(e)}"
        logging.error(error_msg)
        return False, error_msg

def generate_presigned_url(filename: str, expiration: int = 3600) -> Tuple[bool, str, Optional[str]]:
    """
    Generate a presigned URL for a file in R2 storage.
    
    Args:
        filename: Name of the file
        expiration: URL expiration time in seconds
        
    Returns:
        Tuple containing:
        - Boolean indicating success or failure
        - Presigned URL if successful, error message if failed
        - Error details if failed, None if successful
    """
    try:
        # Get R2 client and bucket name
        r2_client = get_r2_client()
        bucket_name = get_bucket_name()
        
        # Generate presigned URL
        url = r2_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket_name,
                'Key': filename
            },
            ExpiresIn=expiration
        )
        
        return True, url, None
        
    except ClientError as e:
        error_msg = f"R2 client error: {str(e)}"
        logging.error(error_msg)
        return False, error_msg, str(e)
    except Exception as e:
        error_msg = f"Error generating presigned URL: {str(e)}"
        logging.error(error_msg)
        return False, error_msg, str(e)

def file_exists(filename: str) -> bool:
    """
    Check if a file exists in R2 storage.
    
    Args:
        filename: Name of the file to check
        
    Returns:
        Boolean indicating if the file exists
    """
    try:
        # Get R2 client and bucket name
        r2_client = get_r2_client()
        bucket_name = get_bucket_name()
        
        # Check if the file exists
        r2_client.head_object(Bucket=bucket_name, Key=filename)
        return True
        
    except ClientError as e:
        # If error code is 404, file doesn't exist
        if e.response['Error']['Code'] == '404':
            return False
        # For other errors, log and return False
        logging.error(f"R2 client error: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"Error checking if file exists: {str(e)}")
        return False