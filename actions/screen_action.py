# ARCHIVED - Screen action feature disabled temporarily
# This feature will be re-enabled when a working vision API is configured

# import pyautogui
# import base64
# import io
# import os
# import requests
# from PIL import Image
# from dotenv import load_dotenv
# from tts import edge_speak

# load_dotenv()

# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# VISION_MODEL = "gemini-1.5-flash-001"


# def capture_screen() -> Image.Image:
#     """Capture the entire screen."""
#     screenshot = pyautogui.screenshot()
#     return screenshot


# def image_to_base64(image: Image.Image) -> str:
#     """Convert PIL Image to base64 string."""
#     buffered = io.BytesIO()
#     image.save(buffered, format="PNG")
#     img_str = base64.b64encode(buffered.getvalue()).decode()
#     return img_str


# def analyze_screen_with_vision(image: Image.Image, user_command: str) -> dict:
#     """
#     Send screenshot to vision model and get coordinates or instructions.
#     Returns: {"action": "click", "x": 100, "y": 200, "message": "Clicking the first link"}
#     """
#     
#     if not GOOGLE_API_KEY:
#         return {
#             "action": "none",
#             "message": "Sir, the Google API key is missing for screen analysis."
#         }
# 
#     img_base64 = image_to_base64(image)
#     width, height = image.size
# 
#     prompt_text = f"""You are a screen navigation assistant. The user will give you a command like "click the first link" or "scroll down".
# Analyze the screenshot and provide coordinates or actions.
# 
# Screen resolution: {width}x{height}
# 
# Your response MUST be a JSON object with this structure:
# {{
#     "action": "click" or "scroll" or "type" or "none",
#     "x": <pixel x coordinate, only for click>,
#     "y": <pixel y coordinate, only for click>,
#     "direction": "up" or "down" (only for scroll),
#     "amount": <scroll amount in pixels, only for scroll>,
#     "text": "<text to type, only for type>",
#     "message": "Brief description of what you're doing"
# }}
# 
# For "click" actions, provide exact pixel coordinates.
# For "scroll" actions, provide direction and amount.
# For "type" actions, provide the text to type.
# If you can't identify what to do, use action: "none" with an explanation message.
# 
# User command: {user_command}
# 
# RETURN ONLY THE JSON, NO OTHER TEXT."""
# 
#     payload = {
#         "contents": [
#             {
#                 "parts": [
#                     {
#                         "text": prompt_text
#                     },
#                     {
#                         "inline_data": {
#                             "mime_type": "image/png",
#                             "data": img_base64
#                         }
#                     }
#                 ]
#             }
#         ],
#         "generationConfig": {
#             "temperature": 0.1,
#             "maxOutputTokens": 500
#         }
#     }
# 
#     try:
#         url = f"https://generativelanguage.googleapis.com/v1beta/models/{VISION_MODEL}:generateContent?key={GOOGLE_API_KEY}"
#         
#         print(f"DEBUG: Calling Google Vision API...")
#         print(f"DEBUG: Model: {VISION_MODEL}")
#         print(f"DEBUG: URL: {url[:80]}...")
#         
#         response = requests.post(
#             url,
#             json=payload,
#             timeout=30
#         )
# 
#         print(f"DEBUG: Response status: {response.status_code}")
#         
#         if response.status_code != 200:
#             print(f"❌ Vision API Error: {response.text}")
#             return {
#                 "action": "none",
#                 "message": f"Sir, API error: {response.status_code}"
#             }
# 
#         data = response.json()
#         
#         # Extract content from Gemini response
#         if "candidates" in data and len(data["candidates"]) > 0:
#             content = data["candidates"][0]["content"]["parts"][0]["text"]
#         else:
#             print(f"Unexpected response format: {data}")
#             return {
#                 "action": "none",
#                 "message": "Sir, I couldn't understand the screen layout."
#             }
# 
#         # Parse JSON response
#         import json
#         
#         # Extract JSON from response
#         if "```json" in content:
#             start = content.index("```json") + 7
#             end = content.index("```", start)
#             content = content[start:end].strip()
#         elif "```" in content:
#             start = content.index("```") + 3
#             end = content.index("```", start)
#             content = content[start:end].strip()
#         
#         # Try to find JSON object
#         try:
#             start = content.index("{")
#             end = content.rindex("}") + 1
#             json_str = content[start:end]
#             result = json.loads(json_str)
#             return result
#         except:
#             print(f"Failed to parse vision response: {content}")
#             return {
#                 "action": "none",
#                 "message": "Sir, I couldn't understand the screen layout."
#             }
# 
#     except Exception as e:
#         print(f"VISION ERROR: {e}")
#         return {
#             "action": "none",
#             "message": "Sir, the screen analysis failed."
#         }
# 
# 
# def execute_screen_action(action_data: dict) -> bool:
#     """Execute the action returned by the vision model."""
#     
#     action = action_data.get("action", "none")
#     message = action_data.get("message", "")
#     
#     try:
#         if action == "click":
#             x = action_data.get("x")
#             y = action_data.get("y")
#             if x is not None and y is not None:
#                 print(f"DEBUG: Clicking at ({x}, {y})")
#                 pyautogui.click(x, y)
#                 return True
#         
#         elif action == "scroll":
#             direction = action_data.get("direction", "down")
#             amount = action_data.get("amount", 300)
#             scroll_amount = -amount if direction == "down" else amount
#             print(f"DEBUG: Scrolling {direction} by {amount}px")
#             pyautogui.scroll(scroll_amount)
#             return True
#         
#         elif action == "type":
#             text = action_data.get("text", "")
#             if text:
#                 print(f"DEBUG: Typing: {text}")
#                 pyautogui.write(text, interval=0.05)
#                 return True
#         
#         return False
#     
#     except Exception as e:
#         print(f"ACTION EXECUTION ERROR: {e}")
#         return False
# 
# 
# def screen_action(
#     parameters: dict,
#     player=None,
#     session_memory=None
# ) -> bool:
#     """
#     Main screen action handler.
#     Captures screen, analyzes it, and executes the requested action.
#     
#     parameters:
#         - command (str): The user's command (e.g., "click the first link")
#     """
#     
#     command = (parameters or {}).get("command", "").strip()
#     
#     if not command:
#         msg = "Sir, I didn't understand what you want me to do on the screen."
#         if player:
#             player.write_log(msg)
#         edge_speak(msg, player)
#         return False
#     
#     # Capture screen
#     print("DEBUG: Capturing screen...")
#     screenshot = capture_screen()
#     
#     # Analyze with vision model
#     print(f"DEBUG: Analyzing screen for command: {command}")
#     action_data = analyze_screen_with_vision(screenshot, command)
#     
#     message = action_data.get("message", "")
#     
#     # Speak the message
#     if message:
#         if player:
#             player.write_log(f"AI: {message}")
#         edge_speak(message, player)
#     
#     # Execute the action
#     if action_data.get("action") != "none":
#         success = execute_screen_action(action_data)
#         if success and session_memory:
#             session_memory.set_open_app(f"Screen action: {command}")
#         return success
#     
#     return False
