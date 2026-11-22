# Saathi: so Maa never has to ask, and you never have to worry

An AI companion on WhatsApp for parents who live alone. It remembers their health history, guards their money, and keeps their children in the loop.

**Live demo:** [buildathon.replit.app](https://buildathon.replit.app) (parent) · [buildathon.replit.app/family](https://buildathon.replit.app/family) (child)

Built solo at Product (Un)Conference Speedrun, Bengaluru, 22 Nov 2026.

## Problem
Millions of Indian parents over 50 live alone while their children work in other cities or abroad. They can use WhatsApp but little else. They worry about their health and about fraud, and they don't want to keep asking their children for help. Their children want them to be independent, with help ready in the background.

## What Saathi does: one morning for Shanta ji (68, Lucknow, diabetes + BP), in Hindi, by voice note
1. **Acute health:** "I've been dizzy since morning." Saathi rules out danger signs first, asks clarifying questions, and **remembers her history** ("same as 18 Aug, when you skipped dinner on Metformin; sugar was 68 and juice helped"). It guides low-sugar first aid and logs her readings.
2. **Chronic care:** it connects today's episode to tomorrow's fasting blood test, with preparation instructions, and notes it for her doctor.
3. **Medicine check:** the chemist hands her "Glycomet-GP 1" and says it's the same. Saathi spots the extra glimepiride, which risks another low and conflicts with her sulfa allergy, and tells her not to take it. Works from a photo of the strip too.
4. **Fraud:** a ₹4,999 Google Pay "refund" asking for her UPI PIN, or a "bank" caller asking her to add a payee for KYC. Saathi explains that the PIN sends money, tells her to press Decline, and alerts her son.
5. **Child behind the scenes:** her son Arjun gets a WhatsApp feed (an alert as soon as something starts, then a summary). He can ask "How is Maa?", update her medicines or appointments, or send a lab report photo for Saathi to read into her record.

## How it maps to real WhatsApp
Saathi is a WhatsApp Business number. The parent sends text, photos or voice notes. Saathi replies with a text message, plus a voice note she taps to hear when she spoke. 📞 starts a WhatsApp Business voice call, the one place Saathi speaks straight away. The same assistant can sit behind a regular phone number for parents who can't read.

## Safety
- Never diagnoses, changes doses, or tells her to stop a prescribed medicine. It triages, remembers, and escalates.
- Danger signs (chest pain, slurred speech, one-sided weakness, fainting…) mean "call 108 now" plus an urgent alert to family.
- Never asks for or stores OTPs, PINs or passwords. It cannot make or approve payments.

## Tools used
- **Claude (Opus 5.5):** reasoning over the parent's longitudinal record; tool use (`log_health_event`, `notify_family`, `flag_message`, `update_record`); vision for medicine strips, scam screenshots and lab reports; replies in Indian languages
- **ElevenLabs:** speech-to-text (Scribe) and text-to-speech (Flash v2.5 for Hindi, eleven_v3 for Kannada, Telugu and other languages). Sarvam AI is supported as a backup voice provider.
- **Flask** (Python) and plain HTML/JS, hosted on **Replit**

## What's mocked
- **WhatsApp:** a WhatsApp-style web page stands in for a WhatsApp Business number (which needs Meta approval). The child's WhatsApp is the /family page; no real messages are sent.
- **Health history:** sample data for one demo user (Shanta, 68). In the product, children forward reports and PDFs on WhatsApp.
- **Demo clock:** starts at 7:40 AM (set `DEMO_CLOCK=off` for real time).
- **One shared demo session:** use **reset demo** on /family before each run.

## Next
A read-only bank and UPI connection (via India's Account Aggregator framework) to spot unusual spending, step-by-step phone help, a phone line for parents who can't read, and a home voice device.

## Run it
```bash
pip install -r requirements.txt
# put ANTHROPIC_API_KEY and ELEVENLABS_API_KEY in .env (or Replit Secrets)
python main.py   # http://localhost:5050  ·  child view at /family
```
