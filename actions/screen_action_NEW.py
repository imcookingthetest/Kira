# Screen action feature - OCR + Color detection for reliable link clicking
# Much more reliable than vision model coordinates

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

# Try to import OCR libraries (optional)
try:
    import easyocr
    HAS_EASYOCR = True
except ImportError:
    HAS_EASYOCR = False
    print("Info: easyocr not installed. Using color detection only.")


def capture_screen():
    """Capture the entire screen."""
    screenshot = pyautogui.screenshot()
    return screenshot
