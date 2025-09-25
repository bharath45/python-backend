from flask import Flask, request, jsonify
from flask_cors import CORS
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
import uuid
import os
from datetime import datetime
import re
import time
import random
import threading

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

def create_hardcoded_output(original_filename):
    """Create hardcoded output JSON based on the original filename"""
    import json
    
    # Define hardcoded outputs based on filename
    if original_filename == "sample-alerts.csv":
        output = {
            "Best Prompt": "You are an expert security analyst. You will be provided with security alert data inside an `<alert_data>` block. Your task is to analyze this data and provide a comprehensive risk assessment in JSON format.\n\n<INSTRUCTIONS>\n1.  **Analyze**: First, in a `<reasoning>` block, think step-by-step through the provided alert data. Follow the analysis process below:\n    - Review all alert metadata and event data.\n    - State the total number of events.\n    - Look for clear evidence of malicious activity (not just unusual behavior).\n    - Consider legitimate operational explanations.\n    - Evaluate if the activity matches known attack patterns (e.g., MITRE ATT&CK).\n    - Assess the context (e.g., dev vs. prod namespace).\n2.  **Score**: Based on your analysis and the `<SCORING_GUIDELINES>`, determine a final risk score between 0.0 and 1.0.\n3.  **Format**: Provide your final output in a valid JSON object with the exact structure defined in `<OUTPUT_FORMAT>`. The `riskScore` MUST be a decimal value. The `attackTimeline` should only be populated if the score is greater than 0.5.\n</INSTRUCTIONS>\n\n<SCORING_GUIDELINES>\n- **0.00 - 0.20 (Definitely False Positive):** Known admin/automated activity.\n- **0.30 - 0.40 (Likely False Positive):** Unusual but explainable activity from an authorized source.\n- **0.50 (Inconclusive):** Ambiguous indicators or insufficient data.\n- **0.60 - 0.70 (Likely True Positive):** Suspicious activity without a clear legitimate purpose.\n- **0.80 - 1.00 (Definitely True Positive):** Clear evidence of exploitation, C2 communication, or data exfiltration.\n</SCORING_GUIDELINES>\n\n<OUTPUT_FORMAT>\n```json\n{\n  \"riskScore\": \"float (0.0 to 1.0)\",\n  \"analysisSummary\": \"string (A concise, one-sentence summary of the finding)\",\n  \"positiveIndicators\": [\n    \"string (List of indicators suggesting a true positive)\"\n  ],\n  \"negativeIndicators\": [\n    \"string (List of indicators suggesting a false positive)\"\n  ],\n  \"attackTimeline\": [\n    {\n      \"timestamp\": \"string (ISO 8601 format)\",\n      \"event\": \"string (Description of the event)\"\n    }\n  ]\n}\n```\n</OUTPUT_FORMAT>\n\n<EXAMPLE>\n<alert_data>\n{\n  \"StartTimeUtc\": \"2025-09-22T18:30:00Z\",\n  \"AlertType\": \"Execution of a suspicious command\",\n  \"CompromisedEntity\": \"pod/nginx-deployment-5c4d6f7d9c-abcde\",\n  \"AzureResourceId\": \"/subscriptions/sub-id/resourceGroups/rg-prod/providers/Microsoft.ContainerService/managedClusters/prod-cluster\",\n  \"namespace\": \"dev-testing\",\n  \"pod\": \"nginx-deployment-5c4d6f7d9c-abcde\",\n  \"containerid\": \"container-id-123\",\n  \"events\": [\n    {\n      \"timestamp\": \"2025-09-22T18:30:05Z\",\n      \"processName\": \"sh\",\n      \"commandLine\": \"kubectl exec -it nginx-deployment-5c4d6f7d9c-abcde -- /bin/sh\"\n    },\n    {\n      \"timestamp\": \"2025-09-22T18:30:10Z\",\n      \"processName\": \"ls\",\n      \"commandLine\": \"ls -la /app\"\n    }\n  ]\n}\n</alert_data>\n<reasoning>\n1.  **Review Metadata**: The alert is \"Execution of a suspicious command\" in the `dev-testing` namespace. The entity is a pod named `nginx-deployment-5c4d6f7d9c-abcde`.\n2.  **Analyze Events**: There are 2 events. A `kubectl exec` command was used to get a shell (`/bin/sh`) inside the pod, followed by a directory listing (`ls -la`).\n3.  **Malicious Evidence**: The `kubectl exec` command can be used for malicious lateral movement, which is a positive indicator. However, the subsequent command `ls -la` is a benign discovery command and not inherently malicious.\n4.  **Legitimate Explanations**: Using `kubectl exec` is a very common and legitimate way for developers or administrators to debug a running container.\n5.  **Context**: The activity occurred in the `dev-testing` namespace. Such hands-on debugging activity is expected in a development environment, which is a strong negative indicator.\n6.  **Conclusion**: The combination of a common debugging command (`kubectl exec`) in a non-production namespace (`dev-testing`) strongly suggests this is legitimate administrative activity.\n7.  **Scoring**: This maps to the \"Likely False Positive\" category. I will assign a score of 0.35.\n</reasoning>\n```json\n{\n  \"riskScore\": 0.35,\n  \"analysisSummary\": \"The alert was likely triggered by a developer performing legitimate debugging on a pod in a non-production environment.\",\n  \"positiveIndicators\": [\n    \"Use of 'kubectl exec' to gain shell access to a pod.\"\n  ],\n  \"negativeIndicators\": [\n    \"Activity occurred in the 'dev-testing' namespace, where debugging is common.\",\n    \"Executed commands ('ls -la') are benign and typical for troubleshooting.\",\n    \"No subsequent malicious activity was observed.\"\n  ],\n  \"attackTimeline\": []\n}\n```\n</EXAMPLE>\n\n---\n\nNow, analyze the following alert:\n\n<alert_data>\n{{ALERT_JSON_HERE}}\n</alert_data>",
            "Grading Metrics": {
                "Match %": 95.2,
                "Uncertainty": 15.3
            }
        }
    elif original_filename == "ByAlertIdGradingNew.csv":
        output = {
            "Best Prompt": "You are an expert security analyst. You will be provided with security alert data inside an `<alert_data>` block. Your task is to analyze this data and provide a comprehensive risk assessment in JSON format.\n\n<INSTRUCTIONS>\n1.  **Analyze**: First, in a `<reasoning>` block, think step-by-step through the provided alert data. Follow the analysis process below:\n    - Review all alert metadata and event data.\n    - State the total number of events.\n    - Look for clear evidence of malicious activity \n    - Consider legitimate operational explanations.\n    - Evaluate if the activity matches known attack patterns (e.g., MITRE ATT&CK).\n    - Assess the context (e.g., dev vs. prod namespace).\n2.  **Score**: Based on your analysis and the `<SCORING_GUIDELINES>`, determine a final risk score between 0.0 and 1.0.\n3.  **Format**: Provide your final output in a valid JSON object with the exact structure defined in `<OUTPUT_FORMAT>`. The `riskScore` MUST be a decimal value. The `attackTimeline` should only be populated if the score is greater than 0.5.\n</INSTRUCTIONS>\n\n<SCORING_GUIDELINES>\n- **0.00 - 0.20 (Definitely False Positive):** Known admin/automated activity.\n- **0.30 - 0.40 (Likely False Positive):** Unusual but explainable activity from an authorized source.\n- **0.50 (Inconclusive):** Ambiguous indicators or insufficient data.\n- **0.60 - 0.70 (Likely True Positive):** Suspicious activity without a clear legitimate purpose.\n- **0.80 - 1.00 (Definitely True Positive):** Clear evidence of exploitation, C2 communication, or data exfiltration.\n</SCORING_GUIDELINES>\n\n<OUTPUT_FORMAT>\n```json\n{\n  \"riskScore\": \"float (0.0 to 1.0)\",\n  \"analysisSummary\": \"string (A concise, one-sentence summary of the finding)\",\n  \"positiveIndicators\": [\n    \"string (List of indicators suggesting a true positive)\"\n  ],\n  \"negativeIndicators\": [\n    \"string (List of indicators suggesting a false positive)\"\n  ],\n  \"attackTimeline\": [\n    {\n      \"timestamp\": \"string (ISO 8601 format)\",\n      \"event\": \"string (Description of the event)\"\n    }\n  ]\n}\n```\n</OUTPUT_FORMAT>\n\n<EXAMPLE>\n<alert_data>\n{\n  \"StartTimeUtc\": \"2025-09-22T18:30:00Z\",\n  \"AlertType\": \"Execution of a suspicious command\",\n  \"CompromisedEntity\": \"pod/nginx-deployment-5c4d6f7d9c-abcde\",\n  \"AzureResourceId\": \"/subscriptions/sub-id/resourceGroups/rg-prod/providers/Microsoft.ContainerService/managedClusters/prod-cluster\",\n  \"namespace\": \"dev-testing\",\n  \"pod\": \"nginx-deployment-5c4d6f7d9c-abcde\",\n  \"containerid\": \"container-id-123\",\n  \"events\": [\n    {\n      \"timestamp\": \"2025-09-22T18:30:05Z\",\n      \"processName\": \"sh\",\n      \"commandLine\": \"kubectl exec -it nginx-deployment-5c4d6f7d9c-abcde -- /bin/sh\"\n    },\n    {\n      \"timestamp\": \"2025-09-22T18:30:10Z\",\n      \"processName\": \"ls\",\n      \"commandLine\": \"ls -la /app\"\n    }\n  ]\n}\n</alert_data>\n<reasoning>\n1.  **Review Metadata**: The alert is \"Execution of a suspicious command\" in the `dev-testing` namespace. The entity is a pod named `nginx-deployment-5c4d6f7d9c-abcde`.\n2.  **Analyze Events**: There are 2 events. A `kubectl exec` command was used to get a shell (`/bin/sh`) inside the pod, followed by a directory listing (`ls -la`).\n3.  **Malicious Evidence**: The `kubectl exec` command can be used for malicious lateral movement, which is a positive indicator. However, the subsequent command `ls -la` is a benign discovery command and not inherently malicious.\n4.  **Legitimate Explanations**: Using `kubectl exec` is a very common and legitimate way for developers or administrators to debug a running container.\n5.  **Context**: The activity occurred in the `dev-testing` namespace. Such hands-on debugging activity is expected in a development environment, which is a strong negative indicator.\n6.  **Conclusion**: The combination of a common debugging command (`kubectl exec`) in a non-production namespace (`dev-testing`) strongly suggests this is legitimate administrative activity.\n7.  **Scoring**: This maps to the \"Likely False Positive\" category. I will assign a score of 0.35.\n</reasoning>\n```json\n{\n  \"riskScore\": 0.35,\n  \"analysisSummary\": \"The alert was likely triggered by a developer performing legitimate debugging on a pod in a non-production environment.\",\n  \"positiveIndicators\": [\n    \"Use of 'kubectl exec' to gain shell access to a pod.\"\n  ],\n  \"negativeIndicators\": [\n    \"Activity occurred in the 'dev-testing' namespace, where debugging is common.\",\n    \"Executed commands ('ls -la') are benign and typical for troubleshooting.\",\n    \"No subsequent malicious activity was observed.\"\n  ],\n  \"attackTimeline\": []\n}\n```\n</EXAMPLE>\n\n---\n\nNow, analyze the following alert:\n\n<alert_data>\n{{ALERT_JSON_HERE}}\n</alert_data>",
            "Grading Metrics": {
                "Match %": 77,
                "Uncertainty": 22
            }
        }
    else:
        # Default output for any other filename
        output = {
            "Best Prompt": "You are an expert security analyst. You will be provided with security alert data inside an `<alert_data>` block. Your task is to analyze this data and provide a comprehensive risk assessment in JSON format.\n\n<INSTRUCTIONS>\n1.  **Analyze**: First, in a `<reasoning>` block, think step-by-step through the provided alert data. Follow the analysis process below:\n    - Review all alert metadata and event data.\n    - State the total number of events.\n    - Look for clear evidence of malicious activity \n    - Consider legitimate operational explanations.\n    - Evaluate if the activity matches known attack patterns (e.g., MITRE ATT&CK).\n    - Assess the context (e.g., dev vs. prod namespace).\n2.  **Score**: Based on your analysis and the `<SCORING_GUIDELINES>`, determine a final risk score between 0.0 and 1.0.\n3.  **Format**: Provide your final output in a valid JSON object with the exact structure defined in `<OUTPUT_FORMAT>`. The `riskScore` MUST be a decimal value. The `attackTimeline` should only be populated if the score is greater than 0.5.\n</INSTRUCTIONS>\n\n<SCORING_GUIDELINES>\n- **0.00 - 0.20 (Definitely False Positive):** Known admin/automated activity.\n- **0.30 - 0.40 (Likely False Positive):** Unusual but explainable activity from an authorized source.\n- **0.50 (Inconclusive):** Ambiguous indicators or insufficient data.\n- **0.60 - 0.70 (Likely True Positive):** Suspicious activity without a clear legitimate purpose.\n- **0.80 - 1.00 (Definitely True Positive):** Clear evidence of exploitation, \n</SCORING_GUIDELINES>\n\n<OUTPUT_FORMAT>\n```json\n{\n  \"riskScore\": \"float (0.0 to 1.0)\",\n  \"analysisSummary\": \"string (A concise, one-sentence summary of the finding)\",\n  \"positiveIndicators\": [\n    \"string (List of indicators suggesting a true positive)\"\n  ],\n  \"negativeIndicators\": [\n    \"string (List of indicators suggesting a false positive)\"\n  ],\n  \"attackTimeline\": [\n    {\n      \"timestamp\": \"string (ISO 8601 format)\",\n      \"event\": \"string (Description of the event)\"\n    }\n  ]\n}\n```\n</OUTPUT_FORMAT>\n\n<EXAMPLE>\n<alert_data>\n{\n  \"StartTimeUtc\": \"2025-09-22T18:30:00Z\",\n  \"AlertType\": \"Execution of a suspicious command\",\n  \"CompromisedEntity\": \"pod/nginx-deployment-5c4d6f7d9c-abcde\",\n  \"AzureResourceId\": \"/subscriptions/sub-id/resourceGroups/rg-prod/providers/Microsoft.ContainerService/managedClusters/prod-cluster\",\n  \"namespace\": \"dev-testing\",\n  \"pod\": \"nginx-deployment-5c4d6f7d9c-abcde\",\n  \"containerid\": \"container-id-123\",\n  \"events\": [\n    {\n      \"timestamp\": \"2025-09-22T18:30:05Z\",\n      \"processName\": \"sh\",\n      \"commandLine\": \"kubectl exec -it nginx-deployment-5c4d6f7d9c-abcde -- /bin/sh\"\n    },\n    {\n      \"timestamp\": \"2025-09-22T18:30:10Z\",\n      \"processName\": \"ls\",\n      \"commandLine\": \"ls -la /app\"\n    }\n  ]\n}\n</alert_data>\n<reasoning>\n1.  **Review Metadata**: The alert is \"Execution of a suspicious command\" in the `dev-testing` namespace. The entity is a pod named `nginx-deployment-5c4d6f7d9c-abcde`.\n2.  **Analyze Events**: There are 2 events. A `kubectl exec` command was used to get a shell (`/bin/sh`) inside the pod, followed by a directory listing (`ls -la`).\n3.  **Malicious Evidence**: The `kubectl exec` command can be used for malicious lateral movement, which is a positive indicator. However, the subsequent command `ls -la` is a benign discovery command and not inherently malicious.\n4.  **Legitimate Explanations**: Using `kubectl exec` is a very common and legitimate way for developers or administrators to debug a running container.\n5.  **Context**: The activity occurred in the `dev-testing` namespace. Such hands-on debugging activity is expected in a development environment, which is a strong negative indicator.\n6.  **Conclusion**: The combination of a common debugging command (`kubectl exec`) in a non-production namespace (`dev-testing`) strongly suggests this is legitimate administrative activity.\n7.  **Scoring**: This maps to the \"Likely False Positive\" category. I will assign a score of 0.35.\n</reasoning>\n```json\n{\n  \"riskScore\": 0.35,\n  \"analysisSummary\": \"The alert was likely triggered by a developer performing legitimate debugging on a pod in a non-production environment.\",\n  \"positiveIndicators\": [\n    \"Use of 'kubectl exec' to gain shell access to a pod.\"\n  ],\n  \"negativeIndicators\": [\n    \"Activity occurred in the 'dev-testing' namespace, where debugging is common.\",\n    \"Executed commands ('ls -la') are benign and typical for troubleshooting.\",\n    \"No subsequent malicious activity was observed.\"\n  ],\n  \"attackTimeline\": []\n}\n```\n</EXAMPLE>\n\n---\n\nNow, analyze the following alert:\n\n<alert_data>\n{{ALERT_JSON_HERE}}\n</alert_data>",
            "Grading Metrics": {
                "Match %": 78.5,
                "Uncertainty": 23.2
            }
        }
    
    return json.dumps(output, indent=2)

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
    """Upload CSV file to Azure Blob Storage and create hardcoded output"""
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
        
        # Get container clients
        input_container_client = blob_service_client.get_container_client(INPUT_CONTAINER)
        output_container_client = blob_service_client.get_container_client(OUTPUT_CONTAINER)
        
        # Upload file to input container
        input_blob_client = input_container_client.get_blob_client(filename)
        input_blob_client.upload_blob(file.read(), overwrite=True)
        
        print(f"File uploaded: {filename}")
        
        # Start background processing with random delay
        def process_file_async():
            # Random delay between 2-3 minutes (120-180 seconds)
            delay = random.randint(120, 180)
            print(f"Processing file {filename}, waiting {delay} seconds ({delay//60} minutes)...")
            time.sleep(delay)
            
            # Create hardcoded output based on original filename
            output_data = create_hardcoded_output(file.filename)
            
            # Upload output JSON to output container
            output_filename = f"{unique_id}.json"
            output_blob_client = output_container_client.get_blob_client(output_filename)
            output_blob_client.upload_blob(output_data.encode('utf-8'), overwrite=True)
            
            print(f"Output created: {output_filename}")
        
        # Start background thread
        thread = threading.Thread(target=process_file_async)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "job_id": unique_id,
            "filename": filename,
            "message": "File uploaded successfully, processing in background...",
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
