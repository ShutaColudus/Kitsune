# User interface components for Kitsune
import bpy
from bpy.props import (
    StringProperty,
    BoolProperty,
    CollectionProperty,
    IntProperty,
    PointerProperty,
    EnumProperty,
    FloatVectorProperty
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
    get_provider_instance, 
    format_code_for_execution,
    create_context_info
)
# Fixed import
from .preferences import get_active_provider

# Define a property group to store file attachments
class KitsuneAttachment(PropertyGroup):
    """Properties for a file attachment."""
    
    filepath: StringProperty(
        name="File Path",
        description="Path to the attached file",
        default=""
    )
    
    name: StringProperty(
        name="File Name",
        description="Name of the attached file",
        default=""
    )
    
    thumbnail_id: IntProperty(
        name="Thumbnail ID",
        description="ID of the thumbnail preview",
        default=0
    )

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
    
    # Attachments collection
    attachments: CollectionProperty(
        name="Attachments",
        description="Files attached to this message",
        type=KitsuneAttachment
    )
    
    has_attachments: BoolProperty(
        name="Has Attachments",
        description="Whether this message has file attachments",
        default=False
    )

# Define a property group to store chat sessions
class KitsuneChatSession(PropertyGroup):
    """Properties for a chat session."""
    
    name: StringProperty(
        name="Name",
        description="Name of the chat session",
        default="New Chat"
    )
    
    is_active: BoolProperty(
        name="Is Active",
        description="Whether this chat session is currently active",
        default=False
    )
    
    # Messages collection - Now KitsuneChatMessage is defined before this reference
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
    
    # Scroll position for this chat
    scroll_position: IntProperty(
        name="Scroll Position",
        description="Current scroll position in the chat history",
        default=0
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
    
    # Sessions collection
    chat_sessions: CollectionProperty(
        name="Chat Sessions",
        description="Chat sessions",
        type=KitsuneChatSession
    )
    
    # Active session index
    active_session_index: IntProperty(
        name="Active Session Index",
        description="Index of the active chat session",
        default=0
    )
    
    # Legacy messages support (keeps compatibility with older code)
    messages: CollectionProperty(
        name="Messages",
        description="Chat message history (legacy support)",
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
    
    # Settings visibility 
    show_settings: BoolProperty(
        name="Show Settings",
        description="Whether to show settings panel",
        default=False
    )
    
    # Scroll position
    scroll_position: IntProperty(
        name="Scroll Position",
        description="Current scroll position in the chat history",
        default=0,
        min=0
    )
    
    # View mode enum
    view_mode: EnumProperty(
        name="View Mode",
        description="Current UI view mode",
        items=[
            ('CHAT', "Chat", "Chat interface"),
            ('SETTINGS', "Settings", "Settings interface")
        ],
        default='CHAT'
    )
    
    # Temporary file path for attachments
    temp_attachment_path: StringProperty(
        name="Temporary Attachment",
        description="Path to file being attached",
        default="",
        subtype='FILE_PATH'
    )
    
    # UI theme colors
    user_message_color: FloatVectorProperty(
        name="User Message Color",
        description="Background color for user messages",
        subtype='COLOR',
        size=4,
        default=(0.2, 0.4, 0.8, 0.1),
        min=0.0, max=1.0
    )
    
    ai_message_color: FloatVectorProperty(
        name="AI Message Color",
        description="Background color for AI messages",
        subtype='COLOR',
        size=4,
        default=(0.2, 0.6, 0.2, 0.1),
        min=0.0, max=1.0
    )

# Main chat panel
class KITSUNE_PT_chat_panel(Panel):
    """Kitsune Chat Panel in the 3D View sidebar."""
    
    bl_label = "Kitsune Chat"
    bl_idname = "KITSUNE_PT_chat_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Kitsune'
    
    def draw(self, context):
        try:
            layout = self.layout
            ui_props = context.scene.kitsune_ui
            preferences = context.preferences.addons[__package__].preferences
            
            # Get session data
            if not ui_props.chat_sessions:
                # Create first session if none exist
                new_session = ui_props.chat_sessions.add()
                new_session.name = "New Chat"
                new_session.is_active = True
            
            active_session_idx = ui_props.active_session_index
            if active_session_idx >= len(ui_props.chat_sessions):
                active_session_idx = 0
                ui_props.active_session_index = 0
            
            active_session = ui_props.chat_sessions[active_session_idx]
            
            # Determine which view to display
            if ui_props.view_mode == 'SETTINGS':
                self.draw_settings_view(context, layout, ui_props, preferences)
            else:
                self.draw_chat_view(context, layout, ui_props, preferences, active_session)
        except Exception as e:
            layout = self.layout
            layout.label(text=f"Error: {str(e)}", icon='ERROR')
            from . import utils
            utils.log_error(f"UI draw error: {str(e)}")
    
    def draw_chat_view(self, context, layout, ui_props, preferences, active_session):
        """Draw the chat interface."""
        # Header with AI assistant title and controls
        header_box = layout.box()
        header_row = header_box.row(align=True)
        
        # Provider info
        provider_name = preferences.api_provider.capitalize()
        model_attr = f"{preferences.api_provider}_model"
        model_name = getattr(preferences, model_attr, "Unknown").split('/')[-1]
        
        # Assistant title
        header_row.label(text=f"AI Assistant", icon='BLENDER')
        
        # Control buttons
        header_buttons = header_row.row(align=True)
        header_buttons.alignment = 'RIGHT'
        header_buttons.operator("kitsune.new_chat", text="", icon='ADD')
        
        # Settings/chat toggle button
        if ui_props.view_mode == 'CHAT':
            settings_op = header_buttons.operator("kitsune.toggle_view_mode", text="", icon='PREFERENCES')
            settings_op.mode = 'SETTINGS'
        else:
            chat_op = header_buttons.operator("kitsune.toggle_view_mode", text="", icon='BACK')
            chat_op.mode = 'CHAT'
        
        # Session selection if multiple sessions exist
        if len(ui_props.chat_sessions) > 1:
            sessions_row = layout.row()
            sessions_row.template_list(
                "KITSUNE_UL_chat_sessions", 
                "", 
                ui_props, 
                "chat_sessions", 
                ui_props, 
                "active_session_index",
                rows=1
            )
        
        # Chat message container
        chat_box = layout.box()
        
        # Get messages from active session for backward compatibility
        messages = active_session.messages if hasattr(active_session, "messages") else ui_props.messages
        
        if not messages:
            chat_box.label(text="No messages yet. Type something to begin.")
        else:
            # Scrollable message list
            message_col = chat_box.column()
            message_col.scale_y = 0.7
            
            # Add some vertical spacing at the top for better appearance
            message_col.separator(factor=0.5)
            
            # Calculate visible message range based on scroll position
            start_idx = min(ui_props.scroll_position, len(messages) - 1)
            # Show at most 15 messages at once for performance
            end_idx = min(start_idx + 15, len(messages))
            
            # Scroll controls if needed
            if len(messages) > 15:
                scroll_row = layout.row(align=True)
                scroll_row.alignment = 'RIGHT'
                
                # Up scroll
                up_op = scroll_row.operator("kitsune.scroll_chat", text="", icon='TRIA_UP')
                up_op.direction = 'UP'
                
                # Down scroll
                down_op = scroll_row.operator("kitsune.scroll_chat", text="", icon='TRIA_DOWN')
                down_op.direction = 'DOWN'
                
                # Scroll to bottom
                bottom_op = scroll_row.operator("kitsune.scroll_chat", text="", icon='TRIA_DOWN_BAR')
                bottom_op.direction = 'BOTTOM'
            
            # Draw visible messages
            for idx in range(start_idx, end_idx):
                msg = messages[idx]
                
                # Different styling based on sender
                if msg.is_user:
                    # User message - right aligned with user styling
                    message_box = message_col.box()
                    message_box.alignment = 'RIGHT'
                    
                    # User message header
                    header_row = message_box.row()
                    header_row.alignment = 'RIGHT'
                    
                    # Add timestamp on the left if enabled
                    if preferences.show_timestamps and msg.timestamp:
                        header_row.label(text=msg.timestamp, icon='SMALL_CAPS')
                    
                    header_row.label(text="You", icon='USER')
                    
                    # Message content with right alignment
                    content_col = message_box.column()
                    content_col.alignment = 'RIGHT'
                    content_col.scale_y = 0.7
                    
                    for line in msg.message.split('\n'):
                        if line.strip():
                            content_col.label(text=line)
                    
                    # Show attachments if any
                    if hasattr(msg, "has_attachments") and msg.has_attachments:
                        self.draw_attachments(message_box, msg)
                else:
                    # AI message - left aligned with AI styling
                    message_box = message_col.box()
                    message_box.alignment = 'LEFT'
                    
                    # AI message header
                    header_row = message_box.row()
                    header_row.alignment = 'LEFT'
                    header_row.label(text="Kitsune", icon='BLENDER')
                    
                    # Add timestamp on the right if enabled
                    if preferences.show_timestamps and msg.timestamp:
                        header_row.label(text=msg.timestamp, icon='SMALL_CAPS')
                    
                    # Message content with left alignment
                    content_col = message_box.column()
                    content_col.alignment = 'LEFT'
                    content_col.scale_y = 0.7
                    
                    in_code_block = False
                    code_lines = []
                    
                    for line in msg.message.split('\n'):
                        # Detect start and end of code blocks
                        if line.strip().startswith('```'):
                            if in_code_block:
                                # End of code block, display collected code
                                in_code_block = False
                                code_box = content_col.box()
                                code_box.scale_y = 0.7
                                for code_line in code_lines:
                                    code_box.label(text=code_line)
                                code_lines = []
                            else:
                                # Start of code block
                                in_code_block = True
                        elif in_code_block:
                            # Collect code lines
                            code_lines.append(line)
                        elif line.strip():
                            # Regular text line
                            content_col.label(text=line)
                    
                    # Handle any remaining code lines
                    if code_lines:
                        code_box = content_col.box()
                        code_box.scale_y = 0.7
                        for code_line in code_lines:
                            code_box.label(text=code_line)
                    
                    # Show attachments if any
                    if hasattr(msg, "has_attachments") and msg.has_attachments:
                        self.draw_attachments(message_box, msg)
                    
                    # If there's code in the AI message, show buttons
                    if msg.has_code:
                        button_row = message_box.row(align=True)
                        button_row.alignment = 'LEFT'
                        
                        # Preview code button
                        preview_op = button_row.operator("kitsune.preview_code", text="Preview", icon='SCRIPT')
                        preview_op.message_index = idx
                        
                        # Copy code button
                        copy_op = button_row.operator("kitsune.copy_code", text="Copy", icon='COPYDOWN')
                        copy_op.message_index = idx
                
                # Add separator between messages for better readability
                message_col.separator(factor=0.5)
        
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
            button_row = code_box.row(align=True)
            button_row.operator("kitsune.execute_code", text="Execute Code", icon='PLAY')
            button_row.operator("kitsune.cancel_code", text="Cancel", icon='X')
        
        # Input area with modern styling
        input_container = layout.box()
        
        # Display processing indicator
        if ui_props.is_processing:
            input_container.label(text="Processing request...", icon='SORTTIME')
        
        # Attachment preview if any
        if ui_props.temp_attachment_path:
            attach_box = input_container.box()
            attach_row = attach_box.row()
            attach_row.label(text=ui_props.temp_attachment_path.split('/')[-1], icon='FILE')
            clear_op = attach_row.operator("kitsune.clear_attachment", text="", icon='X')
        
        # Chat input field
        input_row = input_container.row(align=True)
        input_row.prop(ui_props, "chat_input", text="")
        
        # Action buttons row
        buttons_row = input_container.row(align=True)
        
        # Attachment button
        attach_op = buttons_row.operator("kitsune.attach_file", text="", icon='ATTACH')
        
        # Send button
        send_op = buttons_row.operator("kitsune.send_message", text="Send", icon='EXPORT')
        
        # Clear conversation button
        if messages:
            clear_op = buttons_row.operator("kitsune.clear_chat", text="Clear", icon='TRASH')
        
        # Disable input while processing
        input_container.enabled = not ui_props.is_processing
    
    def draw_settings_view(self, context, layout, ui_props, preferences):
        """Draw the settings interface."""
        # Settings title
        title_row = layout.row()
        title_row.label(text="AI & Model Settings", icon='PREFERENCES')
        
        # Back button
        back_op = title_row.operator("kitsune.toggle_view_mode", text="", icon='BACK')
        back_op.mode = 'CHAT'
        
        # API Provider selection
        provider_box = layout.box()
        provider_box.label(text="AI Provider:", icon='WORLD')
        provider_box.prop(preferences, "api_provider", text="")
        
        # Provider-specific settings
        selected_provider = preferences.api_provider
        
        if selected_provider == 'anthropic':
            model_box = layout.box()
            model_box.label(text="Anthropic Settings:", icon='SETTINGS')
            model_box.prop(preferences, "anthropic_api_key", text="API Key")
            model_box.prop(preferences, "anthropic_model", text="Model")
            
        elif selected_provider == 'google':
            model_box = layout.box()
            model_box.label(text="Google Gemini Settings:", icon='SETTINGS')
            model_box.prop(preferences, "google_api_key", text="API Key")
            model_box.prop(preferences, "google_model", text="Model")
            
        elif selected_provider == 'deepseek':
            model_box = layout.box()
            model_box.label(text="DeepSeek Settings:", icon='SETTINGS')
            model_box.prop(preferences, "deepseek_api_key", text="API Key")
            model_box.prop(preferences, "deepseek_model", text="Model")
            
        elif selected_provider == 'openai':
            model_box = layout.box()
            model_box.label(text="OpenAI Settings:", icon='SETTINGS')
            model_box.prop(preferences, "openai_api_key", text="API Key")
            model_box.prop(preferences, "openai_model", text="Model")
        
        # Other display settings
        display_box = layout.box()
        display_box.label(text="Display Settings:", icon='DISPLAY')
        display_box.prop(preferences, "show_timestamps", text="Show Message Timestamps")
        display_box.prop(preferences, "auto_scroll", text="Auto-scroll to New Messages")
        display_box.prop(preferences, "confirm_code_execution", text="Confirm Code Execution")
        
        # Validate API key button
        validate_row = layout.row()
        validate_row.operator("kitsune.validate_api_key", text="Validate API Key", icon='CHECKMARK')
    
    def draw_attachments(self, layout, message):
        """Draw attachments for a message."""
        if not hasattr(message, "attachments"):
            return
            
        for attachment in message.attachments:
            attach_row = layout.row()
            attach_row.label(text=attachment.name, icon='FILE')
            
            # If we have a thumbnail ID, display it
            if attachment.thumbnail_id > 0:
                attach_row.template_icon(icon_value=attachment.thumbnail_id)

# List of chat sessions
class KITSUNE_UL_chat_sessions(UIList):
    """UI list for chat sessions."""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # Draw each chat session item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.prop(item, "name", text="", emboss=False, icon='CHAT')
            
            # Delete button for each session except if it's the only one
            if len(context.scene.kitsune_ui.chat_sessions) > 1:
                del_op = row.operator("kitsune.delete_chat", text="", icon='X')
                del_op.session_index = index
        
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.prop(item, "name", text="", emboss=False, icon='CHAT')

# Toggle view mode operator
class KITSUNE_OT_toggle_view_mode(Operator):
    """Toggle between chat and settings view."""
    
    bl_idname = "kitsune.toggle_view_mode"
    bl_label = "Toggle View Mode"
    bl_description = "Switch between chat and settings view"
    
    mode: StringProperty(
        name="Mode",
        description="View mode to switch to",
        default='CHAT'
    )
    
    def execute(self, context):
        ui_props = context.scene.kitsune_ui
        ui_props.view_mode = self.mode
        return {'FINISHED'}

# Scroll chat operator
class KITSUNE_OT_scroll_chat(Operator):
    """Scroll chat history."""
    
    bl_idname = "kitsune.scroll_chat"
    bl_label = "Scroll Chat"
    bl_description = "Scroll the chat history"
    
    direction: StringProperty(
        name="Direction",
        description="Scroll direction (UP, DOWN, TOP, BOTTOM)",
        default='DOWN'
    )
    
    def execute(self, context):
        ui_props = context.scene.kitsune_ui
        
        # Get active session
        active_session = ui_props.chat_sessions[ui_props.active_session_index]
        messages = active_session.messages if hasattr(active_session, "messages") else ui_props.messages
        
        # Calculate scroll amount
        if self.direction == 'UP':
            # Scroll up (decrease index)
            ui_props.scroll_position = max(0, ui_props.scroll_position - 5)
        elif self.direction == 'DOWN':
            # Scroll down (increase index)
            ui_props.scroll_position = min(len(messages) - 1, ui_props.scroll_position + 5)
        elif self.direction == 'TOP':
            # Scroll to top
            ui_props.scroll_position = 0
        elif self.direction == 'BOTTOM':
            # Scroll to bottom
            ui_props.scroll_position = max(0, len(messages) - 15)
        
        return {'FINISHED'}

# New chat session operator
class KITSUNE_OT_new_chat(Operator):
    """Create a new chat session."""
    
    bl_idname = "kitsune.new_chat"
    bl_label = "New Chat"
    bl_description = "Start a new chat session"
    
    def execute(self, context):
        ui_props = context.scene.kitsune_ui
        
        # Create new session
        new_session = ui_props.chat_sessions.add()
        new_session.name = f"Chat {len(ui_props.chat_sessions)}"
        new_session.is_active = True
        
        # Make it active
        ui_props.active_session_index = len(ui_props.chat_sessions) - 1
        
        return {'FINISHED'}

# Delete chat session operator
class KITSUNE_OT_delete_chat(Operator):
    """Delete a chat session."""
    
    bl_idname = "kitsune.delete_chat"
    bl_label = "Delete Chat"
    bl_description = "Delete this chat session"
    
    session_index: IntProperty(
        name="Session Index",
        description="Index of the session to delete",
        default=0
    )
    
    def execute(self, context):
        ui_props = context.scene.kitsune_ui
        
        # Don't allow deleting the last session
        if len(ui_props.chat_sessions) <= 1:
            self.report({'WARNING'}, "Cannot delete the only chat session")
            return {'CANCELLED'}
        
        # Remove the session
        ui_props.chat_sessions.remove(self.session_index)
        
        # Adjust active index if needed
        if ui_props.active_session_index >= len(ui_props.chat_sessions):
            ui_props.active_session_index = len(ui_props.chat_sessions) - 1
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

# Attach file operator
class KITSUNE_OT_attach_file(Operator):
    """Attach a file to a message."""
    
    bl_idname = "kitsune.attach_file"
    bl_label = "Attach File"
    bl_description = "Attach a file to your message"
    
    filepath: StringProperty(
        name="File Path",
        description="Path to the file to attach",
        default="",
        subtype='FILE_PATH'
    )
    
    def execute(self, context):
        ui_props = context.scene.kitsune_ui
        
        # Store the file path
        ui_props.temp_attachment_path = self.filepath
        
        self.report({'INFO'}, f"File selected: {self.filepath}")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# Clear attachment operator
class KITSUNE_OT_clear_attachment(Operator):
    """Clear the current attachment."""
    
    bl_idname = "kitsune.clear_attachment"
    bl_label = "Clear Attachment"
    bl_description = "Clear the current file attachment"
    
    def execute(self, context):
        ui_props = context.scene.kitsune_ui
        ui_props.temp_attachment_path = ""
        return {'FINISHED'}

# Validate API key operator
class KITSUNE_OT_validate_api_key(Operator):
    """Validate the current API key."""
    
    bl_idname = "kitsune.validate_api_key"
    bl_label = "Validate API Key"
    bl_description = "Validate the API key for the selected provider"
    
    def execute(self, context):
        try:
            preferences = context.preferences.addons[__package__].preferences
            
            is_valid, message = preferences.validate_provider_api_key()
            
            if is_valid:
                self.report({'INFO'}, f"API key valid: {message}")
            else:
                self.report({'ERROR'}, f"API key invalid: {message}")
            
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            from . import utils
            utils.log_error(f"UI execute error: {str(e)}")
            return {'CANCELLED'}

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
        try:
            ui_props = context.scene.kitsune_ui
            active_session = ui_props.chat_sessions[ui_props.active_session_index]
            messages = active_session.messages if hasattr(active_session, "messages") else ui_props.messages
            
            # Validate message index
            if self.message_index < 0 or self.message_index >= len(messages):
                self.report({'ERROR'}, "Invalid message index")
                return {'CANCELLED'}
            
            # Get the message and set the pending code
            message = messages[self.message_index]
            if not message.has_code or not message.code:
                self.report({'WARNING'}, "No executable code found in the message")
                return {'CANCELLED'}
            
            ui_props.pending_code = message.code
            ui_props.has_pending_code = True
            
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            from . import utils
            utils.log_error(f"UI execute error: {str(e)}")
            return {'CANCELLED'}

# Execute code operator
class KITSUNE_OT_execute_code(Operator):
    """Execute the pending code."""
    
    bl_idname = "kitsune.execute_code"
    bl_label = "Execute Code"
    bl_description = "Execute the generated code"
    
    def execute(self, context):
        try:
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
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            from . import utils
            utils.log_error(f"UI execute error: {str(e)}")
            return {'CANCELLED'}
    
    def draw(self, context):
        try:
            layout = self.layout
            layout.label(text="Execute code?")
            # Code preview
            code_box = layout.box()
            code_box.label(text="Code:")
            for line in context.scene.kitsune_ui.pending_code.split('\n')[:10]:  # Display only first 10 lines
                code_box.label(text=line)
            if len(context.scene.kitsune_ui.pending_code.split('\n')) > 10:
                code_box.label(text="...")
        except Exception as e:
            layout = self.layout
            layout.label(text=f"Error: {str(e)}", icon='ERROR')
            from . import utils
            utils.log_error(f"UI draw error: {str(e)}")
    
    def invoke(self, context, event):
        try:
            preferences = context.preferences.addons[__package__].preferences
            if preferences.confirm_code_execution:
                return context.window_manager.invoke_props_dialog(self, width=600)
            return self.execute(context)
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            from . import utils
            utils.log_error(f"UI invoke error: {str(e)}")
            return {'CANCELLED'}

# Cancel code execution operator
class KITSUNE_OT_cancel_code(Operator):
    """Cancel pending code execution."""
    
    bl_idname = "kitsune.cancel_code"
    bl_label = "Cancel Code Execution"
    bl_description = "Cancel the pending code execution"
    
    def execute(self, context):
        try:
            ui_props = context.scene.kitsune_ui
            ui_props.has_pending_code = False
            ui_props.pending_code = ""
            self.report({'INFO'}, "Code execution cancelled")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            from . import utils
            utils.log_error(f"UI execute error: {str(e)}")
            return {'CANCELLED'}

# Send message operator
class KITSUNE_OT_send_message(Operator):
    """Send a message to the AI."""
    
    bl_idname = "kitsune.send_message"
    bl_label = "Send Message"
    bl_description = "Send your message to Kitsune"
    
    # Added message parameter to support sending from dialog
    message: StringProperty(
        name="Message",
        description="Message to send",
        default=""
    )
    
    def execute(self, context):
        try:
            ui_props = context.scene.kitsune_ui
            
            # Get message from input field or parameter
            message = self.message if self.message else ui_props.chat_input.strip()
            
            if not message:
                self.report({'WARNING'}, "Please enter a message")
                return {'CANCELLED'}
            
            # Check if AI provider and key are set
            preferences = context.preferences.addons[__package__].preferences
            provider = get_active_provider()
            
            if not provider:
                self.report({'ERROR'}, f"Failed to initialize provider: {preferences.api_provider}")
                return {'CANCELLED'}
            
            # Validate API key
            is_valid, validation_message = preferences.validate_provider_api_key()
            if not is_valid:
                self.report({'ERROR'}, validation_message)
                return {'CANCELLED'}
            
            # Get active session
            active_session = ui_props.chat_sessions[ui_props.active_session_index]
            
            # Add user message to chat
            self.add_message(context, message, is_user=True, attachment_path=ui_props.temp_attachment_path)
            
            # Clear input field and attachment
            ui_props.chat_input = ""
            ui_props.temp_attachment_path = ""
            
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
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            from . import utils
            utils.log_error(f"UI execute error: {str(e)}")
            return {'CANCELLED'}
    
    def add_message(self, context, message_text, is_user=False, attachment_path=""):
        """Add a message to the chat history."""
        try:
            ui_props = context.scene.kitsune_ui
            
            # Get active session and its messages
            active_session = ui_props.chat_sessions[ui_props.active_session_index]
            messages = active_session.messages if hasattr(active_session, "messages") and len(active_session.messages) > 0 else ui_props.messages
            
            # Create new message
            message = messages.add()
            message.message = message_text
            message.is_user = is_user
            message.timestamp = utils.format_timestamp()
            
            # Handle attachment if provided
            if attachment_path and hasattr(message, "attachments"):
                attachment = message.attachments.add()
                attachment.filepath = attachment_path
                attachment.name = attachment_path.split('/')[-1]
                message.has_attachments = True
            
            # Auto-scroll to new message if enabled
            preferences = context.preferences.addons[__package__].preferences
            if preferences.auto_scroll:
                # Set scroll position to show the latest message
                ui_props.scroll_position = max(0, len(messages) - 15)
            
            # Limit conversation length if configured
            max_length = preferences.max_conversation_length if hasattr(preferences, "max_conversation_length") else 100
            if max_length > 0 and len(messages) > max_length:
                # Remove oldest messages
                excess = len(messages) - max_length
                for _ in range(excess):
                    messages.remove(0)
        except Exception as e:
            utils.log_error(f"Error adding message: {str(e)}")
    
    def handle_response(self, result):
        """Handle the API response."""
        try:
            # This runs in the main thread via timer callback
            if bpy.context is None:
                return
                
            ui_props = bpy.context.scene.kitsune_ui
            
            # Get active session and its messages
            active_session = ui_props.chat_sessions[ui_props.active_session_index]
            messages = active_session.messages if hasattr(active_session, "messages") and len(active_session.messages) > 0 else ui_props.messages
            
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
                message = messages.add()
                message.message = response_text
                message.is_user = False
                message.timestamp = utils.format_timestamp()
                
                # Extract code from response if present
                extracted_code = format_code_for_execution(response_text)
                if extracted_code:
                    message.has_code = True
                    message.code = extracted_code
                
                # Auto-scroll to show the new message
                preferences = bpy.context.preferences.addons[__package__].preferences
                if preferences.auto_scroll:
                    ui_props.scroll_position = max(0, len(messages) - 15)
        except Exception as e:
            utils.log_error(f"Error handling response: {str(e)}")

# Clear chat operator
class KITSUNE_OT_clear_chat(Operator):
    """Clear the chat history."""
    
    bl_idname = "kitsune.clear_chat"
    bl_label = "Clear Chat"
    bl_description = "Clear the conversation history"
    
    def execute(self, context):
        try:
            ui_props = context.scene.kitsune_ui
            
            # Get active session
            active_session = ui_props.chat_sessions[ui_props.active_session_index]
            messages = active_session.messages if hasattr(active_session, "messages") else ui_props.messages
            
            # Clear all messages
            messages.clear()
            
            # Reset scroll position
            ui_props.scroll_position = 0
            
            # Clear any pending code
            ui_props.has_pending_code = False
            ui_props.pending_code = ""
            
            self.report({'INFO'}, "Conversation cleared")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            from . import utils
            utils.log_error(f"UI execute error: {str(e)}")
            return {'CANCELLED'}
    
    def draw(self, context):
        try:
            layout = self.layout
            layout.label(text="Are you sure you want to clear the conversation history?")
            layout.label(text="This action cannot be undone.")
        except Exception as e:
            layout = self.layout
            layout.label(text=f"Error: {str(e)}", icon='ERROR')
            from . import utils
            utils.log_error(f"UI draw error: {str(e)}")
    
    def invoke(self, context, event):
        try:
            return context.window_manager.invoke_props_dialog(self)
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            from . import utils
            utils.log_error(f"UI invoke error: {str(e)}")
            return {'CANCELLED'}

# Classes to register
classes = (
    KitsuneAttachment,
    KitsuneChatMessage,
    KitsuneChatSession,
    KitsuneUIProperties,
    KITSUNE_UL_chat_sessions,
    KITSUNE_PT_chat_panel,
    KITSUNE_OT_toggle_view_mode,
    KITSUNE_OT_scroll_chat,
    KITSUNE_OT_new_chat,
    KITSUNE_OT_delete_chat,
    KITSUNE_OT_attach_file,
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