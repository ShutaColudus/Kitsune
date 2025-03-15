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