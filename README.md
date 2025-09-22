# Alert Grader Python Backend

A Flask-based backend API for the Alert Grader application that handles file uploads to Azure Blob Storage and retrieves processing results.

## 🚀 Features

- **File Upload**: Uploads CSV files to Azure Blob Storage with unique IDs
- **Result Polling**: Retrieves JSON results from blob storage
- **Azure Integration**: Uses Azure Blob Storage for input/output data
- **CORS Enabled**: Supports frontend integration
- **Job Management**: List jobs and results
- **Health Monitoring**: Health check endpoint

## 🛠 Setup

### Prerequisites
- Python 3.8 or higher
- Azure account with blob storage access
- Azure CLI configured with proper credentials

### Installation

1. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Azure credentials**:
   ```bash
   az login
   ```

4. **Start the server**:
   ```bash
   python app.py
   ```

## 📡 API Endpoints

### GET /api/health
Health check endpoint.

**Response**:
```json
{
  "status": "OK",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "service": "Alert Grader Backend API"
}
```

### POST /api/upload
Uploads a CSV file to blob storage.

**Request**: Multipart form data with `file` field
**Response**: 
```json
{
  "job_id": "unique-uuid",
  "filename": "unique-uuid.csv",
  "message": "File uploaded successfully",
  "upload_time": "2024-01-15T10:30:00.000Z"
}
```

### GET /api/result/:jobId
Retrieves processing results for a job.

**Response** (pending):
```json
{
  "status": "pending"
}
```

**Response** (completed):
```json
{
  "Best Prompt": "Your generated prompt here",
  "Grading Metrics": {
    "Match %": 87.5,
    "Accuracy": 92.3,
    "Completeness": 89.1,
    "Relevance": 85.7
  }
}
```

### GET /api/jobs
Lists all uploaded jobs.

**Response**:
```json
{
  "jobs": [
    {
      "job_id": "uuid",
      "filename": "uuid.csv",
      "upload_time": "2024-01-15T10:30:00.000Z",
      "size": 1024
    }
  ]
}
```

### GET /api/results
Lists all processing results.

**Response**:
```json
{
  "results": [
    {
      "job_id": "uuid",
      "filename": "uuid.json",
      "created_time": "2024-01-15T10:30:00.000Z",
      "size": 512
    }
  ]
}
```

## 🔧 Configuration

The API uses these Azure Blob Storage containers:
- **Input**: `input-data` - Stores uploaded CSV files
- **Output**: `output-data` - Stores processed JSON results

## 🌐 Blob Storage URLs

- **Input Container**: `https://agstorage11.blob.core.windows.net/input-data`
- **Output Container**: `https://agstorage11.blob.core.windows.net/output-data`

## 🔄 Workflow

1. **Upload**: Frontend uploads CSV → Backend stores as `{uniqueId}.csv` in input-data
2. **Processing**: External system processes the file
3. **Results**: External system stores JSON as `{uniqueId}.json` in output-data
4. **Polling**: Frontend polls for results until available

## 🚀 Deployment

### Local Development
```bash
python app.py
```

### Production (using Gunicorn)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Azure App Service
The backend can be deployed to Azure App Service with Python runtime.

## 📝 Environment Variables

- `PORT`: Server port (default: 5000)
- Azure credentials are handled via DefaultAzureCredential

## 🧪 Testing

### Test with curl
```bash
# Health check
curl http://localhost:5000/api/health

# Upload file
curl -X POST -F "file=@sample-alerts.csv" http://localhost:5000/api/upload

# Check result
curl http://localhost:5000/api/result/{job_id}
```

### Test with Python
```python
import requests

# Health check
response = requests.get('http://localhost:5000/api/health')
print(response.json())

# Upload file
with open('sample-alerts.csv', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:5000/api/upload', files=files)
    print(response.json())
```

## 🔍 Troubleshooting

### Common Issues
1. **Azure Authentication**: Ensure `az login` is completed
2. **Container Access**: Verify blob storage containers exist
3. **CORS Issues**: Check Flask-CORS configuration
4. **File Upload**: Verify file size limits

### Logs
The application logs important events to console:
- File uploads
- Errors
- API requests
