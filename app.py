# app.py
import os
import subprocess
from pathlib import Path

import streamlit as st
import requests
import json
import time
import re
import html
from datetime import datetime
import plotly.graph_objects as go
import pandas as pd
from streamlit_option_menu import option_menu

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="Actiboost AI Negotiator",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    :root {
        --bg: #f3f7ff;
        --panel: #ffffff;
        --panel-soft: #f8faff;
        --line: #e6edf7;
        --text: #0f172a;
        --muted: #64748b;
        --primary: #1d4ed8;
        --primary-dark: #102a6b;
        --success: #16a34a;
        --warning: #f59e0b;
        --danger: #ef4444;
    }

    .main {
        background: linear-gradient(180deg, #f5f8ff 0%, #eef4ff 100%);
        padding: 0 1rem 2rem 1rem;
    }

    .topbar {
        background: linear-gradient(135deg, #0f172a 0%, #172554 100%);
        padding: 1.1rem 1.5rem;
        border-radius: 18px;
        margin-bottom: 1rem;
        border: 1px solid rgba(148, 163, 184, 0.2);
        box-shadow: 0 12px 30px rgba(15, 23, 42, 0.12);
    }

    .topbar h1 {
        margin: 0;
        color: #ffffff;
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.04em;
    }

    .topbar p {
        margin: 0.3rem 0 0 0;
        color: rgba(255,255,255,0.8);
        font-size: 0.98rem;
    }

    .status-strip {
        display: flex;
        flex-wrap: wrap;
        gap: 0.6rem;
        align-items: center;
        justify-content: space-between;
        background: rgba(255,255,255,0.75);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 0.75rem 1rem;
        margin: 0.75rem 0 1rem 0;
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.04);
    }

    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: #eef2ff;
        color: var(--primary-dark);
        padding: 0.38rem 0.7rem;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 700;
    }

    .metric-card {
        background: linear-gradient(180deg, #ffffff 0%, #f8faff 100%);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.03);
    }

    .metric-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: var(--primary-dark);
        margin-bottom: 0.2rem;
    }

    .metric-label {
        font-size: 0.78rem;
        color: var(--muted);
        font-weight: 700;
    }

    .chat-shell {
        background: rgba(255,255,255,0.65);
        border: 1px solid var(--line);
        border-radius: 18px;
        box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
        padding: 0.7rem 0.7rem 0.25rem 0.7rem;
    }

    .message-bubble-user {
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
        color: white;
        border-radius: 18px 18px 6px 18px;
        padding: 0.85rem 1rem 0.75rem 1rem;
        margin: 0.55rem 0;
        max-width: 78%;
        margin-left: auto;
        box-shadow: 0 10px 24px rgba(37, 99, 235, 0.18);
    }

    .message-bubble-assistant {
        background: linear-gradient(180deg, #ffffff 0%, #f8faff 100%);
        color: var(--text);
        border: 1px solid var(--line);
        border-radius: 18px 18px 18px 6px;
        padding: 0.85rem 1rem 0.75rem 1rem;
        margin: 0.6rem 0;
        max-width: 82%;
        box-shadow: 0 10px 18px rgba(15, 23, 42, 0.04);
    }

    .meta-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        font-weight: 700;
        font-size: 0.7rem;
        letter-spacing: 0.02em;
        border-radius: 999px;
        padding: 0.3rem 0.6rem;
        margin-bottom: 0.45rem;
        background: #ecfdf5;
        color: #166534;
    }

    .meta-badge.route {
        background: #eef2ff;
        color: #3730a3;
    }

    .footer {
        text-align: center;
        color: #64748b;
        font-size: 0.8rem;
        margin-top: 1.4rem;
        padding-top: 1rem;
        border-top: 1px solid rgba(148, 163, 184, 0.25);
    }

    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #f1f5f9;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #94a3b8;
    }
</style>
""", unsafe_allow_html=True)

# ==================== SESSION STATE ====================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "phase" not in st.session_state:
    st.session_state.phase = "idle"
if "started" not in st.session_state:
    st.session_state.started = False
if "confidence" not in st.session_state:
    st.session_state.confidence = 0.0
if "violations" not in st.session_state:
    st.session_state.violations = 0
if "message_count" not in st.session_state:
    st.session_state.message_count = 0
if "saved_deals" not in st.session_state:
    st.session_state.saved_deals = []
if "deal_saved_message" not in st.session_state:
    st.session_state.deal_saved_message = ""
if "last_saved_deal" not in st.session_state:
    st.session_state.last_saved_deal = None
if "deal_form_open" not in st.session_state:
    st.session_state.deal_form_open = False
if "last_route" not in st.session_state:
    st.session_state.last_route = "unknown"
if "last_classification" not in st.session_state:
    st.session_state.last_classification = "unknown"
if "voice_mode" not in st.session_state:
    st.session_state.voice_mode = False
if "last_speech_text" not in st.session_state:
    st.session_state.last_speech_text = ""
if "session_start_attempted" not in st.session_state:
    st.session_state.session_start_attempted = False


def get_api_base_url() -> str:
    """
    Get the API base URL - works for both local development and Render deployment
    """
    # For Render deployment
    render_url = os.environ.get("RENDER_EXTERNAL_URL", "")
    if render_url:
        return render_url
    
    # For local development
    try:
        response = requests.get("http://localhost:8000/", timeout=2)
        if response.status_code == 200:
            return "http://localhost:8000"
    except:
        pass
    
    return "http://localhost:8000"


def detect_final_deal_request(text: str) -> bool:
    """Detect if the user is confirming/accepting a deal"""
    normalized = (text or "").lower().strip()
    triggers = [
        "book the deal",
        "book this deal",
        "book on",
        "book at",
        "book for",
        "okay then book",
        "okay then finalize",
        "i am okay with the price",
        "i am okay with this price",
        "i am ok with the price",
        "i am okay with",
        "i am ok with",
        "i agree to the price",
        "i accept the deal",
        "accept the deal",
        "confirm the deal",
        "close the deal",
        "finalize the deal",
        "go ahead with the deal",
        "okay then deal",
        "book the flat",
        "book this flat",
        "ready with the price",
        "deal confirmed",
        "i am ready to book",
        "confirm booking",
        "confirm this deal",
        "finalize this deal",
        "i am ready",
        "i agree",
        "okay with the price"
    ]
    if any(trigger in normalized for trigger in triggers):
        return True
    if "book" in normalized and ("lakh" in normalized or "price" in normalized or "deal" in normalized):
        return True
    if "okay" in normalized and ("book" in normalized or "deal" in normalized or "price" in normalized):
        return True
    if "confirm" in normalized and ("deal" in normalized or "price" in normalized):
        return True
    if "ready" in normalized and ("deal" in normalized or "price" in normalized or "book" in normalized):
        return True
    return False


def start_session_automatically():
    api_url = get_api_base_url()
    
    try:
        # Try GET first
        response = requests.get(
            f"{api_url}/api/session/start",
            params={"student_id": "web_user", "exam_id": "negotiation"},
            timeout=10,
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                st.session_state.session_id = data.get("session_id")
                st.session_state.started = True
                st.session_state.phase = "active"
                st.session_state.deal_form_open = False
                st.session_state.messages = []
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": normalize_chat_text(data.get("welcome_message") or "🏗️ Welcome to Actiboost AI Negotiator! I'm here to help you with your construction needs. What can I assist you with today?"),
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "route": "conversational",
                    "classification": "conversational",
                })
                return True
            except json.JSONDecodeError:
                st.error(f"❌ Invalid response from server: {response.text[:200]}")
                return False
        
        # If GET fails with 405, try POST
        if response.status_code == 405:
            response = requests.post(
                f"{api_url}/api/session/start",
                params={"student_id": "web_user", "exam_id": "negotiation"},
                timeout=10,
            )
            if response.status_code == 200:
                try:
                    data = response.json()
                    st.session_state.session_id = data.get("session_id")
                    st.session_state.started = True
                    st.session_state.phase = "active"
                    st.session_state.deal_form_open = False
                    st.session_state.messages = []
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": normalize_chat_text(data.get("welcome_message") or "🏗️ Welcome to Actiboost AI Negotiator! I'm here to help you with your construction needs. What can I assist you with today?"),
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "route": "conversational",
                        "classification": "conversational",
                    })
                    return True
                except json.JSONDecodeError:
                    st.error(f"❌ Invalid response from server: {response.text[:200]}")
                    return False

        st.error(f"❌ Could not start session: {response.status_code} - {response.text[:200]}")
        return False
    except requests.exceptions.ConnectionError:
        st.error("❌ Connection Error: Could not connect to the API. Please check if the backend is running.")
        return False
    except requests.exceptions.Timeout:
        st.error("❌ Timeout: The API request timed out. Please try again.")
        return False
    except Exception as exc:
        st.error(f"❌ Error: {exc}")
        return False


def render_route_tag(route: str, classification: str) -> str:
    route_map = {
        "llm": "LLM",
        "sql_cache": "SQL Cache",
        "local_guardrail": "Local Guardrail",
        "off_topic": "Off Topic",
        "unknown": "Unknown",
    }
    classification_map = {
        "conversational": "Conversational",
        "technical": "Technical",
        "low_intent": "Low Intent",
        "off_topic": "Off Topic",
        "unknown": "Unknown",
    }
    route_text = route_map.get((route or "unknown").lower(), (route or "unknown").replace("_", " ").title())
    classification_text = classification_map.get((classification or "unknown").lower(), (classification or "unknown").replace("_", " ").title())
    return f"🧠 {classification_text}  •  🔀 {route_text}"


def normalize_chat_text(raw_text: str) -> str:
    if raw_text is None:
        return ""
    text = html.unescape(str(raw_text))
    text = re.sub(r"(?is)<br\s*/?>", "\n", text)
    text = re.sub(r"(?is)<(script|style|svg|img|iframe)[^>]*>.*?</\1>", "", text)
    text = re.sub(r"(?is)<[^>]+>", "", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = html.escape(text, quote=False)
    return text.strip()


def escape_message_html(raw_text: str) -> str:
    text = normalize_chat_text(raw_text)
    return text.replace("\n", "<br>")


def last_assistant_text() -> str:
    for msg in reversed(st.session_state.messages):
        if msg.get("role") == "assistant":
            return normalize_chat_text(msg.get("content", ""))
    return ""


def get_voice_summary(text: str) -> str:
    if not text:
        return ""

    cleaned = normalize_chat_text(text)
    lower = cleaned.lower()
    if "|" in cleaned or "1 bhk" in lower or "2 bhk" in lower or "area" in lower and "price" in lower:
        return "Please check the table below in the chat window for the details."

    short = cleaned.replace("\n", " ").strip()
    if len(short) > 180:
        short = short[:180].rsplit(" ", 1)[0] + "..."
    return short


def render_chat_auto_scroll() -> None:
    st.components.v1.html(
        """
        <script>
        try {
            const chatShell = document.querySelector('.chat-shell');
            if (chatShell) {
                chatShell.scrollTop = chatShell.scrollHeight;
            }
        } catch (e) {}
        </script>
        """,
        height=0,
        scrolling=False,
    )


def render_voice_reply_button() -> None:
    raw_text = last_assistant_text()
    if not raw_text:
        return

    speech_text = get_voice_summary(raw_text)
    if not speech_text:
        return

    if st.button("🔊 Speak Reply", key="voice_reply_button", help="Speak the latest assistant reply"):
        st.session_state.last_speech_text = speech_text
        safe_text = speech_text.replace("'", "\\'").replace("\n", " ")
        st.components.v1.html(
            f"""
            <script>
            try {{
                const speech = new SpeechSynthesisUtterance({safe_text!r});
                speech.lang = 'en-IN';
                speech.rate = 1.0;
                speech.pitch = 1.0;
                window.speechSynthesis.cancel();
                window.speechSynthesis.speak(speech);
            }} catch (e) {{}}
            </script>
            """,
            height=0,
            scrolling=False,
        )


def render_chat_autoscroll_and_voice() -> None:
    render_chat_auto_scroll()
    render_voice_reply_button()


def render_voice_mic_widget() -> None:
    st.components.v1.html(
        """
        <div style="margin: 0 0 18px 0; display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
          <button id="voiceChatButton" style="background:linear-gradient(135deg,#2563eb,#1d4ed8); color:#fff; border:none; border-radius:12px; padding:11px 18px; font-weight:800; cursor:pointer; box-shadow:0 8px 20px rgba(37,99,235,0.25);">🎤 Voice Input</button>
          <span id="voiceStatus" style="color:#475569; font-size:0.9rem; font-weight:600;">Ready</span>
        </div>
        <script>
        const voiceButton = document.getElementById('voiceChatButton');
        const status = document.getElementById('voiceStatus');
        let recognition = null;

        function setTextareaValue(text) {
            const textarea = document.querySelector('textarea[aria-label="Type your message"], textarea');
            if (!textarea) return false;
            const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
            nativeSetter.call(textarea, text);
            textarea.dispatchEvent(new Event('input', { bubbles: true }));
            textarea.dispatchEvent(new Event('change', { bubbles: true }));
            textarea.focus();
            return true;
        }

        if (voiceButton) {
            voiceButton.addEventListener('click', () => {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!SpeechRecognition) {
                    status.textContent = 'Speech is not supported in this browser.';
                    return;
                }

                if (recognition) {
                    recognition.stop();
                    recognition = null;
                    voiceButton.textContent = '🎤 Voice Input';
                    status.textContent = 'Stopped';
                    return;
                }

                recognition = new SpeechRecognition();
                recognition.lang = 'en-IN';
                recognition.continuous = false;
                recognition.interimResults = false;
                recognition.maxAlternatives = 1;
                voiceButton.textContent = '⏹ Stop';
                status.textContent = 'Listening...';

                recognition.onresult = (event) => {
                    const transcript = event.results[0][0].transcript;
                    if (setTextareaValue(transcript)) {
                        status.textContent = 'Captured';
                    } else {
                        status.textContent = 'Input box not found. Refresh the page and try again.';
                    }
                };

                recognition.onerror = () => {
                    status.textContent = 'Microphone access is blocked or unavailable.';
                    voiceButton.textContent = '🎤 Voice Input';
                    recognition = null;
                };

                recognition.onend = () => {
                    status.textContent = 'Ready';
                    voiceButton.textContent = '🎤 Voice Input';
                    recognition = null;
                };

                try {
                    recognition.start();
                } catch (err) {
                    status.textContent = 'Microphone is busy. Please try again.';
                    voiceButton.textContent = '🎤 Voice Input';
                    recognition = null;
                }
            });
        }
        </script>
        """,
        height=120,
        scrolling=False,
    )

# ==================== HEADER ====================
st.markdown("""
<div class="topbar">
    <h1>🏗️ Actiboost AI Negotiator</h1>
    <p>Intelligent construction and real-estate negotiation assistant</p>
</div>
""", unsafe_allow_html=True)

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("### 🎛️ Control Panel")
    
    # Session Controls
    if not st.session_state.started:
        if not st.session_state.session_start_attempted:
            st.session_state.session_start_attempted = True
            with st.spinner("🔄 Starting session automatically..."):
                if start_session_automatically():
                    st.rerun()

        if st.button("🚀 Start New Session", width="stretch", type="primary"):
            st.session_state.session_start_attempted = False
            with st.spinner("🔄 Starting session..."):
                if start_session_automatically():
                    st.rerun()
    else:
        st.success(f"✅ Session Active")
        st.info(f"🆔 ID: {st.session_state.session_id[:8]}...")
        
        if st.button("🔚 End Session", width="stretch"):
            st.session_state.started = False
            st.session_state.session_id = None
            st.session_state.messages = []
            st.session_state.phase = "idle"
            st.session_state.deal_form_open = False
            st.rerun()
    
    st.divider()
    
    # Session Stats
    if st.session_state.started:
        st.markdown("### 📊 Session Statistics")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{len(st.session_state.messages)}</div>
                <div class="metric-label">💬 Messages</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            emoji = "🟢" if st.session_state.phase == "active" else "🟠"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{emoji}</div>
                <div class="metric-label">📊 {st.session_state.phase.upper()}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Confidence Gauge
        if st.session_state.confidence > 0:
            st.markdown("#### 🎯 Confidence Score")
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=st.session_state.confidence * 100,
                number={'suffix': "%", 'font': {'size': 20}},
                title={'text': ""},
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [0, 100], 'tickwidth': 1},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 30], 'color': '#ff6b6b'},
                        {'range': [30, 70], 'color': '#ffd93d'},
                        {'range': [70, 100], 'color': '#6bcb77'}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig.update_layout(height=200, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
    
    st.divider()
    
    # Quick Questions
    st.markdown("### 💡 Quick Questions")
    quick_questions = [
        "🏠 What construction services do you offer?",
        "💰 How much does a 2BHK flat cost?",
        "🏗️ Tell me about land development",
        "🔧 What materials do you use?",
        "✅ Do you provide warranty?"
    ]
    
    for q in quick_questions:
        if st.button(q, width="stretch", key=f"quick_{hash(q)}"):
            st.session_state.quick_question = q
            st.rerun()
    
    st.divider()
    st.markdown("""
    <div style="font-size:0.8rem; color:#999; text-align:center;">
        🚀 Powered by GROQ AI<br>
        ⚡ Actiboost v1.0
    </div>
    """, unsafe_allow_html=True)

# ==================== MAIN CONTENT ====================
if st.session_state.started:
    if st.button("📋 View Saved Deals", key="top_view_saved_deals", width="stretch"):
        try:
            response = requests.get(f"{get_api_base_url()}/api/deals", timeout=15)
            if response.status_code == 200:
                st.session_state.saved_deals = response.json()
                if st.session_state.saved_deals:
                    st.success(f"Loaded {len(st.session_state.saved_deals)} saved deal(s).")
                else:
                    st.info("No deals saved yet.")
            else:
                st.error(f"Unable to load deals: {response.text}")
        except Exception as e:
            st.error(f"❌ Error loading saved deals: {e}")

    # Status bar
    status_emoji = {"active": "🟢", "research": "🟠", "idle": "⚪", "completed": "🔵"}
    status = status_emoji.get(st.session_state.phase, "⚪")
    route_label = (st.session_state.last_route or "unknown").replace("_", " ").title()
    classification_label = (st.session_state.last_classification or "unknown").replace("_", " ").title()
    st.markdown("<div class='status-strip'><div class='status-pill'>📊 " + st.session_state.phase.upper() + "</div><div>💬 Messages: " + str(len(st.session_state.messages)) + "</div><div>🎯 Confidence: " + f"{st.session_state.confidence * 100:.0f}%" + "</div><div>🧠 Type: " + classification_label + "</div><div>🔀 Route: " + route_label + "</div></div>", unsafe_allow_html=True)

    # Chat container
    st.markdown("<div class='chat-shell'>", unsafe_allow_html=True)
    last_assistant_index = max(
        (i for i, msg in enumerate(st.session_state.messages) if msg.get("role") == "assistant"),
        default=-1,
    )

    for idx, msg in enumerate(st.session_state.messages):
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.write(normalize_chat_text(msg["content"]))
                st.caption(f"🕐 {msg.get('timestamp', '')}")
        else:
            route = msg.get("route") or st.session_state.last_route
            classification = msg.get("classification") or st.session_state.last_classification
            with st.chat_message("assistant"):
                st.caption(render_route_tag(route, classification))
                st.write(normalize_chat_text(msg["content"]))
                st.caption(f"🕐 {msg.get('timestamp', '')}")
                if idx == last_assistant_index:
                    render_voice_reply_button()
    st.markdown("</div>", unsafe_allow_html=True)
    render_chat_auto_scroll()

    show_final_deal_form = st.session_state.deal_form_open

    if show_final_deal_form:
        st.markdown("### ✅ Final Deal Form")
        st.info("📝 Please fill in your details to confirm the deal. All fields are required.")
        
        with st.form("final_deal_form_chat", clear_on_submit=False):
            col1, col2 = st.columns(2)
            with col1:
                customer_name = st.text_input("Customer Name *", placeholder="Enter your full name")
                customer_email = st.text_input("Email *", placeholder="your@email.com")
            with col2:
                customer_phone = st.text_input("Contact Number *", placeholder="+91 9876543210")
                project_type = st.text_input("Project Type", value="Construction")
            
            final_price = st.number_input("Final Negotiated Price (₹) *", min_value=0.0, step=1000.0, format="%.2f", value=0.0)
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                save_deal_clicked = st.form_submit_button("💾 Confirm & Save Deal", width="stretch", type="primary")

        if save_deal_clicked:
            errors = []
            if not customer_name.strip():
                errors.append("Customer Name is required")
            if not customer_email.strip():
                errors.append("Email is required")
            elif "@" not in customer_email.strip():
                errors.append("Please enter a valid email address")
            if not customer_phone.strip():
                errors.append("Contact Number is required")
            if final_price <= 0:
                errors.append("Please enter a valid price")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                payload = {
                    "customer_name": customer_name.strip(),
                    "customer_email": customer_email.strip(),
                    "customer_phone": customer_phone.strip(),
                    "project_type": project_type.strip() or "Construction",
                    "project_size": "",
                    "location": "",
                    "initial_price": float(final_price),
                    "final_price": float(final_price),
                    "session_id": st.session_state.session_id or "manual_deal",
                    "negotiation_history": [{
                        "role": "agent",
                        "content": "Final deal confirmed by customer and agent.",
                        "timestamp": datetime.now().isoformat()
                    }]
                }
                try:
                    with st.spinner("💾 Saving deal..."):
                        response = requests.post(
                            f"{get_api_base_url()}/api/deal/create",
                            json=payload,
                            timeout=15
                        )
                        if response.status_code == 200:
                            result = response.json()
                            st.session_state.deal_saved_message = (
                                f"✅ Deal confirmed successfully for {customer_name.strip()}! "
                                f"Record ID: {result.get('deal_id')}"
                            )
                            st.session_state.last_saved_deal = {
                                "customer_name": customer_name.strip(),
                                "customer_email": customer_email.strip(),
                                "customer_phone": customer_phone.strip(),
                                "project_type": project_type.strip() or "Construction",
                                "final_price": float(final_price),
                                "status": "confirmed"
                            }
                            st.session_state.deal_form_open = False
                            st.success(st.session_state.deal_saved_message)
                            st.rerun()
                        else:
                            st.error(f"❌ Deal save failed: {response.text}")
                except Exception as e:
                    st.error(f"❌ Could not save deal: {e}")

        if st.session_state.deal_saved_message:
            st.info(st.session_state.deal_saved_message)

        if st.session_state.last_saved_deal:
            st.markdown("#### 🧾 Last Confirmed Deal")
            st.json(st.session_state.last_saved_deal)

        if st.session_state.saved_deals:
            st.markdown("#### 📊 All Saved Deals")
            records = []
            for deal in st.session_state.saved_deals:
                records.append({
                    "Name": deal.get("customer_name", ""),
                    "Email": deal.get("customer_email") or "N/A",
                    "Contact": deal.get("customer_phone") or "N/A",
                    "Project": deal.get("project_type", ""),
                    "Price (₹)": deal.get("final_price", 0),
                    "Status": deal.get("status", "pending")
                })
            st.dataframe(pd.DataFrame(records), width="stretch")

    # Quick question handler
    if hasattr(st.session_state, 'quick_question') and st.session_state.quick_question:
        question = st.session_state.quick_question
        st.session_state.quick_question = None
        
        st.session_state.messages.append({
            "role": "user",
            "content": normalize_chat_text(question),
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        
        with st.spinner("🤔 Thinking..."):
            try:
                response = requests.post(
                    f"{get_api_base_url()}/api/session/{st.session_state.session_id}/message",
                    json={"message": question},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    assistant_message = normalize_chat_text(data.get("response", "I'm thinking about that..."))
                    st.session_state.phase = data.get("phase", st.session_state.phase)
                    st.session_state.confidence = data.get("confidence", st.session_state.confidence)
                    st.session_state.last_route = data.get("route", st.session_state.last_route)
                    st.session_state.last_classification = data.get("classification", st.session_state.last_classification)
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_message,
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "route": data.get("route", st.session_state.last_route),
                        "classification": data.get("classification", st.session_state.last_classification),
                    })
                    
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    render_voice_mic_widget()

    prompt = st.chat_input("💬 Ask about construction, flats, pricing...")
    if prompt:
        user_prompt = prompt.strip()
        
        if detect_final_deal_request(user_prompt):
            st.session_state.deal_form_open = True
            st.success("✅ Great! Please fill in your details below to confirm the deal.")
        else:
            st.session_state.deal_form_open = False

        st.session_state.messages.append({
            "role": "user",
            "content": normalize_chat_text(user_prompt),
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })

        with st.spinner("🤔 Analyzing..."):
            try:
                response = requests.post(
                    f"{get_api_base_url()}/api/session/{st.session_state.session_id}/message",
                    json={"message": user_prompt},
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    assistant_message = data.get("response", "I'm thinking about that...")
                    st.session_state.phase = data.get("phase", st.session_state.phase)
                    st.session_state.confidence = data.get("confidence", st.session_state.confidence)
                    st.session_state.message_count = data.get("message_count", 0)
                    st.session_state.last_route = data.get("route", st.session_state.last_route)
                    st.session_state.last_classification = data.get("classification", st.session_state.last_classification)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_message,
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "route": data.get("route", st.session_state.last_route),
                        "classification": data.get("classification", st.session_state.last_classification),
                    })
                    
                    if "deal" in assistant_message.lower() and ("confirm" in assistant_message.lower() or "ready" in assistant_message.lower()):
                        st.session_state.deal_form_open = True

                    st.rerun()

            except requests.exceptions.Timeout:
                st.error("⏰ Request timed out. Please try again.")
            except Exception as e:
                st.error(f"❌ Error: {e}")

else:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center; padding:3rem 1rem;">
            <div style="font-size:5rem;">🏗️</div>
            <h2 style="color:#1a237e;">Ready to Start?</h2>
            <p style="color:#666; font-size:1.1rem;">
                Click <strong>"Start New Session"</strong> in the sidebar<br>
                to begin your conversation with Actiboost AI Negotiator.
            </p>
            <div style="background:#f8f9fa; padding:1rem; border-radius:10px; margin-top:1rem;">
                <p style="color:#999; font-size:0.9rem;">
                    💡 Ask about:<br>
                    <span style="color:#1a237e;">🏠 House Construction</span> &bull;
                    <span style="color:#1a237e;">🏢 Flat Sales</span> &bull;
                    <span style="color:#1a237e;">🏗️ Land Development</span>
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==================== FOOTER ====================
st.markdown("""
<div class="footer">
    Actiboost AI Negotiator v1.0 | Powered by GROQ AI 🚀 | Built with ❤️
</div>
""", unsafe_allow_html=True)