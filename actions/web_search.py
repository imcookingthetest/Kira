import re
from serpapi import GoogleSearch
from tts import edge_speak


MAX_SNIPPETS = 3
MIN_SENTENCE_LENGTH = 30


def clean(text: str) -> str:
    """Clean text: remove extra spaces, ..., brackets."""
    if not text:
        return ""

    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\.\.\.+", ".", text)          
    text = re.sub(r"\[.*?\]", "", text)           
    text = re.sub(r"\(.*?\)", "", text)           
    return text.strip()


def split_sentences(text: str):
    """Split text into sentences and avoid very short or incomplete ones."""
    sentences = re.split(r"(?<=[.!?])\s+", text)

    valid_sentences = []
    buffer = ""

    for s in sentences:
        s = clean(s)
        if not s:
            continue

        last_word = s.split()[-1].lower()
        if last_word in [
            "of", "in", "at", "on", "by",
            "after", "before", "with", "for", "to"
        ]:
            buffer += s + " "
            continue

        if buffer:
            s = buffer + s
            buffer = ""

        if len(s) >= MIN_SENTENCE_LENGTH:
            valid_sentences.append(s)

    return valid_sentences


def is_noise(text: str) -> bool:
    """Check if a sentence is noise or irrelevant."""
    t = text.lower()

    noise_keywords = [
        "read more",
        "learn more",
        "click here",
        "infographic",
        "google trends",
        "year in search",
        "most searched",
        "top 100",
        "subscribe",
        "share this",
        "advertisement",
        "ad:"
    ]

    return any(word in t for word in noise_keywords)


def select_best_sentence(snippets):
    """Combine up to MAX_SNIPPETS and return a single coherent sentence."""
    final_text = ""
    count = 0

    for snippet in snippets:
        if not snippet or is_noise(snippet):
            continue

        sentences = split_sentences(snippet)

        for s in sentences:
            if is_noise(s):
                continue

            final_text = f"{final_text} {s}".strip()
            count += 1

            if count >= MAX_SNIPPETS:
                return final_text

    return final_text if final_text else None


def serpapi_answer(query: str, api_key: str) -> str:
    """Perform search and return a single coherent sentence."""
    params = {
        "q": query,
        "engine": "google",
        "hl": "en",
        "gl": "us",
        "num": 3,
        "api_key": api_key
    }

    try:
        data = GoogleSearch(params).get_dict()
    except Exception as e:
        print(f"WEB SEARCH ERROR: {e}")
        return "Sir, the web search failed."

    if "error" in data:
        print(f"SERPAPI ERROR: {data['error']}")
        return f"Sir, search error: {data['error']}"

    organic = data.get("organic_results", [])
    if not organic:
        print(f"DEBUG: No organic results found. Data keys: {data.keys()}")
        # Fallback: return special marker to trigger browser search
        return None  # This will trigger browser fallback in web_search()

    snippets = [
        r.get("snippet", "")
        for r in organic
        if r.get("snippet")
    ]

    answer = select_best_sentence(snippets)

    if not answer:
        return "Sir, I found information online, but couldn't summarize it clearly."

    return answer



def web_search(
    parameters: dict,
    player=None,
    session_memory=None,
    api_key: str = ""
):
    """
    Main web search:
    - Returns 1 coherent sentence
    - Does NOT append previous answers
    - Combines multiple snippets if needed to avoid cut-offs
    """

    query = (parameters or {}).get("query", "").strip()

    if not api_key or "INSERT_YOUR" in api_key or "API_KEY" == api_key:
        msg = "Sir, the web search API key is missing or invalid."
        if player:
            player.write_log(msg)
        edge_speak(msg)
        return msg

    if not query:
        msg = "Sir, I couldn't understand the search request."
        if player:
            player.write_log(msg)
        edge_speak(msg)
        return msg

    answer = serpapi_answer(query, api_key)
    
    # If API search fails or returns no results, open browser instead
    if not answer:
        import webbrowser
        import urllib.parse
        search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        webbrowser.open(search_url)
        msg = f"Ho aperto la ricerca nel browser, Sir."
        if player:
            player.write_log(msg)
        edge_speak(msg)
        return msg

    if player:
        player.write_log(f"AI: {answer}")

    edge_speak(answer)

    if session_memory:
        session_memory.set_last_search(query, answer)

    return answer
