# OpenAI API integration for Kitsune
import json
import bpy
from ..vendor import requests
from . import APIProvider
from ..utils import log_debug, log_error

class OpenAIProvider(APIProvider):
    """API Provider implementation for OpenAI."""
    
    def __init__(self):
        self._models = [
            ('openai/gpt-4o-mini', 'GPT-4o Mini', '')
        ]
        self._base_url = "https://api.openai.com/v1/chat/completions"
        self._default_model = "openai/gpt-4o-mini"
    
    @property
    def name(self):
        return "OpenAI"
    
    def get_models(self):
        return self._models
    
    def validate_api_key(self, api_key):
        if not api_key or len(api_key.strip()) < 10:
            return False, "API key appears to be invalid"
        
        # Simple format validation for OpenAI API keys
        if not api_key.startswith("sk-"):
            return False, "OpenAI API keys should start with 'sk-'"
            
        # 実際にAPIにテストリクエストを送信して認証をチェック
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # モデルリストを取得するエンドポイントを使用してAPIキーの有効性を検証
        try:
            response = requests.get(
                "https://api.openai.com/v1/models",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "API key is valid"
            elif response.status_code == 401:
                return False, "Invalid API key: Authentication failed"
            else:
                try:
                    error_json = response.json()
                    if 'error' in error_json:
                        error_message = error_json['error'].get('message', str(error_json['error']))
                        return False, f"API error: {error_message}"
                except:
                    pass
                return False, f"API error: HTTP {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, "Connection to OpenAI API timed out"
        except Exception as e:
            return False, f"Error validating API key: {str(e)}"
    
    def _convert_model_name(self, full_model_name):
        """Convert full model name to OpenAI API format."""
        # Remove provider prefix
        if full_model_name.startswith('openai/'):
            return full_model_name[len('openai/'):]
        
        return full_model_name
    
    def _build_system_prompt(self):
        """Create the system prompt for OpenAI."""
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
        Build messages for OpenAI API.
        
        Args:
            prompt (str): User prompt
            context_info (dict): Blender context information
            
        Returns:
            list: Messages for OpenAI API
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
        Send a request to the OpenAI API.
        
        Args:
            prompt (str): The user's input prompt
            context_info (dict): Context information from Blender
            callback (callable): Function to call with results
        """
        addon_prefs = bpy.context.preferences.addons["kitsune"].preferences
        api_key = addon_prefs.openai_api_key
        model = addon_prefs.openai_model
        
        if not api_key:
            error_msg = "No API key provided for OpenAI. Please set your API key in the addon preferences."
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
            log_debug(f"Sending request to OpenAI API with model: {model_name}")
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
                error_msg = "Unexpected response structure from OpenAI API"
                log_error(error_msg)
                bpy.app.timers.register(
                    lambda: callback({"error": error_msg}),
                    first_interval=0.1
                )
                return
            
            # If we get here, something went wrong
            error_message = f"OpenAI API error: {response.status_code}"
            try:
                error_json = response.json()
                if 'error' in error_json:
                    error_message = f"OpenAI API error: {error_json['error'].get('message', str(error_json['error']))}"
            except:
                error_message = f"OpenAI API error: {response.status_code} - {response.text}"
            
            log_error(error_message)
            bpy.app.timers.register(
                lambda: callback({"error": error_message}),
                first_interval=0.1
            )
            
        except requests.exceptions.Timeout:
            error_msg = "Request to OpenAI API timed out. Please try again."
            log_error(error_msg)
            bpy.app.timers.register(
                lambda: callback({"error": error_msg}),
                first_interval=0.1
            )
            
        except Exception as e:
            error_msg = f"Error communicating with OpenAI API: {str(e)}"
            log_error(error_msg)
            bpy.app.timers.register(
                lambda: callback({"error": error_msg}),
                first_interval=0.1
            )