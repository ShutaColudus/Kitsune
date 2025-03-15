# Vendor package for Kitsune addon
#
# This package contains third-party dependencies to ensure the addon
# works without requiring external installations.
#
# Current included packages:
# - requests: HTTP library for making API calls

import sys
import os

# Get the current directory
__path__ = [os.path.dirname(__file__)]

# Add all subdirectories to the path to ensure imports work properly
for item in os.listdir(__path__[0]):
    item_path = os.path.join(__path__[0], item)
    if os.path.isdir(item_path) and item_path not in sys.path:
        sys.path.insert(0, item_path)