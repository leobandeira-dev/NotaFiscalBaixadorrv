#!/usr/bin/env python3
"""
Test script para debug do download XML
"""
import logging
import sys
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_download_debug():
    """Test com debug detalhado"""
    try:
        # Import automation system
        from automation_fixed import InvoiceDownloader
        
        # Test with a real invoice key
        test_key = "42250485179240000239550020004175491355349509"
        
        logger.info(f"Starting debug test with invoice key: {test_key}")
        
        # Create downloader
        downloader = InvoiceDownloader()
        
        # Test download with debug
        result = downloader.download_invoice_xml(
            invoice_key=test_key,
            job_id="debug_test",
            download_type="xml",
            user_id=None  # No charging for debug
        )
        
        logger.info(f"Download result: {result}")
        
        # Cleanup
        downloader.cleanup()
        
        return result
        
    except Exception as e:
        logger.error(f"Debug test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    print("=== XML Download Debug Test ===")
    result = test_download_debug()
    print(f"Final result: {result}")