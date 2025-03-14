# Google Gemini API integration for Kitsune
import json
import bpy
from ..vendor import requests
from . import APIProvider
from ..utils import log_debug, log_error

class GoogleProvider(APIProvider):
    """API Provider implementation for Google Gemini."""
    
    def __init__(self):
        self._models = [
            ('google/gemini-2.0-flash-001', 'Gemini 2.0 Flash 001', ''),
            ('google/gemini-2.0-pro-exp-02-05:free', 'Gemini 2.0 Pro Exp (Free)', '')
        ]
        self._base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self._default_model = "google/gemini-2.0-flash-001"
    
    @property
    def name(self):
        return "Google Gemini"
    
    def get_models(self):
        return self._models
    
    def validate_api_key(self, api_key):
        if not api_key or len(api_key.strip()) < 10:
            return False, "API key appears to be invalid"
            
        return True, ""
    
    def _convert_model_name(self, full_model_name):
        """Convert full model name to Google API format."""
        # Remove provider prefix
        if full_model_name.startswith('google/'):
            model_name = full_model_name[len('google/'):]
            
            # Remove ':free' suffix if present
            if model_name.endswith(':free'):
                model_name = model_name[:-len(':free')]
                
            return model_name
        
        return full_model_name
    
    def _build_system_prompt(self):
        """Create the system prompt for Google Gemini."""
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
    
    def _build_content(self, prompt, context_info):
        """
        Build content for Google Gemini API.
        
        Args:
            prompt (str): User prompt
            context_info (dict): Blender context information
            
        Returns:
            dict: Content structure for Google API
        """
        system_prompt = self._build_system_prompt()
        
        context_str = f"""Here's information about my current Blender scene:
{json.dumps(context_info, indent=2)}

My request: {prompt}

Please respond with Python code that I can run in Blender to accomplish this."""
        
        return {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": context_str}]
                }
            ],
            "systemInstruction": {
                "role": "system",
                "parts": [{"text": system_prompt}]
            },
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.95,
                "topK": 40,
                "maxOutputTokens": 4096
            }
        }
    
    def send_request(self, prompt, context_info, callback):
        """
        Send a request to the Google Gemini API.
        
        Args:
            prompt (str): The user's input prompt
            context_info (dict): Context information from Blender
            callback (callable): Function to call with results
        """
        addon_prefs = bpy.context.preferences.addons["kitsune"].preferences
        api_key = addon_prefs.google_api_key
        model = addon_prefs.google_model
        
        if not api_key:
            error_msg = "No API key provided for Google Gemini. Please set your API key in the addon preferences."
            log_error(error_msg)
            bpy.app.timers.register(
                lambda: callback({"error": error_msg}),
                first_interval=0.1
            )
            return
        
        model_name = self._convert_model_name(model or self._default_model)
        request_url = f"{self._base_url}/{model_name}:generateContent?key={api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        data = self._build_content(prompt, context_info)
        
        try:
            log_debug(f"Sending request to Google Gemini API with model: {model_name}")
            response = requests.post(
                request_url,
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                response_json = response.json()
                
                if ('candidates' in response_json and 
                    response_json['candidates'] and 
                    'content' in response_json['candidates'][0] and
                    'parts' in response_json['candidates'][0]['content'] and
                    response_json['candidates'][0]['content']['parts']):
                    
                    content = response_json['candidates'][0]['content']['parts'][0]['text']
                    bpy.app.timers.register(
                        lambda: callback({"response": content}),
                        first_interval=0.1
                    )
                    return
                else:
                    error_msg = "Unexpected response structure from Google Gemini API"
                    log_error(error_msg)
                    bpy.app.timers.register(
                        lambda: callback({"error": error_msg}),
                        first_interval=0.1
                    )
                    return
            
            # If we get here, something went wrong
            error_message = f"Google Gemini API error: {response.status_code}"
            try:
                error_json = response.json()
                if 'error' in error_json:
                    error_message = f"Google Gemini API error: {error_json['error'].get('message', str(error_json['error']))}"
            except:
                error_message = f"Google Gemini API error: {response.status_code} - {response.text}"
            
            log_error(error_message)
            bpy.app.timers.register(
                lambda: callback({"error": error_message}),
                first_interval=0.1
            )
            
        except requests.exceptions.Timeout:
            error_msg = "Request to Google Gemini API timed out. Please try again."
            log_error(error_msg)
            bpy.app.timers.register(
                lambda: callback({"error": error_msg}),
                first_interval=0.1
            )
            
        except Exception as e:
            error_msg = f"Error communicating with Google Gemini API: {str(e)}"
            log_error(error_msg)
            bpy.app.timers.register(
                lambda: callback({"error": error_msg}),
                first_interval=0.1
            )