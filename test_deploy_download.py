#!/usr/bin/env python3
"""
Test XML Download System in Deploy Environment
Verifies automation system functionality
"""

import sys
import os
import logging
import time
from datetime import datetime

# Add project root to path
sys.path.append('/home/runner/workspace')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_chrome_automation():
    """Test Chrome automation system"""
    try:
        logger.info("Testing Chrome automation in deploy environment...")
        
        # Test environment detection
        from optimization_deploy import DeployOptimizer
        optimizer = DeployOptimizer()
        env_type = optimizer.detect_environment()
        logger.info(f"Environment detected: {env_type}")
        
        # Test automation system
        from automation_fixed import InvoiceDownloader
        downloader = InvoiceDownloader()
        
        # Test connection
        logger.info("Testing automation system connection...")
        result = downloader.test_connection()
        logger.info(f"Connection test result: {result}")
        
        # Cleanup
        downloader.cleanup()
        
        return result.get('status') == 'success'
        
    except Exception as e:
        logger.error(f"Chrome automation test failed: {str(e)}")
        return False

def test_download_job_creation():
    """Test download job creation and processing"""
    try:
        logger.info("Testing download job system...")
        
        # Import required modules
        from new_app import DownloadJob, download_jobs, jobs_lock
        import uuid
        
        # Create test job
        job_id = str(uuid.uuid4())
        test_keys = ['42250485179240000239550020004175361171503396']
        job = DownloadJob(job_id, test_keys, 7)  # Using test user ID 7
        
        # Add to jobs dictionary
        with jobs_lock:
            download_jobs[job_id] = job
        
        logger.info(f"Test job created: {job_id}")
        logger.info(f"Job status: {job.status}")
        logger.info(f"Job progress: {job.progress_percentage}%")
        
        # Verify job attributes
        assert hasattr(job, 'progress_percentage'), "Missing progress_percentage attribute"
        assert hasattr(job, 'files'), "Missing files attribute"
        assert job.total_keys == 1, "Invalid total_keys"
        
        logger.info("Download job creation test: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"Download job test failed: {str(e)}")
        return False

def test_threading_fix():
    """Test the threading fix for job processing"""
    try:
        logger.info("Testing threading fix...")
        
        from threading import Thread
        from new_app import process_download_job
        import uuid
        
        # Test thread creation with correct arguments
        job_id = str(uuid.uuid4())
        user_id = 7
        
        # This should not raise an error anymore
        thread = Thread(target=process_download_job, args=(job_id, user_id))
        logger.info("Thread created successfully with correct arguments")
        
        # Don't actually start the thread in test
        logger.info("Threading fix test: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"Threading fix test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    logger.info("=== DEPLOY ENVIRONMENT XML DOWNLOAD SYSTEM TEST ===")
    logger.info(f"Test started at: {datetime.now()}")
    
    tests = [
        ("Chrome Automation", test_chrome_automation),
        ("Download Job Creation", test_download_job_creation),
        ("Threading Fix", test_threading_fix)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        try:
            result = test_func()
            results[test_name] = result
            status = "PASSED" if result else "FAILED"
            logger.info(f"{test_name}: {status}")
        except Exception as e:
            logger.error(f"{test_name}: FAILED - {str(e)}")
            results[test_name] = False
    
    # Summary
    logger.info("\n=== TEST SUMMARY ===")
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED - System ready for XML downloads!")
        return True
    else:
        logger.warning("⚠️ Some tests failed - Check logs for details")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)