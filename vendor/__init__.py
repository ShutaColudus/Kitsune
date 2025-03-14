# Vendor packages for Kitsune
# This directory contains third-party dependencies

# Ensure the vendored packages are properly accessible
import sys
import os
import importlib

# Add this directory to path to ensure proper package import
vendor_dir = os.path.dirname(__file__)
if vendor_dir not in sys.path:
    sys.path.insert(0, vendor_dir)

# Import the actual requests package
try:
    import requests
    # 明示的にサブモジュールをインポート
    from requests import sessions
    from requests import adapters
    from requests import auth
    from requests import hooks
    print("[KITSUNE INFO] Successfully loaded requests module and submodules.")
except ImportError as e:
    print(f"[KITSUNE ERROR] Failed to import requests module: {e}")