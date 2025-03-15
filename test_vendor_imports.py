#!/usr/bin/env python3
# Test script to verify that vendor packages are properly loaded
import os
import sys

# Add the current directory to the path so we can import from the addon
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

print("Testing vendor package imports...")

# Set up vendor directory
from vendor import __init__ as vendor_init
print("✓ Vendor package imported correctly")

# Test requests import
try:
    from vendor import requests
    print(f"✓ Requests library imported correctly (version: {requests.__version__})")
    
    # Test importing key submodules that are used in the addon
    from vendor.requests import adapters
    print("✓ requests.adapters imported correctly")
    
    from vendor.requests import auth
    print("✓ requests.auth imported correctly")
    
    from vendor.requests import sessions
    print("✓ requests.sessions imported correctly")
    
    # Make a simple test request to verify the library works
    print("Testing HTTP request to httpbin.org...")
    response = requests.get("https://httpbin.org/get", timeout=5)
    if response.status_code == 200:
        print(f"✓ HTTP request successful (status code: {response.status_code})")
    else:
        print(f"✗ HTTP request failed (status code: {response.status_code})")
        
except ImportError as e:
    print(f"✗ Failed to import requests: {str(e)}")
except Exception as e:
    print(f"✗ Error testing requests: {str(e)}")

print("\nAll tests completed")