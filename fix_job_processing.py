"""
Correção definitiva para o sistema de processamento de jobs
Remove conflitos entre múltiplas definições da função process_download_job
"""

import logging
import json
from datetime import datetime
from models import DownloadJob as DBDownloadJob, db

logger = logging.getLogger(__name__)

def fix_job_processing():
    """Corrige conflitos no sistema de processamento de jobs"""
    
    # Remove old process_download_job definition from new_app.py
    with open('new_app.py', 'r') as f:
        content = f.read()
    
    # Check for multiple function definitions
    if content.count('def process_download_job') > 1:
        logger.warning("Multiple process_download_job definitions found - fixing...")
        
        # Find and remove the old definition (with single parameter)
        lines = content.split('\n')
        new_lines = []
        skip_function = False
        function_indent = 0
        
        for line in lines:
            if 'def process_download_job(job_id):' in line:
                # Start skipping this function
                skip_function = True
                function_indent = len(line) - len(line.lstrip())
                continue
            elif skip_function:
                # Check if we're still inside the function
                current_indent = len(line) - len(line.lstrip())
                if line.strip() == '' or current_indent > function_indent:
                    # Still inside function or empty line
                    continue
                else:
                    # Function ended
                    skip_function = False
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        # Write back the corrected content
        with open('new_app.py', 'w') as f:
            f.write('\n'.join(new_lines))
        
        logger.info("Fixed multiple function definitions")
    
    return True

if __name__ == "__main__":
    fix_job_processing()