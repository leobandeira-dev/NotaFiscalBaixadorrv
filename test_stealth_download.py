#!/usr/bin/env python3
"""
Test script to simulate the stealth download with the provided invoice key
"""

import requests
import time
import json

# Configuration
BASE_URL = "http://localhost:5000"
LOGIN_EMAIL = "admin@xmldownloader.com"
LOGIN_PASSWORD = "admin123"
TEST_KEY = "42250485179240000239550020004175361171503396"

def test_stealth_download():
    """Test the stealth download functionality"""
    
    # Create session
    session = requests.Session()
    
    print("=" * 60)
    print("🧪 TESTING STEALTH DOWNLOAD SYSTEM")
    print("=" * 60)
    
    # Step 1: Login
    print("\n1️⃣ Logging in as admin...")
    login_data = {
        'email': LOGIN_EMAIL,
        'password': LOGIN_PASSWORD
    }
    response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=True)
    
    if response.status_code == 200:
        print("✅ Login successful")
    else:
        print(f"❌ Login failed: {response.status_code}")
        return
    
    # Step 2: Submit download request
    print(f"\n2️⃣ Submitting download request for key: {TEST_KEY}")
    download_data = {
        'invoice_keys': TEST_KEY
    }
    response = session.post(f"{BASE_URL}/NotaFiscalBaixador", data=download_data, allow_redirects=False)
    
    if response.status_code == 302:
        redirect_url = response.headers.get('Location', '')
        print(f"✅ Download request accepted")
        print(f"   Redirect to: {redirect_url}")
        
        # Extract job ID from redirect
        if '/download-status/' in redirect_url:
            job_id = redirect_url.split('/download-status/')[-1]
            print(f"   Job ID: {job_id}")
            
            # Step 3: Monitor job status
            print("\n3️⃣ Monitoring job status...")
            print("   (This may take 30-60 seconds with stealth mode)")
            print("   ⏳ Waiting for automation to complete...\n")
            
            for i in range(60):  # Monitor for up to 60 seconds
                time.sleep(2)
                
                # Check job status
                status_response = session.get(f"{BASE_URL}/download-status/{job_id}")
                
                if status_response.status_code == 200:
                    # Try to extract status from HTML or make API call
                    api_response = session.get(f"{BASE_URL}/api/v1/jobs/{job_id}")
                    
                    if api_response.status_code == 200:
                        try:
                            job_data = api_response.json()
                            status = job_data.get('status', 'unknown')
                            processed = job_data.get('processed', 0)
                            total = job_data.get('total_keys', 1)
                            successful = job_data.get('successful', 0)
                            failed = job_data.get('failed', 0)
                            
                            print(f"   [{i*2}s] Status: {status} | Processed: {processed}/{total} | Success: {successful} | Failed: {failed}")
                            
                            if status in ['completed', 'failed']:
                                print(f"\n✅ Job finished with status: {status}")
                                
                                if successful > 0:
                                    print(f"   ✅ Successfully downloaded {successful} file(s)")
                                    
                                    # Show files
                                    files = job_data.get('downloaded_files', [])
                                    if files:
                                        print("\n   📁 Downloaded files:")
                                        for file_path in files:
                                            print(f"      - {file_path}")
                                
                                if failed > 0:
                                    print(f"   ❌ Failed: {failed} file(s)")
                                    
                                    errors = job_data.get('errors', [])
                                    if errors:
                                        print("\n   ⚠️ Errors:")
                                        for error in errors:
                                            print(f"      - Key: {error.get('invoice_key')}")
                                            print(f"        Error: {error.get('error')}")
                                
                                break
                        except json.JSONDecodeError:
                            print(f"   [{i*2}s] Waiting for job to start...")
                
                if i == 59:
                    print("\n⏱️ Timeout reached - job still running")
                    print("   Check the application logs for detailed progress")
        
    else:
        print(f"❌ Download request failed: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
    
    print("\n" + "=" * 60)
    print("🏁 TEST COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    test_stealth_download()
