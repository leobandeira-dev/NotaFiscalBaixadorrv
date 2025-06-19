#!/usr/bin/env python3
"""
Test script to manually update job status and verify the system is working
"""
import requests
import time
import json

def test_job_update():
    base_url = "http://localhost:5000"
    
    # Submit a test job
    print("Submitting test job...")
    response = requests.post(f"{base_url}/submit_keys", 
                           data={"invoice_keys": "35250162954987000130550020001854371034511150"})
    
    if response.status_code == 200:
        # Extract job ID from redirect
        job_id = response.url.split('/')[-1]
        print(f"Job ID: {job_id}")
        
        # Monitor job status
        for i in range(30):  # Check for up to 30 seconds
            try:
                status_response = requests.get(f"{base_url}/api/job_status/{job_id}")
                if status_response.status_code == 200:
                    data = status_response.json()
                    print(f"Attempt {i+1}: Status={data['status']}, Processed={data['processed']}, Success={data['successful']}")
                    
                    if data['status'] == 'completed':
                        print("Job completed successfully!")
                        print(f"Downloaded files: {data['downloaded_files']}")
                        break
                        
                time.sleep(2)
            except Exception as e:
                print(f"Error checking status: {e}")
                
    else:
        print(f"Failed to submit job: {response.status_code}")

if __name__ == "__main__":
    test_job_update()