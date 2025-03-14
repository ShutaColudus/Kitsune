# DeepSeek API integration for Kitsune
import json
import bpy
from ..vendor import requests
from . import APIProvider
from ..utils import log_debug, log_error

class DeepSeekProvider(APIProvider):
    """API Provider implementation for DeepSeek."""
    
    def __init__(self):
        self._models = [
            ('deepseek/deepseek-r1:free', 'DeepSeek R1 (Free)', ''),
            ('deepseek/deepseek-chat:free', 'DeepSeek Chat (Free)', '')
        ]
        self._base_url = "https://api.deepseek.com/v1/chat/completions"
        self._default_model = "deepseek/deepseek-r1:free"
    
    @property
    def name(self):
        return "DeepSeek"
    
    def get_models(self):
        return self._models
    
    def validate_api_key(self, api_key):
        if not api_key or len(api_key.strip()) < 10:
            return False, "API key appears to be invalid"
        
        # Simple format validation - basic check
        if not api_key.startswith("sk-"):
            return False, "DeepSeek API keys typically start with 'sk-'"
            
        return True, ""
    
    def _convert_model_name(self, full_model_name):
        """Convert full model name to DeepSeek API format."""
        # Remove provider prefix
        if full_model_name.startswith('deepseek/'):
            model_name = full_model_name[len('deepseek/'):]
            
            # Remove ':free' suffix if present
            if model_name.endswith(':free'):
                model_name = model_name[:-len(':free')]
                
            return model_name
        
        return full_model_name
    
    def _build_system_prompt(self):
        """Create the system prompt for DeepSeek."""
        return """You are Kitsune, an AI assistant specialized in helping users with 3D modeling in Blender. 
Your primary goal is to generate Python code using Blender's Python API (bpy) to help users create and modify 3D models.

When the user asks you to create or modify 3D models:
1. Generate working Python code that accomplishes the user's request
2. Surround your code with triple backticks (```) 
3. Explain briefly what the code does
4. Keep explanations concise - users primarily need working code

Some important guidelines:
- Use `bpy.context.selected_objects` to work with what the user has selected
- Respect the current edit mode the user is in
- Provide code that works with Blender 3.0 or later
- Make your code robust with error checking where appropriate
- Assume your code will be executed in the main Blender Python context

IMPORTANT: When given information about the current scene, use it to tailor your code to the user's specific context.
"""
    
    def _build_messages(self, prompt, context_info):
        """
        Build messages for DeepSeek API.
        
        Args:
            prompt (str): User prompt
            context_info (dict): Blender context information
            
        Returns:
            list: Messages for DeepSeek API
        """
        system_prompt = self._build_system_prompt()
        
        # Format the context and prompt
        context_prompt = f"""Here's information about my current Blender scene:
{json.dumps(context_info, indent=2)}

My request: {prompt}

Please respond with Python code that I can run in Blender to accomplish this."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context_prompt}
        ]
        
        return messages
    
    def send_request(self, prompt, context_info, callback):
        """
        Send a request to the DeepSeek API.
        
        Args:
            prompt (str): The user's input prompt
            context_info (dict): Context information from Blender
            callback (callable): Function to call with results
        """
        addon_prefs = bpy.context.preferences.addons["kitsune"].preferences
        api_key = addon_prefs.deepseek_api_key
        model = addon_prefs.deepseek_model
        
        if not api_key:
            error_msg = "No API key provided for DeepSeek. Please set your API key in the addon preferences."
            log_error(error_msg)
            bpy.app.timers.register(
                lambda: callback({"error": error_msg}),
                first_interval=0.1
            )
            return
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        model_name = self._convert_model_name(model or self._default_model)
        
        data = {
            "model": model_name,
            "messages": self._build_messages(prompt, context_info),
            "temperature": 0.3,
            "max_tokens": 4000
        }
        
        try:
            log_debug(f"Sending request to DeepSeek API with model: {model_name}")
            response = requests.post(
                self._base_url,
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                response_json = response.json()
                
                if 'choices' in response_json and response_json['choices']:
                    message = response_json['choices'][0].get('message', {})
                    content = message.get('content', '')
                    
                    if content:
                        bpy.app.timers.register(
                            lambda: callback({"response": content}),
                            first_interval=0.1
                        )
                        return
                
                # If we get here, response was successful but content invalid
                error_msg = "Unexpected response structure from DeepSeek API"
                log_error(error_msg)
                bpy.app.timers.register(
                    lambda: callback({"error": error_msg}),
                    first_interval=0.1
                )
                return
            
            # If we get here, something went wrong
            error_message = f"DeepSeek API error: {response.status_code}"
            try:
                error_json = response.json()
                if 'error' in error_json:
                    error_message = f"DeepSeek API error: {error_json['error'].get('message', str(error_json['error']))}"
            except:
                error_message = f"DeepSeek API error: {response.status_code} - {response.text}"
            
            log_error(error_message)
            bpy.app.timers.register(
                lambda: callback({"error": error_message}),
                first_interval=0.1
            )
            
        except requests.exceptions.Timeout:
            error_msg = "Request to DeepSeek API timed out. Please try again."
            log_error(error_msg)
            bpy.app.timers.register(
                lambda: callback({"error": error_msg}),
                first_interval=0.1
            )
            
        except Exception as e:
            error_msg = f"Error communicating with DeepSeek API: {str(e)}"
            log_error(error_msg)
            bpy.app.timers.register(
                lambda: callback({"error": error_msg}),
                first_interval=0.1
            )