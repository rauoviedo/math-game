import streamlit as st
import random
import time
from datetime import datetime
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
            "mode": "Battle", 
            "session_active": True,
            "groups": {f"Group {i}": {
                "display_name": f"Group {i}",
                "captain": None,
                "pep_talk": "",
                "score": 0, 
                "players": {}, 
                "turn_idx": 0,
                "started": False,
                "q": "10/25", "a": "2/5",
                "start_time": time.time(),
                "history": []
            } for i in range(1, GROUP_COUNT + 1)}
        }
    return rooms

all_rooms = get_all_rooms()

# --- 3. SESSION STATE ---
if "user_fullname" not in st.session_state: st.session_state.user_fullname = None
if "room_id" not in st.session_state: st.session_state.room_id = None
if "my_group_key" not in st.session_state: st.session_state.my_group_key = None

st.set_page_config(page_title="Fraction Nexus: Team Edition", layout="wide")

# --- LOGIN (First & Last Name) ---
if st.session_state.user_fullname is None:
    st.title("🛡️ Fraction Nexus: Login")
    t1, t2 = st.tabs(["Student Entry", "Teacher Admin"])
    with t1:
        s_room = st.selectbox("Class Period:", ["Select..."] + ROOM_OPTIONS)
        c_fn, c_ln = st.columns(2)
        s_first = c_fn.text_input("First Name")
        s_last = c_ln.text_input("Last Name")
        if st.button("Join Session", use_container_width=True):
            if s_room != "Select..." and s_first and s_last:
                st.session_state.room_id = s_room
                st.session_state.user_fullname = f"{s_first} {s_last}"
                st.rerun()
    with t2:
        t_pass = st.text_input("Admin Password", type="password")
        if st.button("Access Dashboard"):
            if t_pass == TEACHER_PASSWORD:
                st.session_state.user_fullname = "Teacher"; st.session_state.role = "Teacher"; st.rerun()

# --- TEACHER DASHBOARD ---
elif st.session_state.get("role") == "Teacher":
    st.title(f"👨‍🏫 Teacher Dashboard - {st.session_state.room_id}")
    room = all_rooms[st.session_state.room_id]
    room["mode"] = st.radio("Mode:", ["Battle", "Team Fusion", "Practice"], horizontal=True)
    
    st.divider()
    g_cols = st.columns(4)
    for i in range(1, GROUP_COUNT + 1):
        g_key = f"Group {i}"
        g = room["groups"][g_key]
        with g_cols[(i-1)%4]:
            with st.container(border=True):
                st.subheader(g["display_name"])
                st.caption(f"Captain: {g['captain'] if g['captain'] else 'NONE'}")
                
                num_ready = sum(1 for p in g["players"].values() if p["ready"])
                total = len(g["players"])
                has_pep = len(g["pep_talk"].strip()) >= 3
                
                can_start = (total > 0 and num_ready == total and g["captain"] and has_pep)
                
                if not g["started"]:
                    st.button(f"🚀 Start {g_key}", key=f"s_{g_key}", disabled=not can_start, 
                              on_click=lambda g=g: g.update({"started": True, "start_time": time.time()}))
                    if not g["captain"]: st.error("No Captain")
                    elif not has_pep: st.warning("Needs Pep Talk")
                else:
                    st.success("Match Live")
                    if st.button("Stop", key=f"stop_{g_key}"): g["started"] = False; st.rerun()

# --- STUDENT GAMEPLAY ---
else:
    room = all_rooms[st.session_state.room_id]
    
    # Select Team
    if st.session_state.my_group_key is None:
        st.header("Select Your Team")
        cols = st.columns(4)
        for i in range(1, GROUP_COUNT + 1):
            g_key = f"Group {i}"
            if st.button(f"Join {room['groups'][g_key]['display_name']}", key=f"j_{g_key}"):
                st.session_state.my_group_key = g_key
                now = datetime.now().strftime("%H:%M")
                room["groups"][g_key]["players"][st.session_state.user_fullname] = {"ready": False, "joined": now}
                st.rerun()
    else:
        g_data = room["groups"][st.session_state.my_group_key]
        is_captain = (st.session_state.user_fullname == g_data["captain"])

        if not g_data["started"]:
            st.header(f"Lobby: {g_data['display_name']}")
            
            # --- CAPTAIN LOGIC ---
            if g_data["captain"] is None:
                if st.button("🗳️ Nominate Myself as Captain", use_container_width=True):
                    g_data["captain"] = st.session_state.user_fullname
                    st.rerun()
            
            elif is_captain:
                st.success("🌟 YOU ARE THE CAPTAIN")
                pep = st.text_input("Encouraging Phrase:", value=g_data["pep_talk"])
                if st.button("Save Pep Talk"):
                    g_data["pep_talk"] = pep
                    st.rerun()
                
                # THE RESIGN BUTTON
                if st.button("❌ Never mind, I do not want to be a captain", type="secondary"):
                    g_data["captain"] = None
                    g_data["pep_talk"] = ""
                    st.rerun()
            
            else:
                st.info(f"Team Captain: **{g_data['captain']}**")
                if g_data["pep_talk"]:
                    st.write(f"📢 **Captain says:** _{g_data['pep_talk']}_")

            # Ready Up
            p_data = g_data["players"][st.session_state.user_fullname]
            if st.button("✅ READY" if not p_data["ready"] else "⏳ NOT READY"):
                p_data["ready"] = not p_data["ready"]
                st.rerun()
        else:
            # Active Game (Simplified turn-based fraction logic)
            st.info(f"💪 TEAM MOTIVATION: {g_data['pep_talk']}")
            st.title(f"Score: {g_data['score']}")
            st.write("Go team! (Use 1/2 format for fractions)")
