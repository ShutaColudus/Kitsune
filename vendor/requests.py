# Minimal requests library mock
# This is a placeholder to allow the addon to load
# Real API requests will not work with this mock

class Response:
    def __init__(self, status_code=200, text="", json_data=None):
        self.status_code = status_code
        self.text = text
        self._json = json_data or {}
    
    def json(self):
        return self._json

def post(url, headers=None, json=None, timeout=None):
    """Mock post function that returns a simulated error response"""
    return Response(
        status_code=503,
        text="Mock requests library - API communication not available",
        json_data={"error": {"message": "Mock requests library - actual API communication not available"}}
    )

def get(url, headers=None, params=None, timeout=None):
    """Mock get function that returns a simulated error response"""
    return Response(
        status_code=503,
        text="Mock requests library - API communication not available",
        json_data={"error": {"message": "Mock requests library - actual API communication not available"}}
    )

class exceptions:
    class RequestException(Exception):
        """Base class for all request exceptions"""
        pass
    
    class Timeout(RequestException):
        """Request timed out"""
        pass
    
    class ConnectionError(RequestException):
        """Connection error"""
        pass
    
    class HTTPError(RequestException):
        """HTTP error"""
        pass