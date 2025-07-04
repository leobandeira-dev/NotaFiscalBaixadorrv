#!/usr/bin/env python3
"""
Test script for new meudanfe.com.br layout
Tests the updated automation system with the new interface
"""

import os
import sys
import logging
from automation_fixed import InvoiceDownloader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_new_layout():
    """Test the updated automation system with new layout"""
    
    # Test invoice key provided by user
    test_invoice_key = "35250513516247000107550010000113401146202508"
    test_job_id = "test_new_layout"
    
    logger.info("Testing new website layout automation...")
    logger.info(f"Using invoice key: {test_invoice_key}")
    
    downloader = InvoiceDownloader()
    
    try:
        # Test the download process
        result = downloader.download_invoice_xml(
            invoice_key=test_invoice_key,
            job_id=test_job_id,
            download_type='xml'
        )
        
        logger.info(f"Test result: {result}")
        
        if result.get('success'):
            logger.info("✅ NEW LAYOUT TEST SUCCESSFUL!")
            logger.info(f"XML successfully downloaded: {result.get('file_path', 'Unknown path')}")
            logger.info(f"File size: {result.get('file_size', 'Unknown size')} bytes")
        else:
            logger.error("❌ NEW LAYOUT TEST FAILED!")
            logger.error(f"Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"❌ TEST EXCEPTION: {str(e)}")
        
    finally:
        # Clean up
        try:
            downloader.cleanup()
        except:
            pass

if __name__ == "__main__":
    test_new_layout()