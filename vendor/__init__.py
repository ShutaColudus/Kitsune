"""
Vendor package for third-party dependencies.

This package contains third-party libraries that are required by Kitsune
but are not part of the standard Blender Python distribution.

Libraries included:
- requests: HTTP library for making API calls
"""

import os
import sys
import importlib
import importlib.util

# Import and expose the requests library for other modules
try:
    # Try to use system installed requests first
    import requests
except ImportError:
    # If not available, check if we have it in our vendor directory
    vendor_requests_path = os.path.join(os.path.dirname(__file__), "requests")
    
    if os.path.exists(vendor_requests_path) and os.path.isdir(vendor_requests_path):
        if vendor_requests_path not in sys.path:
            sys.path.append(vendor_requests_path)
            
        try:
            import requests
        except ImportError:
            # Create a simple placeholder for development/testing
            # This will be replaced with the actual requests library when packaging the addon
            from types import ModuleType
            
            class DummyResponse:
                def __init__(self):
                    self.status_code = 500
                    self.text = "Requests module not properly installed"
                    
                def json(self):
                    return {"error": "Requests module not properly installed"}
            
            class DummyRequests(ModuleType):
                def __init__(self):
                    super().__init__("requests")
                    self.exceptions = type('obj', (object,), {
                        'RequestException': Exception,
                        'Timeout': Exception
                    })
                    
                def get(self, *args, **kwargs):
                    return DummyResponse()
                    
                def post(self, *args, **kwargs):
                    return DummyResponse()
            
            # Create a dummy requests module
            requests = DummyRequests()
            sys.modules['requests'] = requests
            
            # Log error
            print("WARNING: requests module not available. Please install it for full functionality.")
    else:
        # No requests module available - create a placeholder
        from types import ModuleType
        
        class DummyResponse:
            def __init__(self):
                self.status_code = 500
                self.text = "Requests module not properly installed"
                
            def json(self):
                return {"error": "Requests module not properly installed"}
        
        class DummyRequests(ModuleType):
            def __init__(self):
                super().__init__("requests")
                self.exceptions = type('obj', (object,), {
                    'RequestException': Exception,
                    'Timeout': Exception
                })
                
            def get(self, *args, **kwargs):
                return DummyResponse()
                
            def post(self, *args, **kwargs):
                return DummyResponse()
        
        # Create a dummy requests module
        requests = DummyRequests()
        sys.modules['requests'] = requests
        
        # Log error
        print("WARNING: requests module not available. Please install it for full functionality.")

# Export the requests module
__all__ = ['requests']