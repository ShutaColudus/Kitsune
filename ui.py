# User interface components for Kitsune
import bpy
from bpy.props import (
    StringProperty,
    BoolProperty,
    CollectionProperty,
    IntProperty,
    PointerProperty
)
from bpy.types import (
    Panel,
    Operator,
    PropertyGroup,
    UIList
)
import json
import time
from . import utils
from .api import (
    APIRequestThread,
    format_code_for_execution,
    create_context_info
)
from .preferences import get_active_provider

# Define a property group to store chat messages
class KitsuneChatMessage(PropertyGroup):
    """Properties for a single chat message."""
    
    message: StringProperty(
        name="Message",
        description="The message content",
        default=""
    )
    
    is_user: BoolProperty(
        name="Is User",
        description="Whether this message was sent by the user",
        default=False
    )
    
    timestamp: StringProperty(
        name="Timestamp",
        description="When the message was sent",
        default=""
    )
    
    has_code: BoolProperty(
        name="Has Code",
        description="Whether this message contains executable code",
        default=False
    )
    
    code: StringProperty(
        name="Code",
        description="Extracted code from the message",
        default=""
    )

# Stored UI state for persistence
class KitsuneUIProperties(PropertyGroup):
    """Properties for the Kitsune UI state."""
    
    # Chat input
    chat_input: StringProperty(
        name="Chat Input",
        description="User input for the chat",
        default=""
    )
    
    # Messages collection
    messages: CollectionProperty(
        name="Messages",
        description="Chat message history",
        type=KitsuneChatMessage
    )
    
    # Current message index for UI list
    active_message_index: IntProperty(
        name="Active Message Index",
        default=0
    )
    
    # Pending request flag
    is_processing: BoolProperty(
        name="Is Processing",
        description="Whether a request is currently being processed",
        default=False
    )
    
    # Code execution state
    has_pending_code: BoolProperty(
        name="Has Pending Code",
        description="Whether there is code pending execution",
        default=False
    )
    
    pending_code: StringProperty(
        name="Pending Code",
        description="Code that can be executed",
        default=""
    )

# Chat panel
class KITSUNE_PT_chat_panel(Panel):
    """Kitsune Chat Panel in the 3D View sidebar."""
    
    bl_label = "Kitsune AI Assistant"
    bl_idname = "KITSUNE_PT_chat_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Kitsune'
    
    def draw(self, context):
        layout = self.layout
        ui_props = context.scene.kitsune_ui
        
        # Provider info
        provider_row = layout.row()
        preferences = context.preferences.addons["kitsune"].preferences
        provider_name = preferences.api_provider.capitalize()
        model_attr = f"{preferences.api_provider}_model"
        model_name = getattr(preferences, model_attr, "Unknown").split('/')[-1]
        
        provider_row.label(text=f"Provider: {provider_name} - {model_name}")
        
        # Show message history
        history_box = layout.box()
        history_box.label(text="Conversation History:")
        
        if not ui_props.messages:
            history_box.label(text="No messages yet. Type something to begin.")
        else:
            # Scrollable message list
            message_col = history_box.column()
            message_col.scale_y = 0.7
            
            for idx, msg in enumerate(ui_props.messages):
                message_box = message_col.box()
                header_row = message_box.row()
                
                # Icon and sender
                if msg.is_user:
                    header_row.label(text="You:", icon='USER')
                else:
                    header_row.label(text="Kitsune:", icon='BLENDER')
                
                # Timestamp on the right if enabled
                if preferences.show_timestamps and msg.timestamp:
                    header_row.label(text=msg.timestamp)
                
                # Message content
                content_col = message_box.column()
                content_col.scale_y = 0.7
                
                for line in msg.message.split('\n'):
                    if line.strip():
                        content_col.label(text=line)
                
                # If there's code in the AI message, show execute button
                if not msg.is_user and msg.has_code:
                    code_row = message_box.row()
                    code_row.operator("kitsune.preview_code", text="Preview Code").message_index = idx
        
        # Clear history button
        if ui_props.messages:
            history_box.operator("kitsune.clear_chat", text="Clear Conversation")
        
        # Code execution UI
        if ui_props.has_pending_code:
            code_box = layout.box()
            code_box.label(text="Generated Code:", icon='SCRIPT')
            
            # Display code with scrolling
            code_col = code_box.column()
            code_col.scale_y = 0.7
            
            # Split code into lines for display
            for line in ui_props.pending_code.split('\n'):
                code_col.label(text=line)
            
            # Action buttons
            button_row = code_box.row()
            button_row.operator("kitsune.execute_code", text="Execute Code", icon='PLAY')
            button_row.operator("kitsune.cancel_code", text="Cancel", icon='X')
        
        # Display processing indicator
        if ui_props.is_processing:
            layout.label(text="Processing request...", icon='SORTTIME')
        
        # Input area
        input_box = layout.box()
        input_box.label(text="Ask Kitsune:", icon='TEXT')
        
        input_col = input_box.column()
        input_col.prop(ui_props, "chat_input", text="")
        
        # Send button
        input_col.operator("kitsune.send_message", text="Send", icon='EXPORT')
        input_col.enabled = not ui_props.is_processing

# Preview code operator
class KITSUNE_OT_preview_code(Operator):
    """Preview the code from a message for execution."""
    
    bl_idname = "kitsune.preview_code"
    bl_label = "Preview Code"
    bl_description = "Preview the code from this message for execution"
    
    message_index: IntProperty(
        name="Message Index",
        description="Index of the message containing the code",
        default=0
    )
    
    def execute(self, context):
        ui_props = context.scene.kitsune_ui
        
        # Validate message index
        if self.message_index < 0 or self.message_index >= len(ui_props.messages):
            self.report({'ERROR'}, "Invalid message index")
            return {'CANCELLED'}
        
        # Get the message and set the pending code
        message = ui_props.messages[self.message_index]
        if not message.has_code or not message.code:
            self.report({'WARNING'}, "No executable code found in the message")
            return {'CANCELLED'}
        
        ui_props.pending_code = message.code
        ui_props.has_pending_code = True
        
        return {'FINISHED'}

# Execute code operator
class KITSUNE_OT_execute_code(Operator):
    """Execute the pending code."""
    
    bl_idname = "kitsune.execute_code"
    bl_label = "Execute Code"
    bl_description = "Execute the generated code"
    
    def execute(self, context):
        ui_props = context.scene.kitsune_ui
        
        if not ui_props.has_pending_code or not ui_props.pending_code:
            self.report({'ERROR'}, "No code to execute")
            return {'CANCELLED'}
        
        # Execute the code
        code = ui_props.pending_code
        success, result = utils.safe_execute_code(code)
        
        if success:
            self.report({'INFO'}, "Code executed successfully")
            ui_props.has_pending_code = False
            ui_props.pending_code = ""
        else:
            self.report({'ERROR'}, f"Error executing code: {result}")
        
        return {'FINISHED'}
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="実行しますか？")
        # コードプレビュー
        code_box = layout.box()
        code_box.label(text="コード:")
        for line in context.scene.kitsune_ui.pending_code.split('\n')[:10]:  # 最初の10行のみ表示
            code_box.label(text=line)
        if len(context.scene.kitsune_ui.pending_code.split('\n')) > 10:
            code_box.label(text="...")
    
    def invoke(self, context, event):
        preferences = context.preferences.addons["kitsune"].preferences
        if preferences.confirm_code_execution:
            return context.window_manager.invoke_props_dialog(self, width=600)
        return self.execute(context)

# Cancel code execution operator
class KITSUNE_OT_cancel_code(Operator):
    """Cancel pending code execution."""
    
    bl_idname = "kitsune.cancel_code"
    bl_label = "Cancel Code Execution"
    bl_description = "Cancel the pending code execution"
    
    def execute(self, context):
        ui_props = context.scene.kitsune_ui
        ui_props.has_pending_code = False
        ui_props.pending_code = ""
        self.report({'INFO'}, "Code execution cancelled")
        return {'FINISHED'}

# Send message operator
class KITSUNE_OT_send_message(Operator):
    """Send a message to the AI."""
    
    bl_idname = "kitsune.send_message"
    bl_label = "Send Message"
    bl_description = "Send your message to Kitsune"
    
    def execute(self, context):
        ui_props = context.scene.kitsune_ui
        
        # Get message from input field
        message = ui_props.chat_input.strip()
        
        if not message:
            self.report({'WARNING'}, "Please enter a message")
            return {'CANCELLED'}
        
        # Check if AI provider and key are set
        preferences = context.preferences.addons["kitsune"].preferences
        provider = get_active_provider()
        
        if not provider:
            self.report({'ERROR'}, f"Failed to initialize provider: {preferences.api_provider}")
            return {'CANCELLED'}
        
        # Validate API key
        is_valid, validation_message = preferences.validate_provider_api_key()
        if not is_valid:
            self.report({'ERROR'}, validation_message)
            return {'CANCELLED'}
        
        # Add user message to chat
        self.add_message(context, message, is_user=True)
        
        # Clear input field
        ui_props.chat_input = ""
        
        # Set processing flag
        ui_props.is_processing = True
        
        # Get context information from Blender
        context_info = create_context_info()
        
        # Start a thread to send the request
        thread = APIRequestThread(
            provider=provider,
            prompt=message,
            context_info=context_info,
            callback=self.handle_response
        )
        thread.start()
        
        return {'FINISHED'}
    
    def add_message(self, context, message_text, is_user=False):
        """Add a message to the chat history."""
        ui_props = context.scene.kitsune_ui
        
        # Create new message
        message = ui_props.messages.add()
        message.message = message_text
        message.is_user = is_user
        message.timestamp = utils.format_timestamp()
        
        # Auto-scroll to new message if enabled
        preferences = context.preferences.addons["kitsune"].preferences
        if preferences.auto_scroll:
            ui_props.active_message_index = len(ui_props.messages) - 1
        
        # Limit conversation length if configured
        max_length = preferences.max_conversation_length
        if max_length > 0 and len(ui_props.messages) > max_length:
            # Remove oldest messages
            excess = len(ui_props.messages) - max_length
            for _ in range(excess):
                ui_props.messages.remove(0)
                ui_props.active_message_index = max(0, ui_props.active_message_index - 1)
    
    def handle_response(self, result):
        """Handle the API response."""
        # This runs in the main thread via timer callback
        if bpy.context is None:
            return
            
        ui_props = bpy.context.scene.kitsune_ui
        
        # Clear processing flag
        ui_props.is_processing = False
        
        if "error" in result:
            # Show error as a system message
            error_message = f"Error: {result['error']}"
            self.add_message(bpy.context, error_message, is_user=False)
            utils.log_error(error_message)
            return
            
        if "response" in result:
            response_text = result["response"]
            
            # Add message to chat
            message = ui_props.messages.add()
            message.message = response_text
            message.is_user = False
            message.timestamp = utils.format_timestamp()
            
            # Extract code from response if present
            extracted_code = format_code_for_execution(response_text)
            if extracted_code:
                message.has_code = True
                message.code = extracted_code

# Clear chat operator
class KITSUNE_OT_clear_chat(Operator):
    """Clear the chat history."""
    
    bl_idname = "kitsune.clear_chat"
    bl_label = "Clear Chat"
    bl_description = "Clear the conversation history"
    
    def execute(self, context):
        ui_props = context.scene.kitsune_ui
        
        # Clear all messages
        ui_props.messages.clear()
        ui_props.active_message_index = 0
        
        # Clear any pending code
        ui_props.has_pending_code = False
        ui_props.pending_code = ""
        
        self.report({'INFO'}, "Conversation cleared")
        return {'FINISHED'}
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="会話履歴を消去しますか？")
        layout.label(text="この操作は取り消せません。")
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

# チャットを開始するボタンを表示するパネル
class KITSUNE_PT_chat_launcher(Panel):
    """Kitsune Chat Launcher Panel in the 3D View sidebar."""
    
    bl_label = "Kitsune Chat"
    bl_idname = "KITSUNE_PT_chat_launcher"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Kitsune'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        layout.operator("kitsune.start_chat", text="チャットを開始", icon='OUTLINER_OB_FONT')

# チャットモーダルを起動するオペレーター
class KITSUNE_OT_start_chat(Operator):
    """Start a chat session with Kitsune."""
    
    bl_idname = "kitsune.start_chat"
    bl_label = "Start Chat"
    bl_description = "Open a chat dialog with Kitsune"
    
    chat_input: StringProperty(
        name="Message",
        description="Type your message here"
    )
    
    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=500)
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="Kitsuneとチャット")
        
        # メッセージ入力欄
        layout.prop(self, "chat_input")
        
        # サイドバーへの誘導
        info_box = layout.box()
        info_box.label(text="サイドバーの'Kitsune'タブで")
        info_box.label(text="より詳細なチャット機能をご利用いただけます")

# Classes to register
classes = (
    KitsuneChatMessage,
    KitsuneUIProperties,
    KITSUNE_PT_chat_panel,
    KITSUNE_PT_chat_launcher,
    KITSUNE_OT_preview_code,
    KITSUNE_OT_execute_code,
    KITSUNE_OT_cancel_code,
    KITSUNE_OT_send_message,
    KITSUNE_OT_start_chat,
    KITSUNE_OT_clear_chat
)

def register():
    """Register UI classes."""
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Register properties on the scene
    bpy.types.Scene.kitsune_ui = PointerProperty(type=KitsuneUIProperties)

def unregister():
    """Unregister UI classes."""
    # Remove properties from the scene
    del bpy.types.Scene.kitsune_ui
    
    # Unregister classes in reverse order
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)