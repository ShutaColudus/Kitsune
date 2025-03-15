import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty, PointerProperty, CollectionProperty, FloatProperty
from . import utils

# チャットの添付ファイル
class KitsuneAttachment(bpy.types.PropertyGroup):
    """チャットに添付されるファイル情報"""
    path: StringProperty(
        name="Path",
        description="添付ファイルのパス",
        default=""
    )
    name: StringProperty(
        name="Name",
        description="添付ファイルの表示名",
        default=""
    )
    type: StringProperty(
        name="Type",
        description="添付ファイルの種類",
        default="FILE"
    )
    preview_image: StringProperty(
        name="Preview Image",
        description="画像プレビュー用のデータパス",
        default=""
    )

# チャットメッセージ
class KitsuneChatMessage(bpy.types.PropertyGroup):
    """個々のチャットメッセージを表すクラス"""
    content: StringProperty(
        name="Content",
        description="メッセージの内容",
        default=""
    )
    sender: StringProperty(
        name="Sender",
        description="メッセージの送信者 (USER/AI)",
        default="USER"
    )
    timestamp: StringProperty(
        name="Timestamp",
        description="メッセージのタイムスタンプ",
        default=""
    )
    code: StringProperty(
        name="Code",
        description="AIが生成したコード",
        default=""
    )
    attachments: CollectionProperty(
        type=KitsuneAttachment,
        name="Attachments",
        description="メッセージに添付されたファイル"
    )

# チャットセッション
class KitsuneChatSession(bpy.types.PropertyGroup):
    """チャットセッションを表すクラス"""
    name: StringProperty(
        name="Name",
        description="チャットセッションの名前",
        default="New Chat"
    )
    messages: CollectionProperty(
        type=KitsuneChatMessage,
        name="Messages",
        description="チャットセッション内のメッセージリスト"
    )
    active_message_index: IntProperty(
        name="Active Message Index",
        description="現在アクティブなメッセージのインデックス",
        default=0
    )
    created_at: StringProperty(
        name="Created At",
        description="セッションの作成日時",
        default=""
    )

# UI設定プロパティ
class KitsuneUIProperties(bpy.types.PropertyGroup):
    """Kitsune UIのプロパティグループ"""
    input_text: StringProperty(
        name="Input",
        description="ユーザー入力テキスト",
        default=""
    )
    chat_sessions: CollectionProperty(
        type=KitsuneChatSession,
        name="Chat Sessions",
        description="チャットセッションのリスト"
    )
    active_session_index: IntProperty(
        name="Active Session Index",
        description="現在アクティブなセッションのインデックス",
        default=0
    )
    is_processing: BoolProperty(
        name="Is Processing",
        description="AIが処理中かどうか",
        default=False
    )
    view_mode: EnumProperty(
        name="View Mode",
        description="表示モード",
        items=[
            ('CHAT', "Chat", "チャットモード"),
            ('CODE', "Code", "コードモード"),
            ('SETTINGS', "Settings", "設定モード"),
        ],
        default='CHAT'
    )
    attachment_path: StringProperty(
        name="Attachment Path",
        description="添付ファイルのパス",
        default="",
        subtype='FILE_PATH'
    )
    panel_height: FloatProperty(
        name="Panel Height",
        description="パネルの高さ（0〜1の値、1で最大高）",
        default=0.7,
        min=0.3,
        max=1.0
    )
    # チャット表示設定
    chat_display_settings: BoolProperty(
        name="Display Settings",
        description="チャット表示設定を展開表示",
        default=False
    )
    # 画像添付の設定
    image_preview_size: EnumProperty(
        name="Image Preview Size",
        description="添付画像のプレビューサイズ",
        items=[
            ('SMALL', "Small", "小サイズ (128px)"),
            ('MEDIUM', "Medium", "中サイズ (256px)"),
            ('LARGE', "Large", "大サイズ (512px)"),
        ],
        default='MEDIUM'
    )

# チャットセッションリスト
class KITSUNE_UL_chat_sessions(bpy.types.UIList):
    """チャットセッションのUIリスト"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.name, icon='OUTLINER_DATA_GP_LAYER')
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon='OUTLINER_DATA_GP_LAYER')

# APIキー設定パネル
class KITSUNE_PT_api_settings(bpy.types.Panel):
    """API設定パネル"""
    bl_label = "API Settings"
    bl_idname = "KITSUNE_PT_api_settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Kitsune'
    bl_parent_id = "KITSUNE_PT_chat_panel"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        return context.scene.kitsune_ui.view_mode == 'SETTINGS'
    
    def draw(self, context):
        layout = self.layout
        preferences = context.preferences.addons.get(__package__, None)
        
        if not preferences:
            layout.label(text="アドオン設定が見つかりません", icon='ERROR')
            return
            
        prefs = preferences.preferences
        
        # API Provider選択
        layout.label(text="AIプロバイダー選択:", icon='WORLD')
        layout.prop(prefs, "api_provider", text="")
        
        # 選択したプロバイダーの設定
        selected_provider = prefs.api_provider
        box = layout.box()
        
        if selected_provider == 'anthropic':
            box.label(text="Anthropic設定:", icon='SETTINGS')
            box.prop(prefs, "anthropic_api_key", text="API Key")
            box.prop(prefs, "anthropic_model", text="Model")
            
        elif selected_provider == 'google':
            box.label(text="Google Gemini設定:", icon='SETTINGS')
            box.prop(prefs, "google_api_key", text="API Key")
            box.prop(prefs, "google_model", text="Model")
            
        elif selected_provider == 'deepseek':
            box.label(text="DeepSeek設定:", icon='SETTINGS')
            box.prop(prefs, "deepseek_api_key", text="API Key")
            box.prop(prefs, "deepseek_model", text="Model")
            
        elif selected_provider == 'openai':
            box.label(text="OpenAI設定:", icon='SETTINGS')
            box.prop(prefs, "openai_api_key", text="API Key")
            box.prop(prefs, "openai_model", text="Model")
        
        # 検証ボタン
        layout.operator("kitsune.validate_api_key", text="APIキーを検証", icon='CHECKMARK')

# チャット設定パネル
class KITSUNE_PT_chat_settings(bpy.types.Panel):
    """チャット設定パネル"""
    bl_label = "Chat Settings"
    bl_idname = "KITSUNE_PT_chat_settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Kitsune'
    bl_parent_id = "KITSUNE_PT_chat_panel"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        return context.scene.kitsune_ui.view_mode == 'SETTINGS'
    
    def draw(self, context):
        layout = self.layout
        preferences = context.preferences.addons.get(__package__, None)
        
        if not preferences:
            layout.label(text="アドオン設定が見つかりません", icon='ERROR')
            return
            
        prefs = preferences.preferences
        
        # チャット設定
        layout.label(text="チャット設定:", icon='OUTLINER_OB_FONT')
        layout.prop(prefs, "max_conversation_length", text="最大会話長")
        layout.prop(prefs, "auto_scroll", text="自動スクロール")
        layout.prop(prefs, "show_timestamps", text="タイムスタンプを表示")
        
        # UI設定
        layout.label(text="UI設定:", icon='WINDOW')
        kitsune_ui = context.scene.kitsune_ui
        layout.prop(kitsune_ui, "panel_height", text="パネル高さ")
        layout.prop(kitsune_ui, "image_preview_size", text="画像プレビューサイズ")

# メインパネル
class KITSUNE_PT_chat_panel(bpy.types.Panel):
    """Kitsuneメインパネル"""
    bl_label = "Kitsune AI Assistant"
    bl_idname = "KITSUNE_PT_chat_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Kitsune'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        kitsune_ui = scene.kitsune_ui
        
        # パネルの高さを設定（領域の下部までいっぱいに表示）
        region_height = context.region.height
        panel_height = int(region_height * kitsune_ui.panel_height)
        
        # 表示モード切り替え
        row = layout.row(align=True)
        row.prop(kitsune_ui, "view_mode", expand=True)
        
        # チャットモードのUI
        if kitsune_ui.view_mode == 'CHAT' or kitsune_ui.view_mode == 'CODE':
            # チャットセッション管理
            row = layout.row()
            row.template_list("KITSUNE_UL_chat_sessions", "", kitsune_ui, "chat_sessions", 
                            kitsune_ui, "active_session_index", rows=2)
            
            col = row.column(align=True)
            col.operator("kitsune.new_chat", icon='ADD', text="")
            col.operator("kitsune.delete_chat", icon='REMOVE', text="")
            
            # メッセージ表示エリア - 高さを拡張
            box = layout.box()
            box.scale_y = panel_height / 100  # スケール調整
            
            # ここにメッセージを表示（実際にはスクリプトで処理）
            box.label(text="メッセージ履歴がここに表示されます")
            
            # スクロールボタン
            row = layout.row(align=True)
            row.operator("kitsune.scroll_chat", text="↑").direction = 'UP'
            row.operator("kitsune.scroll_chat", text="↓").direction = 'DOWN'
            
            # ファイル添付ボタンと入力フィールド
            box = layout.box()
            row = box.row(align=True)
            
            # 添付ファイル関連
            if kitsune_ui.attachment_path:
                row.label(text=f"添付ファイル: {kitsune_ui.attachment_path.split('/')[-1]}")
                row.operator("kitsune.clear_attachment", text="", icon='X')
            else:
                row.operator("kitsune.attach_file", text="", icon='FILE')
                row.operator("kitsune.attach_image", text="", icon='IMAGE')
            
            # 入力フィールドと送信ボタン
            row = layout.row()
            row.prop(kitsune_ui, "input_text", text="")
            row.operator("kitsune.send_message", text="Send", icon='EXPORT')
        
        # 設定モードのUI
        elif kitsune_ui.view_mode == 'SETTINGS':
            # 設定タブは子パネルで実装
            pass

# 画像添付オペレータ
class KITSUNE_OT_attach_image(bpy.types.Operator):
    """画像ファイルを添付します"""
    bl_idname = "kitsune.attach_image"
    bl_label = "Attach Image"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    filepath: StringProperty(
        name="File Path",
        description="添付する画像ファイルのパス",
        subtype='FILE_PATH'
    )
    
    def execute(self, context):
        utils.log_debug(f"画像を添付します: {self.filepath}")
        context.scene.kitsune_ui.attachment_path = self.filepath
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# 表示モード切り替え
class KITSUNE_OT_toggle_view_mode(bpy.types.Operator):
    """表示モードを切り替えます"""
    bl_idname = "kitsune.toggle_view_mode"
    bl_label = "Toggle View Mode"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    def execute(self, context):
        kitsune_ui = context.scene.kitsune_ui
        modes = ['CHAT', 'CODE', 'SETTINGS']
        current_index = modes.index(kitsune_ui.view_mode)
        next_index = (current_index + 1) % len(modes)
        kitsune_ui.view_mode = modes[next_index]
        return {'FINISHED'}

# チャットスクロール
class KITSUNE_OT_scroll_chat(bpy.types.Operator):
    """チャット履歴をスクロールします"""
    bl_idname = "kitsune.scroll_chat"
    bl_label = "Scroll Chat"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    direction: EnumProperty(
        name="Direction",
        items=[('UP', "Up", "上にスクロール"), ('DOWN', "Down", "下にスクロール")],
        default='DOWN'
    )
    
    def execute(self, context):
        utils.log_debug(f"チャットを{self.direction}方向にスクロールします")
        return {'FINISHED'}

# 新規チャット
class KITSUNE_OT_new_chat(bpy.types.Operator):
    """新しいチャットセッションを作成します"""
    bl_idname = "kitsune.new_chat"
    bl_label = "New Chat"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    def execute(self, context):
        utils.log_debug("新しいチャットセッションを作成します")
        return {'FINISHED'}

# チャット削除
class KITSUNE_OT_delete_chat(bpy.types.Operator):
    """選択されたチャットセッションを削除します"""
    bl_idname = "kitsune.delete_chat"
    bl_label = "Delete Chat"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    confirm: BoolProperty(
        name="Confirm",
        description="削除を確認",
        default=False
    )
    
    def execute(self, context):
        if self.confirm:
            utils.log_debug("チャットセッションを削除します")
            return {'FINISHED'}
        return {'CANCELLED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="このチャットセッションを削除しますか？")
        layout.prop(self, "confirm", text="確認")

# ファイル添付
class KITSUNE_OT_attach_file(bpy.types.Operator):
    """ファイルを添付します"""
    bl_idname = "kitsune.attach_file"
    bl_label = "Attach File"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    filepath: StringProperty(
        name="File Path",
        description="添付するファイルのパス",
        subtype='FILE_PATH'
    )
    
    def execute(self, context):
        utils.log_debug(f"ファイルを添付します: {self.filepath}")
        context.scene.kitsune_ui.attachment_path = self.filepath
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# 添付ファイルクリア
class KITSUNE_OT_clear_attachment(bpy.types.Operator):
    """添付ファイルをクリアします"""
    bl_idname = "kitsune.clear_attachment"
    bl_label = "Clear Attachment"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    def execute(self, context):
        utils.log_debug("添付ファイルをクリアします")
        context.scene.kitsune_ui.attachment_path = ""
        return {'FINISHED'}

# APIキー検証
class KITSUNE_OT_validate_api_key(bpy.types.Operator):
    """APIキーの有効性を検証します"""
    bl_idname = "kitsune.validate_api_key"
    bl_label = "Validate API Key"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    def execute(self, context):
        utils.log_debug("APIキーを検証します")
        
        preferences = context.preferences.addons.get(__package__, None)
        if not preferences:
            self.report({'ERROR'}, "アドオン設定が見つかりません")
            return {'CANCELLED'}
            
        prefs = preferences.preferences
        is_valid, message = prefs.validate_provider_api_key(context)
        
        if is_valid:
            self.report({'INFO'}, f"APIキーは有効です: {message}")
        else:
            self.report({'ERROR'}, f"APIキーエラー: {message}")
            
        return {'FINISHED'}

# コードプレビュー
class KITSUNE_OT_preview_code(bpy.types.Operator):
    """生成されたコードをプレビューします"""
    bl_idname = "kitsune.preview_code"
    bl_label = "Preview Code"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    code: StringProperty(
        name="Code",
        description="プレビューするコード",
        default=""
    )
    
    def execute(self, context):
        utils.log_debug("コードをプレビューします")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=600)
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="生成されたコード:")
        layout.separator()
        
        # コードを表示するテキストエリア
        for line in self.code.split('\n'):
            layout.label(text=line)

# コード実行
class KITSUNE_OT_execute_code(bpy.types.Operator):
    """生成されたコードを実行します"""
    bl_idname = "kitsune.execute_code"
    bl_label = "Execute Code"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    code: StringProperty(
        name="Code",
        description="実行するコード",
        default=""
    )
    
    def execute(self, context):
        utils.log_debug("コードを実行します")
        try:
            exec(self.code)
            self.report({'INFO'}, "コードが正常に実行されました")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"コード実行エラー: {str(e)}")
            return {'CANCELLED'}

# コードキャンセル
class KITSUNE_OT_cancel_code(bpy.types.Operator):
    """コード実行をキャンセルします"""
    bl_idname = "kitsune.cancel_code"
    bl_label = "Cancel Code"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    def execute(self, context):
        utils.log_debug("コード実行をキャンセルしました")
        return {'FINISHED'}

# メッセージ送信
class KITSUNE_OT_send_message(bpy.types.Operator):
    """メッセージを送信します"""
    bl_idname = "kitsune.send_message"
    bl_label = "Send Message"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    def execute(self, context):
        kitsune_ui = context.scene.kitsune_ui
        message = kitsune_ui.input_text
        
        if not message.strip():
            self.report({'WARNING'}, "メッセージを入力してください")
            return {'CANCELLED'}
        
        utils.log_debug(f"メッセージを送信します: {message}")
        # メッセージ送信処理
        
        # 添付ファイルの処理
        if kitsune_ui.attachment_path:
            utils.log_debug(f"添付ファイル付きで送信: {kitsune_ui.attachment_path}")
            # 添付ファイル処理コード
            
            # 送信後にパスをクリア
            kitsune_ui.attachment_path = ""
        
        # 入力フィールドをクリア
        kitsune_ui.input_text = ""
        
        return {'FINISHED'}

# チャットクリア
class KITSUNE_OT_clear_chat(bpy.types.Operator):
    """チャット履歴をクリアします"""
    bl_idname = "kitsune.clear_chat"
    bl_label = "Clear Chat"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    confirm: BoolProperty(
        name="Confirm",
        description="クリアを確認",
        default=False
    )
    
    def execute(self, context):
        if self.confirm:
            utils.log_debug("チャット履歴をクリアします")
            return {'FINISHED'}
        return {'CANCELLED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="チャット履歴をクリアしますか？")
        layout.prop(self, "confirm", text="確認")

# Classes to register
classes = (
    KitsuneAttachment,
    KitsuneChatMessage,
    KitsuneChatSession,
    KitsuneUIProperties,
    KITSUNE_UL_chat_sessions,
    KITSUNE_PT_chat_panel,
    KITSUNE_PT_api_settings,
    KITSUNE_PT_chat_settings,
    KITSUNE_OT_toggle_view_mode,
    KITSUNE_OT_scroll_chat,
    KITSUNE_OT_new_chat,
    KITSUNE_OT_delete_chat,
    KITSUNE_OT_attach_file,
    KITSUNE_OT_attach_image,
    KITSUNE_OT_clear_attachment,
    KITSUNE_OT_validate_api_key,
    KITSUNE_OT_preview_code,
    KITSUNE_OT_execute_code,
    KITSUNE_OT_cancel_code,
    KITSUNE_OT_send_message,
    KITSUNE_OT_clear_chat
)

def register():
    """Register UI classes."""
    # 既に登録されているクラスを確認してアンレジスターする
    # これにより、「already registered」エラーを回避
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
            utils.log_error(f"Failed to register class {cls.__name__}: {str(e)}")
    
    # Register properties on the scene
    try:
        bpy.types.Scene.kitsune_ui = PointerProperty(type=KitsuneUIProperties)
    except Exception as e:
        utils.log_error(f"Failed to register kitsune_ui property: {str(e)}")

def unregister():
    """Unregister UI classes."""
    # Remove properties from the scene
    try:
        del bpy.types.Scene.kitsune_ui
    except Exception as e:
        utils.log_error(f"Failed to unregister kitsune_ui property: {str(e)}")
    
    # Unregister classes in reverse order
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception as e:
            utils.log_error(f"Failed to unregister class {cls.__name__}: {str(e)}")