import streamlit as st
import random
import time
from fractions import Fraction
import base64

# --- 1. SETTINGS & DBZ THEME INJECTION ---
TEACHER_PASSWORD = "mathrocks2026"
ROOM_OPTIONS = ["Period 1", "Period 2", "Period 3", "Period 4"]
GROUP_COUNT = 8 
WINNING_SCORE = 100

# Function to inject CSS for background image
def add_bg_from_url(url):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("{url}");
            background-attachment: fixed;
            background-size: cover;
        }}
        
        /* Add a semi-transparent overlay to keep text readable */
        .st-block {{
            background-color: rgba(255, 255, 255, 0.85); /* Slightly transparent white */
            padding: 20px;
            border-radius: 10px;
            border: 2px solid orange; /* Theme Color */
        }}

        /* Style headers for the theme */
        h1, h2, h3, h4 {{
            color: #d35400; /* Dark Orange */
            font-family: 'Luckiest Guy', cursive; /* Optional: Fun font if available */
        }}
        
        /* Style Buttons to match */
        .stButton>button {{
            background-color: #f39c12; /* Blue */
            color: white;
            border: 2px solid #d35400;
        }}
        .stButton>button:hover {{
            background-color: #e67e22; /* Lighter Orange */
            border: 2px solid #f39c12;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Set the page configuration early
st.set_page_config(page_title="Dragon Ball Fraction Z", layout="wide", page_icon="🐉")

# Inject the DBZ Background (Replace URL with any direct image link)
# dbz_bg_url = "https://images.alphacoders.com/208/208398.jpg" # A generic high-quality DBZ image
# dbz_bg_url = "https://w.wallhaven.cc/full/8o/wallhaven-8o77jy.png" # Another cool option
dbz_bg_url = "https://img.wallpapersafari.com/desktop/1680/1050/66/12/Y0G3pA.jpg" # Classic Goku
add_bg_from_url(dbz_bg_url)

# --- 2. SHARED DATA (UNCHANGED) ---
@st.cache_resource
def get_all_rooms():
    rooms = {}
    for r in ROOM_OPTIONS:
        rooms[r] = {
            "groups": {f"Group {i}": {
                "display_name": f"Group {i}",
                "leader": None,
                "score": 0, 
                "players": [], 
                "turn_idx": 0,
                "started": False,
                "q": "10/12", "a": "5/6",
                "start_time": time.time(),
                "history": [],
                "global_msg": "" # Placeholder for group-specific messages if needed
            } for i in range(1, GROUP_COUNT + 1)},
            "timer_enabled": True,
            "global_msg": "" # Placeholder for teacher messages
        }
    return rooms

all_rooms = get_all_rooms()

# --- 3. SESSION STATE (UNCHANGED) ---
if "user_name" not in st.session_state: st.session_state.user_name = None
if "role" not in st.session_state: st.session_state.role = "Student"
if "room_id" not in st.session_state: st.session_state.room_id = None
if "my_group_key" not in st.session_state: st.session_state.my_group_key = None

# --- Add themed header image/banner ---
st.markdown(
    '<img src="https://fontmeme.com/permalink/240522/a322197170b615b1df6f8f7c97805178.png" alt="dragon-ball-z-font" border="0" style="display: block; margin-left: auto; margin-right: auto; width: 50%;">',
    unsafe_allow_html=True
)

# --- LOGIN ---
if st.session_state.user_name is None:
    st.markdown("<h1 style='text-align: center; color: white;'>🛡️ Fraction Z: Saiyan Showdown</h1>", unsafe_allow_html=True)
    st.markdown("<div class='st-block'>", unsafe_allow_html=True) # Start stylized block
    
    t1, t2 = st.tabs(["🔥 Warrior Join", "🎮 Kami's Lookout (Teacher)"])
    with t1:
        s_room = st.selectbox("Select Your Battleground:", ["Select..."] + ROOM_OPTIONS)
        s_first = st.text_input("First Name")
        s_last = st.text_input("Last Name")
        if st.button("Power Up & Join"):
            if s_room != "Select..." and s_first and s_last:
                st.session_state.room_id = s_room
                st.session_state.user_name = f"{s_first} {s_last}"
                st.rerun()
    with t2:
        st.subheader("Kami's Access Panel")
        t_pass = st.text_input("Teacher Password", type="password")
        if st.button("Ascend to Dashboard"):
            if t_pass == TEACHER_PASSWORD:
                st.session_state.user_name = "Teacher"; st.session_state.role = "Teacher"
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True) # End stylized block

# --- TEACHER DASHBOARD ---
elif st.session_state.role == "Teacher":
    st.title("👨‍🏫 Teacher Command Center")
