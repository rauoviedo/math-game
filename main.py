import streamlit as st
import random
import time
import pandas as pd
from streamlit_autorefresh import st_autorefresh # NEW: Import for live updates
from datetime import datetime
from fractions import Fraction

# --- 1. SETTINGS & REFRESH ---
# This line tells the app to refresh every 3 seconds (3000 milliseconds)
# We give it a unique 'key' so it doesn't interfere with other timers.
refresh_count = st_autorefresh(interval=3000, limit=None, key="framer_refresh")

TEACHER_PASSWORD = "mathrocks2026"
ROOM_OPTIONS = ["Period 1", "Period 2", "Period 3", "Period 4"]
GROUP_COUNT = 8 

# --- 2. DATA STORAGE ---
@st.cache_resource
def get_all_rooms():
    rooms = {}
    for r in ROOM_OPTIONS:
        rooms[r] = {
            "groups": {f"Group {i}": {
                "display_name": f"Group {i}",
                "mode": "Match Up",
                "goal": 100,
                "captain": None,
                "pep_talk": "",
                "score": 0, 
                "players": {}, 
                "turn_idx": 0,
                "started": False,
                "start_time": None,
                "q": "9/12", "a": "3/4",
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

st.set_page_config(page_title="Fraction Nexus Live", layout="wide")

# --- 4. RECONNECT LOGIC ---
# (Checks if user is already in a group when they log in)
def check_reconnect(full_name, room_id):
    room = all_rooms[room_id]
    for g_key, g_data in room["groups"].items():
        if full_name in g_data["players"]:
            return g_key
    return None

# --- 5. LOGIN SCREEN ---
if st.session_state.user_fullname is None:
    st.title("🛡️ Fraction Nexus: Live")
    t1, t2 = st.tabs(["👤 Student", "🔑 Teacher"])
    
    with t1:
        s_room = st.selectbox("Class:", ["Select..."] + ROOM_OPTIONS)
        c1, c2 = st.columns(2)
        fn, ln = c1.text_input("First Name"), c2.text_input("Last Name")
        if st.button("Join", use_container_width=True):
            if s_room != "Select..." and fn and ln:
                st.session_state.user_fullname = f"{fn.strip()} {ln.strip()}"
                st.session_state.room_id = s_room
                st.session_state.my_group_key = check_reconnect(st.session_state.user_fullname, s_room)
                st.rerun()
    with t2:
        pw = st.text_input("Password:", type="password")
        if st.button("Admin Login"):
            if pw.strip().lower() == TEACHER_PASSWORD:
                st.session_state.user_fullname, st.session_state.role = "Teacher", "Teacher"
                if not st.session_state.room_id: st.session_state.room_id = "Period 1"
                st.rerun()

# --- 6. TEACHER DASHBOARD (Updates Live) ---
elif st.session_state.role == "Teacher":
    st.title(f"👨‍🏫 Live Monitor: {st.session_state.room_id}")
    room = all_rooms[st.session_state.room_id]
    
    # Show active player count total
    total_players = sum(len(g["players"]) for g in room["groups"].values())
    st.sidebar.metric("Total Students Online", total_players)

    cols = st.columns(4)
    for i in range(1, GROUP_COUNT + 1):
        gk = f"Group {i}"
        g = room["groups"][gk]
        with cols[(i-1)%4]:
            with st.container(border=True):
                st.subheader(gk)
                st.write(f"Players: **{len(g['players'])}**")
                if g["started"]:
                    st.success(f"Score: {g['score']}")
                else:
                    st.info("In Lobby")

# --- 7. STUDENT GAMEPLAY (Updates Live) ---
else:
    room = all_rooms[st.session_state.room_id]
    
    if st.session_state.my_group_key is None:
        st.header("Step 1: Choose Your Team")
        sc = st.columns(4)
        for i in range(1, GROUP_COUNT + 1):
            gk = f"Group {i}"
            # The count here updates every 3 seconds!
            count = len(room["groups"][gk]["players"])
            with sc[(i-1)%4]:
                if st.button(f"{gk} ({count})", key=f"join_{gk}"):
                    st.session_state.my_group_key = gk
                    room["groups"][gk]["players"][st.session_state.user_fullname] = {"ready": False}
                    st.rerun()
    
    else:
        g_data = room["groups"][st.session_state.my_group_key]
        
        # LOBBY VIEW
        if not g_data["started"]:
            st.header(f"Lobby: {g_data['display_name']}")
            
            # This list updates automatically when someone joins
            with st.expander("Team Roster", expanded=True):
                for name, p_info in g_data["players"].items():
                    st.write(f"{'✅' if p_info['ready'] else '⏳'} {name}")
            
            # Captain Logic
            if not g_data["captain"]:
                if st.button("🗳️ Become Captain"): 
                    g_data["captain"] = st.session_state.user_fullname
                    st.rerun()
            
            # READY UP
            ready = g_data["players"][st.session_state.user_fullname]["ready"]
            if st.button("READY UP" if not ready else "WAIT", use_container_width=True):
                g_data["players"][st.session_state.user_fullname]["ready"] = not ready
                st.rerun()
            
            # AUTO-START: If the Captain clicks start, everyone's screen changes!
            if g_data["started"]:
                st.rerun()

        # GAMEPLAY VIEW
        else:
            st.title("Game Started!")
            # (Turn logic goes here...)
