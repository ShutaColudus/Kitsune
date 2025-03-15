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
import importlib
from bpy.types import AddonPreferences

# Use directory name as addon ID
ADDON_ID = os.path.basename(os.path.dirname(__file__))
print(f"Addon ID: {ADDON_ID}")
from . import (
    ui,
    preferences,
    utils,
    operators
)

# Setup paths to include vendor packages
def setup_vendor_packages():
    """Setup vendor packages for imports."""
    vendor_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "vendor"))
    print(f"Vendor directory: {vendor_dir}")
    
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
        
        # Explicitly reload requests
        if 'requests' in sys.modules:
            importlib.reload(sys.modules['requests'])
            utils.log_debug("Requests module reloaded")
        
        # Try to import actual requests package
        try:
            import requests
            # Explicit import of submodules
            import requests.adapters
            import requests.auth
            import requests.sessions
            
            utils.log_debug(f"Requests module found: {requests.__version__ if hasattr(requests, '__version__') else 'unknown version'}")
        except ImportError as e:
            utils.log_error(f"Requests module import error: {str(e)}")
    except ImportError as e:
        utils.log_error(f"Vendor package not properly initialized: {str(e)}")

def cleanup_on_startup():
    """Perform cleanup operations on startup."""
    utils.log_info("Performing startup cleanup...")
    success, message = utils.cleanup_unused_files()
    if success:
        utils.log_info(message)
    else:
        utils.log_error(message)

def check_ui_capabilities():
    """Check UI capabilities and resources."""
    ui_check = utils.check_ui_resources()
    if ui_check:
        utils.log_info("UI resources check passed")
    else:
        utils.log_error("UI resources check failed - Modal dialogs may not display properly")

# Operator for displaying startup messages
class KITSUNE_OT_startup_message(bpy.types.Operator):
    """Show startup message."""
    
    bl_idname = "kitsune.startup_message"
    bl_label = "Kitsune Startup Complete"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    message: bpy.props.StringProperty(
        default="Kitsune addon has been successfully registered.\nYou can access it from the 'Kitsune' tab in the sidebar."
    )
    
    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)
    
    def draw(self, context):
        layout = self.layout
        for line in self.message.split('\n'):
            layout.label(text=line)

# Timer function for showing startup message
def show_startup_message():
    try:
        bpy.ops.kitsune.startup_message('INVOKE_DEFAULT')
    except Exception as e:
        utils.log_error(f"Error showing startup message: {str(e)}")
    return None  # Run timer only once

# Global timer handle
_timer_handle = None

def register():
    """Register the addon."""
    global _timer_handle
    
    # Set debug mode from environment variable if available
    debug_env = os.environ.get("KITSUNE_DEBUG", "").lower()
    if debug_env in ("1", "true", "yes", "on"):
        utils.set_debug_mode(True)

    # Check Blender compatibility
    is_compatible, message = utils.check_blender_compatibility()
    if not is_compatible:
        utils.log_error(message)
        # We'll still register, but warning is logged
    
    # Execute cleanup
    cleanup_on_startup()
    
    # Setup vendor packages
    try:
        setup_vendor_packages()
        print("Vendor packages setup completed")
    except Exception as e:
        print(f"Error setting up vendor packages: {e}")
    
    # Check UI resources
    check_ui_capabilities()
    
    # Unregister first to prevent 'already registered' errors
    try:
        bpy.utils.unregister_class(KITSUNE_OT_startup_message)
    except:
        pass
    
    # Register startup message operator
    bpy.utils.register_class(KITSUNE_OT_startup_message)
    
    # Unregister preferences first to prevent 'already registered' errors
    try:
        bpy.utils.unregister_class(preferences.KitsuneAddonPreferences)
    except:
        pass
    
    # Register preferences 
    bpy.utils.register_class(preferences.KitsuneAddonPreferences)
    
    # Register operators
    operators.register()
    
    # Register UI components
    ui.register()
    
    # Display registration complete message
    utils.log_info("Kitsune addon registered successfully")
    
    # Add a slight delay to show the message (after Blender startup is complete)
    try:
        if hasattr(bpy.app, "timers"):
            _timer_handle = bpy.app.timers.register(show_startup_message, first_interval=1.0)
    except Exception as e:
        utils.log_error(f"Error registering timer: {str(e)}")

def unregister():
    """Unregister the addon."""
    global _timer_handle
    
    # Remove timers
    try:
        if hasattr(bpy.app, "timers") and _timer_handle is not None:
            if _timer_handle in bpy.app.timers:
                bpy.app.timers.unregister(_timer_handle)
    except Exception as e:
        utils.log_error(f"Error removing timer: {str(e)}")
    
    # Unregister UI components
    try:
        ui.unregister()
    except Exception as e:
        utils.log_error(f"Error unregistering UI: {str(e)}")
    
    # Unregister operators
    try:
        operators.unregister()
    except Exception as e:
        utils.log_error(f"Error unregistering operators: {str(e)}")
    
    # Unregister preferences
    try:
        bpy.utils.unregister_class(preferences.KitsuneAddonPreferences)
    except Exception as e:
        utils.log_error(f"Error unregistering preferences: {str(e)}")
    
    # Unregister startup message operator
    try:
        bpy.utils.unregister_class(KITSUNE_OT_startup_message)
    except Exception as e:
        utils.log_error(f"Error unregistering startup message: {str(e)}")
    
    utils.log_info("Kitsune addon unregistered")

# For testing in Blender text editor
if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()