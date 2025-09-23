from flask import Flask, request, jsonify
from flask_cors import CORS
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
import uuid
import os
from datetime import datetime
import re

app = Flask(__name__)

# Security: Restrict CORS to specific origins
CORS(app, origins=[
    "https://agstorage11.z19.web.core.windows.net",
    "http://localhost:5173",  # For local development
    "http://localhost:3000"   # Alternative local dev port
])

# Security: Add security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Azure Blob Storage configuration - Use environment variables
BLOB_ACCOUNT_URL = os.environ.get('BLOB_ACCOUNT_URL', 'https://agstorage11.blob.core.windows.net')
INPUT_CONTAINER = os.environ.get('INPUT_CONTAINER', 'input-data')
OUTPUT_CONTAINER = os.environ.get('OUTPUT_CONTAINER', 'output-data')

# Initialize blob service client
blob_service_client = BlobServiceClient(
    account_url=BLOB_ACCOUNT_URL,
    credential=DefaultAzureCredential()
)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "OK",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Alert Grader Backend API"
    })

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload CSV file to Azure Blob Storage"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Security: Validate file type and size
        allowed_extensions = {'.csv', '.xlsx', '.xls'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            return jsonify({"error": "Invalid file type. Only CSV and Excel files are allowed."}), 400
        
        # Security: Check file size (max 10MB)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        if file_size > 10 * 1024 * 1024:  # 10MB limit
            return jsonify({"error": "File too large. Maximum size is 10MB."}), 400
        
        # Security: Validate filename
        if not re.match(r'^[a-zA-Z0-9._-]+$', file.filename):
            return jsonify({"error": "Invalid filename. Only alphanumeric characters, dots, underscores, and hyphens are allowed."}), 400
        
        # Generate unique ID
        unique_id = str(uuid.uuid4())
        filename = f"{unique_id}.csv"
        
        # Get container client
        container_client = blob_service_client.get_container_client(INPUT_CONTAINER)
        
        # Upload file to blob storage
        blob_client = container_client.get_blob_client(filename)
        blob_client.upload_blob(file.read(), overwrite=True)
        
        print(f"File uploaded: {filename}")
        
        return jsonify({
            "job_id": unique_id,
            "filename": filename,
            "message": "File uploaded successfully",
            "upload_time": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        print(f"Upload error: {str(e)}")
        return jsonify({"error": f"Failed to upload file: {str(e)}"}), 500

@app.route('/api/result/<job_id>', methods=['GET'])
def get_result(job_id):
    """Get processing result from Azure Blob Storage"""
    try:
        filename = f"{job_id}.json"
        
        # Get container client for output data
        container_client = blob_service_client.get_container_client(OUTPUT_CONTAINER)
        blob_client = container_client.get_blob_client(filename)
        
        # Check if blob exists
        if not blob_client.exists():
            return jsonify({"status": "pending"})
        
        # Download and return the JSON result
        blob_data = blob_client.download_blob().readall()
        result = blob_data.decode('utf-8')
        
        # Parse JSON and return
        import json
        json_result = json.loads(result)
        return jsonify(json_result)
        
    except Exception as e:
        print(f"Result error: {str(e)}")
        return jsonify({"error": f"Failed to get result: {str(e)}"}), 500

# REMOVED: Admin endpoints for security
# These endpoints exposed sensitive data and were removed for production security

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    # Security: Disable debug mode in production
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
