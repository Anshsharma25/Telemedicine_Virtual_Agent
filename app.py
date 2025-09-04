# app.py (updated)
import os
import re
import uuid
import secrets
import time
from pathlib import Path
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from dotenv import load_dotenv

# Optional project imports (best-effort)
try:
    from agents import symptom_chain, connect_agent, search_agent, followup_chain
except Exception:
    symptom_chain = connect_agent = search_agent = followup_chain = None

try:
    from document import maindocument
except Exception:
    maindocument = None

try:
    from Database.DB import create_table, get_user, save_user, update_user
except Exception:
    create_table = get_user = save_user = update_user = None

# doctor data import (optional)
_doctors = None
try:
    from Database import doctor_data as _dd
    _doctors = getattr(_dd, "doctors", None)
except Exception:
    _doctors = None

# fallback sample doctors for testing if DB not present
if not _doctors:
    _doctors = [
        {"id": "D1001", "name": "Dr. Amit", "specialty": "General Physician",
         "slots": ["09:00 AM", "10:00 AM", "11:30 AM", "03:00 PM"], "booked_slots": []},
        {"id": "D1002", "name": "Dr. Rupa Sharma", "specialty": "General Physician",
         "slots": ["09:30 AM", "11:30 AM", "01:00 PM", "04:00 PM"], "booked_slots": []}
    ]

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = ROOT_DIR / "templates"
STATIC_DIR = ROOT_DIR / "static"
UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = Flask(
    __name__,
    template_folder=str(TEMPLATES_DIR),
    static_folder=str(STATIC_DIR),
    static_url_path="/static"
)
CORS(app)

# --- session & metadata config ---
SESSIONS = {}  # in-memory; replace with Redis for production
META_ORDER_DEFAULT = ["visited_before", "name", "gender", "location"]
META_PROMPTS = {
    "visited_before": "Have you visited before? (yes/no)",
    "existing_user_id": "Please enter your previous User ID (or type 'new' to register as new).",
    "name": "What's your name?",
    "gender": "What is your gender (male/female/other)?",
    "location": "Please tell me your location (city).",
    "symptom_improved": "Have your previous symptoms improved? (yes/no)",
    "book_appointment": "Would you like me to book an appointment with a doctor? (yes/no)",
    "book_doctor_id": "Please enter the Doctor ID you'd like to book (from the list).",
    "book_slot": "Please enter your preferred slot for the selected doctor (e.g., 10:30 AM)."
}
EXIT_COMMANDS = {"by", "exit", "quit", "bye"}


def init_app():
    try:
        if create_table:
            create_table()
            app.logger.info("DB create_table() executed (startup init).")
    except Exception as e:
        app.logger.warning("DB create_table failed during startup init: %s", e)


init_app()


def new_session():
    sid = secrets.token_hex(8)
    SESSIONS[sid] = {
        "created": time.time(),
        "state": "collecting_meta",
        "meta_order": META_ORDER_DEFAULT.copy(),
        "meta": {},
        "last_bot": "Hello! I'm your telemedicine assistant.",
        "pending_followups": "",
        "booking": {},
        # doctor-mode fields:
        "doctor_mode": False,
        "doctor_turns": 0,
    }
    return sid


def check_exit(val: str):
    return str(val or "").strip().lower() in EXIT_COMMANDS


def speak_response(resp):
    if hasattr(resp, "content"):
        return resp.content
    elif isinstance(resp, dict) and "content" in resp:
        return resp["content"]
    else:
        return str(resp)


# ---------------- small helper to call chains robustly ----------------
def call_chain(chain, payload):
    """
    Call a langchain-style chain robustly. Prefer invoke if present, else run, else __call__.
    """
    if chain is None:
        raise ValueError("No chain provided")
    try:
        if hasattr(chain, "invoke"):
            return chain.invoke(payload)
        elif hasattr(chain, "run"):
            # keep using run for backwards compatibility
            return chain.run(payload)
        else:
            return chain(payload)
    except Exception as e:
        # re-raise for caller to handle
        raise


# ---------------- structured 9-point helpers ----------------
def extract_numbered_sections(text):
    out = {}
    if not text:
        return out
    pattern = re.compile(r'(?ms)^\s*(\d{1,2})\.\s*(.+?)(?=^\s*\d{1,2}\.\s+|\Z)', re.MULTILINE)
    for num_str, body in pattern.findall(text):
        try:
            out[int(num_str)] = body.strip()
        except:
            continue
    if not out:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        for i, ln in enumerate(lines[:9], start=1):
            out[i] = ln
    return out


def build_9_point_from_text(text, meta=None, meet_link=None):
    extracted = extract_numbered_sections(text or "")
    items = [None] * 9
    for i in range(1, 10):
        items[i - 1] = extracted.get(i)

    lower = (text or "").lower()
    # sensible defaults
    if not items[0]:
        items[0] = (text or "").splitlines()[0].strip() if text else "Diagnosis not available."
    if not items[1]:
        items[1] = ("Gynecologist / Endocrinologist" if any(k in lower for k in ("period", "menstru", "pcos", "ovary"))
                    else "General Physician / Specialist as advised")
    if not items[2]:
        items[2] = "OTC & immediate remedies (examples): antacids, analgesics or PPIs as appropriate. Consult doctor before starting."
    if not items[3]:
        items[3] = "Preventive measures: maintain healthy weight, avoid triggers, regular exercise, avoid late heavy meals."
    if not items[4]:
        items[4] = "Diet recommendations: balanced diet, avoid excessive spicy/fatty foods, stay hydrated."
    if not items[5]:
        items[5] = "Home remedies: warm compress for cramps, chew gum after meals, rest, ginger/peppermint for digestion if suitable."
    if not items[6]:
        items[6] = "Recommended tests: as per clinician (e.g., ultrasound, hormone panel, CBC) — urgent if red flags present."
    if not items[7]:
        items[7] = "Follow-up: review with clinician in 1-2 weeks or earlier if symptoms worsen or red flags appear."
    if not items[8]:
        loc = meta.get("location") if meta else "(unknown)"
        uid = meta.get("user_id") if meta else None
        items[8] = f"Location: {loc}" + (f" • User ID: {uid}" if uid else "")

    if meet_link:
        items[8] = items[8] + f" • Telemedicine: {meet_link}"

    # build HTML (string) and return list
    html_lines = ["<ol style='margin:0 0 0 16px;padding:0'>"]
    for v in items:
        safe = v or "-"
        html_lines.append(f"<li style='margin:6px 0'>{safe}</li>")
    html_lines.append("</ol>")
    return items, "\n".join(html_lines)


# Compose bot message but avoid repeating same last_bot
def compose_and_dedupe(session, main_text, extra_prompt=None):
    bot_text = (main_text or "").strip()
    if extra_prompt and extra_prompt not in bot_text:
        bot_text = bot_text + "\n\n" + extra_prompt
    # if exactly same as previously stored last_bot, return only extra_prompt (so frontend shows only prompt once)
    if bot_text == session.get("last_bot"):
        bot_text = extra_prompt or ""
    session["last_bot"] = bot_text
    return bot_text


# ---------------- API ----------------
@app.route("/")
def index():
    idx = TEMPLATES_DIR / "index.html"
    if not idx.exists():
        return "templates/index.html not found", 404
    return render_template("index.html")


@app.route("/favicon.ico")
def favicon():
    fav = ROOT_DIR / "favicon.ico"
    if fav.exists():
        return send_file(str(fav))
    return "", 204


@app.route("/api/doctors")
def api_doctors():
    out = []
    for d in _doctors:
        out.append({
            "id": d.get("id"),
            "name": d.get("name"),
            "specialty": d.get("specialty"),
            "slots": d.get("slots", []),
            "booked_slots": d.get("booked_slots", [])
        })
    return jsonify(success=True, doctors=out)


@app.route("/api/patients")
def api_patients():
    patients = []
    for sid, s in SESSIONS.items():
        m = s.get("meta") or {}
        uid = m.get("user_id")
        name = m.get("name")
        if uid:
            patients.append({"id": uid, "name": name or "Patient"})
    return jsonify(success=True, patients=patients)


@app.route("/api/book", methods=["POST"])
def api_book():
    data = request.get_json() or {}
    doctor_id = data.get("doctor_id")
    slot = data.get("slot")
    if not doctor_id or not slot:
        return jsonify(success=False, error="doctor_id and slot required"), 400

    try:
        from Appointment import book_appointment as external_book
    except Exception:
        external_book = None

    found = None
    for d in _doctors:
        if str(d.get("id")) == str(doctor_id):
            found = d
            break

    if found:
        available = found.get("slots", [])
        booked = found.setdefault("booked_slots", [])
        if slot not in available:
            return jsonify(success=False, error="Slot not found for this doctor", available_slots=available), 400
        if slot in booked:
            free = [s for s in available if s not in booked]
            return jsonify(success=False, error="Slot already booked", available_slots=free), 409
        booked.append(slot)
        return jsonify(success=True, result={"doctor_id": doctor_id, "slot": slot, "message": f"Booked {found.get('name')} at {slot}"}), 200

    if external_book:
        try:
            result = external_book(str(doctor_id), slot)
            return jsonify(success=True, result=result), 200
        except Exception as e:
            return jsonify(success=False, error=f"External booking failed: {e}"), 500

    return jsonify(success=False, error="Doctor not found"), 404


@app.route("/api/submit", methods=["POST"])
def submit():
    try:
        form = request.form
        session_id = form.get("session_id", "") or ""
        mode = form.get("mode", "").lower()
        user_message = form.get("message", "").strip()
        file = request.files.get("file")
        # doctor_mode may be sent by client (as '1' or 'true')
        doctor_mode_flag = str(form.get("doctor_mode", "") or "").lower() in ("1", "true", "yes")

        # create session if missing or if client asked init
        if mode == "init" or not session_id:
            session_id = new_session()
            first_field = SESSIONS[session_id]["meta_order"][0]
            bot_text = SESSIONS[session_id]["last_bot"] + " " + META_PROMPTS[first_field]
            return jsonify({
                "success": True,
                "session_id": session_id,
                "bot_message": bot_text,
                "expecting_field": first_field
            })

        # ping support
        if mode == "ping":
            session = SESSIONS.get(session_id)
            if not session:
                session_id = new_session()
                first_field = SESSIONS[session_id]["meta_order"][0]
                bot_text = SESSIONS[session_id]["last_bot"] + " " + META_PROMPTS[first_field]
                return jsonify({
                    "success": True,
                    "session_id": session_id,
                    "bot_message": bot_text,
                    "expecting_field": first_field
                })
            return jsonify(success=True, session_id=session_id, bot_message=session.get("last_bot", ""))

        # ensure session exists
        session = SESSIONS.get(session_id)
        if not session:
            session_id = new_session()
            first_field = SESSIONS[session_id]["meta_order"][0]
            bot_text = SESSIONS[session_id]["last_bot"] + " " + META_PROMPTS[first_field]
            return jsonify({
                "success": True,
                "session_id": session_id,
                "bot_message": bot_text,
                "expecting_field": first_field
            })

        # If client requested to enable doctor mode on session (e.g., upload or user toggle)
        if doctor_mode_flag:
            session["doctor_mode"] = True
            session["doctor_turns"] = 0

        # universal exit handling
        if check_exit(user_message):
            SESSIONS.pop(session_id, None)
            return jsonify(success=True, session_id=session_id, bot_message="Session ended. To start again call init.")

        # quick state shortcuts
        state = session.get("state", "collecting_meta")

        # If we asked the returning user whether symptoms improved
        if state == "awaiting_improvement":
            ans = user_message.strip().lower()
            if ans in ("yes", "y"):
                bot_text = "Very good! Glad to hear your symptoms improved. If you need further help later, start a new session."
                session["state"] = "ready"
                session["last_bot"] = bot_text
                return jsonify(success=True, session_id=session_id, bot_message=bot_text, meta=session.get("meta"))
            else:
                session["state"] = "ready"
                bot_text = "I'm sorry to hear that. Please describe your current symptoms in a few sentences so I can help."
                session["last_bot"] = bot_text
                return jsonify(success=True, session_id=session_id, bot_message=bot_text)

        # booking flow ...
        if state == "awaiting_book_confirmation":
            ans = user_message.strip().lower()
            if ans in ("yes", "y"):
                doctors = _doctors if _doctors else []
                session["state"] = "awaiting_book_doctor"
                session["last_bot"] = "Please choose a Doctor ID from the list."
                return jsonify(success=True, session_id=session_id, bot_message="Sure — here are available doctors.", doctors=doctors, expecting_field="book_doctor_id")
            else:
                session["state"] = "ready"
                session["last_bot"] = "Okay — no appointment will be booked now. Let me know if you need anything else."
                return jsonify(success=True, session_id=session_id, bot_message=session["last_bot"])

        if state == "awaiting_book_doctor":
            chosen_id = user_message.strip()
            doctors = _doctors if _doctors else []
            found = None
            for d in doctors:
                if str(d.get("id")) == str(chosen_id) or str(d.get("id")) == str(chosen_id).strip():
                    found = d
                    break
            if not found:
                return jsonify(success=False, error="Doctor ID not found. Please enter a valid Doctor ID from the provided list."), 400
            session["booking"] = {"doctor_id": found.get("id")}
            session["state"] = "awaiting_book_slot"
            session["last_bot"] = f"Selected {found.get('name')}. Please enter preferred slot (e.g., 10:30 AM) or choose from available slots: {', '.join([s for s in found.get('slots',[]) if s not in found.get('booked_slots',[])])}"
            return jsonify(success=True, session_id=session_id, bot_message=session["last_bot"], expecting_field="book_slot")

        if state == "awaiting_book_slot":
            slot = user_message.strip()
            booking_info = session.get("booking", {})
            doctor_id = booking_info.get("doctor_id")
            if not doctor_id:
                session["state"] = "ready"
                return jsonify(success=False, error="No doctor selected. Please start booking again."), 400
            try:
                found = None
                for d in _doctors:
                    if str(d.get("id")) == str(doctor_id):
                        found = d
                        break
                if found:
                    if slot not in found.get("slots", []):
                        free = [s for s in found.get("slots", []) if s not in found.get("booked_slots", [])]
                        return jsonify(success=False, error="Slot not found for this doctor", available_slots=free), 400
                    if slot in found.get("booked_slots", []):
                        free = [s for s in found.get("slots", []) if s not in found.get("booked_slots", [])]
                        return jsonify(success=False, error="Slot already booked", available_slots=free), 409
                    found.setdefault("booked_slots", []).append(slot)
                    session["state"] = "ready"
                    session["booking"] = {}
                    session["last_bot"] = f"Booking result: ✅ Booked {found.get('name')} at {slot}"
                    return jsonify(success=True, session_id=session_id, bot_message=session["last_bot"])
                from Appointment import book_appointment
                result = book_appointment(str(doctor_id), slot)
                session["state"] = "ready"
                session["booking"] = {}
                session["last_bot"] = f"Booking result: {result}"
                return jsonify(success=True, session_id=session_id, bot_message=session["last_bot"])
            except Exception as e:
                return jsonify(success=False, error=f"Booking failed: {e}"), 500

        # ------------ Meta collection special-case: handle visited_before=yes by asking for existing_user_id ------------
        if session["state"] == "collecting_meta":
            if not session["meta_order"]:
                session["state"] = "ready"
            else:
                current_field = session["meta_order"].pop(0)
                if current_field == "visited_before":
                    val = user_message.strip().lower()
                    session["meta"]["visited_before"] = val
                    if val in ("yes", "y"):
                        session["meta_order"] = ["existing_user_id"] + [f for f in session["meta_order"] if f != "existing_user_id"]
                        next_field = "existing_user_id"
                        session["last_bot"] = META_PROMPTS[next_field]
                        return jsonify(success=True, session_id=session_id, bot_message=META_PROMPTS[next_field], expecting_field=next_field)
                    else:
                        if session["meta_order"]:
                            next_field = session["meta_order"][0]
                            session["last_bot"] = META_PROMPTS[next_field]
                            return jsonify(success=True, session_id=session_id, bot_message=META_PROMPTS[next_field], expecting_field=next_field)
                        else:
                            session["state"] = "ready"
                            session["last_bot"] = "Thanks. Please describe your symptoms in a few sentences so I can help."
                            return jsonify(success=True, session_id=session_id, bot_message=session["last_bot"])

                elif current_field == "existing_user_id":
                    provided = user_message.strip()
                    if provided.lower() == "new":
                        session["meta"]["visited_before"] = "no"
                        session["meta_order"] = [f for f in META_ORDER_DEFAULT if f != "visited_before"]
                        next_field = session["meta_order"][0]
                        session["last_bot"] = META_PROMPTS[next_field]
                        return jsonify(success=True, session_id=session_id, bot_message=session["last_bot"], expecting_field=next_field)
                    try:
                        urec = get_user(provided) if get_user else None
                    except Exception:
                        urec = None
                    if urec:
                        try:
                            session["meta"]["user_id"] = provided
                            if len(urec) > 1 and urec[1]:
                                session["meta"]["name"] = urec[1]
                            if len(urec) > 2 and urec[2]:
                                session["meta"]["previous_symptoms"] = urec[2]
                            if len(urec) > 4 and urec[4]:
                                session["meta"]["previous_diagnosis"] = urec[4]
                            if len(urec) > 3 and urec[3]:
                                session["meta"]["location"] = urec[3]
                            session["meta"]["visited_before"] = "yes"
                        except Exception:
                            pass
                        session["state"] = "awaiting_improvement"
                        prev_sym = session["meta"].get("previous_symptoms", "N/A")
                        prev_diag = session["meta"].get("previous_diagnosis", "N/A")
                        name = session["meta"].get("name", "")
                        loc = session["meta"].get("location", "")
                        bot_text = f"Welcome back {name or ''}.\nPrevious Symptoms: {prev_sym}\nPrevious Diagnosis: {prev_diag}\nLocation: {loc}\n\n{META_PROMPTS['symptom_improved']}"
                        session["last_bot"] = bot_text
                        return jsonify(success=True, session_id=session_id, bot_message=bot_text, meta=session["meta"], expecting_field="symptom_improved")
                    else:
                        session["meta"]["visited_before"] = "no"
                        session["meta_order"] = [f for f in META_ORDER_DEFAULT if f != "visited_before"]
                        next_field = session["meta_order"][0]
                        session["last_bot"] = f"User ID not found. {META_PROMPTS[next_field]}"
                        return jsonify(success=True, session_id=session_id, bot_message=session["last_bot"], expecting_field=next_field)

                else:
                    session["meta"][current_field] = user_message
                    if session["meta_order"]:
                        next_field = session["meta_order"][0]
                        session["last_bot"] = META_PROMPTS[next_field]
                        return jsonify(success=True, session_id=session_id, bot_message=session["last_bot"], expecting_field=next_field)
                    else:
                        session["state"] = "ready"
                        session["last_bot"] = "Thanks. Please describe your symptoms in a few sentences so I can help."
                        return jsonify(success=True, session_id=session_id, bot_message=session["last_bot"])

        # --- session ready: handle file uploads & message as symptom text ---
        meta = session.get("meta", {})
        visited_before = meta.get("visited_before", "no")
        name = meta.get("name", "Anonymous")
        gender = meta.get("gender", "other")
        location = meta.get("location", "")

        user_input_text = user_message
        # handle file uploads
        if file:
            fname = f"{secrets.token_hex(8)}_{file.filename}"
            saved_path = UPLOAD_DIR / fname
            # explicit save as string path
            file.save(str(saved_path))
            # if client explicitly set doctor_mode flag, keep it (we already set above)
            # process file by mode
            if mode == "document":
                if maindocument:
                    try:
                        user_input_text = maindocument(str(saved_path)) or ""
                    except Exception as e:
                        app.logger.exception("Document processing failed: %s", e)
                        return jsonify(success=False, error="Document processing failed on server."), 500
                else:
                    # fallback: return success but indicate we don't have document pipeline
                    # still allow doctor-mode to be enabled
                    return jsonify(success=True, session_id=session_id, bot_message="Document uploaded (no parser available). You can ask questions about the document.", doctor_mode_enabled=True)
            elif mode == "image":
                try:
                    from tools import analyze_medical_image
                    user_input_text = analyze_medical_image(str(saved_path)) or ""
                except Exception:
                    user_input_text = ""
            elif mode == "audio":
                try:
                    import speech_utils as su
                    transcribe_audio_file = getattr(su, "transcribe_audio_file", None)
                except Exception:
                    transcribe_audio_file = None
                if transcribe_audio_file:
                    try:
                        user_input_text = transcribe_audio_file(str(saved_path)) or ""
                    except Exception as e:
                        app.logger.exception("Audio transcription failed: %s", e)
                        user_input_text = ""
                else:
                    return jsonify(success=False, error="Audio received but no transcription available on server."), 400

        # Doctor-mode behaviour: act like a real doctor for up to 2 message turns, do not follow prompt templates
        if session.get("doctor_mode", False) and session.get("state", "") in ("ready", "awaiting_followups", ""):
            # increment doctor turns
            session["doctor_turns"] = session.get("doctor_turns", 0) + 1

            # Build a payload that includes the required keys (some chains expect user_location and followup_answers)
            payload = {
                "input": user_input_text or "",
                "search_results": (search_agent.run(user_input_text) if search_agent else "No search agent"),
                "user_location": location or "",
                "followup_answers": ""
            }

            try:
                # prefer invoke/run/__call__ robustly
                resp = call_chain(symptom_chain, payload) if symptom_chain else {"content": "Doctor (mock): Based on your input, please rest and hydrate. Seek care if worse."}
            except ValueError as ve:
                # often ValueError from langchain indicates missing input keys; try to recover by adding missing keys as empty
                app.logger.exception("Doctor-mode symptom_chain initial call raised ValueError: %s", ve)
                try:
                    # attempt to extract missing keys from the exception message
                    missing = set()
                    m = re.findall(r"\{(.+?)\}", str(ve))
                    # fallback: ensure keys exist
                    payload.setdefault("user_location", payload.get("user_location", ""))
                    payload.setdefault("followup_answers", "")
                    # try again
                    resp = call_chain(symptom_chain, payload) if symptom_chain else {"content": "Doctor (mock): Based on your input, please rest and hydrate. Seek care if worse."}
                except Exception as e2:
                    app.logger.exception("Doctor-mode symptom_chain.retry failed: %s", e2)
                    resp = {"content": "Doctor (error): I couldn't generate a full answer, please try again or ask to connect to a real clinician."}
            except Exception as e:
                app.logger.exception("Doctor-mode symptom_chain.run failed: %s", e)
                resp = {"content": "Doctor (error): I couldn't generate a full answer, please try again or ask to connect to a real clinician."}

            bot_text = speak_response(resp)

            # after doctor reply count reaches 2, disable doctor_mode automatically
            if session["doctor_turns"] >= 2:
                session["doctor_mode"] = False
                session["doctor_turns"] = 0
                return jsonify(success=True, session_id=session_id, bot_message=bot_text, doctor_mode_ended=True)

            return jsonify(success=True, session_id=session_id, bot_message=bot_text, doctor_mode_still_active=True)

        if not user_input_text:
            bot_text = "Please describe your symptoms in a few sentences so I can help."
            session["last_bot"] = bot_text
            return jsonify(success=True, session_id=session_id, bot_message=bot_text)

        # If server waiting for followups (previously generated), treat this message as answers
        if session.get("state") == "awaiting_followups":
            followup_answers = user_input_text
            session["pending_followups"] = ""
            session["state"] = "ready"

            combined_input = f"Gender: {gender}\nFollowup Answers: {followup_answers}\nSymptoms: {user_input_text}"
            try:
                search_results = "No additional context available."
                if search_agent:
                    search_query = f"{user_input_text} near {location}" if location else user_input_text
                    search_results = search_agent.run(search_query)
            except Exception:
                search_results = "No additional context available."

            try:
                if symptom_chain:
                    diagnosis_response = symptom_chain.run({
                        "input": combined_input,
                        "search_results": search_results,
                        "user_location": location,
                        "followup_answers": followup_answers
                    })
                else:
                    diagnosis_response = {"content": "Mock diagnosis: rest and fluids recommended."}
            except Exception as e:
                app.logger.exception("symptom_chain.run failed: %s", e)
                return jsonify(success=False, error="Failed to generate diagnosis."), 500

            diagnosis_text = speak_response(diagnosis_response)

            # Save/update DB
            try:
                if visited_before.lower() in ("no", "n"):
                    if save_user:
                        uid = str(uuid.uuid4())[:8]
                        save_user(name, user_input_text, location, diagnosis_response, uid)
                        session["meta"]["user_id"] = uid
                else:
                    uid = session["meta"].get("user_id", "")
                    if uid and update_user:
                        update_user(uid, user_input_text, location, diagnosis_response)
            except Exception:
                app.logger.warning("DB save/update failed.")

            meet_link = None
            try:
                lower_diag = str(diagnosis_response).lower()
                if ("immediate medical attention" in lower_diag or "life-threatening" in lower_diag) and connect_agent:
                    connection_output = connect_agent.run("Check availability and generate meet link")
                    urls = re.findall(r"https?://\S+", str(connection_output))
                    meet_link = urls[0] if urls else None
            except Exception:
                pass

            structured_list, structured_html = build_9_point_from_text(diagnosis_text, meta=session["meta"], meet_link=meet_link)

            doctors = _doctors if _doctors else []

            session["state"] = "awaiting_book_confirmation"
            bot_message = compose_and_dedupe(session, diagnosis_text, META_PROMPTS["book_appointment"])
            resp = {
                "success": True,
                "session_id": session_id,
                "bot_message": bot_message,
                "structured": structured_list,
                "structured_html": structured_html,
                "meta": session["meta"],
                "followup_questions": "",
                "expecting_followup": False,
                "meet_link": meet_link,
                "ask_book_appointment": True,
                "doctors": doctors,
                "expecting_field": "book_appointment"
            }
            session["last_bot"] = bot_message
            return jsonify(resp)

        # Normal ready -> attempt to generate follow-ups first
        followup_questions = ""
        try:
            if followup_chain and not session.get("pending_followups") and session.get("state") == "ready":
                followup_questions = followup_chain.run(user_input_text) or ""
        except Exception:
            followup_questions = ""

        if followup_questions and str(followup_questions).strip():
            session["pending_followups"] = followup_questions
            session["state"] = "awaiting_followups"
            session["last_bot"] = followup_questions
            return jsonify({
                "success": True,
                "session_id": session_id,
                "bot_message": followup_questions,
                "followup_questions": followup_questions,
                "expecting_followup": True,
                "meta": session["meta"]
            })

        # No followups -> generate diagnosis immediately
        try:
            search_results = "No additional context available."
            if search_agent:
                search_query = f"{user_input_text} near {location}" if location else user_input_text
                search_results = search_agent.run(search_query)
        except Exception:
            search_results = "No additional context available."

        try:
            combined_input = f"Gender: {gender}\nSymptoms: {user_input_text}"
            if symptom_chain:
                diagnosis_response = symptom_chain.run({
                    "input": combined_input,
                    "search_results": search_results,
                    "user_location": location,
                    "followup_answers": ""
                })
            else:
                diagnosis_response = {"content": "Mock diagnosis: based on your symptoms, rest and fluids recommended."}
        except Exception as e:
            app.logger.exception("symptom_chain.run failed: %s", e)
            return jsonify(success=False, error="Failed to generate diagnosis."), 500

        diagnosis_text = speak_response(diagnosis_response)

        # Save/update DB
        try:
            if visited_before.lower() in ("no", "n"):
                if save_user:
                    uid = str(uuid.uuid4())[:8]
                    save_user(name, user_input_text, location, diagnosis_response, uid)
                    session["meta"]["user_id"] = uid
            else:
                uid = session["meta"].get("user_id", "")
                if uid and update_user:
                    update_user(uid, user_input_text, location, diagnosis_response)
        except Exception:
            app.logger.warning("DB save/update failed.")

        meet_link = None
        try:
            lower_diag = str(diagnosis_response).lower()
            if ("immediate medical attention" in lower_diag or "life-threatening" in lower_diag) and connect_agent:
                connection_output = connect_agent.run("Check availability and generate meet link")
                urls = re.findall(r"https?://\S+", str(connection_output))
                meet_link = urls[0] if urls else None
        except Exception:
            pass

        structured_list, structured_html = build_9_point_from_text(diagnosis_text, meta=session["meta"], meet_link=meet_link)

        doctors = _doctors if _doctors else []

        session["state"] = "awaiting_book_confirmation"
        bot_message = compose_and_dedupe(session, diagnosis_text, META_PROMPTS["book_appointment"])
        resp = {
            "success": True,
            "session_id": session_id,
            "bot_message": bot_message,
            "structured": structured_list,
            "structured_html": structured_html,
            "followup_questions": "",
            "expecting_followup": False,
            "meta": session["meta"],
            "meet_link": meet_link,
            "ask_book_appointment": True,
            "doctors": doctors,
            "expecting_field": "book_appointment"
        }
        session["last_bot"] = bot_message
        return jsonify(resp)

    except Exception as exc:
        app.logger.exception("Unexpected error in /api/submit: %s", exc)
        return jsonify(success=False, error=str(exc)), 500


if __name__ == "__main__":
    print(f"Starting app.py from: {ROOT_DIR}")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=False)

