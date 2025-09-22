#!/usr/bin/env python3
"""
Test script for Alert Grader Python Backend API
"""

import requests
import json
import time

def test_health():
    """Test health endpoint"""
    print("1. Testing health endpoint...")
    try:
        response = requests.get('http://localhost:5001/api/health')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check: {data['status']}")
            print(f"   Service: {data['service']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_upload():
    """Test file upload"""
    print("\n2. Testing file upload...")
    try:
        # Create a sample CSV content
        csv_content = """Alert ID,Description,Severity,Category
ALERT-001,High CPU usage detected,High,Performance
ALERT-002,Memory leak detected,Critical,Performance
ALERT-003,Database connection timeout,Medium,Database"""
        
        files = {'file': ('test-alerts.csv', csv_content, 'text/csv')}
        response = requests.post('http://localhost:5001/api/upload', files=files)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ File uploaded successfully")
            print(f"   Job ID: {data['job_id']}")
            print(f"   Filename: {data['filename']}")
            return data['job_id']
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return None

def test_result(job_id):
    """Test result endpoint"""
    print(f"\n3. Testing result endpoint for job: {job_id}")
    try:
        response = requests.get(f'http://localhost:5001/api/result/{job_id}')
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'pending':
                print("✅ Result endpoint working (status: pending)")
            else:
                print("✅ Result endpoint working (status: completed)")
                print(f"   Best Prompt: {data.get('Best Prompt', 'N/A')[:50]}...")
                print(f"   Metrics: {data.get('Grading Metrics', {})}")
            return True
        else:
            print(f"❌ Result check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Result error: {e}")
        return False

def test_jobs():
    """Test jobs listing"""
    print("\n4. Testing jobs listing...")
    try:
        response = requests.get('http://localhost:5001/api/jobs')
        if response.status_code == 200:
            data = response.json()
            jobs = data.get('jobs', [])
            print(f"✅ Jobs listing: {len(jobs)} jobs found")
            for job in jobs[:3]:  # Show first 3 jobs
                print(f"   - {job['job_id']}: {job['filename']}")
            return True
        else:
            print(f"❌ Jobs listing failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Jobs listing error: {e}")
        return False

def test_results():
    """Test results listing"""
    print("\n5. Testing results listing...")
    try:
        response = requests.get('http://localhost:5001/api/results')
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"✅ Results listing: {len(results)} results found")
            for result in results[:3]:  # Show first 3 results
                print(f"   - {result['job_id']}: {result['filename']}")
            return True
        else:
            print(f"❌ Results listing failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Results listing error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Alert Grader Python Backend API...\n")
    
    # Test health
    if not test_health():
        print("\n❌ Health check failed. Make sure the server is running.")
        return
    
    # Test upload
    job_id = test_upload()
    if not job_id:
        print("\n❌ Upload test failed.")
        return
    
    # Test result
    test_result(job_id)
    
    # Test listings
    test_jobs()
    test_results()
    
    print("\n🎉 All tests completed!")
    print("\n📝 Next steps:")
    print("   1. Your CSV file is now in Azure Blob Storage")
    print("   2. Process the file with your external system")
    print("   3. Save the JSON result to output-data container")
    print("   4. Frontend will automatically display the results")

if __name__ == "__main__":
    main()
