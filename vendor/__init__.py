# Vendor packages for Kitsune
# This directory contains third-party dependencies

# Explicitly import the modules to make them available
# when importing from vendor package
from . import requests

# Inform that we're using mocked modules
print("[KITSUNE INFO] Using mocked requests module. API functionality will be limited.")