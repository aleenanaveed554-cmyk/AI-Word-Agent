import streamlit as st
from datetime import datetime

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="AI Agent World",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------
# CUSTOM CSS
# -----------------------------
st.markdown("""
<style>
    .stApp {
        background:
        radial-gradient(circle at top left, #182848 0%, transparent 35%),
        radial-gradient(circle at bottom right, #4b134f 0%, transparent 35%),
        #070b17;
        color: white;
    }

    [data-testid="stSidebar"] {
        background: #0d1224;
        border-right: 1px solid #252d4a;
    }

    .main-title {
        font-size: 48px;
        font-weight: 800;
        text-align: center;
        margin-top: 10px;
        background: linear-gradient(90deg, #00e5ff, #8b5cf6, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .subtitle {
        text-align: center;
        color: #a9b2c8;
        font-size: 18px;
        margin-bottom: 30px;
    }

    .card {
        background: rgba(18, 25, 48, 0.85);
        border: 1px solid #293353;
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 15px;
        box-shadow: 0 10px 35px rgba(0,0,0,0.25);
    }

    .agent-card {
        background: linear-gradient(145deg, #111a33, #0d1224);
        border: 1px solid #293353;
        border-radius: 18px;
        padding: 20px;
        min-height: 170px;
    }

    .agent-icon {
        font-size: 38px;
    }

    .agent-name {
        font-size: 20px;
        font-weight: 700;
        margin-top: 8px;
    }

    .agent-desc {
        color: #9da8c2;
        font-size: 14px;
    }

    .status {
        color: #39e58c;
        font-weight: 600;
    }

    .small-text {
        color: #8f9ab4;
        font-size: 13px;
    }

    div.stButton > button {
        width: 100%;
        border-radius: 12px;
        border: 1px solid #354269;
        background: linear-gradient(90deg, #2563eb, #7c3aed);
        color: white;
        font-weight: 700;
        min-height: 45px;
    }

    div.stButton > button:hover {
        border-color: #00e5ff;
        box-shadow: 0 0 20px rgba(0,229,255,0.25);
    }

    .chat-box {
        background: #11182e;
        border: 1px solid #293353;
        border-radius: 16px;
        padding: 18px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# SESSION STATE
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "selected_agent" not in st.session_state:
    st.session_state.selected_agent = "General AI Agent"

# -----------------------------
# SIDEBAR
# -----------------------------
with st.sidebar:

    st.markdown("## 🤖 AI Agent World")

    st.markdown("---")

    st.markdown("### 🌐 Navigation")

    page = st.radio(
        "Choose page",
        [
            "🏠 Dashboard",
            "💬 AI Chat",
            "🤖 Agents",
            "📊 Activity",
            "⚙️ Settings"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")

    st.markdown("### 🟢 System")

    st.markdown(
        '<p class="status">● All systems operational</p>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<p class="small-text">AI Agent World v1.0</p>',
        unsafe_allow_html=True
    )

# -----------------------------
# AGENTS
# -----------------------------
agents = {
    "General AI Agent": {
        "icon": "🤖",
        "description": "General-purpose intelligent assistant"
    },
    "Writer Agent": {
        "icon": "✍️",
        "description": "Creates articles, captions and content"
    },
    "Designer Agent": {
        "icon": "🎨",
        "description": "Helps with creative design ideas"
    },
    "Code Agent": {
        "icon": "💻",
        "description": "Helps create and explain code"
    },
    "Research Agent": {
        "icon": "🔎",
        "description": "Organizes research and information"
    },
    "Study Agent": {
        "icon": "📚",
        "description": "Explains educational topics"
    }
}

# -----------------------------
# DASHBOARD
# -----------------------------
if page == "🏠 Dashboard":

    st.markdown(
        '<div class="main-title">AI AGENT WORLD</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Your intelligent workspace for AI-powered tasks'
        '</div>',
        unsafe_allow_html=True
    )

    # Stats
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("🤖 AI Agents", "6")

    with c2:
        st.metric("⚡ Tasks", len(st.session_state.messages))

    with c3:
        st.metric("🟢 System", "Online")

    with c4:
        st.metric("🚀 Version", "1.0")

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("## 🚀 Choose Your AI Agent")

    cols = st.columns(3)

    for index, (name, info) in enumerate(agents.items()):

        with cols[index % 3]:

            st.markdown(
                f"""
                <div class="agent-card">
                    <div class="agent-icon">{info["icon"]}</div>
                    <div class="agent-name">{name}</div>
                    <div class="agent-desc">{info["description"]}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(
                f"Use {name}",
                key=f"agent_{index}"
            ):
                st.session_state.selected_agent = name
                st.success(f"{name} selected!")

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("## ✨ Quick Start")

    q1, q2, q3 = st.columns(3)

    with q1:
        if st.button("✍️ Write Content"):
            st.session_state.selected_agent = "Writer Agent"
            st.info("Writer Agent selected.")

    with q2:
        if st.button("🎨 Design Idea"):
            st.session_state.selected_agent = "Designer Agent"
            st.info("Designer Agent selected.")

    with q3:
        if st.button("💻 Create Code"):
            st.session_state.selected_agent = "Code Agent"
            st.info("Code Agent selected.")

# -----------------------------
# AI CHAT
# -----------------------------
elif page == "💬 AI Chat":

    st.markdown(
        '<div class="main-title">AI CHAT</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f'<div class="subtitle">'
        f'Active Agent: <b>{st.session_state.selected_agent}</b>'
        f'</div>',
        unsafe_allow_html=True
    )

    # Agent selector
    selected = st.selectbox(
        "Select AI Agent",
        list(agents.keys()),
        index=list(agents.keys()).index(
            st.session_state.selected_agent
        )
    )

    st.session_state.selected_agent = selected

    st.markdown("---")

    # Previous messages
    for message in st.session_state.messages:

        role = message["role"]
        content = message["content"]

        if role == "user":
            st.markdown(
                f"""
                <div class="chat-box">
                <b>👤 You</b><br><br>
                {content}
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div class="chat-box">
                <b>🤖 {st.session_state.selected_agent}</b><br><br>
                {content}
                </div>
                """,
                unsafe_allow_html=True
            )

    user_input = st.chat_input(
        "Ask your AI Agent something..."
    )

    if user_input:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_input
            }
        )

        # Demo response
        response = (
            f"I am your {st.session_state.selected_agent}. "
            f"I received your request: '{user_input}'. "
            f"Connect an AI API in the next step to generate "
            f"real AI-powered responses."
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response
            }
        )

        st.rerun()

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# -----------------------------
# AGENTS PAGE
# -----------------------------
elif page == "🤖 Agents":

    st.markdown(
        '<div class="main-title">AI AGENTS</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Manage and explore your intelligent agents'
        '</div>',
        unsafe_allow_html=True
    )

    for name, info in agents.items():

        col1, col2 = st.columns([4, 1])

        with col1:
            st.markdown(
                f"""
                <div class="card">
                    <div style="font-size:30px">
                        {info["icon"]}
                    </div>
                    <h3>{name}</h3>
                    <p class="small-text">
                        {info["description"]}
                    </p>
                    <p class="status">● Ready</p>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:
            st.markdown("<br><br>", unsafe_allow_html=True)

            if st.button(
                "Activate",
                key=f"activate_{name}"
            ):
                st.session_state.selected_agent = name
                st.success("Activated")

# -----------------------------
# ACTIVITY
# -----------------------------
elif page == "📊 Activity":

    st.markdown(
        '<div class="main-title">ACTIVITY</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Recent AI Agent activity'
        '</div>',
        unsafe_allow_html=True
    )

    if not st.session_state.messages:

        st.info("No activity yet.")

    else:

        for i, message in enumerate(
            st.session_state.messages
        ):

            role = (
                "You"
                if message["role"] == "user"
                else "AI Agent"
            )

            st.markdown(
                f"""
                <div class="card">
                    <b>{role}</b>
                    <p>{message["content"]}</p>
                    <span class="small-text">
                        Activity #{i + 1}
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )

# -----------------------------
# SETTINGS
# -----------------------------
elif page == "⚙️ Settings":

    st.markdown(
        '<div class="main-title">SETTINGS</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Customize your AI Agent World'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="card">',
        unsafe_allow_html=True
    )

    st.markdown("### 🎨 Appearance")

    theme = st.selectbox(
        "Theme",
        ["Dark", "Midnight", "Professional"]
    )

    st.markdown("### 🤖 Agent Settings")

    temperature = st.slider(
        "AI Creativity",
        0.0,
        1.0,
        0.7
    )

    st.markdown("### 🔔 Notifications")

    notifications = st.toggle(
        "Enable notifications",
        value=True
    )

    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("💾 Save Settings"):
        st.success("Settings saved successfully!")

# -----------------------------
# FOOTER
# -----------------------------
st.markdown(
    """
    <br><br>
    <div style="text-align:center;color:#6f7892;">
        🤖 AI Agent World • Smart AI Workspace • 2026
    </div>
    """,
    unsafe_allow_html=True
)
