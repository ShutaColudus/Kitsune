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
        
        # 明示的にrequestsを再ロード
        if 'requests' in sys.modules:
            importlib.reload(sys.modules['requests'])
            utils.log_debug("Requests module reloaded")
        
        # Try to import actual requests package
        try:
            import requests
            # サブモジュールの明示的なインポート
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
        utils.log_error("UI resources check failed - モーダルダイアログが表示されない可能性があります")

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
    
    # クリーンアップの実行
    cleanup_on_startup()
    
    # Setup vendor packages
    setup_vendor_packages()
    
    # UIリソースのチェック
    check_ui_capabilities()
    
    # Register preferences 
    bpy.utils.register_class(preferences.KitsuneAddonPreferences)
    
    # Register UI components
    ui.register()
    
    # 登録完了メッセージを表示
    utils.log_info("Kitsune addon registered successfully")
    
    # インストール確認メッセージをモーダルで表示
    def show_startup_message():
        utils.show_message_box(
            "Kitsuneアドオンが正常に登録されました。\n"
            "サイドバーの'Kitsune'タブからアクセスできます。",
            "Kitsune起動完了",
            'INFO'
        )
    
    # 少し遅延させてメッセージを表示（Blenderの起動完了後に表示）
    bpy.app.timers.register(show_startup_message, first_interval=1.0)

def unregister():
    """Unregister the addon."""
    # タイマーの削除
    for timer in bpy.app.timers.items():
        if 'show_startup_message' in str(timer):
            bpy.app.timers.remove(timer)
    
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