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
- Librerie Python (gestite tramite requirements.txt)

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
