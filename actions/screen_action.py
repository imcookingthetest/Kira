# Screen action feature - Vision-powered screen interaction
# Uses OpenRouter vision model for screen analysis

import pyautogui
import base64
import io
import os
import requests
from PIL import Image
from dotenv import load_dotenv
from tts import edge_speak

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
VISION_MODEL = "google/gemma-3-4b-it:free"


def capture_screen() -> Image.Image:
    """Capture the entire screen."""
    screenshot = pyautogui.screenshot()
    return screenshot


def save_screenshot_debug(image: Image.Image, command: str):
    """Save screenshot for debugging purposes."""
    try:
        import time
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        # Sanitize command for filename
        safe_command = "".join(c for c in command if c.isalnum() or c in (' ', '_')).strip()[:30]
        filename = f"debug_screenshot_{timestamp}_{safe_command}.png"
        
        # Create screenshot folder in project root
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)  # Go up from Kira/ to Kira_Project/
        screenshot_folder = os.path.join(project_root, "screenshot VISION MODEL")
        
        # Create folder if it doesn't exist
        os.makedirs(screenshot_folder, exist_ok=True)
        
        filepath = os.path.join(screenshot_folder, filename)
        
        image.save(filepath)
        print(f"DEBUG: Screenshot saved to {filepath}")
    except Exception as e:
        print(f"Warning: Could not save debug screenshot: {e}")


def image_to_base64(image: Image.Image) -> str:
    """Convert PIL Image to base64 string."""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str


def analyze_screen_with_vision(image: Image.Image, user_command: str, conversation_context: str = "") -> dict:
    """
    Send screenshot to vision model and get coordinates or instructions.
    Returns: {"action": "click", "x": 100, "y": 200, "message": "Clicking the first link"}
    """
    
    if not OPENROUTER_API_KEY:
        return {
            "action": "none",
            "message": "La chiave API è mancante per l'analisi dello schermo."
        }

    img_base64 = image_to_base64(image)
    width, height = image.size

    context_section = ""
    if conversation_context:
        context_section = f"\n\nRecent conversation context:\n{conversation_context}\n"

    prompt_text = f"""You are analyzing a Google search results page. Your task is to find SEARCH RESULT LINKS and click on them.

Screen resolution: {width}x{height}{context_section}

╔════════════════════════════════════════════════════════════════╗
║  HOW GOOGLE SEARCH RESULTS LOOK - VISUAL STRUCTURE            ║
╚════════════════════════════════════════════════════════════════╝

A typical Google search result has this EXACT structure:

┌─────────────────────────────────────────────────┐
│ [Small Icon] BLUE CLICKABLE TITLE TEXT          │ ← THIS IS THE LINK! CLICK HERE!
│              https://website.com › path          │ ← Green URL (smaller text)
│              Brief description of the page...    │ ← Gray description text
└─────────────────────────────────────────────────┘

KEY VISUAL CHARACTERISTICS OF A REAL SEARCH RESULT LINK:
1. ✓ Has a small circular favicon/icon on the left (16-20px)
2. ✓ Large BLUE text title (the main clickable part)
3. ✓ Title is usually 18-22px font size
4. ✓ Below the blue title: GREEN URL text (smaller, 14px)
5. ✓ Below the green URL: GRAY description snippet
6. ✓ The blue title is the CLICKABLE area - click on it!
7. ✓ Usually located in LEFT-CENTER of the screen
8. ✓ Vertical spacing: about 60-100px between each result

╔════════════════════════════════════════════════════════════════╗
║  WHAT TO IGNORE (NOT SEARCH RESULTS)                          ║
╚════════════════════════════════════════════════════════════════╝

DO NOT click on these:
✗ Top navigation bar (Web, Immagini, Video, Notizie, etc.)
✗ "Le persone hanno chiesto anche" section (expandable questions with ▼)
✗ "Altre domande" boxes
✗ Video thumbnails or image galleries
✗ Sidebar information boxes (usually on the right side)
✗ Related searches at the bottom
✗ Any section that doesn't have the [Icon] + Blue Title + Green URL structure

╔════════════════════════════════════════════════════════════════╗
║  STEP-BY-STEP: HOW TO FIND THE FIRST/SECOND/THIRD LINK        ║
╚════════════════════════════════════════════════════════════════╝

STEP 1: Scan the page from TOP to BOTTOM
STEP 2: Look for the pattern: [Small Icon] BLUE TEXT with green URL below
STEP 3: Find ALL search results that match this pattern
STEP 4: Count them from top to bottom:
        - First link = The FIRST blue title you find
        - Second link = The SECOND blue title you find
        - Third link = The THIRD blue title you find

STEP 5: For the requested link, identify its position:
        - Find where the blue title text starts (left edge)
        - Find where the blue title text ends (right edge)
        - Find the top of the blue title text
        - Find the bottom of the blue title text

STEP 6: Calculate CENTER coordinates:
        x = (left_edge + right_edge) / 2
        y = (top_edge + bottom_edge) / 2

EXAMPLE:
If the first search result blue title spans:
- Horizontally: from x=195 to x=500
- Vertically: from y=215 to y=240
Then click at: x=347, y=227 (the center)

╔════════════════════════════════════════════════════════════════╗
║  TYPICAL PAGE LAYOUT (approximate Y coordinates)              ║
╚════════════════════════════════════════════════════════════════╝

y=0-100:    Google logo and search bar
y=100-150:  Navigation tabs (Web, Immagini, Video...)
y=150-250:  FIRST search result usually starts here
y=250-350:  Might be FAQ section or second result
y=350-450:  Another search result
y=450-550:  Another search result
... and so on

Search results are typically in the LEFT portion of the screen:
x=150-700:  Main content area where search results appear
x=700-1200: Sidebar (knowledge panels, related info) - IGNORE THIS

Your response MUST be this JSON:
{{
    "action": "click" or "scroll" or "type" or "none",
    "x": <INTEGER pixel x coordinate>,
    "y": <INTEGER pixel y coordinate>,
    "message": "Italian description",
    "debug_info": "Example: Found first search result 'Vasco Rossi - Come Stai Lyrics' at icon position (195,220), title spans (220,215) to (520,240), clicking center at (370,227)"
}}

User command: {user_command}

CRITICAL: 
- Look for the [Icon] + BLUE TITLE + green url pattern
- Click on the CENTER of the BLUE TITLE text
- Count only real search results, ignore FAQ sections
- Return ONLY the JSON object, nothing else
"""

    # Create message with image
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt_text
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img_base64}"
                    }
                }
            ]
        }
    ]

    payload = {
        "model": VISION_MODEL,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 500
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "Kira-Assistant"
    }

    try:
        print(f"DEBUG: Calling OpenRouter Vision API...")
        print(f"DEBUG: Model: {VISION_MODEL}")
        
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        print(f"DEBUG: Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Vision API Error: {response.text}")
            return {
                "action": "none",
                "message": f"Errore API: {response.status_code}"
            }

        data = response.json()
        
        # Extract content from OpenRouter response
        if "choices" in data and len(data["choices"]) > 0:
            content = data["choices"][0]["message"]["content"]
        else:
            print(f"Unexpected response format: {data}")
            return {
                "action": "none",
                "message": "Non riesco a capire il layout dello schermo."
            }

        # Parse JSON response
        import json
        
        # Extract JSON from response
        if "```json" in content:
            start = content.index("```json") + 7
            end = content.index("```", start)
            content = content[start:end].strip()
        elif "```" in content:
            start = content.index("```") + 3
            end = content.index("```", start)
            content = content[start:end].strip()
        
        # Try to find JSON object
        try:
            start = content.index("{")
            end = content.rindex("}") + 1
            json_str = content[start:end]
            result = json.loads(json_str)
            return result
        except Exception:
            print(f"Failed to parse vision response: {content}")
            return {
                "action": "none",
                "message": "Non riesco a capire il layout dello schermo."
            }

    except Exception as e:
        print(f"VISION ERROR: {e}")
        return {
            "action": "none",
            "message": "L'analisi dello schermo è fallita."
        }


def execute_screen_action(action_data: dict) -> bool:
    """Execute the action returned by the vision model."""
    
    action = action_data.get("action", "none")
    message = action_data.get("message", "")
    
    try:
        if action == "click":
            x = action_data.get("x")
            y = action_data.get("y")
            if x is not None and y is not None:
                # Get screen size for validation
                screen_width, screen_height = pyautogui.size()
                print(f"\n=== CLICK DEBUG ===")
                print(f"Screen size: {screen_width}x{screen_height}")
                print(f"Target coordinates: ({x}, {y})")
                print(f"Action data: {action_data}")
                
                # Validate coordinates are within screen bounds
                if x < 0 or x > screen_width or y < 0 or y > screen_height:
                    print(f"ERROR: Coordinates out of bounds!")
                    return False
                
                # Move to position first (smoother and more reliable)
                print(f"Moving mouse to ({x}, {y})...")
                pyautogui.moveTo(x, y, duration=0.5)
                
                # Small pause to ensure position is reached
                import time
                time.sleep(0.3)
                
                # Get current position to verify
                current_x, current_y = pyautogui.position()
                print(f"Mouse position after move: ({current_x}, {current_y})")
                
                # Perform the click with a slight pause
                print(f"Clicking at ({x}, {y})...")
                pyautogui.click(x, y, duration=0.15)
                
                # Additional small pause after click
                time.sleep(0.2)
                print(f"Click completed!\n")
                
                return True
        
        elif action == "scroll":
            direction = action_data.get("direction", "down")
            amount = action_data.get("amount", 300)
            scroll_amount = -amount if direction == "down" else amount
            print(f"DEBUG: Scrolling {direction} by {amount}px")
            pyautogui.scroll(scroll_amount)
            return True
        
        elif action == "type":
            text = action_data.get("text", "")
            if text:
                print(f"DEBUG: Typing: {text}")
                pyautogui.write(text, interval=0.05)
                return True
        
        return False
    
    except Exception as e:
        print(f"ACTION EXECUTION ERROR: {e}")
        return False


def screen_action(
    parameters: dict,
    player=None,
    session_memory=None
) -> bool:
    """
    Main screen action handler.
    Captures screen, analyzes it, and executes the requested action.
    
    parameters:
        - command (str): The user's command (e.g., "click the first link")
    """
    
    command = (parameters or {}).get("command", "").strip()
    
    if not command:
        msg = "Non ho capito cosa vuoi che faccia sullo schermo."
        if player:
            player.write_log(msg)
        edge_speak(msg, player)
        return False
    
    # Capture screen
    print("\n" + "="*50)
    print("SCREEN ACTION DEBUG")
    print("="*50)
    print(f"User command: {command}")
    print("Capturing screen...")
    screenshot = capture_screen()
    print(f"Screenshot captured: {screenshot.size[0]}x{screenshot.size[1]}")
    
    # Save screenshot for debugging
    save_screenshot_debug(screenshot, command)
    
    # Get conversation context from memory if available
    conversation_context = ""
    if session_memory:
        history = session_memory.get_history_for_prompt()
        if history:
            # Get last few exchanges
            lines = history.split('\n')[-6:]
            conversation_context = '\n'.join(lines)
            print(f"Conversation context provided: {len(lines)} lines")
    
    # Analyze with vision model
    print(f"Analyzing screen with vision model...")
    action_data = analyze_screen_with_vision(screenshot, command, conversation_context)
    
    print(f"\nVision model response:")
    print(f"  Action: {action_data.get('action')}")
    if action_data.get('action') == 'click':
        print(f"  Coordinates: ({action_data.get('x')}, {action_data.get('y')})")
    print(f"  Message: {action_data.get('message')}")
    if 'debug_info' in action_data:
        print(f"  Debug info: {action_data.get('debug_info')}")
    print("="*50 + "\n")
    
    message = action_data.get("message", "")
    
    # Speak the message
    if message:
        if player:
            player.write_log(f"AI: {message}")
        edge_speak(message, player)
    
    # Execute the action
    if action_data.get("action") != "none":
        success = execute_screen_action(action_data)
        if success and session_memory:
            session_memory.set_open_app(f"Screen action: {command}")
        return success
    
    return False
