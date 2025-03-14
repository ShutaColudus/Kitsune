# Addon preferences for Kitsune
import bpy
from bpy.props import (
    StringProperty,
    BoolProperty,
    EnumProperty,
    IntProperty
)
from . import utils
from .api import get_provider_instance

class KitsuneAddonPreferences(bpy.types.AddonPreferences):
    """Addon preferences for Kitsune."""
    
    bl_idname = "kitsune"
    
    # Debug mode
    debug_mode: BoolProperty(
        name="Debug Mode",
        description="Enable debug logging",
        default=False
    )
    
    # Provider selection
    api_provider: EnumProperty(
        name="AI Provider",
        description="Select the AI provider to use",
        items=[
            ('anthropic', "Anthropic", "Use Anthropic's Claude"),
            ('google', "Google Gemini", "Use Google's Gemini models"),
            ('deepseek', "DeepSeek", "Use DeepSeek's models"),
            ('openai', "OpenAI", "Use OpenAI's models")
        ],
        default='anthropic'
    )
    
    # API Keys for different providers (stored as password - hidden)
    anthropic_api_key: StringProperty(
        name="Anthropic API Key",
        description="API key for Anthropic Claude",
        default="",
        subtype='PASSWORD'
    )
    
    google_api_key: StringProperty(
        name="Google API Key",
        description="API key for Google Gemini",
        default="",
        subtype='PASSWORD'
    )
    
    deepseek_api_key: StringProperty(
        name="DeepSeek API Key",
        description="API key for DeepSeek",
        default="",
        subtype='PASSWORD'
    )
    
    openai_api_key: StringProperty(
        name="OpenAI API Key",
        description="API key for OpenAI",
        default="",
        subtype='PASSWORD'
    )
    
    # Model selections for each provider
    anthropic_model: EnumProperty(
        name="Anthropic Model",
        description="Select the Anthropic model to use",
        items=[
            ('anthropic/claude-3.7-sonnet', "Claude 3.7 Sonnet", "Claude 3.7 Sonnet model"),
            ('anthropic/claude-3.7-sonnet:thinking', "Claude 3.7 Sonnet (Thinking)", "Claude 3.7 Sonnet with thinking capabilities")
        ],
        default='anthropic/claude-3.7-sonnet'
    )
    
    google_model: EnumProperty(
        name="Google Model",
        description="Select the Google model to use",
        items=[
            ('google/gemini-2.0-flash-001', "Gemini 2.0 Flash 001", "Faster response, good for most tasks"),
            ('google/gemini-2.0-pro-exp-02-05:free', "Gemini 2.0 Pro Exp (Free)", "Free tier of Gemini 2.0 Pro Experimental")
        ],
        default='google/gemini-2.0-flash-001'
    )
    
    deepseek_model: EnumProperty(
        name="DeepSeek Model",
        description="Select the DeepSeek model to use",
        items=[
            ('deepseek/deepseek-r1:free', "DeepSeek R1 (Free)", "Free tier of DeepSeek R1"),
            ('deepseek/deepseek-chat:free', "DeepSeek Chat (Free)", "Free tier of DeepSeek Chat")
        ],
        default='deepseek/deepseek-r1:free'
    )
    
    openai_model: EnumProperty(
        name="OpenAI Model",
        description="Select the OpenAI model to use",
        items=[
            ('openai/gpt-4o-mini', "GPT-4o Mini", "Smaller, faster version of GPT-4o")
        ],
        default='openai/gpt-4o-mini'
    )
    
    # Chat settings
    max_conversation_length: IntProperty(
        name="Max Conversation Length",
        description="Maximum number of messages to keep in the conversation history (0 for unlimited)",
        min=0,
        max=100,
        default=20
    )
    
    auto_scroll: BoolProperty(
        name="Auto-scroll",
        description="Automatically scroll to the latest message",
        default=True
    )
    
    show_timestamps: BoolProperty(
        name="Show Timestamps",
        description="Show timestamps for messages",
        default=True
    )
    
    # Code execution settings
    confirm_code_execution: BoolProperty(
        name="Confirm Code Execution",
        description="Always ask for confirmation before executing code",
        default=True
    )
    
    syntax_highlighting: BoolProperty(
        name="Syntax Highlighting",
        description="Use syntax highlighting for code blocks",
        default=True
    )
    
    def validate_provider_api_key(self, context=None):
        """
        Validate the current provider's API key.
        
        Returns:
            tuple: (is_valid, message)
        """
        provider_id = self.api_provider
        api_key_attr = f"{provider_id}_api_key"
        
        if not hasattr(self, api_key_attr):
            return False, f"Unknown provider: {provider_id}"
            
        api_key = getattr(self, api_key_attr)
        
        if not api_key:
            return False, f"API key for {provider_id} is not set. Please add your API key in the addon preferences."
            
        # Get provider instance and validate key
        provider = get_provider_instance(provider_id)
        if provider:
            return provider.validate_api_key(api_key)
        
        return False, f"Failed to initialize provider: {provider_id}"
    
    def draw(self, context):
        layout = self.layout
        
        # Debug mode setting
        debug_box = layout.box()
        debug_box.label(text="Debug Settings:", icon='CONSOLE')
        debug_box.prop(self, "debug_mode")
        
        # API Provider selection
        provider_box = layout.box()
        provider_box.label(text="AI Provider Settings:", icon='WORLD')
        provider_box.prop(self, "api_provider")
        
        # Provider-specific settings
        selected_provider = self.api_provider
        
        if selected_provider == 'anthropic':
            model_box = provider_box.box()
            model_box.label(text="Anthropic Settings:", icon='SETTINGS')
            model_box.prop(self, "anthropic_api_key")
            model_box.prop(self, "anthropic_model")
            
        elif selected_provider == 'google':
            model_box = provider_box.box()
            model_box.label(text="Google Gemini Settings:", icon='SETTINGS')
            model_box.prop(self, "google_api_key")
            model_box.prop(self, "google_model")
            
        elif selected_provider == 'deepseek':
            model_box = provider_box.box()
            model_box.label(text="DeepSeek Settings:", icon='SETTINGS')
            model_box.prop(self, "deepseek_api_key")
            model_box.prop(self, "deepseek_model")
            
        elif selected_provider == 'openai':
            model_box = provider_box.box()
            model_box.label(text="OpenAI Settings:", icon='SETTINGS')
            model_box.prop(self, "openai_api_key")
            model_box.prop(self, "openai_model")
        
        # Chat settings
        chat_box = layout.box()
        chat_box.label(text="Chat Settings:", icon='OUTLINER_OB_FONT')
        chat_box.prop(self, "max_conversation_length")
        chat_box.prop(self, "auto_scroll")
        chat_box.prop(self, "show_timestamps")
        
        # Code execution settings
        code_box = layout.box()
        code_box.label(text="Code Execution Settings:", icon='SCRIPT')
        code_box.prop(self, "confirm_code_execution")
        code_box.prop(self, "syntax_highlighting")
        
        # Version and compatibility info
        compatibility_box = layout.box()
        compatibility_box.label(text="Compatibility Information:", icon='INFO')
        
        is_compatible, message = utils.check_blender_compatibility()
        icon = 'CHECKMARK' if is_compatible else 'ERROR'
        compatibility_box.label(text=message, icon=icon)
        
        deps_ok, missing = utils.check_dependencies()
        if deps_ok:
            compatibility_box.label(text="All dependencies are installed", icon='CHECKMARK')
        else:
            compatibility_box.label(text=f"Missing dependencies: {', '.join(missing)}", icon='ERROR')

# Function to get active provider
def get_active_provider():
    """
    Get the currently active provider instance based on preferences.
    
    Returns:
        APIProvider: The active provider instance
    """
    preferences = bpy.context.preferences.addons["kitsune"].preferences
    provider_id = preferences.api_provider
    return get_provider_instance(provider_id)