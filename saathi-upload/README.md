# Saathi: a voice-first AI companion for older adults in India

Built solo at Product (Un)Conference Speedrun, Bengaluru, 22 Nov 2026.

**Problem:** millions of Indian parents over 50 live alone while their children work in other cities or abroad. They can use WhatsApp but little else. They worry about their health and about fraud, and they don't want to keep asking their children for help.

**What Saathi does (one flow, in Hindi, by voice):**
1. **Acute health:** "I've been dizzy since morning." Saathi checks for danger signs, asks clarifying questions, and **remembers her history** ("same as 18 Aug, when you skipped dinner on Metformin, sugar 68, juice helped"). It guides low-sugar first aid and logs readings.
2. **Chronic care:** it connects today's episode to tomorrow's fasting blood test, with preparation instructions, and notes it for her doctor.
3. **Fraud:** "A bank caller asked me to add a payee for KYC." Saathi blocks it.
4. **Child behind the scenes:** her son Arjun gets a WhatsApp-style feed (summaries, urgent alerts) and her live health record.

## Tools used
- **Claude (Opus 5.5)**: reasoning, tool use (log_health_event, notify_family, flag_message), vision to read scam screenshots, and replies in Indian languages
- **ElevenLabs**: speech-to-text (Scribe) and text-to-speech (eleven_v3) for Indian languages, including Kannada. Sarvam AI is supported as a backup voice provider.
- **Flask** (Python), plain HTML/JS; hosted on **Replit**

## What's mocked
- **WhatsApp:** a WhatsApp-style web chat stands in for a WhatsApp Business number (that needs Meta approval).
- **Family WhatsApp** is shown on the /family page; no real messages are sent.
- Health history is sample data for one demo user (Shanta, 68). In the product, children forward reports and PDFs on WhatsApp.
- A demo clock starts at 7:40 AM (set DEMO_CLOCK=off for real time).
- Passwords are deliberately **not** stored.

## Run it
```bash
pip install -r requirements.txt
# put ANTHROPIC_API_KEY and ELEVENLABS_API_KEY in .env (or Replit Secrets)
python app.py   # http://localhost:5050  ·  family view at /family
```
