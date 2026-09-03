# app.py
import streamlit as st
import requests
import json
import time
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
    /* Main container */
    .main {
        padding: 0rem 1rem;
    }
    
    /* Header */
    .header-container {
        background: linear-gradient(135deg, #1a237e, #0d47a1);
        padding: 1.5rem 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .header-title {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
    }
    .header-subtitle {
        color: rgba(255,255,255,0.8);
        font-size: 1.1rem;
        margin: 0;
    }
    
    /* Chat messages */
    .chat-container {
        background: #f5f7fa;
        border-radius: 15px;
        padding: 1.5rem;
        height: 500px;
        overflow-y: auto;
        border: 1px solid #e8ecf1;
        margin-bottom: 1rem;
    }
    
    .message-user {
        background: linear-gradient(135deg, #e3f2fd, #bbdefb);
        padding: 0.8rem 1.2rem;
        border-radius: 18px 18px 4px 18px;
        margin: 0.5rem 0;
        max-width: 80%;
        align-self: flex-end;
        float: right;
        clear: both;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    
    .message-assistant {
        background: black;
        padding: 0.8rem 1.2rem;
        border-radius: 18px 18px 18px 4px;
        margin: 0.5rem 0;
        max-width: 80%;
        align-self: flex-start;
        float: left;
        clear: both;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border: 1px solid #e8ecf1;
    }
    
    .message-time {
        font-size: 0.7rem;
        color: #888;
        margin-top: 0.2rem;
    }
    
    /* Sidebar */
    .sidebar-container {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        padding: 1rem;
        border-radius: 12px;
        text-align: center;
        margin: 0.5rem 0;
        border-left: 4px solid #1a237e;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1a237e;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #666;
        margin-top: 0.2rem;
    }
    
    /* Buttons */
    .btn-primary {
        background: linear-gradient(135deg, #1a237e, #0d47a1);
        color: white;
        border: none;
        padding: 0.6rem 1.5rem;
        border-radius: 25px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s;
        width: 100%;
    }
    .btn-primary:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(26,35,126,0.3);
    }
    .btn-danger {
        background: linear-gradient(135deg, #c62828, #b71c1c);
        color: white;
        border: none;
        padding: 0.6rem 1.5rem;
        border-radius: 25px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s;
        width: 100%;
    }
    .btn-danger:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(198,40,40,0.3);
    }
    
    /* Quick questions */
    .quick-btn {
        background: #f0f2f6;
        border: 1px solid #ddd;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        cursor: pointer;
        transition: all 0.2s;
        margin: 0.2rem 0;
        width: 100%;
        text-align: left;
    }
    .quick-btn:hover {
        background: #e3f2fd;
        border-color: #1a237e;
        transform: translateX(5px);
    }
    
    /* Status badge */
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
        display: inline-block;
    }
    .status-active {
        background: #4caf50;
        color: white;
    }
    .status-research {
        background: #ff9800;
        color: white;
    }
    .status-completed {
        background: #2196f3;
        color: white;
    }
    .status-idle {
        background: #9e9e9e;
        color: white;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #999;
        font-size: 0.8rem;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #eee;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #a1a1a1;
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

# ==================== HEADER ====================
st.markdown(f"""
<div class="header-container">
    <h1 class="header-title">🏗️ Actiboost AI Negotiator</h1>
    <p class="header-subtitle">🚀 Intelligent Construction & Real Estate Assistant</p>
</div>
""", unsafe_allow_html=True)

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("### 🎛️ Control Panel")
    
    # Session Controls
    if not st.session_state.started:
        if st.button("🚀 Start New Session", use_container_width=True, type="primary"):
            with st.spinner("🔄 Starting session..."):
                try:
                    response = requests.post(
                        "http://localhost:8000/api/session/start",
                        params={"student_id": "web_user", "exam_id": "negotiation"},
                        timeout=10
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.session_id = data.get("session_id")
                        st.session_state.started = True
                        st.session_state.phase = "active"
                        st.session_state.messages = []
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": "🏗️ Welcome to Actiboost AI Negotiator! I'm here to help you with your construction needs. What can I assist you with today?",
                            "timestamp": datetime.now().strftime("%H:%M:%S")
                        })
                        st.rerun()
                    else:
                        st.error(f"❌ Error: {response.text}")
                except Exception as e:
                    st.error(f"❌ Connection error: {e}")
    else:
        st.success(f"✅ Session Active")
        st.info(f"🆔 ID: {st.session_state.session_id[:8]}...")
        
        if st.button("🔚 End Session", use_container_width=True):
            st.session_state.started = False
            st.session_state.session_id = None
            st.session_state.messages = []
            st.session_state.phase = "idle"
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
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
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
        if st.button(q, use_container_width=True, key=f"quick_{hash(q)}"):
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
    # Status bar
    status_emoji = {"active": "🟢", "research": "🟠", "idle": "⚪", "completed": "🔵"}
    status = status_emoji.get(st.session_state.phase, "⚪")
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; background:#f8f9fa; padding:0.5rem 1rem; border-radius:10px; margin-bottom:1rem;">
        <span>📊 <strong>Status:</strong> <span class="status-badge status-{st.session_state.phase}">{status} {st.session_state.phase.upper()}</span></span>
        <span>💬 <strong>Messages:</strong> {len(st.session_state.messages)}</span>
        <span>🎯 <strong>Confidence:</strong> {st.session_state.confidence * 100:.0f}%</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Chat container
    with st.container():
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="message-user">
                    <strong>👤 You</strong>
                    <div>{msg["content"]}</div>
                    <div class="message-time">🕐 {msg.get("timestamp", "")}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="message-assistant">
                    <strong>🤖 Actiboost AI</strong>
                    <div>{msg["content"]}</div>
                    <div class="message-time">🕐 {msg.get("timestamp", "")}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Quick question handler
    if hasattr(st.session_state, 'quick_question') and st.session_state.quick_question:
        question = st.session_state.quick_question
        st.session_state.quick_question = None
        
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": question,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        
        # Process
        with st.spinner("🤔 Thinking..."):
            try:
                response = requests.post(
                    f"http://localhost:8000/api/session/{st.session_state.session_id}/message",
                    json={"message": question},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    assistant_message = data.get("response", "I'm thinking about that...")
                    st.session_state.phase = data.get("phase", st.session_state.phase)
                    st.session_state.confidence = data.get("confidence", st.session_state.confidence)
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_message,
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                    
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    # Chat input
    if prompt := st.chat_input("💬 Ask about construction, flats, pricing..."):
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        
        # Process
        with st.spinner("🤔 Analyzing..."):
            try:
                response = requests.post(
                    f"http://localhost:8000/api/session/{st.session_state.session_id}/message",
                    json={"message": prompt},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    assistant_message = data.get("response", "I'm thinking about that...")
                    st.session_state.phase = data.get("phase", st.session_state.phase)
                    st.session_state.confidence = data.get("confidence", st.session_state.confidence)
                    st.session_state.message_count = data.get("message_count", 0)
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_message,
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                    
                    st.rerun()
                    
            except requests.exceptions.Timeout:
                st.error("⏰ Request timed out. Please try again.")
            except Exception as e:
                st.error(f"❌ Error: {e}")

else:
    # Welcome screen when not started
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