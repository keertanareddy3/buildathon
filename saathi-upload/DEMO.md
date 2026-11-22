# Saathi: demo script (3 min)

**Setup:** two Chrome windows side by side.
- Left: `localhost:5050`. Maa's WhatsApp chat with Saathi, plus a **Behind the scenes** panel showing what Saathi does.
- Right: `localhost:5050/family`. Arjun's WhatsApp with Saathi, plus Maa's live record.

Click **Reset demo** before starting.

**How it maps to real WhatsApp:** Saathi is a WhatsApp Business number. Maa sends **voice notes** (🎤). Saathi replies with a **text message plus a voice note** that she taps ▶ to hear; nothing plays by itself. Typed messages get text replies. 📞 in the header is a WhatsApp voice call, the one place Saathi speaks straight away.

## 0:00 – 0:20 · The user
"Shanta ji is 68 and lives alone in Lucknow. Her son Arjun is in Bengaluru. She can use WhatsApp, but nothing else. Saathi lets her look after her health and her phone herself, in Hindi, while Arjun stays in the background."

## 0:20 – 1:50 · Acute: dizzy in the morning (speak with 🎤 or type)
1. **"सुबह से थोड़ा चक्कर सा आ रहा है"** ("I've been a bit dizzy since morning.")
   → Saathi checks for **danger signs** first.
2. **"नहीं, ऐसा कुछ नहीं है। बस हल्का चक्कर और थोड़ी कमज़ोरी है"** ("No, nothing like that. Just a little dizzy and a bit weak.")
   → It **remembers 18 August**: the same dizziness, sugar 68, and juice helped. It asks her to check her sugar and whether she ate dinner.
3. **"रात को भूख नहीं थी, बस चाय पी थी। रात की दवाई ले ली थी। अभी sugar 64 आई है"** ("I wasn't hungry last night, I only had tea. I took my night medicine. My sugar is 64 now.")
   → Low-sugar steps: half a glass of juice, recheck in 15 minutes. Diary entries appear.
4. **"जूस पी लिया, अब sugar 98 है, थोड़ा बेहतर लग रहा है"** ("I drank the juice. Sugar is 98 now and I feel a bit better.")
   → **Chronic link:** "Your fasting test is tomorrow at 8 AM. Eat dinner tonight, then only water. Take Metformin after the test." Arjun is notified.

**Point to the right window:** Arjun's WhatsApp showed "Maa feeling dizzy" right away, and the summary when it was resolved. Today's diary has filled in.
**Then type, as Arjun:** "How is Maa doing?" Saathi answers in 2–3 sentences with readings.

## 1:50 – 2:20 · Fraud
5. *(Optional: switch to a call. Tap 📞 and say the next line out loud. It's the same assistant, speaking straight away.)*
   **"अभी एक आदमी का फ़ोन आया, बोला बैंक से है, KYC के लिए एक payee add करना है। payee कैसे add करते हैं?"** ("A man just called saying he's from the bank. He said I need to add a payee for KYC. How do I add a payee?")
   → "Stop, this is a scam." A red card appears, and Arjun gets a second alert.

## 2:20 – 3:00 · Why it works + what's mocked
- **Claude** gives general health intelligence plus **her own history** (episodes, labs, medicines, upcoming tests), and writes new events back into that history.
- **Safety:** it never diagnoses or changes doses. Danger signs mean 108 plus an urgent alert to family.
- **Mocked:** WhatsApp (a web chat stands in for WhatsApp Business), the health history (sample data; in the product Arjun forwards reports and PDFs), and the demo clock (starts at 7:40 AM).
- **Next:** a phone line for parents who can't read, a home voice device, reading Google Pay and bank statements to spot unusual spending, and step-by-step phone help.

## If something breaks
- Voice fails: type the same lines instead.
- A reply is slow (about 15 s): keep talking over it ("it's checking her history…").
- Things get messy: click **reset demo** and reload.
