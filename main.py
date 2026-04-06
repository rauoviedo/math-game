import streamlit as st
import random
import time
import pandas as pd
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
                "goal": 100,
                "diff": "Medium",
                "captain": None,
                "pep_talk": "",
                "score": 0, 
                "streak": 0,
                "players": {}, 
                "turn_idx": 0,
                "started": False,
                "start_time": None, # Set when teacher clicks start
                "q": "12/18", "a": "2/3",
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

st.set_page_config(page_title="Fraction Nexus", layout="wide", page_icon="🎯")

# --- 4. LOGIN ---
if st.session_state.user_fullname is None:
    st.title("🛡️ Fraction Nexus")
    t1, t2 = st.tabs(["👤 Student Join", "🔑 Teacher Access"])
    with t1:
        s_room = st.selectbox("Class:", ["Select..."] + ROOM_OPTIONS)
        c1, c2 = st.columns(2)
        fn, ln = c1.text_input("First Name"), c2.text_input("Last Name")
        if st.button("Join Session", use_container_width=True):
            if s_room != "Select..." and fn and ln:
                st.session_state.room_id, st.session_state.user_fullname = s_room, f"{fn.strip()} {ln.strip()}"
                st.rerun()
    with t2:
        pw = st.text_input("Admin Password:", type="password")
        if st.button("Unlock Dashboard"):
            if pw.strip().lower() == TEACHER_PASSWORD:
                st.session_state.user_fullname, st.session_state.role = "Teacher", "Teacher"
                if not st.session_state.room_id: st.session_state.room_id = "Period 1"
                st.rerun()

# --- 5. TEACHER DASHBOARD ---
elif st.session_state.role == "Teacher":
    st.title(f"👨‍🏫 Control Center: {st.session_state.room_id}")
    room = all_rooms[st.session_state.room_id]
    
    st.divider()
    cols = st.columns(4)
    for i in range(1, GROUP_COUNT + 1):
        g_key = f"Group {i}"
        g = room["groups"][g_key]
        with cols[(i-1)%4]:
            with st.container(border=True):
                st.subheader(g["display_name"])
                p_count = len(g["players"])
                num_ready = sum(1 for p in g["players"].values() if p["ready"])
                
                if not g["started"]:
                    st.write(f"👥 Players: {p_count} ({num_ready} Ready)")
                    can_start = (p_count > 0 and num_ready == p_count and g["captain"] and len(g["pep_talk"]) > 2)
                    if st.button(f"🚀 Start {g_key}", key=f"btn_{g_key}", disabled=not can_start):
                        g["started"] = True; g["start_time"] = time.time(); st.rerun()
                else:
                    st.success("MATCH LIVE")
                    if st.button("🛑 End Round", key=f"end_{g_key}"):
                        g.update({"started": False, "score": 0, "streak": 0, "history": []}); st.rerun()

# --- 6. STUDENT GAMEPLAY ---
else:
    room = all_rooms[st.session_state.room_id]
    
    if st.session_state.my_group_key is None:
        st.header("Step 1: Choose Your Team")
        sc = st.columns(4)
        for i in range(1, GROUP_COUNT + 1):
            gk = f"Group {i}"
            count = len(room["groups"][gk]["players"])
            with sc[(i-1)%4]:
                if st.button(f"{room['groups'][gk]['display_name']} ({count})", key=f"j_{gk}", use_container_width=True):
                    st.session_state.my_group_key = gk
                    room["groups"][gk]["players"][st.session_state.user_fullname] = {"ready": False}
                    st.rerun()
    
    else:
        g_data = room["groups"][st.session_state.my_group_key]
        
        if not g_data["started"]:
            st.header(f"Lobby: {g_data['display_name']}")
            with st.expander("👥 Team Roster", expanded=True):
                for name, data in g_data["players"].items():
                    st.write(f"{'✅' if data['ready'] else '⏳'} {name}")
            
            if st.button("🚪 Leave Group"):
                if st.session_state.user_fullname in g_data["players"]:
                    del g_data["players"][st.session_state.user_fullname]
                if g_data["captain"] == st.session_state.user_fullname: g_data["captain"] = None
                st.session_state.my_group_key = None; st.rerun()

            if not g_data["captain"]:
                if st.button("🗳️ Become Captain"): g_data["captain"] = st.session_state.user_fullname; st.rerun()
            elif st.session_state.user_fullname == g_data["captain"]:
                pep = st.text_input("Pep Talk:", value=g_data["pep_talk"])
                if st.button("Save Message"): g_data["pep_talk"] = pep; st.rerun()
            
            ready = g_data["players"][st.session_state.user_fullname]["ready"]
            if st.button("✅ READY UP" if not ready else "⏳ UNREADY", use_container_width=True):
                g_data["players"][st.session_state.user_fullname]["ready"] = not ready; st.rerun()

        # --- THE COUNTDOWN LOGIC ---
        elif time.time() - g_data["start_time"] < 5:
            remaining = 5 - int(time.time() - g_data["start_time"])
            st.title("🚀 PREPARING BATTLE...")
            st.header(f"📢 Captain says: {g_data['pep_talk']}")
            st.write(f"## Get ready in... {remaining}")
            st.progress(remaining / 5)
            time.sleep(1)
            st.rerun()

        else:
            # Active Gameplay
            st.title(f"Mode: {g_data['mode']}")
            st.subheader(f"💪 {g_data['pep_talk']}")
            st.write("Match is live! Answer below.")
