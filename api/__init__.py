# Core API functionality for Kitsune
import threading
import json
from abc import ABC, abstractmethod
import bpy
from ..utils import log_debug, log_error

class APIProvider(ABC):
    """Abstract base class for all LLM API providers."""
    
    @abstractmethod
    def get_models(self):
        """Return list of available models for this provider."""
        pass
    
    @abstractmethod
    def send_request(self, prompt, context_info, callback):
        """
        Send a request to the API provider.
        
        Args:
            prompt (str): The user's input prompt
            context_info (dict): Context information from Blender
            callback (callable): Function to call with results
        """
        pass
    
    @property
    @abstractmethod
    def name(self):
        """Return the name of the provider."""
        pass
    
    @abstractmethod
    def validate_api_key(self, api_key):
        """Validate the API key for this provider."""
        pass

class APIRequestThread(threading.Thread):
    """Thread class for asynchronous API requests."""
    
    def __init__(self, provider, prompt, context_info, callback):
        """
        Initialize the request thread.
        
        Args:
            provider (APIProvider): The provider to use for the request
            prompt (str): The user's input prompt
            context_info (dict): Context information from Blender
            callback (callable): Function to call with results
        """
        threading.Thread.__init__(self)
        self.provider = provider
        self.prompt = prompt
        self.context_info = context_info
        self.callback = callback
        self.daemon = True  # Thread will close when Blender exits
        
    def run(self):
        """Execute the API request in a separate thread."""
        try:
            self.provider.send_request(self.prompt, self.context_info, self.callback)
        except Exception as e:
            log_error(f"API request error: {str(e)}")
            # Call callback with error
            if self.callback:
                bpy.app.timers.register(
                    lambda: self.callback({"error": str(e)}),
                    first_interval=0.1
                )

def get_provider_instance(provider_id):
    """
    Get a provider instance based on the provider ID.
    
    Args:
        provider_id (str): The ID of the provider
    
    Returns:
        APIProvider: An instance of the requested provider
    """
    from . import anthropic, google, deepseek, openai
    
    providers = {
        'anthropic': anthropic.AnthropicProvider,
        'google': google.GoogleProvider,
        'deepseek': deepseek.DeepSeekProvider,
        'openai': openai.OpenAIProvider
    }
    
    if provider_id not in providers:
        log_error(f"Unknown provider: {provider_id}")
        return None
    
    return providers[provider_id]()

def format_code_for_execution(response):
    """
    Extract Python code from LLM response.
    
    Args:
        response (str): The response from the LLM
        
    Returns:
        str: Extracted code or None if no code found
    """
    import re
    
    # Look for code blocks with Python, bpy, or Blender markers
    pattern = r"```(?:python|bpy|blender)?\s*([\s\S]*?)```"
    matches = re.findall(pattern, response)
    
    if matches:
        # Return the largest code block found
        return max(matches, key=len).strip()
    
    # If no code blocks found, try to extract any Python-like code
    # This is a fallback and less reliable
    lines = response.split('\n')
    code_lines = []
    in_code = False
    
    for line in lines:
        if line.strip().startswith('import bpy') or line.strip().startswith('from bpy'):
            in_code = True
            
        if in_code:
            code_lines.append(line)
            
    if code_lines:
        return '\n'.join(code_lines)
            
    return None

def create_context_info():
    """
    Create context information about the current Blender state.
    
    Returns:
        dict: Context information
    """
    context = {}
    
    # Get current mode
    context["mode"] = bpy.context.mode
    
    # Get selected objects info
    selected_objects = bpy.context.selected_objects
    context["selected_objects"] = []
    
    for obj in selected_objects:
        obj_info = {
            "name": obj.name,
            "type": obj.type,
            "dimensions": [round(dim, 4) for dim in obj.dimensions],
            "location": [round(loc, 4) for loc in obj.location]
        }
        
        # Include additional type-specific info
        if obj.type == 'MESH':
            obj_info["vertices"] = len(obj.data.vertices)
            obj_info["edges"] = len(obj.data.edges)
            obj_info["polygons"] = len(obj.data.polygons)
        
        context["selected_objects"].append(obj_info)
    
    # Get active object
    active_obj = bpy.context.active_object
    if active_obj:
        context["active_object"] = {
            "name": active_obj.name,
            "type": active_obj.type
        }
    
    # Scene info
    context["scene"] = {
        "name": bpy.context.scene.name,
        "objects_count": len(bpy.context.scene.objects),
        "render_engine": bpy.context.scene.render.engine
    }
    
    return context