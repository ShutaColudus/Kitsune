# Utility functions for Kitsune addon
import bpy
import sys
import os
import threading
import traceback
from datetime import datetime

# Debug mode flag - 開発中はデバッグモードを有効にする
DEBUG_MODE = True

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
    # エラーが発生した場合、モーダルでメッセージを表示
    try:
        show_message_box(message, "Kitsune Error", 'ERROR')
    except Exception as e:
        print(f"[KITSUNE ERROR] Failed to show error message box: {str(e)}")

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
        try:
            # サブモジュールも確認
            import requests.sessions
            import requests.adapters
            log_debug(f"Found requests version: {requests.__version__ if hasattr(requests, '__version__') else 'unknown'} with submodules")
        except ImportError as e:
            log_error(f"Failed to import requests submodules: {str(e)}")
            missing.append("requests submodules")
    except ImportError as e:
        log_error(f"Failed to import requests: {str(e)}")
        missing.append("requests")
    
    return len(missing) == 0, missing

def show_message_box(message, title="Message", icon='INFO'):
    """
    Show a message box to the user.
    
    Args:
        message (str): Message to display
        title (str, optional): Title of the message box. Defaults to "Message".
        icon (str, optional): Icon to display. Defaults to 'INFO'.
    """
    def draw(self, context):
        self.layout.label(text=message)
    
    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)

def cleanup_unused_files():
    """
    Clean up any unused or temporary files.
    
    Returns:
        tuple: (success, message)
    """
    try:
        # この関数に削除対象のファイルを追加
        addon_dir = os.path.dirname(__file__)
        
        # 削除対象のファイルパターン
        patterns_to_remove = [
            "*.pyc",
            "__pycache__",
            "*.bak",
            "*.tmp"
        ]
        
        deleted_count = 0
        
        for pattern in patterns_to_remove:
            for root, dirs, files in os.walk(addon_dir):
                if pattern == "__pycache__":
                    if "__pycache__" in dirs:
                        pycache_path = os.path.join(root, "__pycache__")
                        for pyc_file in os.listdir(pycache_path):
                            try:
                                os.remove(os.path.join(pycache_path, pyc_file))
                                deleted_count += 1
                            except:
                                pass
                        try:
                            os.rmdir(pycache_path)
                            log_debug(f"Removed directory: {pycache_path}")
                        except:
                            pass
                else:
                    import fnmatch
                    for filename in fnmatch.filter(files, pattern):
                        try:
                            os.remove(os.path.join(root, filename))
                            log_debug(f"Removed file: {os.path.join(root, filename)}")
                            deleted_count += 1
                        except:
                            pass
        
        return True, f"Cleaned up {deleted_count} unused files"
    except Exception as e:
        log_exception(e)
        return False, f"Error cleaning up files: {str(e)}"

def check_ui_resources():
    """
    Check if UI resources are available and accessible.
    
    Returns:
        bool: True if all resources are available, False otherwise
    """
    try:
        # UI機能の基本的なチェック
        log_debug("Checking UI resources...")
        
        # Blenderのウィンドウマネージャーが利用可能か確認
        if not hasattr(bpy, "context") or not hasattr(bpy.context, "window_manager"):
            log_error("Window manager not available")
            return False
        
        # モーダルダイアログをサポートしているか確認
        test_operator_registered = False
        
        # テスト用オペレーター
        class KITSUNE_OT_test_modal(bpy.types.Operator):
            bl_idname = "kitsune.test_modal"
            bl_label = "Test Modal"
            bl_options = {'INTERNAL'}
            
            def execute(self, context):
                return {'FINISHED'}
                
            def invoke(self, context, event):
                return context.window_manager.invoke_props_dialog(self)
                
            def draw(self, context):
                self.layout.label(text="Modal test")
        
        try:
            # テスト用オペレーターを一時的に登録
            bpy.utils.register_class(KITSUNE_OT_test_modal)
            test_operator_registered = True
            
            # すぐに登録解除
            bpy.utils.unregister_class(KITSUNE_OT_test_modal)
            log_debug("Modal dialog support confirmed")
            return True
        except Exception as e:
            log_error(f"Failed to register test modal operator: {str(e)}")
            return False
        finally:
            # 万が一登録されたままなら登録解除
            if test_operator_registered:
                try:
                    bpy.utils.unregister_class(KITSUNE_OT_test_modal)
                except:
                    pass
    
    except Exception as e:
        log_exception(e)
        return False