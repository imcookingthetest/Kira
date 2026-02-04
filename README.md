# 🤖 Kira AI — Assistente Desktop AI Locale

## 📜 Copyright

Copyright (c) 2026 [Lorenzo_Miola]

All Rights Reserved.

This code is publicly visible for viewing and educational purposes only.

You are NOT allowed to copy, modify, reuse, redistribute, sublicense, or use any part of this code in other projects without explicit written permission from the author.

The project name, branding, and visual identity may not be reused.

---

## 📖 Descrizione

**Kira AI** è un assistente desktop AI modulare e completamente locale, sviluppato interamente in Python. 

Questo progetto italiano nasce con l'obiettivo di offrire un assistente intelligente che funziona al 100% in locale sul tuo computer, garantendo privacy e controllo totale sui tuoi dati.

Kira AI ti permette di controllare il tuo computer utilizzando comandi vocali attraverso un sistema di riconoscimento intenti → azioni, offrendo un'esperienza fluida e naturale nell'interazione con il tuo sistema.

## 🚀 Funzionalità Principali

- **🎙️ Controllo Vocale**: Comanda il tuo computer usando la voce
- **🔊 Text-to-Speech**: Kira risponde con una voce sintetizzata
- **💬 Conversazione Intelligente**: Chat naturale con memoria del contesto
- **📱 Messaggistica**: Invio messaggi WhatsApp
- **🌐 Ricerca Web**: Effettua ricerche online
- **🌦️ Meteo**: Ottieni previsioni meteorologiche
- **✈️ Report Aerei**: Informazioni su voli e traffico aereo
- **💻 Apertura Applicazioni**: Avvia programmi con un comando
- **🖥️ Controllo Schermo**: Gestisci operazioni dello schermo
- **🧠 Sistema di Memoria**:
  - Memoria temporanea per conversazioni a breve termine
  - Memoria a lungo termine per ricordare informazioni importanti
- **🔌 Architettura Modulare**: Facilmente estendibile con nuove azioni

## 🏗️ Architettura

Kira AI è costruito con un'architettura modulare che separa chiaramente le diverse componenti:

- **main.py**: Entry point dell'applicazione e loop principale
- **speech_to_text.py**: Modulo per il riconoscimento vocale
- **tts.py**: Modulo text-to-speech per le risposte vocali
- **llm.py**: Gestione del modello linguistico e elaborazione comandi
- **ui.py**: Interfaccia utente
- **feedback_sound.py**: Feedback sonori per l'utente
- **actions/**: Directory contenente tutti i moduli di azione
  - aircraft_report.py
  - open_app.py
  - screen_action.py
  - weather_report.py
  - web_search.py
  - whatsapp_action.py
- **memory/**: Sistema di gestione della memoria
  - memory_manager.py: Gestione memoria a lungo termine
  - temporary_memory.py: Gestione memoria temporanea

## 🔐 Sicurezza e Privacy

- ✅ Funziona **100% in locale** sul tuo computer
- ✅ Nessun accesso remoto di default
- ✅ Nessun dato inviato a server esterni
- ✅ Controllo totale su cosa viene eseguito
- ⚠️ Kira esegue solo ciò che **TU hai programmato**

**ATTENZIONE**: Non incollare codice sconosciuto o dare controllo completo del sistema a script non verificati.

## 🛠️ Requisiti

- Python 3.11 o superiore
- Sistema operativo Windows
- Modello Vosk italiano per il riconoscimento vocale

## 📦 Installazione Librerie

### Librerie Fondamentali

Prima di avviare Kira AI, installa tutte le librerie necessarie:

```bash
pip install python-dotenv requests sounddevice vosk pyautogui pillow numpy customtkinter edge-tts pywhatkit SpeechRecognition pyaudio
```

**Librerie principali e loro utilizzo:**

| Libreria | Versione Min | Scopo |
|----------|-------------|-------|
| `customtkinter` | 5.0+ | Interfaccia grafica moderna con dark theme |
| `vosk` | 0.3.45+ | Riconoscimento vocale offline italiano |
| `sounddevice` | 0.4.6+ | Cattura audio dal microfono |
| `edge-tts` | 6.1+ | Sintesi vocale (Text-to-Speech) |
| `pyautogui` | 0.9.54+ | Automazione schermo (click, scroll) |
| `pillow` (PIL) | 10.0+ | Processing immagini per screen detection |
| `numpy` | 1.24+ | Analisi colori per rilevamento link |
| `requests` | 2.31+ | Chiamate API (OpenRouter, SerpAPI) |
| `python-dotenv` | 1.0+ | Gestione variabili d'ambiente (.env) |
| `pywhatkit` | 5.4+ | Invio messaggi WhatsApp |

### Modello Vosk Italiano

Scarica il modello italiano completo per il riconoscimento vocale:

1. **Download**: [vosk-model-it-0.22](https://alphacephei.com/vosk/models) (~1.5GB)
2. **Estrai** la cartella in: `C:\Users\<TuoNome>\Downloads\vosk-model-it-0.22\`
3. **Configura** il path in `speech_to_text.py`:
   ```python
   MODEL_PATH = r"C:\Users\<TuoNome>\Downloads\vosk-model-it-0.22\vosk-model-it-0.22"
   ```

### File .env (Configurazione API)

Crea un file `.env` nella root del progetto con le tue API keys:

```env
OPENROUTER_API_KEY=your_openrouter_key_here
SERP_API_KEY=your_serpapi_key_here
```

**Dove ottenere le API keys:**
- **OpenRouter**: [openrouter.ai](https://openrouter.ai) - per il modello LLM (arcee-ai/trinity-large-preview:free)
- **SerpAPI**: [serpapi.com](https://serpapi.com) - per ricerche web (opzionale, fallback su browser)

## 📋 Limitazioni d'Uso

Questo progetto è protetto da copyright. Consulta la sezione Copyright all'inizio di questo documento per i dettagli completi.

**NON è permesso**:
- Uso commerciale
- Vendita o monetizzazione del progetto
- Rivendere o presentare questo progetto come proprio
- Modificare e ridistribuire senza permesso esplicito
- Riutilizzare il nome, branding o identità visiva del progetto

**È permesso**:
- Visualizzazione del codice a scopo educativo
- Studio dell'architettura e dell'implementazione

---

## 👨‍💻 Autore

Creato da **Lorenzo Miola**

Per qualsiasi domanda, richiesta di permesso o collaborazione, contatta l'autore.
