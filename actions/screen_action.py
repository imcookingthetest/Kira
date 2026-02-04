# Screen action feature - Vision-powered screen interaction
# Uses OCR + pattern matching for reliable link detection

import pyautogui
import base64
import io
import os
import requests
import re
from PIL import Image
from dotenv import load_dotenv
from tts import edge_speak

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
VISION_MODEL = "google/gemma-3-12b-it:free"


# Try to import OCR libraries
try:
    import pytesseract
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False
    print("Warning: pytesseract not installed. Install with: pip install pytesseract")

try:
    import easyocr
    HAS_EASYOCR = True
except ImportError:
    HAS_EASYOCR = False


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


def find_google_links_by_color(image: Image.Image) -> list:
    """
    NEW: Find Google search links using color detection.
    Google uses specific blue color (#1a0dab) for links.
    More reliable than vision model for coordinates.
    """
    import numpy as np
    from collections import defaultdict
    
    img_array = np.array(image)
    height, width = img_array.shape[:2]
    
    blue_pixels = []
    color_samples = []  # DEBUG: collect color samples
    
    # Scan left-center area where Google results appear
    # Expanded area to catch more links
    for y in range(150, min(height, 800), 6):
        for x in range(150, min(width, 800), 4):
            try:
                pixel = img_array[y, x]
                # PIL/numpy uses RGB order
                r, g, b = int(pixel[0]), int(pixel[1]), int(pixel[2])
                
                # DEBUG: Sample some colors
                if len(color_samples) < 20 and y % 50 == 0 and x % 100 == 0:
                    color_samples.append(f"({r},{g},{b})")
                
                # More flexible blue detection for links
                # Allow darker blues and slight variations
                # Typical link blues: RGB(0-80, 0-120, 150-255)
                if r < 120 and g < 150 and b > 100 and b > r and b > g:
                    blue_pixels.append({'x': x, 'y': y, 'color': (r, g, b)})
            except:
                continue
    
    print(f"DEBUG: Color samples from page: {color_samples[:10]}")
    
    if not blue_pixels:
        return []
    
    # Cluster by Y coordinate (same line = same link)
    clusters = defaultdict(list)
    for point in blue_pixels:
        cluster_y = (point['y'] // 25) * 25
        clusters[cluster_y].append(point)
    
    # Get center of each cluster - FILTER for actual links
    links = []
    for cluster_y, points in clusters.items():
        # Real Google links are LONG (many pixels) - filter out short blue text
        if len(points) < 15:  # Increased from 5 - links have many more pixels
            continue
        
        # Check cluster width (X range) - real links span wide
        x_coords = [p['x'] for p in points]
        y_coords = [p['y'] for p in points]
        min_x = min(x_coords)
        max_x = max(x_coords)
        width = max_x - min_x
        
        # Real links are at least 100-150px wide, short labels are <80px
        if width < 100:
            continue
        
        # Real links are not too far left (icons/labels are around x<200)
        avg_x = sum(x_coords) // len(x_coords)
        if avg_x < 220:  # Too far left, probably not a link
            continue
        
        # Use median Y for more accurate positioning (avg can be skewed by outliers)
        y_coords_sorted = sorted(y_coords)
        median_y = y_coords_sorted[len(y_coords_sorted) // 2]
        
        # Skip navigation bar completely (Immagini, Video, Notizie, etc.) - Y < 220
        if median_y < 220:
            continue
        
        # Get most common color in cluster
        if points:
            sample_color = points[0]['color']
            links.append({'x': avg_x, 'y': median_y, 'color': sample_color, 'width': width, 'pixels': len(points)})
    
    # Sort top to bottom
    links.sort(key=lambda l: l['y'])
    
    print(f"DEBUG Color Detection: Found {len(blue_pixels)} blue pixels in {len(links)} valid link clusters")
    for i, link in enumerate(links[:5], 1):
        print(f"  Link {i}: ({link['x']}, {link['y']}) RGB{link['color']} - width:{link['width']}px, pixels:{link['pixels']}")
    
    return links


def extract_links_with_ocr(image: Image.Image) -> list:
    """
    Extract clickable links from screenshot using OCR.
    Returns list of dicts with {text, x, y, width, height}
    """
    links = []
    
    if HAS_EASYOCR:
        try:
            import numpy as np
            reader = easyocr.Reader(['en', 'it'], gpu=False)
            
            # Convert PIL to numpy array
            img_array = np.array(image)
            
            # Extract text with bounding boxes
            results = reader.readtext(img_array)
            
            # Look for patterns that indicate links
            for (bbox, text, confidence) in results:
                if confidence < 0.3:
                    continue
                
                # Calculate center coordinates
                top_left = bbox[0]
                bottom_right = bbox[2]
                x = int((top_left[0] + bottom_right[0]) / 2)
                y = int((top_left[1] + bottom_right[1]) / 2)
                width = int(bottom_right[0] - top_left[0])
                height = int(bottom_right[1] - top_left[1])
                
                # Check if this looks like a link (has URL patterns, is blue text area, etc.)
                is_link = (
                    any(pattern in text.lower() for pattern in ['http', 'www', '.com', '.it', '.org']) or
                    (len(text) > 10 and height > 15 and y > 150 and y < 600)  # Likely title text
                )
                
                if is_link or len(text) > 20:  # Long text is likely a title
                    links.append({
                        'text': text,
                        'x': x,
                        'y': y,
                        'width': width,
                        'height': height,
                        'confidence': confidence
                    })
            
            print(f"DEBUG OCR: Found {len(links)} potential links")
            return links
            
        except Exception as e:
            print(f"EasyOCR error: {e}")
    
    return links


def find_search_result_links(image: Image.Image) -> list:
    """
    Find Google search result links using color detection + OCR.
    Returns list of {text, x, y} sorted from top to bottom.
    """
    import numpy as np
    from collections import defaultdict
    
    img_array = np.array(image)
    height, width = img_array.shape[:2]
    
    # Google search results are typically blue links (#1a0dab is Google's blue)
    # Look for blue-ish pixels in the typical search result area
    blue_links = []
    
    # Scan the left-center area where search results appear
    for y in range(150, min(height, 700), 10):  # Every 10 pixels
        for x in range(180, min(width, 650), 5):  # Left side where results are
            pixel = img_array[y, x]
            b, g, r = pixel[0], pixel[1], pixel[2]
            
            # Check if this is Google's blue color (or similar)
            # Google blue is around RGB(26, 13, 171)
            if r < 100 and g < 80 and b > 120:  # Blue-ish
                blue_links.append({'x': x, 'y': y})
    
    # Group nearby blue pixels (likely same link)
    if not blue_links:
        return []
    
    # Cluster blue pixels by Y coordinate (same line = same link)
    clusters = defaultdict(list)
    for point in blue_links:
        # Round Y to nearest 20 pixels for clustering
        cluster_y = (point['y'] // 20) * 20
        clusters[cluster_y].append(point)
    
    # Get the center of each cluster
    result_links = []
    for cluster_y, points in clusters.items():
        if len(points) < 5:  # Too few points, probably not a link
            continue
        
        avg_x = sum(p['x'] for p in points) // len(points)
        avg_y = sum(p['y'] for p in points) // len(points)
        
        result_links.append({
            'x': avg_x,
            'y': avg_y,
            'text': f'Link at y={avg_y}'
        })
    
    # Sort from top to bottom
    result_links.sort(key=lambda l: l['y'])
    
    print(f"DEBUG: Found {len(result_links)} blue link areas")
    for i, link in enumerate(result_links[:5]):
        print(f"  Link {i+1}: ({link['x']}, {link['y']})")
    
    return result_links


def image_to_base64(image: Image.Image) -> str:
    """Convert PIL Image to base64 string."""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str


def analyze_screen_with_vision(image: Image.Image, user_command: str, conversation_context: str = "") -> dict:
    """
    Analyze screen for actions. 
    NOW: Uses color detection for click commands (more reliable than vision model).
    Direct detection for scroll (no vision model needed).
    Vision model only for type actions.
    """
    
    command_lower = user_command.lower()
    
    # SCROLL: Direct detection (no vision model needed!)
    # Use only specific phrases to avoid false positives with "su" (on) or "ci" (us/there)
    scroll_keywords_down = ['scorri giù', 'scendi', 'scroll down', 'scorri verso il basso', 'vai giù', 'pagina giù']
    scroll_keywords_up = ['scorri su', 'sali', 'scroll up', 'scorri verso l\'alto', 'vai su', 'pagina su']
    
    if any(keyword in command_lower for keyword in scroll_keywords_down):
        print("DEBUG: SCROLL DOWN detected - no vision model needed")
        return {
            "action": "scroll",
            "direction": "down",
            "amount": 300,
            "message": "Scorro verso il basso"
        }
    
    if any(keyword in command_lower for keyword in scroll_keywords_up):
        print("DEBUG: SCROLL UP detected - no vision model needed")
        return {
            "action": "scroll",
            "direction": "up",
            "amount": 300,
            "message": "Scorro verso l'alto"
        }
    
    # CLICK: Color detection
    if any(word in command_lower for word in ['click', 'clic', 'apri', 'link', 'primo', 'secondo', 'terzo']):
        print("DEBUG: Click command detected - using COLOR DETECTION instead of vision model")
        
        # Parse which link number
        link_number = 1
        if 'secondo' in command_lower or 'second' in command_lower or '2' in user_command:
            link_number = 2
        elif 'terzo' in command_lower or 'third' in command_lower or '3' in user_command:
            link_number = 3
        elif 'quarto' in command_lower or '4' in user_command:
            link_number = 4
        
        # Use color detection to find links
        links = find_google_links_by_color(image)
        
        if links and len(links) >= link_number:
            target = links[link_number - 1]
            return {
                "action": "click",
                "x": target['x'],
                "y": target['y'],
                "message": f"Clicco sul {link_number}° link",
                "debug_info": f"Color detection: link {link_number} at ({target['x']}, {target['y']})"
            }
        else:
            return {
                "action": "none",
                "message": f"Non trovo abbastanza link. Ho trovato {len(links)} link ma hai chiesto il {link_number}°"
            }
    
    # TYPE: Only use vision model for typing (needs to see where to type)
    if 'scrivi' in command_lower or 'type' in command_lower or 'digita' in command_lower:
        print("DEBUG: TYPE command - using vision model")
        return analyze_with_vision_model(image, user_command, conversation_context)
    
    # Default: unknown command
    return {
        "action": "none",
        "message": "Non ho capito cosa vuoi che faccia sullo schermo"
    }


def analyze_with_vision_model(image: Image.Image, user_command: str, conversation_context: str = "") -> dict:
    """
    Original vision model analysis - now used only for scroll/type, not for clicks.
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
        context_section = f"\nContext: {conversation_context}\n"

    # MUCH SHORTER PROMPT - Vision models work better with concise instructions
    prompt_text = f"""Analyze this screenshot (resolution: {width}x{height}).{context_section}

User command: "{user_command}"

Task:
- For SCROLL: detect direction and amount
- For TYPE: extract text to type (if command says "scrivi ciò", use context)

Return ONLY this JSON:
{{
    "action": "scroll" or "type" or "none",
    "direction": "up"/"down" (scroll only),
    "amount": <pixels> (scroll only),
    "text": "<text>" (type only),
    "message": "Italian description"
}}

Be concise and precise."""

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
