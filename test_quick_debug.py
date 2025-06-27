#!/usr/bin/env python3
"""
Quick debug test to understand the form submission issue
"""

import time
import logging
from automation_fixed import InvoiceDownloader

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_quick_debug():
    """Quick test with shorter timeouts"""
    invoice_key = "42250485179240000239550020004175491355349509"
    
    logger.info("=== Quick Debug Test ===")
    logger.info(f"Testing with invoice key: {invoice_key}")
    
    downloader = InvoiceDownloader()
    
    try:
        # Test with shorter timeout
        result = downloader.download_invoice_xml(invoice_key, "quick_test", "xml")
        logger.info(f"Result: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return {'success': False, 'error': str(e)}
    finally:
        downloader.cleanup()

if __name__ == "__main__":
    result = test_quick_debug()
    print(f"Final result: {result}")