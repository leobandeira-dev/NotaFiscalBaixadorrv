#!/usr/bin/env python3
import subprocess
import json
import sys

def test_rpa_with_key(invoice_key):
    """Test the RPA script with a specific invoice key"""
    print(f"Testing RPA with invoice key: {invoice_key}")
    
    try:
        # Run the enhanced XML fetcher
        result = subprocess.run([
            'python3', 'server/enhanced_xml_fetcher.py', invoice_key
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            try:
                response = json.loads(result.stdout)
                print(f"Success: {response.get('success', False)}")
                if response.get('success'):
                    xml_content = response.get('xml_content', '')
                    print(f"XML length: {len(xml_content)} characters")
                    
                    # Validate that the XML contains the correct invoice key
                    if invoice_key in xml_content:
                        print("✅ Validation passed: Invoice key found in XML")
                        
                        # Extract key information from XML for verification
                        import re
                        
                        # Find emit (emitente) information
                        emit_match = re.search(r'<emit>.*?</emit>', xml_content, re.DOTALL)
                        if emit_match:
                            emit_info = emit_match.group(0)
                            cnpj_match = re.search(r'<CNPJ>(\d+)</CNPJ>', emit_info)
                            nome_match = re.search(r'<xNome>(.*?)</xNome>', emit_info)
                            if cnpj_match and nome_match:
                                print(f"Emitente: {nome_match.group(1)} (CNPJ: {cnpj_match.group(1)})")
                        
                        # Find dest (destinatário) information
                        dest_match = re.search(r'<dest>.*?</dest>', xml_content, re.DOTALL)
                        if dest_match:
                            dest_info = dest_match.group(0)
                            cnpj_match = re.search(r'<CNPJ>(\d+)</CNPJ>', dest_info)
                            nome_match = re.search(r'<xNome>(.*?)</xNome>', dest_info)
                            if cnpj_match and nome_match:
                                print(f"Destinatário: {nome_match.group(1)} (CNPJ: {cnpj_match.group(1)})")
                        
                        # Find total value
                        total_match = re.search(r'<vNF>([\d.]+)</vNF>', xml_content)
                        if total_match:
                            print(f"Valor total: R$ {total_match.group(1)}")
                            
                        return True
                    else:
                        print("❌ Validation failed: Invoice key not found in XML")
                        
                        # Check what keys are in the XML
                        found_keys = re.findall(r'\d{44}', xml_content)
                        if found_keys:
                            print(f"Found keys in XML: {found_keys}")
                        
                        return False
                else:
                    print(f"Error: {response.get('error', 'Unknown error')}")
                    return False
            except json.JSONDecodeError:
                print(f"Failed to parse JSON response: {result.stdout}")
                return False
        else:
            print(f"Script failed with return code {result.returncode}")
            print(f"Error output: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("RPA script timed out")
        return False
    except Exception as e:
        print(f"Exception running RPA: {e}")
        return False

if __name__ == "__main__":
    # Test with the specific key mentioned in the issue
    test_key = "35250652684982000181550010001110071066188885"
    
    print("=" * 60)
    print("Testing RPA Validation System")
    print("=" * 60)
    
    success = test_rpa_with_key(test_key)
    
    if success:
        print("\n✅ RPA test completed successfully")
    else:
        print("\n❌ RPA test failed - needs improvement")