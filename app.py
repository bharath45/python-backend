from flask import Flask, request, jsonify
from flask_cors import CORS
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
import uuid
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Azure Blob Storage configuration
BLOB_ACCOUNT_URL = "https://agstorage11.blob.core.windows.net"
INPUT_CONTAINER = "input-data"
OUTPUT_CONTAINER = "output-data"

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

@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """List all jobs in the input container"""
    try:
        container_client = blob_service_client.get_container_client(INPUT_CONTAINER)
        blobs = container_client.list_blobs()
        
        jobs = []
        for blob in blobs:
            if blob.name.endswith('.csv'):
                job_id = blob.name.replace('.csv', '')
                jobs.append({
                    "job_id": job_id,
                    "filename": blob.name,
                    "upload_time": blob.last_modified.isoformat(),
                    "size": blob.size
                })
        
        return jsonify({"jobs": jobs})
        
    except Exception as e:
        print(f"List jobs error: {str(e)}")
        return jsonify({"error": f"Failed to list jobs: {str(e)}"}), 500

@app.route('/api/results', methods=['GET'])
def list_results():
    """List all results in the output container"""
    try:
        container_client = blob_service_client.get_container_client(OUTPUT_CONTAINER)
        blobs = container_client.list_blobs()
        
        results = []
        for blob in blobs:
            if blob.name.endswith('.json'):
                job_id = blob.name.replace('.json', '')
                results.append({
                    "job_id": job_id,
                    "filename": blob.name,
                    "created_time": blob.last_modified.isoformat(),
                    "size": blob.size
                })
        
        return jsonify({"results": results})
        
    except Exception as e:
        print(f"List results error: {str(e)}")
        return jsonify({"error": f"Failed to list results: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)
