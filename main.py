import streamlit as st
import random
import time
from datetime import datetime
from fractions import Fraction

# --- 1. CONFIGURATION ---
TEACHER_PASSWORD = "mathrocks2026"
ROOM_OPTIONS = ["Period 1", "Period 2", "Period 3", "Period 4"]
GROUP_COUNT = 8 

# --- 2. DATA STORAGE ---
@st.cache_resource
def get_all_rooms():
    rooms = {}
    for r in ROOM_OPTIONS:
        rooms[r] = {
            "session_active": True,
            "groups": {f"Group {i}": {
                "display_name": f"Group {i}",
                "mode": "Match Up",
                "goal": 100,      # TEACHER SETS THIS
                "diff": "Medium", # TEACHER SETS THIS
                "captain": None,
                "pep_talk": "",
                "score": 0, 
                "streak": 0,
                "players": {}, 
                "turn_idx": 0,
                "started": False,
                "q": "10/20", "a": "1/2",
                "start_time": time.time(),
                "history": []
            } for i in range(1, GROUP_COUNT + 1)}
        }
    return rooms

all_rooms = get_all_rooms()

# --- 3. SESSION STATE ---
if "user_fullname" not in st.session_state: st.session_state.user_fullname = None
if "role" not in st.session_state: st.session_state.role = "Student"
if "room_id" not in st.session_state: st.session_state.room_id = None
if "my_group_key" not in st.session_state: st.session_state.my_group_key = None

st.set_page_config(page_title="Fraction Nexus: Teacher Setup", layout="wide")

# --- 4. LOGIN ---
if st.session_state.user_fullname is None:
    st.title("🛡️ Fraction Nexus")
    t1, t2 = st.tabs(["👤 Student Join", "🔑 Teacher Access"])
    with t1:
        s_room = st.selectbox("Class:", ["Select..."] + ROOM_OPTIONS)
        c1, c2 = st.columns(2)
        fn, ln = c1.text_input("First Name"), c2.text_input("Last Name")
        if st.button("Join", use_container_width=True):
            if s_room != "Select..." and fn and ln:
                st.session_state.room_id, st.session_state.user_fullname = s_room, f"{fn.strip()} {ln.strip()}"
                st.rerun()
    with t2:
        pw = st.text_input("Password:", type="password")
        if st.button("Login"):
            if pw.strip().lower() == TEACHER_PASSWORD:
                st.session_state.user_fullname, st.session_state.role = "Teacher", "Teacher"
                if not st.session_state.room_id: st.session_state.room_id = "Period 1"
                st.rerun()

# --- 5. TEACHER DASHBOARD (Match Setup) ---
elif st.session_state.role == "Teacher":
    st.title(f"👨‍🏫 Match Setup: {st.session_state.room_id}")
    room = all_rooms[st.session_state.room_id]

    # Global Match Setup Panel
    with st.expander("⚙️ GLOBAL MATCH SETUP (Configure all groups)", expanded=True):
        st.write("Set the parameters for the next 'Match Up' battle:")
        col_a, col_b, col_c = st.columns(3)
        new_goal = col_a.number_input("Winning Score Goal:", min_value=10, max_value=1000, value=100, step=10)
        new_diff = col_b.selectbox("Difficulty Level:", ["Easy", "Medium", "Hard"], index=1)
        new_mode = col_c.selectbox("Switch All Modes To:", ["Match Up", "Study in Groups", "Streak
