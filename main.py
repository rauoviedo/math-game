import streamlit as st
import random
import time
from datetime import datetime
from fractions import Fraction

# --- 1. SETTINGS ---
TEACHER_PASSWORD = "mathrocks2026"
ROOM_OPTIONS = ["Period 1", "Period 2", "Period 3", "Period 4"]
GROUP_COUNT = 8 

# --- 2. SHARED DATA ---
@st.cache_resource
def get_all_rooms():
    rooms = {}
    for r in ROOM_OPTIONS:
        rooms[r] = {
            "mode": "Match Up", # Default Mode
            "session_active": True,
            "groups": {f"Group {i}": {
                "display_name": f"Group {i}",
                "captain": None,
                "pep_talk": "",
                "score": 0, 
                "streak": 0, # For "Streak Alive" mode
                "players": {}, 
                "turn_idx": 0,
                "started": False,
                "q": "12/15", "a": "4/5",
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

st.set_page_config(page_title="Fraction Nexus V3", layout="wide")

# --- LOGIN ---
if st.session_state.user_fullname is None:
    st.title("🛡️ Fraction Nexus")
    t1, t2 = st.tabs(["Student Entry", "Teacher Admin"])
    with t1:
        s_room = st.selectbox("Class Period:", ["Select..."] + ROOM_OPTIONS)
        c_fn, c_ln = st.columns(2)
        s_first = c_fn.text_input("First Name")
        s_last = c_ln.text_input("Last Name")
        if st.button("Join Session", use_container_width=True):
            if s_room != "Select..." and s_first and s_last:
                st.session_state.room_id = s_room
                st.session_state.user_fullname = f"{s_first.strip()} {s_last.strip()}"
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
    
    # 1. SELECT MODE (Teacher selects for the whole room)
    st.subheader("🎯 Step 1: Select Game Mode")
    mode_cols = st.columns(3)
    with mode_cols[0]:
        if st.button("⚔️ Match Up (Race)", use_container_width=True): room["mode"] = "Match Up"
    with mode_cols[1]:
        if st.button("📚 Study in Groups", use_container_width=True): room["mode"] = "Study in Groups"
    with mode_cols[2]:
        if st.button("🔥 Streak Alive", use_container_width=True): room["mode"] = "Streak Alive"
    
    st.info(f"Current Mode: **{room['mode']}**")
    st.divider()

    # 2. MANAGE GROUPS
    st.subheader("👥 Step 2: Manage Group Starts")
    g_cols = st.columns(4)
    for i in range(1, GROUP_COUNT + 1):
        g_key = f"Group {i}"
        g = room["groups"][g_key]
        with g_cols[(i-1)%4]:
            with st.container(border=True):
                player_count = len(g["players"])
                st.write(f"**{g['display_name']}** ({player_count} Players)")
                
                num_ready = sum(1 for p in g["players"].values() if p["ready"])
                has_pep = len(g["pep_talk"].strip()) >= 3
                
                if not g["started"]:
                    can_start = (player_count > 0 and num_ready == player_count and g["captain"] and has_pep)
                    st.button(f"🚀 Start {room['mode']}", key=f"s_{g_key}", disabled=not can_start, 
                              on_click=lambda g=g: g.update({"started": True, "start_time": time.time()}))
                else:
                    if room["mode"] == "Streak Alive":
                        st.write(f"Current Streak: **{g['streak']}**")
                    else:
                        st.write(f"Score: **{g['score']}**")
                    if st.button("Reset", key=f"res_{g_key}"): g["started"] = False; g["score"] = 0; g["streak"] = 0; st.rerun()

# --- STUDENT GAMEPLAY ---
else:
    room = all_rooms[st.session_state.room_id]
    
    # STEP 1: PICK GROUP
    if st.session_state.my_group_key is None:
        st.header("Step 1: Join a Team")
        cols = st.columns(4)
        for i in range(1, GROUP_COUNT + 1):
            g_key = f"Group {i}"
            p_count = len(room["groups"][g_key]["players"])
            with cols[(i-1)%4]:
                if st.button(f"{room['groups'][g_key]['display_name']}\n({p_count} Players)", key=f"j_{g_key}", use_container_width=True):
                    st.session_state.my_group_key = g_key
                    room["groups"][g_key]["players"][st.session_state.user_fullname] = {"ready": False, "joined": datetime.now().strftime("%H:%M")}
                    st.rerun()
    
    # STEP 2: LOBBY & MODE PREP
    else:
        g_data = room["groups"][st.session_state.my_group_key]
        if not g_data["started"]:
            st.header(f"Team Lobby: {g_data['display_name']}")
            st.warning(f"Mode for this session: **{room['mode']}**")
            
            # Captain & Pep Talk
            if g_data["captain"] is None:
                if st.button("🗳️ Nominate Myself as Captain"): g_data["captain"] = st.session_state.user_fullname; st.rerun()
            elif st.session_state.user_fullname == g_data["captain"]:
                pep = st.text_input("Encouraging Pep Talk:", value=g_data["pep_talk"])
                if st.button("Save Message"): g_data["pep_talk"] = pep; st.rerun()
                if st.button("Never mind, I don't want to be captain", type="secondary"): g_data["captain"] = None; st.rerun()
            else:
                st.info(f"Captain: {g_data['captain']}")

            # Ready Button
            p_info = g_data["players"][st.session_state.user_fullname]
            if st.button("✅ READY" if not p_info["ready"] else "⏳ NOT READY", use_container_width=True):
                p_info["ready"] = not p_info["ready"]; st.rerun()
            
            st.write(f"Ready: {sum(1 for p in g_data['players'].values() if p['ready'])} / {len(g_data['players'])}")
        
        # STEP 3: GAMEPLAY MODES
        else:
            st.info(f"💪 {g_data['captain']} says: {g_data['pep_talk']}")
            
            if room["mode"] == "Match Up":
                st.subheader("⚔️ Match Up: Race to 100!")
                st.progress(min(g_data["score"] / 100, 1.0))
                # (Fraction turn logic goes here, correct = +10 pts)
                
            elif room["mode"] == "Study in Groups":
                st.subheader("📚 Study Mode: Accuracy Matters")
                st.write("Take your time to simplify correctly.")
                # (Fraction turn logic, no negative points for wrong answers)
                
            elif room["mode"] == "Streak Alive":
                st.subheader("🔥 Streak Alive: Don't miss!")
                st.metric("Current Streak", g_data["streak"])
                # (Fraction turn logic: Correct = Streak +1, Wrong = Streak reset to 0!)
            
            st.button("Refresh status")
