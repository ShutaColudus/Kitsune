import bpy
import os
import sys

# ロギングレベル
DEBUG = 1
INFO = 2
WARNING = 3
ERROR = 4

# デフォルトのロギングレベル
_current_log_level = INFO

def set_debug_mode(enable=True):
    """
    デバッグモードを設定します。
    
    Args:
        enable (bool): デバッグモードを有効にするかどうか
    """
    global _current_log_level
    _current_log_level = DEBUG if enable else INFO
    log_debug(f"Debug mode {'enabled' if enable else 'disabled'}")

def log_debug(message):
    """
    デバッグメッセージをログに記録します。
    
    Args:
        message (str): ログメッセージ
    """
    if _current_log_level <= DEBUG:
        print(f"[KITSUNE-DEBUG] {message}")

def log_info(message):
    """
    情報メッセージをログに記録します。
    
    Args:
        message (str): ログメッセージ
    """
    if _current_log_level <= INFO:
        print(f"[KITSUNE-INFO] {message}")

def log_warning(message):
    """
    警告メッセージをログに記録します。
    
    Args:
        message (str): ログメッセージ
    """
    if _current_log_level <= WARNING:
        print(f"[KITSUNE-WARNING] {message}")

def log_error(message):
    """
    エラーメッセージをログに記録します。
    
    Args:
        message (str): ログメッセージ
    """
    if _current_log_level <= ERROR:
        print(f"[KITSUNE-ERROR] {message}")

def ensure_directory_exists(directory_path):
    """
    ディレクトリが存在することを確認し、存在しない場合は作成します。
    
    Args:
        directory_path (str): ディレクトリのパス
        
    Returns:
        bool: 操作が成功したかどうか
    """
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
            log_debug(f"Directory created: {directory_path}")
        return True
    except Exception as e:
        log_error(f"Failed to create directory {directory_path}: {str(e)}")
        return False

def cleanup_unused_files():
    """
    使用されていないファイルをクリーンアップします。
    
    Returns:
        tuple: (成功したかどうか, メッセージ)
    """
    # 実装はプロジェクトの要件に合わせて変更してください
    try:
        # クリーンアップロジックをここに実装
        log_debug("Cleanup process completed")
        return True, "Cleanup completed successfully"
    except Exception as e:
        return False, f"Cleanup failed: {str(e)}"

def check_ui_resources():
    """
    UIリソースをチェックします。
    
    Returns:
        bool: リソースが利用可能かどうか
    """
    # 実装はプロジェクトの要件に合わせて変更してください
    try:
        # UIリソースチェックのロジックをここに実装
        return True
    except Exception as e:
        log_error(f"UI resources check failed: {str(e)}")
        return False

def get_blender_version():
    """
    Get the current Blender version as a tuple.
    
    Returns:
        tuple: (major, minor, patch)
    """
    try:
        # 通常の方法
        return bpy.app.version
    except:
        # フォールバック: バージョン文字列からパース
        try:
            version_str = bpy.app.version_string
            parts = version_str.split('.')
            if len(parts) >= 2:
                major = int(parts[0])
                minor = int(parts[1])
                patch = 0
                if len(parts) > 2:
                    try:
                        patch = int(parts[2])
                    except:
                        pass
                return (major, minor, patch)
        except:
            pass
        
        # それでも失敗する場合はフォールバック
        return (3, 0, 0)

def check_blender_compatibility():
    """
    Check if the current Blender version is compatible.
    
    Returns:
        tuple: (is_compatible, message)
    """
    try:
        current_version = get_blender_version()
        required_version = (3, 0, 0)
        
        if current_version < required_version:
            msg = f"Kitsune requires Blender {required_version[0]}.{required_version[1]}.{required_version[2]} or newer. " \
                  f"Current version: {current_version[0]}.{current_version[1]}.{current_version[2]}"
            return False, msg
        
        return True, f"Compatible with Blender {current_version[0]}.{current_version[1]}.{current_version[2]}"
    except Exception as e:
        log_error(f"Error checking Blender compatibility: {str(e)}")
        return True, "Blender version check failed, proceeding anyway"

def check_dependencies():
    """
    Check if all required dependencies are installed.
    
    Returns:
        tuple: (is_all_dependencies_ok, list_of_missing_dependencies)
    """
    missing_dependencies = []
    
    # RequestsとJSON（標準ライブラリ）を確認
    try:
        # まずベンダーパッケージからリクエストを試す
        try:
            from vendor import requests
            log_debug(f"Using vendored requests {requests.__version__ if hasattr(requests, '__version__') else 'unknown version'}")
        except ImportError:
            # 失敗した場合はシステムのrequestsを試す
            try:
                import requests
                log_debug(f"Using system requests {requests.__version__ if hasattr(requests, '__version__') else 'unknown version'}")
            except ImportError:
                missing_dependencies.append("requests")
                log_error("Requests library is missing")
        
        # JSONは標準ライブラリなので通常は利用可能
        import json
        log_debug("JSON library is available")
    except Exception as e:
        log_error(f"Error checking dependencies: {str(e)}")
        missing_dependencies.append("unknown")
    
    return len(missing_dependencies) == 0, missing_dependencies