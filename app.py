"""Saathi - a voice-first AI companion for older adults in India, with their children behind the scenes.

One small Flask app:
  /            parent's chat (WhatsApp-style, Hindi voice + text + screenshot)
  /family      child's view (Arjun's WhatsApp-style feed + Maa's health record)
  /api/chat    text (+ optional image) -> Claude agent -> reply (+ spoken audio)
  /api/voice   audio -> speech-to-text -> agent -> text-to-speech
"""
import base64
import datetime as dt
import json
import os
import threading

import anthropic
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

load_dotenv()

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(APP_DIR, "data.json")
SARVAM_KEY = os.environ.get("SARVAM_API_KEY", "")
MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")

LANGUAGES = {
    "hi-IN": "Hindi",
    "kn-IN": "Kannada",
    "ta-IN": "Tamil",
    "te-IN": "Telugu",
    "ml-IN": "Malayalam",
    "mr-IN": "Marathi",
    "bn-IN": "Bengali",
    "gu-IN": "Gujarati",
    "en-IN": "English",
}

app = Flask(__name__, static_folder="static")
client = anthropic.Anthropic()
lock = threading.RLock()

# ---------------------------------------------------------------- seeded demo data (mocked history)


def _d(days):
    return (dt.date.today() + dt.timedelta(days=days)).strftime("%a %d %b %Y")


def seed():
    return {
        "profile": {
            "name": "Shanta Sharma",
            "call_her": "Shanta ji",
            "age": 68,
            "city": "Lucknow (Gomti Nagar), lives alone",
            "language": "hi-IN",
            "conditions": ["Type 2 diabetes (since 2017)", "High blood pressure (since 2019)", "Mild knee arthritis"],
            "allergies": ["Sulfa drugs"],
            "has_at_home": ["Glucometer", "BP machine"],
            "family": [
                {"name": "Arjun", "relation": "son", "city": "Bengaluru", "role": "primary contact, manages Saathi"},
                {"name": "Priya", "relation": "daughter", "city": "Toronto"},
            ],
            "doctor": "Dr. Anil Mehta (physician, Sahara Hospital), clinic 0522-400-0000",
            "emergency": "Ambulance 108; neighbour Mrs. Verma (flat 4B)",
        },
        "medicines": [
            {"name": "Metformin 500 mg", "when": "twice daily, after breakfast and after dinner", "for": "diabetes"},
            {"name": "Amlodipine 5 mg", "when": "every morning", "for": "blood pressure",
             "note": "increased from 2.5 mg on 12 Sep 2026 by Dr. Mehta"},
            {"name": "Calcium + Vitamin D3", "when": "after lunch", "for": "bones"},
        ],
        "history": [
            {"date": "Tue 18 Aug 2026", "type": "episode",
             "text": "Woke up dizzy/lightheaded and shaky. Had skipped dinner the night before (only tea) but took evening Metformin. "
                     "Glucometer reading 68 mg/dL at 7:50 AM. Drank half a glass of orange juice, then breakfast; "
                     "sugar 112 after 20 minutes and dizziness went away. Dr. Mehta (phone) said: low sugar from skipping "
                     "dinner while on Metformin - never skip dinner; if you can't eat, skip the evening Metformin and call him."},
            {"date": "Sun 30 Aug 2026", "type": "lab",
             "text": "Lab report (home collection): HbA1c 7.4% (May: 7.6%, Feb: 7.9%). Fasting sugar 128 mg/dL. "
                     "LDL cholesterol 118 mg/dL. Creatinine 0.9 (normal). Doctor: repeat HbA1c + lipid profile in 3 months."},
            {"date": "Sat 12 Sep 2026", "type": "doctor",
             "text": "Visit to Dr. Mehta: BP 150/95 at clinic. Amlodipine increased 2.5 mg -> 5 mg. Advised less salt, 20 min walk daily."},
            {"date": "Oct 2026", "type": "readings",
             "text": "Home BP readings mostly 128-136 / 80-86 after dose change. Morning fasting sugar 110-135."},
            {"date": _d(-1), "type": "readings", "text": "Evening: BP 132/84. Took evening Metformin at 9:15 PM."},
        ],
        "upcoming": [
            {"title": "Fasting blood test: HbA1c + lipid profile (home collection, lab technician comes home)",
             "when": f"{_d(1)}, 8:00 AM",
             "prep": "No food or tea for 10-12 hours before (water is fine). Take Metformin only after the test, with breakfast. "
                     "Amlodipine can be taken as usual with water."},
            {"title": "Follow-up with Dr. Mehta (bring test report and BP diary)", "when": f"{_d(5)}, 11:00 AM", "prep": ""},
        ],
        "today_log": [],
        "feed": [
            {"time": "Yesterday 9:20 PM", "level": "info", "title": "Evening check-in",
             "text": "Maa took her evening Metformin. BP 132/84 (normal for her). Chatted about Priya's video call."},
            {"time": "Yesterday 6:00 PM", "level": "info", "title": "Reminder set",
             "text": f"Home collection booked for her fasting HbA1c + lipid test on {_d(1)}, 8 AM. Saathi will remind her about fasting the night before."},
        ],
        "alerts": [],
        "med_checks": [],
        "finance": {
            "connected": ["SBI savings a/c xx4821 (read-only, via Account Aggregator)",
                          "Google Pay UPI shanta.sharma@oksbi (read-only)"],
            "guardrail": "Saathi can only READ. It cannot pay, approve, decline or move money.",
            "balance": "Rs 1,84,320",
            "usual_pattern": ("Pension Rs 32,400 credited on the 1st. Usual monthly payments: maid Kamla Rs 3,000 (UPI, 1st-5th), "
                              "Gupta Dairy milk ~Rs 1,800, LESA electricity ~Rs 1,600, Sharma Medicals Rs 1,200-2,500, "
                              "Jio recharge Rs 299, occasional sends to Arjun. Single payments are rarely above Rs 5,000. "
                              "She has never paid an unknown UPI ID and never approved a collect request."),
            "recent": [
                {"date": _d(-1), "what": "Paid Sharma Medicals (UPI)", "amount": "-Rs 1,860"},
                {"date": _d(-3), "what": "Paid Gupta Dairy (UPI)", "amount": "-Rs 1,750"},
                {"date": _d(-6), "what": "LESA electricity bill (UPI)", "amount": "-Rs 1,540"},
                {"date": _d(-9), "what": "Sent to Arjun (UPI)", "amount": "-Rs 2,000"},
                {"date": _d(-20), "what": "Paid Kamla (maid) (UPI)", "amount": "-Rs 3,000"},
                {"date": _d(-21), "what": "Pension credit, SBI", "amount": "+Rs 32,400"},
            ],
            "pending": [
                {"type": "Google Pay COLLECT request (asks HER to pay)", "from": "sbi.refund.kyc@ybl",
                 "shown_name": "SBI Customer Care", "amount": "Rs 4,999",
                 "note_on_request": "KYC refund processing - enter UPI PIN to receive refund", "received": "today, 7:35 AM"},
            ],
        },
    }


def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(seed())
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# Demo clock: the story happens in the morning, so time starts at DEMO_CLOCK (default 07:40) and runs forward.
DEMO_CLOCK = os.environ.get("DEMO_CLOCK", "07:40")
_clock_start = dt.datetime.now()


def now():
    if DEMO_CLOCK.lower() == "off":
        return dt.datetime.now()
    h, m = (int(x) for x in DEMO_CLOCK.split(":"))
    base = dt.datetime.combine(dt.date.today(), dt.time(h, m))
    return base + (dt.datetime.now() - _clock_start)


def now_str():
    return now().strftime("%I:%M %p").lstrip("0")


# ---------------------------------------------------------------- tools

TOOLS = [
    {
        "name": "log_health_event",
        "description": (
            "Write something into Shanta ji's health diary for today: a symptom she reports, a reading she gives "
            "(sugar, BP), food/medicine she took, or how she feels after advice. Call it whenever she tells you a "
            "new health fact, so the history stays up to date for her family and doctor."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "enum": ["symptom", "reading", "food", "medicine", "update"]},
                "summary": {"type": "string", "description": "Short English summary, e.g. 'Sugar 64 mg/dL at 7:45 AM'"},
            },
            "required": ["kind", "summary"],
            "additionalProperties": False,
        },
    },
    {
        "name": "notify_family",
        "description": (
            "Send a WhatsApp update to her son Arjun. level='urgent' for any danger sign or emergency (send immediately). "
            "level='attention' when a health episode has been handled and the family should know (send once the "
            "situation is clear, with a crisp summary: what happened, likely cause, readings, what she did, what's next), "
            "or for a blocked scam. level='info' for routine updates."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "level": {"type": "string", "enum": ["urgent", "attention", "info"]},
                "title": {"type": "string", "description": "3-6 word English title"},
                "message": {"type": "string", "description": "2-4 short English sentences for Arjun"},
            },
            "required": ["level", "title", "message"],
            "additionalProperties": False,
        },
    },
    {
        "name": "flag_message",
        "description": (
            "Record your verdict on a message, call, link or screenshot she asks about: anything involving money, "
            "OTP, PIN, KYC, adding a payee, installing an app, prizes, parcels, police, or account blocking."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "verdict": {"type": "string", "enum": ["scam", "suspicious", "safe"]},
                "risk": {"type": "integer", "description": "0-100 risk score"},
                "summary": {"type": "string", "description": "One English line: what the message/call claims"},
                "reasons": {"type": "string", "description": "Short English reasons"},
            },
            "required": ["verdict", "risk", "summary", "reasons"],
            "additionalProperties": False,
        },
    },
    {
        "name": "check_bank_activity",
        "description": (
            "Read-only look at Shanta ji's connected SBI account and Google Pay: balance, her usual payment pattern, "
            "recent transactions and any PENDING requests (e.g. UPI collect requests). Call this whenever money comes up: "
            "a payment request, refund, collect request, unknown debit, someone asking her to pay/approve/enter PIN."
        ),
        "strict": True,
        "input_schema": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
    },
    {
        "name": "medicine_check",
        "description": (
            "Record your check of a medicine the chemist/pharmacist gave her (brand name, strip or photo), compared "
            "with her prescribed medicine list."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "brand_seen": {"type": "string", "description": "Brand name + strength as on the strip, e.g. 'Glycomet-GP 1'"},
                "contains": {"type": "string", "description": "Active ingredients + strengths, e.g. 'Metformin 500 mg + Glimepiride 1 mg'"},
                "match": {"type": "string", "enum": ["same_medicine", "different", "unsure"]},
                "explanation": {"type": "string", "description": "One English line: how it compares with her prescription and what she should do"},
            },
            "required": ["brand_seen", "contains", "match", "explanation"],
            "additionalProperties": False,
        },
    },
]


def run_tool(name, args, channel, cards):
    with lock:
        data = load_data()
        if name == "log_health_event":
            data["today_log"].append({"time": now_str(), **args})
            cards.append({"type": "logged", **args})
            result = "Logged."
        elif name == "notify_family":
            data["feed"].insert(0, {"time": "Today " + now_str(), **args})
            cards.append({"type": "family", **args})
            result = "Arjun has been sent this on WhatsApp."
        elif name == "flag_message":
            data["alerts"].insert(0, {"time": now_str(), **args})
            cards.append({"type": "scam", **args})
            result = "Recorded."
        elif name == "check_bank_activity":
            cards.append({"type": "bank", "summary": "Read SBI + Google Pay (read-only): balance, usual pattern, recent and pending"})
            result = json.dumps(data.get("finance", {}), ensure_ascii=False)
        elif name == "medicine_check":
            data.setdefault("med_checks", []).insert(0, {"time": now_str(), **args})
            cards.append({"type": "medicine", **args})
            result = "Recorded."
        else:
            result = f"Unknown tool {name}"
        save_data(data)
    return result


# ---------------------------------------------------------------- agent

def system_prompt(lang_code, channel):
    data = load_data()
    lang = LANGUAGES.get(lang_code, "Hindi")
    record = {k: data.get(k) for k in ("profile", "medicines", "history", "upcoming", "today_log", "family_notes")}
    spoken = (
        "This is a PHONE CALL: no lists or symbols, at most 2 short sentences."
        if channel == "phone"
        else "Your reply is shown in a chat AND read aloud: no markdown, no bullet points, no emojis, at most 3 short sentences."
    )
    return f"""You are Saathi, a warm, patient companion for Shanta Sharma, a 68-year-old woman in Lucknow who lives alone. Her children live far away (son Arjun in Bengaluru manages Saathi for her). She uses WhatsApp but struggles with other technology.

Right now it is {now().strftime('%A %d %B %Y, %I:%M %p')}.

LANGUAGE: Always reply in simple, everyday spoken {lang} (Devanagari script for Hindi). Everyday English words Indians use are fine ("sugar", "BP", "test", "juice"). Call her "Shanta ji". {spoken}

HER RECORD (kept up to date by Arjun and by you). This is your memory of her; use it:
{json.dumps(record, ensure_ascii=False, indent=1)}

HOW TO HELP WITH HEALTH
- You are not a doctor and never diagnose with certainty, change medicine doses, or tell her to stop a prescribed medicine. You triage, remember, and connect her to family and doctor.
- When she reports a new symptom: FIRST rule out danger signs with one quick question (e.g. chest pain or pressure, breathlessness, slurred speech, face drooping, weakness on one side, fainting, confusion, very severe headache). If ANY danger sign: tell her to call 108 right now (or ask Mrs. Verma next door), stay calm, and immediately call notify_family with level 'urgent'.
- If no danger signs: ask short clarifying questions, ONE or TWO at a time, choosing the ones that her history makes most relevant (e.g. what she ate last night, whether she took her medicines, her glucometer/BP reading).
- Actively use her history: if something similar happened before, say so specifically, with the date, what the reading was, and what helped (e.g. "18 August ko bhi aisa hua tha..."). Ask if this feels the same.
- Low sugar guidance (standard): if sugar is below 70 mg/dL, have half a glass of fruit juice or 3 teaspoons of sugar in water, sit down, recheck after 15 minutes, then eat breakfast. If still below 70 after two tries, or she feels worse, notify family urgently and call the doctor.
- Log every new fact she tells you (symptom, reading, food, medicine) with log_health_event.
- Keep Arjun in the loop as it happens: the FIRST time she reports a new symptom, immediately call notify_family with level 'info' (e.g. "Maa says she feels dizzy this morning. No danger signs so far; I'm checking her sugar."). Do this in the same turn as your first question.
- Once an episode is handled and she is feeling better (or the situation is clear), send Arjun ONE notify_family 'attention' summary.
- Connect the dots with what's coming up: if an upcoming test or appointment is relevant (e.g. tomorrow's fasting test after today's low-sugar episode), remind her proactively with the exact preparation, and tell her you'll note today's episode for Dr. Mehta.

SAFETY FROM FRAUD
- If she mentions a call, message or person asking her to add a payee, share OTP/PIN/card details, do "KYC", install an app, pay a fee, or threatening to block her account: call flag_message, tell her firmly and kindly to stop and not do it (banks never ask this over the phone), and call notify_family with level 'attention'.
- Never ask for or repeat OTPs, PINs, passwords or card numbers. Never help add a payee or send money because someone else on a call asked her to.

MONEY (bank + UPI connected, READ-ONLY)
- Her SBI account and Google Pay are connected read-only. Whenever money comes up (a payment/collect request, "refund", unknown debit, someone asking her to pay, approve, or enter her UPI PIN), call check_bank_activity FIRST and compare with her usual pattern and pending requests. Mention the specific request you see (amount, UPI ID) so she knows you checked.
- Key facts to explain simply: entering the UPI PIN always SENDS money, it never receives it; a "collect request" asks her to pay; refunds never need a PIN; banks never ask to add a payee or do KYC over the phone.
- You cannot make, approve or decline any payment, and you never move money. Tell her exactly which button to press herself (e.g. "Decline"), and if it's a scam also call flag_message and notify_family ('attention').

MEDICINES FROM THE CHEMIST
- When she asks about a medicine name, strip or photo (e.g. the chemist gave a different brand): work out its active ingredients and strength (Indian brand names), compare with her medicine list, and call medicine_check.
- Same ingredient and strength: reassure her it's the same medicine from another company, take it exactly as before, and never take the old and new strips together.
- Different ingredient or strength (e.g. a combination tablet): tell her NOT to start it yet, keep taking her usual medicine, and ask the chemist or Dr. Mehta. Explain the risk in one simple sentence that uses her history (e.g. an extra sugar-lowering medicine after today's low sugar). Call notify_family ('attention').
- If you are not sure what the brand contains, say so and ask her to send a photo of the back of the strip.

PHONE HELP
- If she asks how to do something on her phone (a genuine request she started herself), guide ONE step at a time and ask her to tell you when it's done."""


# ---------------------------------------------------------------- Arjun's side (child keeps things up to date)

FAMILY_TOOLS = [
    {
        "name": "update_record",
        "description": (
            "Update Maa's health record when Arjun gives new information: a medicine change, a new upcoming "
            "test/appointment, a past event or lab result (e.g. from a report he uploads), or a standing instruction "
            "for Saathi to follow with Maa (e.g. 'remind her to walk 20 min after lunch')."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "section": {"type": "string", "enum": ["medicine", "upcoming", "history", "family_note"]},
                "title": {"type": "string", "description": "medicine name+dose / test or appointment title / event date (e.g. 'Sat 21 Nov 2026') / note"},
                "when": {"type": "string", "description": "medicine timing, or appointment date+time, or '' "},
                "details": {"type": "string", "description": "what it's for / prep instructions / full event text incl. values, or ''"},
            },
            "required": ["section", "title", "when", "details"],
            "additionalProperties": False,
        },
    }
]


def run_family_tool(name, args, cards):
    with lock:
        data = load_data()
        sec = args["section"]
        if sec == "medicine":
            meds = [m for m in data["medicines"] if m["name"].split()[0].lower() != args["title"].split()[0].lower()]
            meds.insert(0, {"name": args["title"], "when": args["when"], "for": args["details"], "note": f"updated by Arjun {now().strftime('%d %b')}"})
            data["medicines"] = meds
        elif sec == "upcoming":
            data["upcoming"].append({"title": args["title"], "when": args["when"], "prep": args["details"]})
        elif sec == "history":
            data["history"].append({"date": args["title"], "type": "added by Arjun", "text": args["details"]})
        else:
            data.setdefault("family_notes", []).append(args["title"] + (" - " + args["details"] if args["details"] else ""))
        save_data(data)
    cards.append({"type": "updated", **args})
    return "Record updated."


def family_system_prompt():
    data = load_data()
    record = {k: data.get(k) for k in ("profile", "medicines", "history", "upcoming", "today_log", "family_notes", "alerts", "med_checks", "finance")}
    recent = data["feed"][:8]
    return f"""You are Saathi, the AI companion that looks after Shanta Sharma (68, Lucknow). You are now talking on WhatsApp with her son Arjun (in Bengaluru), who manages Saathi for her.

Right now it is {now().strftime('%A %d %B %Y, %I:%M %p')}.

Reply in clear, warm English, like a WhatsApp message from a trusted carer: MAXIMUM 3 short sentences (under 60 words), concrete, with readings and times. No lists, no markdown. Mention at most one action for Arjun.

When Arjun asks how Maa is: summarise today's diary, any alerts, and what's coming up, and say if anything needs his action.\nWhen Arjun asks about money or unusual transactions: use the read-only bank/UPI data (balance, usual pattern, recent, pending requests), and point out anything outside her usual pattern. You cannot move or block money; suggest what he or Maa should do (e.g. decline the request, call the bank on the number on her passbook).
When Arjun gives new information (medicine change, new appointment/test, a lab report photo or PDF, an instruction for how to help Maa): call update_record (once per item), then confirm what you saved and how you will use it with Maa. For a lab report image: read the key values, compare with her past values in the record, flag anything out of range, and save it as a history entry.
Never invent readings. You are not a doctor: suggest checking with Dr. Mehta for medical decisions.

MAA'S RECORD:
{json.dumps(record, ensure_ascii=False, indent=1)}

RECENT MESSAGES YOU SENT ARJUN:
{json.dumps(recent, ensure_ascii=False, indent=1)}"""


HISTORY = {"chat": [], "phone": [], "family": []}


def ask_saathi(user_content, lang_code, channel="chat"):
    """Run one user turn through Claude with tools. Returns (reply_text, cards)."""
    history = HISTORY[channel]
    start = len(history)
    try:
        return _run_turn(history, user_content, lang_code, channel)
    except Exception:
        del history[start:]  # roll back a failed turn so the conversation stays valid
        raise


def _run_turn(history, user_content, lang_code, channel):
    history.append({"role": "user", "content": user_content})
    cards = []
    is_family = channel == "family"
    for _ in range(6):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=4000,
            system=family_system_prompt() if is_family else system_prompt(lang_code, channel),
            tools=FAMILY_TOOLS if is_family else TOOLS,
            messages=history,
            extra_headers={"anthropic-beta": "server-side-fallback-2026-07-01"},
            extra_body={"fallbacks": "default", "output_config": {"effort": "low"}},
        )
        history.append({"role": "assistant", "content": resp.content})
        if resp.stop_reason != "tool_use":
            break
        results = []
        for block in resp.content:
            if block.type == "tool_use":
                out = (run_family_tool if is_family else run_tool)(block.name, block.input, *([cards] if is_family else [channel, cards]))
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": out})
        history.append({"role": "user", "content": results})
    if resp.stop_reason == "refusal":
        return "माफ़ कीजिए, इसमें मैं मदद नहीं कर सकती।", cards
    text = " ".join(b.text for b in resp.content if b.type == "text").strip()
    return text, cards


# ---------------------------------------------------------------- voice (ElevenLabs, Sarvam as backup)

ELEVEN_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
ELEVEN_TTS_MODEL = os.environ.get("ELEVENLABS_TTS_MODEL", "eleven_v3")  # v3 covers Hindi + South Indian languages
ELEVEN_STT_MODEL = os.environ.get("ELEVENLABS_STT_MODEL", "scribe_v2")
_voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "")


def eleven_voice_id():
    """Use ELEVENLABS_VOICE_ID if set, else the first female voice on the account."""
    global _voice_id
    if not _voice_id:
        r = requests.get("https://api.elevenlabs.io/v1/voices", headers={"xi-api-key": ELEVEN_KEY}, timeout=20)
        r.raise_for_status()
        voices = r.json().get("voices", [])
        female = [v for v in voices if (v.get("labels") or {}).get("gender") == "female"]
        _voice_id = (female or voices)[0]["voice_id"]
        print("Using ElevenLabs voice:", (female or voices)[0].get("name"), _voice_id)
    return _voice_id


def eleven_stt(audio_bytes, filename, lang_code):
    r = requests.post(
        "https://api.elevenlabs.io/v1/speech-to-text",
        headers={"xi-api-key": ELEVEN_KEY},
        files={"file": (filename, audio_bytes)},
        data={"model_id": ELEVEN_STT_MODEL, "language_code": lang_code.split("-")[0]},
        timeout=60,
    )
    if not r.ok:
        print("ElevenLabs STT error:", r.status_code, r.text[:300])
    r.raise_for_status()
    return r.json().get("text", "")


FAST_TTS_LANGS = {"hi", "ta", "en"}  # covered by the low-latency Flash model; others need eleven_v3


def eleven_tts(text, lang_code):
    lang = lang_code.split("-")[0]
    model = os.environ.get("ELEVENLABS_FAST_MODEL", "eleven_flash_v2_5") if lang in FAST_TTS_LANGS else ELEVEN_TTS_MODEL
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{eleven_voice_id()}?output_format=mp3_44100_64",
        headers={"xi-api-key": ELEVEN_KEY, "Content-Type": "application/json"},
        json={"text": text[:4500], "model_id": model, "language_code": lang},
        timeout=60,
    )
    if not r.ok and model != ELEVEN_TTS_MODEL:
        print("Fast TTS failed, falling back to", ELEVEN_TTS_MODEL, r.status_code, r.text[:200])
        r = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{eleven_voice_id()}?output_format=mp3_44100_64",
            headers={"xi-api-key": ELEVEN_KEY, "Content-Type": "application/json"},
            json={"text": text[:4500], "model_id": ELEVEN_TTS_MODEL, "language_code": lang},
            timeout=60,
        )
    if not r.ok:
        print("ElevenLabs TTS error:", r.status_code, r.text[:300])
    r.raise_for_status()
    return base64.b64encode(r.content).decode()


def sarvam_stt(audio_bytes, filename, lang_code):
    r = requests.post(
        "https://api.sarvam.ai/speech-to-text",
        headers={"api-subscription-key": SARVAM_KEY},
        files={"file": (filename, audio_bytes)},
        data={"model": "saaras:v4", "language_code": lang_code or "unknown"},
        timeout=60,
    )
    r.raise_for_status()
    return r.json().get("transcript", "")


def sarvam_tts(text, lang_code):
    r = requests.post(
        "https://api.sarvam.ai/text-to-speech",
        headers={"api-subscription-key": SARVAM_KEY, "Content-Type": "application/json"},
        json={"text": text[:2500], "language_code": lang_code, "model": "bulbul:v3", "speaker": "priya",
              "pace": 0.9, "output_audio_codec": "mp3", "speech_sample_rate": 22050},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["audios"][0]


def speech_to_text(audio_bytes, filename, lang_code):
    if ELEVEN_KEY:
        return eleven_stt(audio_bytes, filename, lang_code)
    return sarvam_stt(audio_bytes, filename, lang_code)


def text_to_speech(text, lang_code):
    if not text or lang_code not in LANGUAGES:
        return None
    try:
        if ELEVEN_KEY:
            return eleven_tts(text, lang_code)
        if SARVAM_KEY:
            return sarvam_tts(text, lang_code)
    except Exception as e:  # keep the chat working even if voice fails
        print("TTS error:", e)
    return None


# ---------------------------------------------------------------- routes

@app.get("/")
def index():
    return send_from_directory("static", "index.html")


@app.get("/family")
def family():
    return send_from_directory("static", "family.html")


@app.get("/api/state")
def state():
    return jsonify(load_data())


def image_block(data_url):
    header, b64 = data_url.split(",", 1)
    return {"type": "image", "source": {"type": "base64", "media_type": header.split(";")[0][5:], "data": b64}}


@app.post("/api/chat")
def chat():
    body = request.get_json(force=True)
    lang = body.get("lang", "hi-IN")
    text = (body.get("text") or "").strip()
    image = body.get("image")
    content = [image_block(image)] if image and image.startswith("data:") else []
    content.append({"type": "text", "text": text or "(She sent this photo without any text. Look at it carefully, work out what it is, and tell her what to do about it.)"})
    reply, cards = ask_saathi(content, lang, "chat")
    return jsonify({"reply": reply, "cards": cards})


@app.post("/api/voice")
def voice():
    lang = request.form.get("lang", "hi-IN")
    f = request.files["audio"]
    transcript = speech_to_text(f.read(), f.filename or "voice.webm", lang)
    image = request.form.get("image")
    content = [image_block(image)] if image and image.startswith("data:") else []
    content.append({"type": "text", "text": transcript or "(could not hear clearly)"})
    reply, cards = ask_saathi(content, lang, "chat")
    return jsonify({"transcript": transcript, "reply": reply, "cards": cards})


@app.post("/api/family_chat")
def family_chat():
    body = request.get_json(force=True)
    text = (body.get("text") or "").strip()
    image = body.get("image")
    content = [image_block(image)] if image and image.startswith("data:") else []
    content.append({"type": "text", "text": text or "Here's Maa's latest report. Please read it and update her record."})
    with lock:
        data = load_data()
        data["feed"].insert(0, {"time": "Today " + now_str(), "level": "arjun", "title": "", "text": text or "📎 Sent a report",
                                "has_image": bool(image)})
        save_data(data)
    reply, cards = ask_saathi(content, "en-IN", "family")
    with lock:
        data = load_data()
        data["feed"].insert(0, {"time": "Today " + now_str(), "level": "reply", "title": "", "text": reply})
        save_data(data)
    return jsonify({"reply": reply, "cards": cards})


@app.get("/api/clock")
def clock():
    return jsonify({"ms": int(now().timestamp() * 1000)})


@app.get("/favicon.ico")
def favicon():
    return ("", 204)


@app.post("/api/tts")
def tts():
    body = request.get_json(force=True)
    return jsonify({"audio": text_to_speech(body.get("text", ""), body.get("lang", "hi-IN"))})


@app.post("/api/reset")
def reset():
    global _clock_start
    with lock:
        save_data(seed())
        _clock_start = dt.datetime.now()
    for h in HISTORY.values():
        h.clear()
    return jsonify({"ok": True})


@app.errorhandler(Exception)
def on_error(e):
    print("ERROR:", repr(e))
    msg = str(e)
    if "credit balance" in msg:
        msg = "Claude API has no credits on this key yet."
    return jsonify({"error": msg[:300]}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5050)), debug=False)
