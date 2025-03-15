# Anthropic API integration for Kitsune
import json
import bpy
from ..vendor import requests
from . import APIProvider
from ..utils import log_debug, log_error

class AnthropicProvider(APIProvider):
    """API Provider implementation for Anthropic."""
    
    def __init__(self):
        self._models = [
            ('anthropic/claude-3.7-sonnet', 'Claude 3.7 Sonnet', ''),
            ('anthropic/claude-3.7-sonnet:thinking', 'Claude 3.7 Sonnet (Thinking)', '')
        ]
        self._base_url = "https://api.anthropic.com/v1/messages"
        self._default_model = "anthropic/claude-3.7-sonnet"
    
    @property
    def name(self):
        return "Anthropic"
    
    def get_models(self):
        return self._models
    
    def validate_api_key(self, api_key):
        if not api_key or len(api_key.strip()) < 10:
            return False, "API key appears to be invalid"
        
        # Simple format validation for Anthropic API keys
        if not api_key.startswith("sk-ant-"):
            return False, "Anthropic API keys should start with 'sk-ant-'"
        
        # 実際にAPIにテストリクエストを送信して認証をチェック
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # モデルリストを取得するエンドポイントを使用してAPIキーの有効性を検証
        try:
            response = requests.get(
                "https://api.anthropic.com/v1/models",
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
            return False, "Connection to Anthropic API timed out"
        except Exception as e:
            return False, f"Error validating API key: {str(e)}"
    
    def _build_system_prompt(self):
        """Create the system prompt for Anthropic."""
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
        Build messages for Anthropic API.
        
        Args:
            prompt (str): User prompt
            context_info (dict): Blender context information
            
        Returns:
            list: Messages for Anthropic API
        """
        messages = [{
            "role": "user",
            "content": [{
                "type": "text",
                "text": f"""Here's information about my current Blender scene:
{json.dumps(context_info, indent=2)}

My request: {prompt}

Please respond with Python code that I can run in Blender to accomplish this."""
            }]
        }]
        
        return messages
    
    def send_request(self, prompt, context_info, callback):
        """
        Send a request to the Anthropic API.
        
        Args:
            prompt (str): The user's input prompt
            context_info (dict): Context information from Blender
            callback (callable): Function to call with results
        """
        addon_prefs = bpy.context.preferences.addons["kitsune"].preferences
        api_key = addon_prefs.anthropic_api_key
        model = addon_prefs.anthropic_model
        
        if not api_key:
            error_msg = "No API key provided for Anthropic. Please set your API key in the addon preferences."
            log_error(error_msg)
            bpy.app.timers.register(
                lambda: callback({"error": error_msg}),
                first_interval=0.1
            )
            return
        
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        messages = self._build_messages(prompt, context_info)
        
        data = {
            "model": model or self._default_model,
            "messages": messages,
            "system": self._build_system_prompt(),
            "max_tokens": 4000,
            "temperature": 0.3,
        }
        
        try:
            log_debug(f"Sending request to Anthropic API with model: {model}")
            response = requests.post(
                self._base_url,
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                response_json = response.json()
                if 'content' in response_json and response_json['content']:
                    content_parts = [part for part in response_json['content'] if part.get('type') == 'text']
                    if content_parts:
                        text_content = content_parts[0].get('text', '')
                        bpy.app.timers.register(
                            lambda: callback({"response": text_content}),
                            first_interval=0.1
                        )
                        return
            
            # If we get here, something went wrong
            error_message = f"Anthropic API error: {response.status_code}"
            try:
                error_json = response.json()
                if 'error' in error_json:
                    error_message = f"Anthropic API error: {error_json['error'].get('message', str(error_json['error']))}"
            except:
                error_message = f"Anthropic API error: {response.status_code} - {response.text}"
            
            log_error(error_message)
            bpy.app.timers.register(
                lambda: callback({"error": error_message}),
                first_interval=0.1
            )
            
        except requests.exceptions.Timeout:
            error_msg = "Request to Anthropic API timed out. Please try again."
            log_error(error_msg)
            bpy.app.timers.register(
                lambda: callback({"error": error_msg}),
                first_interval=0.1
            )
            
        except Exception as e:
            error_msg = f"Error communicating with Anthropic API: {str(e)}"
            log_error(error_msg)
            bpy.app.timers.register(
                lambda: callback({"error": error_msg}),
                first_interval=0.1
            )