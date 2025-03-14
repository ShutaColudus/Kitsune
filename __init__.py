# Kitsune: AI-powered modeling assistant for Blender
# Main addon registration module

bl_info = {
    "name": "Kitsune",
    "author": "Shuta",
    "version": (0, 1, 0),
    "blender": (3, 0, 0),
    "location": "3D View > Sidebar > Kitsune",
    "description": "AI-powered modeling assistant",
    "category": "3D View",
    "wiki_url": "https://github.com/ShutaColudus/kitsune",
    "tracker_url": "https://github.com/ShutaColudus/kitsune/issues",
}

import bpy
import sys
import os
from bpy.types import AddonPreferences
from . import (
    ui,
    preferences,
    utils
)

# Setup paths to include vendor packages
def setup_vendor_packages():
    """Setup vendor packages for imports."""
    vendor_dir = os.path.join(os.path.dirname(__file__), "vendor")
    
    # Ensure vendor directory exists
    utils.ensure_directory_exists(vendor_dir)
    
    # Add vendor directory to path if not already there
    if vendor_dir not in sys.path:
        sys.path.insert(0, vendor_dir)
    
    # Initialize vendor package
    try:
        # Import vendor to initialize it
        from . import vendor
        utils.log_debug("Vendor package initialized")
        
        # Try to import actual requests package
        try:
            import requests
            utils.log_debug(f"Requests module found: {requests.__version__ if hasattr(requests, '__version__') else 'unknown version'}")
        except ImportError as e:
            utils.log_error(f"Requests module import error: {str(e)}")
    except ImportError as e:
        utils.log_error(f"Vendor package not properly initialized: {str(e)}")

def register():
    """Register the addon."""
    # Set debug mode from environment variable if available
    debug_env = os.environ.get("KITSUNE_DEBUG", "").lower()
    if debug_env in ("1", "true", "yes", "on"):
        utils.set_debug_mode(True)

    # Check Blender compatibility
    is_compatible, message = utils.check_blender_compatibility()
    if not is_compatible:
        utils.log_error(message)
        # We'll still register, but warning is logged
    
    # Setup vendor packages
    setup_vendor_packages()
    
    # Register preferences 
    bpy.utils.register_class(preferences.KitsuneAddonPreferences)
    
    # Register UI components
    ui.register()
    
    utils.log_info("Kitsune addon registered successfully")

def unregister():
    """Unregister the addon."""
    # Unregister UI components
    ui.unregister()
    
    # Unregister preferences
    bpy.utils.unregister_class(preferences.KitsuneAddonPreferences)
    
    utils.log_info("Kitsune addon unregistered")

# For testing in Blender text editor
if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()