import bpy
import datetime
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty, PointerProperty, CollectionProperty, FloatProperty
from . import utils
from .api import get_provider_instance, create_context_info, APIRequestThread

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
    # スクロール位置
    scroll_position: IntProperty(
        name="Scroll Position",
        description="チャット履歴のスクロール位置",
        default=0
    )

# チャットメッセージ描画関数
def draw_chat_message(layout, message, addon_prefs):
    """チャットメッセージを描画する"""
    
    is_user = message.sender == "USER"
    
    # メッセージボックス
    box = layout.box()
    box.scale_y = 0.9  # メッセージのスケール調整
    
    # ヘッダー（送信者と時間）
    row = box.row()
    
    if is_user:
        row.label(text="あなた", icon='USER')
    else:
        row.label(text="AI", icon='LIGHT')
        
    if addon_prefs.show_timestamps and message.timestamp:
        row.label(text=message.timestamp)
    
    # メッセージコンテンツ
    content_box = box.column()
    content_box.scale_y = 0.9
    
    # メッセージのテキスト（行ごとに表示）
    for line in message.content.split("\n"):
        if line.strip():  # 空行をスキップ
            content_box.label(text=line)
        else:
            content_box.separator()
    
    # 添付ファイルがある場合
    if len(message.attachments) > 0:
        box.separator()
        attachment_box = box.box()
        attachment_box.label(text="添付ファイル:", icon='FILE')
        
        for attachment in message.attachments:
            row = attachment_box.row()
            row.label(text=attachment.name)
    
    # AIからのコードがある場合
    if not is_user and message.code:
        code_box = box.box()
        code_box.label(text="生成されたコード:", icon='SCRIPT')
        
        code_col = code_box.column()
        code_col.scale_y = 0.85
        
        # コードを表示
        for line in message.code.split("\n"):
            code_col.label(text=line)
        
        # コード操作ボタン
        row = code_box.row(align=True)
        copy_op = row.operator("kitsune.copy_code", text="コピー", icon='COPYDOWN')
        copy_op.code = message.code
        
        preview_op = row.operator("kitsune.preview_code", text="プレビュー", icon='HIDE_OFF')
        preview_op.code = message.code
        
        execute_op = row.operator("kitsune.execute_code", text="実行", icon='PLAY')
        execute_op.code = message.code

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
        
        # 表示モード切り替え
        row = layout.row(align=True)
        row.prop(kitsune_ui, "view_mode", expand=True)
        
        # チャットモードのUI
        if kitsune_ui.view_mode == 'CHAT':
            # パネルの高さを設定（領域の下部までいっぱいに表示）
            region_height = context.region.height
            panel_height = int(region_height * kitsune_ui.panel_height)
            
            # チャットセッション管理
            row = layout.row(align=True)
            row.scale_y = 1.2
            
            # 新規チャットボタン
            new_chat_op = row.operator("kitsune.new_chat", text="新規チャット", icon='ADD')
            
            if len(kitsune_ui.chat_sessions) > 0:
                # セッション名を表示（ドロップダウンメニューのように）
                if kitsune_ui.active_session_index < len(kitsune_ui.chat_sessions):
                    active_session = kitsune_ui.chat_sessions[kitsune_ui.active_session_index]
                    row.label(text=active_session.name, icon='TEXT')
                    
                # セッション切り替えと削除ボタン
                sub_row = row.row(align=True)
                sub_row.scale_x = 0.6
                op = sub_row.operator("kitsune.rename_chat", text="", icon='GREASEPENCIL')
                op.chat_index = kitsune_ui.active_session_index
                sub_row.operator("kitsune.delete_chat", text="", icon='X')
            
            # メッセージ表示エリア - Claudeのようなシンプルなデザインに
            chat_box = layout.box()
            chat_box.scale_y = panel_height / 200  # スケール調整
            
            # メッセージを表示
            if kitsune_ui.active_session_index < len(kitsune_ui.chat_sessions):
                active_session = kitsune_ui.chat_sessions[kitsune_ui.active_session_index]
                messages = active_session.messages
                
                # メッセージがなければプレースホルダーを表示
                if len(messages) == 0:
                    placeholder = chat_box.column(align=True)
                    placeholder.alignment = 'CENTER'
                    placeholder.label(text="Kitsune AI Assistant")
                    placeholder.label(text="なにかご質問がありますか？")
                    placeholder.separator()
                else:
                    # メッセージがあればそれらを表示
                    # スクロール位置に応じて表示メッセージを制限
                    addon_prefs = context.preferences.addons[__package__].preferences
                    scroll_pos = kitsune_ui.scroll_position
                    
                    # 表示するメッセージを選択
                    visible_messages = messages
                    if len(messages) > 5:  # ビューポートに入る数に制限
                        start_idx = max(0, min(scroll_pos, len(messages) - 5))
                        visible_messages = messages[start_idx:start_idx+5]
                    
                    message_col = chat_box.column(align=True)
                    for msg in visible_messages:
                        draw_chat_message(message_col, msg, addon_prefs)
                        message_col.separator(factor=0.5)
                    
                    # スクロールボタン（メッセージが多い場合）
                    if len(messages) > 5:
                        scroll_row = layout.row(align=True)
                        scroll_row.scale_y = 0.8
                        scroll_up = scroll_row.operator("kitsune.scroll_chat", text="↑")
                        scroll_up.direction = 'UP'
                        scroll_down = scroll_row.operator("kitsune.scroll_chat", text="↓")
                        scroll_down.direction = 'DOWN'
            
            # 処理中表示
            if kitsune_ui.is_processing:
                processing_row = layout.row()
                processing_row.alignment = 'CENTER'
                processing_row.label(text="AI処理中...", icon='SORTTIME')
            
            # ファイル添付と入力フィールド
            input_box = layout.column(align=True)
            
            # 添付ファイル関連（画像のみなら画像アイコンのみ表示）
            attach_row = input_box.row(align=True)
            attach_row.scale_y = 1.1
            attach_row.scale_x = 0.9
            
            if kitsune_ui.attachment_path:
                file_name = kitsune_ui.attachment_path.split('/')[-1]
                attach_row.label(text=file_name, icon='FILE_TICK')
                attach_row.operator("kitsune.clear_attachment", text="", icon='X')
            else:
                attach_row.operator("kitsune.attach_image", text="", icon='IMAGE_DATA')
            
            # 入力フィールドと送信ボタン
            input_row = input_box.row(align=True)
            input_row.scale_y = 1.2
            
            # テキスト入力フィールド (拡大)
            input_field = input_row.column()
            input_field.prop(kitsune_ui, "input_text", text="")
            
            # 送信ボタン
            send_btn = input_row.operator("kitsune.send_message", text="", icon='EXPORT')
            
            # プレスホルダーテキスト
            if not kitsune_ui.input_text.strip():
                placeholder_text = "メッセージを入力..."
                input_box.label(text=placeholder_text, icon='GHOST')
        
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
        modes = ['CHAT', 'SETTINGS']
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
        kitsune_ui = context.scene.kitsune_ui
        
        if self.direction == 'UP':
            kitsune_ui.scroll_position = max(0, kitsune_ui.scroll_position - 1)
        else:
            active_session = kitsune_ui.chat_sessions[kitsune_ui.active_session_index]
            max_scroll = max(0, len(active_session.messages) - 5)
            kitsune_ui.scroll_position = min(max_scroll, kitsune_ui.scroll_position + 1)
            
        utils.log_debug(f"チャットを{self.direction}方向にスクロールしました。位置: {kitsune_ui.scroll_position}")
        return {'FINISHED'}

# 新規チャット
class KITSUNE_OT_new_chat(bpy.types.Operator):
    """新しいチャットセッションを作成します"""
    bl_idname = "kitsune.new_chat"
    bl_label = "New Chat"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    def execute(self, context):
        kitsune_ui = context.scene.kitsune_ui
        
        # 新しいセッションを作成
        new_session = kitsune_ui.chat_sessions.add()
        new_session.name = f"新規チャット {len(kitsune_ui.chat_sessions)}"
        
        # タイムスタンプを設定
        now = datetime.datetime.now()
        new_session.created_at = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # 新しいセッションをアクティブに
        kitsune_ui.active_session_index = len(kitsune_ui.chat_sessions) - 1
        
        utils.log_debug(f"新しいチャットセッションを作成しました: {new_session.name}")
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
            kitsune_ui = context.scene.kitsune_ui
            index = kitsune_ui.active_session_index
            
            if index >= 0 and index < len(kitsune_ui.chat_sessions):
                session_name = kitsune_ui.chat_sessions[index].name
                kitsune_ui.chat_sessions.remove(index)
                
                # インデックスが範囲外にならないように調整
                if len(kitsune_ui.chat_sessions) > 0:
                    kitsune_ui.active_session_index = min(index, len(kitsune_ui.chat_sessions) - 1)
                else:
                    kitsune_ui.active_session_index = 0
                
                utils.log_debug(f"チャットセッションを削除しました: {session_name}")
                return {'FINISHED'}
        return {'CANCELLED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="このチャットセッションを削除しますか？")
        layout.prop(self, "confirm", text="確認")

# チャットセッションの名前を変更
class KITSUNE_OT_rename_chat(bpy.types.Operator):
    """チャットセッションの名前を変更します"""
    bl_idname = "kitsune.rename_chat"
    bl_label = "Rename Chat"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    chat_index: IntProperty(
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
        kitsune_ui = context.scene.kitsune_ui
        
        if self.chat_index >= 0 and self.chat_index < len(kitsune_ui.chat_sessions):
            old_name = kitsune_ui.chat_sessions[self.chat_index].name
            kitsune_ui.chat_sessions[self.chat_index].name = self.new_name
            utils.log_debug(f"チャット名を変更しました: {old_name} → {self.new_name}")
            return {'FINISHED'}
            
        return {'CANCELLED'}
    
    def invoke(self, context, event):
        kitsune_ui = context.scene.kitsune_ui
        
        if self.chat_index >= 0 and self.chat_index < len(kitsune_ui.chat_sessions):
            self.new_name = kitsune_ui.chat_sessions[self.chat_index].name
            
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "new_name")

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
        message_text = kitsune_ui.input_text.strip()
        
        if not message_text:
            self.report({'WARNING'}, "メッセージを入力してください")
            return {'CANCELLED'}
        
        # すでに処理中なら何もしない
        if kitsune_ui.is_processing:
            self.report({'WARNING'}, "AIが処理中です。しばらくお待ちください")
            return {'CANCELLED'}
        
        # アクティブなセッションを取得または作成
        if len(kitsune_ui.chat_sessions) == 0:
            bpy.ops.kitsune.new_chat()
        
        active_session = kitsune_ui.chat_sessions[kitsune_ui.active_session_index]
        
        # ユーザーメッセージを作成
        now = datetime.datetime.now()
        timestamp = now.strftime("%H:%M")
        
        user_message = active_session.messages.add()
        user_message.content = message_text
        user_message.sender = "USER"
        user_message.timestamp = timestamp
        
        # 添付ファイルがあれば追加
        if kitsune_ui.attachment_path:
            attachment = user_message.attachments.add()
            attachment.path = kitsune_ui.attachment_path
            attachment.name = kitsune_ui.attachment_path.split('/')[-1]
            
            # ファイルタイプの検出（簡易版）
            file_ext = attachment.name.split('.')[-1].lower() if '.' in attachment.name else ''
            if file_ext in ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tga']:
                attachment.type = "IMAGE"
            else:
                attachment.type = "FILE"
                
            # 添付ファイルパスをクリア
            kitsune_ui.attachment_path = ""
        
        # 入力フィールドをクリア
        kitsune_ui.input_text = ""
        
        # 処理中フラグを立てる
        kitsune_ui.is_processing = True
        
        # 最新のメッセージにスクロール
        active_session.active_message_index = len(active_session.messages) - 1
        
        # APIプロバイダーを取得してリクエスト送信
        utils.log_debug(f"メッセージを送信します: {message_text}")
        
        try:
            # アドオン設定からプロバイダー取得
            preferences = context.preferences.addons[__package__].preferences
            provider_id = preferences.api_provider
            provider = get_provider_instance(provider_id)
            
            if not provider:
                self.report({'ERROR'}, f"APIプロバイダーの初期化に失敗しました: {provider_id}")
                kitsune_ui.is_processing = False
                return {'CANCELLED'}
            
            # プロバイダーのAPIキーが設定されているか確認
            api_key_attr = f"{provider_id}_api_key"
            api_key = getattr(preferences, api_key_attr, "")
            
            if not api_key:
                self.report({'ERROR'}, f"{provider_id}のAPIキーが設定されていません。設定から追加してください。")
                kitsune_ui.is_processing = False
                return {'CANCELLED'}
            
            # コンテキスト情報の作成
            context_info = create_context_info()
            
            # チャット履歴の追加
            context_info["chat_history"] = []
            for msg in active_session.messages:
                context_info["chat_history"].append({
                    "role": "user" if msg.sender == "USER" else "assistant",
                    "content": msg.content
                })
            
            # APIリクエストのコールバック関数
            def api_response_callback(response):
                try:
                    # 別スレッドからの呼び出しなので、UIの更新はBlenderのメインスレッドで行う
                    def update_ui():
                        try:
                            # AIの応答メッセージを作成
                            ai_message = active_session.messages.add()
                            ai_message.sender = "AI"
                            ai_message.timestamp = datetime.datetime.now().strftime("%H:%M")
                            
                            # エラーチェック
                            if "error" in response:
                                ai_message.content = f"エラーが発生しました: {response['error']}"
                                utils.log_error(f"API応答エラー: {response['error']}")
                            else:
                                ai_message.content = response.get("text", "応答が空です")
                                
                                # コードが含まれていれば抽出
                                from .api import format_code_for_execution
                                code = format_code_for_execution(ai_message.content)
                                if code:
                                    ai_message.code = code
                            
                            # 処理完了フラグを下げる
                            kitsune_ui.is_processing = False
                            
                            # UIの更新を要求
                            for area in bpy.context.screen.areas:
                                if area.type == 'VIEW_3D':
                                    area.tag_redraw()
                                    
                            # 最新のメッセージにスクロール
                            if len(active_session.messages) > 0:
                                active_session.active_message_index = len(active_session.messages) - 1
                            
                            utils.log_debug("APIリクエスト完了、UI更新")
                            return None
                            
                        except Exception as e:
                            utils.log_error(f"UI更新エラー: {str(e)}")
                            kitsune_ui.is_processing = False
                            return None
                    
                    # メインスレッドでUIを更新
                    bpy.app.timers.register(update_ui, first_interval=0.1)
                    
                except Exception as e:
                    utils.log_error(f"コールバックエラー: {str(e)}")
                    kitsune_ui.is_processing = False
            
            # APIリクエストを別スレッドで実行
            request_thread = APIRequestThread(
                provider=provider,
                prompt=message_text,
                context_info=context_info,
                callback=api_response_callback
            )
            request_thread.start()
            
            return {'FINISHED'}
            
        except Exception as e:
            utils.log_error(f"メッセージ送信エラー: {str(e)}")
            self.report({'ERROR'}, f"エラーが発生しました: {str(e)}")
            kitsune_ui.is_processing = False
            return {'CANCELLED'}

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
            kitsune_ui = context.scene.kitsune_ui
            
            if kitsune_ui.active_session_index < len(kitsune_ui.chat_sessions):
                active_session = kitsune_ui.chat_sessions[kitsune_ui.active_session_index]
                active_session.messages.clear()
                utils.log_debug("チャット履歴をクリアしました")
                return {'FINISHED'}
        return {'CANCELLED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="チャット履歴をクリアしますか？")
        layout.prop(self, "confirm", text="確認")

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
    KITSUNE_OT_rename_chat,
    KITSUNE_OT_attach_file,
    KITSUNE_OT_attach_image,
    KITSUNE_OT_clear_attachment,
    KITSUNE_OT_validate_api_key,
    KITSUNE_OT_preview_code,
    KITSUNE_OT_execute_code,
    KITSUNE_OT_cancel_code,
    KITSUNE_OT_send_message,
    KITSUNE_OT_clear_chat,
    KITSUNE_OT_copy_code
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