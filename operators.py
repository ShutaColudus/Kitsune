# Operators for Kitsune
import bpy
from bpy.props import StringProperty, BoolProperty, IntProperty
from bpy.types import Operator
import json
import time
from . import utils
from .api import create_context_info, get_provider_instance

class KITSUNE_OT_chat_in_dialog(Operator):
    """Open a dialog window for chatting with Kitsune."""
    
    bl_idname = "kitsune.chat_in_dialog"
    bl_label = "Chat with Kitsune"
    bl_description = "Open a dialog for chatting with Kitsune AI assistant"
    bl_options = {'REGISTER', 'UNDO'}
    
    # Dialog properties
    width: IntProperty(
        name="Width",
        description="Dialog width",
        default=600,
        min=400,
        max=1200
    )
    
    height: IntProperty(
        name="Height",
        description="Dialog height",
        default=500,
        min=300,
        max=900
    )
    
    input_text: StringProperty(
        name="Message",
        description="Type your message to Kitsune",
        default=""
    )
    
    def invoke(self, context, event):
        # Set up the dialog properties
        return context.window_manager.invoke_props_dialog(self, width=self.width)
    
    def draw(self, context):
        layout = self.layout
        ui_props = context.scene.kitsune_ui
        preferences = context.preferences.addons["kitsune"].preferences
        
        # Header with provider info
        provider_name = preferences.api_provider.capitalize()
        model_attr = f"{preferences.api_provider}_model"
        model_name = getattr(preferences, model_attr, "Unknown").split('/')[-1]
        
        header = layout.box()
        header.label(text=f"Kitsune AI Assistant ({provider_name} - {model_name})", icon='BLENDER')
        
        # Conversation history - show last 10 messages at most
        history_box = layout.box()
        history_col = history_box.column()
        history_col.scale_y = 0.7
        
        if not ui_props.messages:
            history_col.label(text="No messages yet. Type something to begin.")
        else:
            # Only show last 10 messages to keep the dialog manageable
            start_idx = max(0, len(ui_props.messages) - 10)
            for msg in ui_props.messages[start_idx:]:
                msg_box = history_col.box()
                
                # Message header
                if msg.is_user:
                    header_row = msg_box.row()
                    header_row.label(text="You:", icon='USER')
                    if preferences.show_timestamps and msg.timestamp:
                        header_row.label(text=msg.timestamp)
                else:
                    header_row = msg_box.row()
                    header_row.label(text="Kitsune:", icon='BLENDER')
                    if preferences.show_timestamps and msg.timestamp:
                        header_row.label(text=msg.timestamp)
                
                # Message content
                content_col = msg_box.column()
                content_col.scale_y = 0.7
                
                # Limit message display to keep dialog manageable
                lines = msg.message.split('\n')
                max_lines = 15  # Maximum lines to show
                
                # Simple check for code blocks
                in_code_block = False
                code_lines = []
                
                for i, line in enumerate(lines):
                    if i >= max_lines:
                        content_col.label(text="... (message truncated)")
                        break
                    
                    if line.strip().startswith('```'):
                        if in_code_block:
                            # End of code block
                            in_code_block = False
                            code_box = content_col.box()
                            for code_line in code_lines:
                                code_box.label(text=code_line)
                            code_lines = []
                        else:
                            # Start of code block
                            in_code_block = True
                    elif in_code_block:
                        code_lines.append(line)
                    elif line.strip():
                        content_col.label(text=line)
                
                # Handle any remaining code lines
                if code_lines:
                    code_box = content_col.box()
                    for code_line in code_lines:
                        code_box.label(text=code_line)
                        
                # If AI message has code, show preview button
                if not msg.is_user and msg.has_code:
                    button_row = msg_box.row()
                    op = button_row.operator("kitsune.preview_code", text="Preview Code", icon='SCRIPT')
                    op.message_index = ui_props.messages.find(msg)
        
        # Processing indicator
        if ui_props.is_processing:
            layout.label(text="Processing request...", icon='SORTTIME')
            
        # Input area
        input_box = layout.box()
        input_row = input_box.row(align=True)
        input_row.prop(self, "input_text", text="")
        send_button = input_row.operator("kitsune.send_from_dialog", text="", icon='EXPORT')
        
        # Disable input while processing
        input_row.enabled = not ui_props.is_processing
        
        # Note about full interface
        note = layout.box()
        note.label(text="For full features, use the Kitsune panel in the sidebar", icon='INFO')
    
    def execute(self, context):
        # This is called when the dialog is closed
        return {'FINISHED'}

class KITSUNE_OT_send_from_dialog(Operator):
    """Send a message from the dialog interface."""
    
    bl_idname = "kitsune.send_from_dialog"
    bl_label = "Send Message"
    bl_description = "Send your message to Kitsune from the dialog"
    
    def execute(self, context):
        # Get the input text from the active dialog
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'PROPERTIES':
                    for region in area.regions:
                        if region.type == 'WINDOW':
                            for space in area.spaces:
                                if space.type == 'PROPERTIES':
                                    for operator in context.window_manager.operators:
                                        if operator.bl_idname == "kitsune.chat_in_dialog":
                                            message = operator.input_text
                                            if message.strip():
                                                # Reset the input field
                                                operator.input_text = ""
                                                # Send the message using the regular send operator
                                                bpy.context.scene.kitsune_ui.chat_input = message
                                                bpy.ops.kitsune.send_message()
                                            return {'FINISHED'}
        
        self.report({'WARNING'}, "Could not find dialog input text")
        return {'CANCELLED'}

class KITSUNE_OT_copy_code(Operator):
    """Copy code from a message to clipboard."""
    
    bl_idname = "kitsune.copy_code"
    bl_label = "Copy Code"
    bl_description = "Copy the code from this message to clipboard"
    
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
        
        # Get the message
        message = ui_props.messages[self.message_index]
        if not message.has_code or not message.code:
            self.report({'WARNING'}, "No executable code found in the message")
            return {'CANCELLED'}
        
        # Copy to clipboard
        context.window_manager.clipboard = message.code
        self.report({'INFO'}, "Code copied to clipboard")
        
        return {'FINISHED'}

class KITSUNE_OT_export_chat(Operator):
    """Export the conversation to a text file."""
    
    bl_idname = "kitsune.export_chat"
    bl_label = "Export Conversation"
    bl_description = "Export the conversation to a text file"
    
    filepath: StringProperty(
        name="File Path",
        description="Path to save the exported conversation",
        default="//kitsune_conversation.txt",
        subtype='FILE_PATH'
    )
    
    def execute(self, context):
        ui_props = context.scene.kitsune_ui
        
        if not ui_props.messages:
            self.report({'WARNING'}, "No messages to export")
            return {'CANCELLED'}
        
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                f.write("# Kitsune Conversation Export\n")
                f.write(f"# Date: {utils.format_timestamp()}\n\n")
                
                for msg in ui_props.messages:
                    if msg.is_user:
                        f.write(f"## You ({msg.timestamp}):\n")
                    else:
                        f.write(f"## Kitsune ({msg.timestamp}):\n")
                    
                    f.write(f"{msg.message}\n\n")
                    
                    if msg.has_code:
                        f.write("### Generated Code:\n")
                        f.write(f"```python\n{msg.code}\n```\n\n")
            
            self.report({'INFO'}, f"Conversation exported to {self.filepath}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to export conversation: {str(e)}")
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# List of classes to register
classes = (
    KITSUNE_OT_chat_in_dialog,
    KITSUNE_OT_send_from_dialog,
    KITSUNE_OT_copy_code,
    KITSUNE_OT_export_chat
)

def register():
    """Register operators."""
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    """Unregister operators."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)