# Utility functions for Kitsune addon
import bpy
import sys
import os
import threading
import traceback
from datetime import datetime

# Debug mode flag
DEBUG_MODE = False

def set_debug_mode(enabled):
    """
    Set the debug mode flag.
    
    Args:
        enabled (bool): Whether to enable debug mode
    """
    global DEBUG_MODE
    DEBUG_MODE = enabled
    log_debug(f"Debug mode {'enabled' if enabled else 'disabled'}")

def log_debug(message):
    """
    Log a debug message if debug mode is enabled.
    
    Args:
        message (str): The message to log
    """
    if DEBUG_MODE:
        print(f"[KITSUNE DEBUG] {message}")

def log_info(message):
    """
    Log an info message.
    
    Args:
        message (str): The message to log
    """
    print(f"[KITSUNE INFO] {message}")

def log_error(message):
    """
    Log an error message.
    
    Args:
        message (str): The message to log
    """
    print(f"[KITSUNE ERROR] {message}")

def log_exception(e):
    """
    Log an exception with traceback.
    
    Args:
        e (Exception): The exception to log
    """
    log_error(f"Exception: {str(e)}")
    log_error(traceback.format_exc())

def format_timestamp():
    """
    Get a formatted timestamp for the current time.
    
    Returns:
        str: Formatted timestamp
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def truncate_string(text, max_length=100):
    """
    Truncate a string to the specified maximum length.
    
    Args:
        text (str): The text to truncate
        max_length (int, optional): Maximum length. Defaults to 100.
        
    Returns:
        str: Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def safe_execute_code(code, globals_dict=None, locals_dict=None):
    """
    Safely execute the provided Python code with error handling.
    
    Args:
        code (str): The Python code to execute
        globals_dict (dict, optional): Global variables dictionary. Defaults to None.
        locals_dict (dict, optional): Local variables dictionary. Defaults to None.
        
    Returns:
        tuple: (success, result_or_error)
    """
    if globals_dict is None:
        globals_dict = {}
    
    if locals_dict is None:
        locals_dict = {}
    
    # Include bpy module in globals
    globals_dict['bpy'] = bpy
    
    try:
        # Compile the code to catch syntax errors
        compiled_code = compile(code, '<string>', 'exec')
        
        # Execute the code
        exec(compiled_code, globals_dict, locals_dict)
        
        return True, "Code executed successfully"
    except Exception as e:
        error_msg = f"Error executing code: {str(e)}\n{traceback.format_exc()}"
        log_error(error_msg)
        return False, error_msg

def ensure_directory_exists(path):
    """
    Ensure that the specified directory exists, creating it if necessary.
    
    Args:
        path (str): The directory path
        
    Returns:
        bool: True if directory exists or was created, False otherwise
    """
    try:
        if not os.path.exists(path):
            os.makedirs(path)
            log_debug(f"Created directory: {path}")
        return True
    except Exception as e:
        log_error(f"Failed to create directory {path}: {str(e)}")
        return False

def escape_html(text):
    """
    Escape HTML special characters in text.
    
    Args:
        text (str): Text to escape
        
    Returns:
        str: Escaped text
    """
    if not text:
        return ""
        
    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        "'": "&apos;",
        ">": "&gt;",
        "<": "&lt;",
    }
    
    return "".join(html_escape_table.get(c, c) for c in text)

def get_blender_version():
    """
    Get the current Blender version as a tuple.
    
    Returns:
        tuple: (major, minor, patch)
    """
    return bpy.app.version

def check_blender_compatibility():
    """
    Check if the current Blender version is compatible.
    
    Returns:
        tuple: (is_compatible, message)
    """
    current_version = get_blender_version()
    required_version = (3, 0, 0)
    
    if current_version < required_version:
        msg = f"Kitsune requires Blender {required_version[0]}.{required_version[1]}.{required_version[2]} or newer. " \
              f"Current version: {current_version[0]}.{current_version[1]}.{current_version[2]}"
        return False, msg
    
    return True, f"Compatible with Blender {current_version[0]}.{current_version[1]}.{current_version[2]}"

def check_dependencies():
    """
    Check if all required dependencies are available.
    
    Returns:
        tuple: (all_dependencies_met, missing_dependencies)
    """
    missing = []
    
    # Add the vendored modules to the path if not there
    vendor_path = os.path.join(os.path.dirname(__file__), "vendor")
    if vendor_path not in sys.path:
        sys.path.append(vendor_path)
    
    # Check for requests
    try:
        import requests
    except ImportError:
        missing.append("requests")
    
    return len(missing) == 0, missing