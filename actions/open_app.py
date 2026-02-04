import time
import pyautogui
import webbrowser
from urllib.parse import quote_plus
from tts import edge_speak


def open_app(
    parameters: dict,
    response: str | None = None,
    player=None,
    session_memory=None
) -> bool:
    """
    Opens an application using Windows search.
    If it's a browser and search_query is provided, opens the browser with a search.

    parameters:
        - app_name (str): Name of the application
        - search_query (str, optional): Search query for browsers

    Memory behavior:
        - Uses ONLY session memory
        - No long-term memory writes
    """

    app_name = ((parameters or {}).get("app_name") or "").strip()
    search_query = ((parameters or {}).get("search_query") or "").strip()

    if not app_name and session_memory:
        app_name = session_memory.open_app or ""

    if not app_name:
        msg = "Sir, I couldn't determine which application to open."
        if player:
            player.write_log(msg)
        edge_speak(msg, player)
        return False

    if response:
        if player:
            player.write_log(response)
        edge_speak(response, player)

    try:
        # Check if it's a browser and we have a search query
        browsers = ["chrome", "firefox", "edge", "opera", "opera gx", "brave", "safari"]
        is_browser = any(browser in app_name.lower() for browser in browsers)

        if is_browser and search_query:
            # Open browser with search query
            search_url = f"https://www.google.com/search?q={quote_plus(search_query)}"
            webbrowser.open(search_url)
            time.sleep(1)
            
            if session_memory:
                session_memory.set_open_app(f"{app_name} (searching: {search_query})")
            
            return True
        else:
            # Normal app opening via Windows search
            pyautogui.PAUSE = 0.1

            pyautogui.press("win")
            time.sleep(0.3)

            pyautogui.write(app_name, interval=0.03)
            time.sleep(0.2)

            pyautogui.press("enter")
            time.sleep(0.6)

            if session_memory:
                session_memory.set_open_app(app_name)

            return True

    except Exception as e:
        msg = f"Sir, I failed to open {app_name}."
        if player:
            player.write_log(f"{msg} ({e})")
        edge_speak(msg, player)
        return False
