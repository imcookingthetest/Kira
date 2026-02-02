import os
import re
import webbrowser
from difflib import SequenceMatcher
from dotenv import load_dotenv
from tts import edge_speak
import pywhatkit as kit
import time

load_dotenv()

# Contact mapping from environment variables
# Format in .env: CONTACT_NAME=+391234567890
def load_contacts():
    """Load contacts from .env file with CONTACT_ prefix"""
    contacts = {}
    for key, value in os.environ.items():
        if key.startswith("CONTACT_"):
            name = key.replace("CONTACT_", "").lower().replace("_", " ")
            contacts[name] = value
    return contacts

CONTACTS = load_contacts()

# State management for 2-step message sending
whatsapp_state = {
    "waiting_for_message": False,
    "contact_name": None
}

def normalize(text: str):
    """Normalize text for comparison"""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def smart_match(user_input: str, command: str):
    """Smart matching algorithm for commands"""
    user = normalize(user_input)
    cmd = normalize(command)

    if cmd in user:
        return True

    user_words = set(user.split())
    cmd_words = set(cmd.split())

    if cmd_words and len(user_words & cmd_words) / len(cmd_words) >= 0.6:
        return True

    return SequenceMatcher(None, user, cmd).ratio() >= 0.6


def match_commands(user_input: str, commands: list):
    """Check if user input matches any command in the list"""
    return any(smart_match(user_input, cmd) for cmd in commands)


def extract_contact_name(user_text: str):
    """Extract contact name from user text"""
    normalized = normalize(user_text)
    
    # Patterns to match contact name (Italian + English)
    patterns = [
        r"(?:invia|manda|messaggio|send|message)(?:\s+un)?(?:\s+messaggio)?(?:\s+whatsapp)?(?:\s+a|to|per)\s+(\w+)",
        r"whatsapp(?:\s+a|to|per)\s+(\w+)",
        r"(?:apri|mostra|open|show)(?:\s+chat)?(?:\s+whatsapp)?(?:\s+con|with|a)?\s+(\w+)",
        r"(?:scrivi|scrivere|write)(?:\s+a|to)\s+(\w+)",
        r"^(\w+)(?:\s+whatsapp|\s+messaggio)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, normalized)
        if match:
            potential_name = match.group(1).strip()
            skip_words = ["whatsapp", "messaggio", "message", "chat", "invia", "manda", "send", "un", "una"]
            if potential_name in skip_words:
                continue
                
            # Check if this name exists in contacts
            if potential_name in CONTACTS:
                return potential_name
            # Check for partial matches
            for contact_name in CONTACTS.keys():
                if potential_name in contact_name or contact_name in potential_name:
                    return contact_name
    
    return None


def extract_message(user_text: str):
    """Extract message content from user text"""
    normalized_text = user_text.lower()
    
    # Patterns to extract message (Italian + English)
    patterns = [
        r"(?:chiedendogli|chiedendole|chiedigli|chiedile|chiedendo|ask|asking)(?:\s+se)?(?:\s+come)?\s+(.+)",
        r"(?:digli|dille|tell)(?:\s+che)?\s+(.+)",
        r"(?:dicendo|saying)\s+(.+)",
        r"['\"](.+)['\"]",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, normalized_text)
        if match:
            message = match.group(1).strip()
            # Remove contact name from message if it appears at start
            for contact_name in CONTACTS.keys():
                if message.startswith(contact_name):
                    message = message[len(contact_name):].strip()
                if message.startswith(f"a {contact_name}"):
                    message = message[len(f"a {contact_name}"):].strip()
            skip_words = ["a", "per", "su", "whatsapp", "messaggio", "message"]
            if message and len(message) > 2 and message not in skip_words:
                if not (message.startswith("a ") and len(message.split()) <= 2):
                    return message
    
    return None


def get_contact_number(contact_name: str):
    """Get phone number for a contact"""
    normalized_name = normalize(contact_name)
    return CONTACTS.get(normalized_name)


def list_available_contacts():
    """Get formatted list of available contacts"""
    if not CONTACTS:
        return "Nessun contatto configurato."
    
    contact_list = ", ".join([name.title() for name in CONTACTS.keys()])
    return f"Contatti disponibili: {contact_list}"


def send_whatsapp_instant(phone_number: str, message: str, player):
    """Send WhatsApp message using pywhatkit instantly"""
    try:
        if player:
            player.write_log(f"Apro WhatsApp per {phone_number}")
        
        kit.sendwhatmsg_instantly(
            phone_no=phone_number,
            message=message,
            wait_time=7,  # Ridotto da 15 a 7 secondi
            tab_close=False,
            close_time=2  # Ridotto da 3 a 2 secondi
        )
        
        time.sleep(1)  # Ridotto da 2 a 1 secondo
        return True
    except Exception as e:
        print(f"Error sending WhatsApp message: {e}")
        return False


def open_whatsapp_chat(contact_name: str, player):
    """Open WhatsApp Web chat with a specific contact"""
    phone_number = get_contact_number(contact_name)
    
    if not phone_number:
        text = f"Non trovo {contact_name} nei tuoi contatti. {list_available_contacts()}"
        if player:
            player.write_log(text)
        edge_speak(text, player)
        return
    
    url = f"https://web.whatsapp.com/send?phone={phone_number.replace('+', '')}"
    webbrowser.open(url)
    
    text = f"Apro la chat WhatsApp con {contact_name.title()}."
    if player:
        player.write_log(text)
    edge_speak(text, player)


def send_whatsapp_message(contact_name: str, message: str, player):
    """Send a WhatsApp message to a contact"""
    phone_number = get_contact_number(contact_name)
    
    if not phone_number:
        text = f"Non trovo {contact_name} nei tuoi contatti. {list_available_contacts()}"
        if player:
            player.write_log(text)
        edge_speak(text, player)
        return
    
    if not message:
        text = f"Nessun messaggio rilevato. Per favore specifica cosa vuoi inviare a {contact_name.title()}."
        if player:
            player.write_log(text)
        edge_speak(text, player)
        return
    
    text = f"Preparo l'invio del messaggio a {contact_name.title()}: '{message}'. Invio ora."
    if player:
        player.write_log(text)
    edge_speak(text, player)
    
    success = send_whatsapp_instant(phone_number, message, player)
    
    if success:
        text = f"Messaggio inviato con successo a {contact_name.title()}."
        if player:
            player.write_log(text)
        edge_speak(text, player)
    else:
        text = f"Impossibile inviare il messaggio a {contact_name.title()}. Controlla la connessione a WhatsApp Web."
        if player:
            player.write_log(text)
        edge_speak(text, player)


def handle_whatsapp_command(user_text, player):
    """Main handler for WhatsApp commands"""
    global whatsapp_state
    
    # Check if we're waiting for message content (2-step process)
    if whatsapp_state["waiting_for_message"]:
        contact_name = whatsapp_state["contact_name"]
        user_input = user_text.strip().lower()
        
        # Check if user is just repeating the contact name
        is_just_contact_name = False
        cleaned_input = user_input
        for prefix in ["a ", "per ", "si ", "sì ", "ok ", "yes "]:
            if cleaned_input.startswith(prefix):
                cleaned_input = cleaned_input[len(prefix):]
        
        if cleaned_input == contact_name or cleaned_input in contact_name or contact_name in cleaned_input:
            if len(user_input.split()) <= 3:
                is_just_contact_name = True
        
        if is_just_contact_name:
            text = f"Hai già specificato {contact_name.title()} come destinatario. Dimmi il messaggio che vuoi inviargli."
            if player:
                player.write_log(text)
            edge_speak(text, player)
            return True
        
        # Input is the actual message
        message = user_text.strip()
        
        # Reset state
        whatsapp_state["waiting_for_message"] = False
        whatsapp_state["contact_name"] = None
        
        # Send the message
        send_whatsapp_message(contact_name, message, player)
        return True
    
    # Command: Open WhatsApp Web
    if match_commands(user_text, [
        "apri whatsapp",
        "apri whatsapp web",
        "avvia whatsapp",
        "open whatsapp",
        "open whatsapp web",
        "launch whatsapp"
    ]):
        webbrowser.open("https://web.whatsapp.com")
        text = "Apro WhatsApp Web."
        if player:
            player.write_log(text)
        edge_speak(text, player)
        return True
    
    # Command: List contacts
    if match_commands(user_text, [
        "lista contatti",
        "mostra contatti",
        "contatti whatsapp",
        "a chi posso scrivere",
        "list contacts",
        "show contacts",
        "whatsapp contacts",
        "who can i message"
    ]):
        text = list_available_contacts()
        if player:
            player.write_log(text)
        edge_speak(text, player)
        return True
    
    # Command: Open chat with specific contact
    # IMPORTANT: Solo se contiene "chat" o "whatsapp" nel comando
    if match_commands(user_text, [
        "apri chat",
        "apri chat whatsapp",
        "apri whatsapp chat",
        "mostra chat",
        "chat whatsapp con",
        "open chat",
        "open whatsapp chat",
        "show chat",
        "whatsapp chat with"
    ]) and ("chat" in user_text.lower() or "whatsapp" in user_text.lower()):
        contact_name = extract_contact_name(user_text)
        if contact_name:
            open_whatsapp_chat(contact_name, player)
        else:
            text = f"Per favore specifica quale contatto. {list_available_contacts()}"
            if player:
                player.write_log(text)
            edge_speak(text, player)
        return True
    
    # Command: Send WhatsApp message
    if match_commands(user_text, [
        "invia whatsapp",
        "invia messaggio",
        "invia un messaggio",
        "messaggio whatsapp",
        "invia messaggio su whatsapp",
        "messaggio su whatsapp",
        "manda whatsapp",
        "manda messaggio",
        "manda un messaggio",
        "scrivi su whatsapp",
        "scrivi a",
        "scrivi un messaggio",
        "send whatsapp",
        "whatsapp message",
        "send message on whatsapp",
        "message on whatsapp",
        "send a whatsapp"
    ]):
        contact_name = extract_contact_name(user_text)
        message = extract_message(user_text)
        
        # If contact found but no message, enter 2-step mode
        if contact_name and not message:
            whatsapp_state["waiting_for_message"] = True
            whatsapp_state["contact_name"] = contact_name
            text = f"Cosa vuoi inviare a {contact_name.title()}?"
            if player:
                player.write_log(text)
            edge_speak(text, player)
            return True
        
        # If both contact and message found, send directly
        if contact_name and message:
            send_whatsapp_message(contact_name, message, player)
            return True
        
        # If no contact found at all
        if not contact_name:
            text = f"Per favore specifica a chi vuoi inviare il messaggio. {list_available_contacts()}"
            if player:
                player.write_log(text)
            edge_speak(text, player)
            return True
    
    return False
