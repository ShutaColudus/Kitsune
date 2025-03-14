# Vendor packages for Kitsune
# This directory contains third-party dependencies

# Ensure the vendored packages are properly accessible
import sys
import os

# Add this directory to path to ensure proper package import
vendor_dir = os.path.dirname(__file__)
if vendor_dir not in sys.path:
    sys.path.insert(0, vendor_dir)

# Import the actual requests package
try:
    import requests
    print("[KITSUNE INFO] Successfully loaded requests module.")
except ImportError as e:
    print(f"[KITSUNE ERROR] Failed to import requests module: {e}")