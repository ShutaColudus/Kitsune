# List of classes to register
classes = (
    KITSUNE_OT_chat_in_dialog,
    KITSUNE_OT_send_from_dialog,
    KITSUNE_OT_copy_code,
    KITSUNE_OT_export_chat,
    KITSUNE_OT_rename_chat
)

def register():
    """Register operators."""
    # 既に登録されているクラスを確認してアンレジスターする
    for cls in classes:
        try:
            bpy.utils.unregister_class(cls)
        except:
            pass
    
    # クラスを登録
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception as e:
            from . import utils
            utils.log_error(f"Failed to register operator {cls.__name__}: {str(e)}")

def unregister():
    """Unregister operators."""
    # クラスをアンレジスター
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception as e:
            from . import utils
            utils.log_error(f"Failed to unregister operator {cls.__name__}: {str(e)}")