import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty
from . import utils

# チャットダイアログオペレータ
class KITSUNE_OT_chat_in_dialog(bpy.types.Operator):
    """AIとのチャットをダイアログで表示します"""
    bl_idname = "kitsune.chat_dialog"
    bl_label = "Chat with AI"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        utils.log_debug("チャットダイアログを開始します")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=600)
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="チャットダイアログ")

# ダイアログからメッセージを送信
class KITSUNE_OT_send_from_dialog(bpy.types.Operator):
    """ダイアログからメッセージを送信します"""
    bl_idname = "kitsune.send_from_dialog"
    bl_label = "Send Message"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    message: StringProperty(
        name="Message",
        description="送信するメッセージ",
        default=""
    )
    
    def execute(self, context):
        utils.log_debug(f"メッセージを送信します: {self.message}")
        return {'FINISHED'}

# コードをクリップボードにコピー
class KITSUNE_OT_copy_code(bpy.types.Operator):
    """生成されたコードをクリップボードにコピーします"""
    bl_idname = "kitsune.copy_code"
    bl_label = "Copy Code"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    code: StringProperty(
        name="Code",
        description="コピーするコード",
        default=""
    )
    
    def execute(self, context):
        utils.log_debug("コードをクリップボードにコピーします")
        context.window_manager.clipboard = self.code
        self.report({'INFO'}, "コードをクリップボードにコピーしました")
        return {'FINISHED'}

# チャット履歴をエクスポート
class KITSUNE_OT_export_chat(bpy.types.Operator):
    """チャット履歴をファイルにエクスポートします"""
    bl_idname = "kitsune.export_chat"
    bl_label = "Export Chat"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    filepath: StringProperty(
        name="File Path",
        description="エクスポート先のファイルパス",
        subtype='FILE_PATH'
    )
    
    def execute(self, context):
        utils.log_debug(f"チャット履歴をエクスポートします: {self.filepath}")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# チャットセッションの名前を変更
class KITSUNE_OT_rename_chat(bpy.types.Operator):
    """チャットセッションの名前を変更します"""
    bl_idname = "kitsune.rename_chat"
    bl_label = "Rename Chat"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    chat_index: bpy.props.IntProperty(
        name="Chat Index",
        description="名前を変更するチャットのインデックス",
        default=0
    )
    
    new_name: StringProperty(
        name="New Name",
        description="新しいチャット名",
        default=""
    )
    
    def execute(self, context):
        utils.log_debug(f"チャット名を変更します: インデックス {self.chat_index}, 新しい名前: {self.new_name}")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "new_name")

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