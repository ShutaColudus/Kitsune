# Vendor packages for Kitsune
# This directory contains third-party dependencies

# Ensure requests package is accessible
try:
    from requests import *
    print("[KITSUNE INFO] Successfully loaded requests module.")
except ImportError as e:
    print(f"[KITSUNE ERROR] Failed to import requests module: {e}")