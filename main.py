import streamlit as st
import random
import time
from fractions import Fraction

# --- 1. SETTINGS ---
TEACHER_PASSWORD = "mathrocks2026"
ROOM_OPTIONS = ["Period 1", "Period 2", "Period 3", "Period 4"]
GROUP_COUNT = 8 
WINNING_SCORE = 100

# --- 2. SHARED DATA ---
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
                "q": "12/18", "a": "2/3",
                "start_time": time.time(),
                "history": []
            } for i in range(1, GROUP_COUNT + 1)},
            "timer_enabled": True,
            "global_msg": ""
        }
    return rooms

all_rooms = get_all_rooms()

# --- 3. SESSION STATE ---
if "user_name" not in st.session_state: st.session_state.user_name = None
if "role" not in st.session_state: st.session_state.role = "Student"
if "room_id" not in st.session_state: st.session_state.room_id = None
if "my_group_key" not in st.session_state: st.session_state.my_group_key = None

st.set_page_config(page_title="Fraction Battle Royale", layout="wide")

# --- LOGIN SCREEN ---
if st.session_state.user_name is None:
    st.title("🛡️ Fraction Battle Royale")
    t1, t2 = st.tabs(["Student Join", "Teacher Login"])
    
    with t1:
        s_room = st.selectbox("Select Class:", ["Select..."] + ROOM_OPTIONS)
        s_first = st.text_input("First Name")
        s_last = st.text_input("Last Name")
        if st.button("Join Game", use_container_width=True):
            if s_room != "Select..." and s_first and s_last:
                st.session_state.room_id = s_room
                st.session_state.user_name = f"{s_first} {s_last}"
                st.rerun()
            else:
                st.error("Please fill in all fields.")

    with t2:
        st.subheader("Teacher Access")
        t_pass = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if t_pass == TEACHER_PASSWORD:
                st.session_state.user_name = "Teacher"; st.session_state.role = "Teacher"
                st.rerun()

# --- TEACHER DASHBOARD ---
elif st.session_state.role == "Teacher":
    st.title("👨‍🏫 Teacher Command Center")
    view_room = st.selectbox("Manage Period:", ROOM_OPTIONS)
    room = all_rooms[view_room]
    
    room["timer_enabled"] = st.toggle("Enable Speed Bonus (under 10s)", value=room["timer_enabled"])
    
    st.divider()
    g_cols = st.columns(4)
    for i in range(1, GROUP_COUNT +
