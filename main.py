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
        new_mode = col_c.selectbox("Switch All Modes To:", ["Match Up", "Study in Groups", "Streak Alive"])
        
        if st.button("Apply Setup to All Groups", use_container_width=True):
            for g in room["groups"].values():
                g["goal"] = new_goal
                g["diff"] = new_diff
                g["mode"] = new_mode
                # Generate first question based on difficulty
                cf = random.randint(2, 5) if new_diff == "Easy" else random.randint(4, 12)
                n = random.randint(1, 4) if new_diff == "Easy" else random.randint(5, 15)
                d = random.randint(5, 10) if new_diff == "Easy" else random.randint(16, 30)
                g["q"] = f"{n*cf}/{d*cf}"; g["a"] = str(Fraction(n, d))
            st.success("Match configurations updated!")

    st.divider()
    cols = st.columns(4)
    for i in range(1, GROUP_COUNT + 1):
        g_key = f"Group {i}"
        g = room["groups"][g_key]
        with cols[(i-1)%4]:
            with st.container(border=True):
                st.subheader(g["display_name"])
                st.caption(f"🎯 Goal: {g['goal']} | ⚖️ {g['diff']}")
                
                p_count = len(g["players"])
                num_ready = sum(1 for p in g["players"].values() if p["ready"])
                has_pep = len(g["pep_talk"].strip()) >= 3

                if not g["started"]:
                    can_start = (p_count > 0 and num_ready == p_count and g["captain"] and has_pep)
                    if st.button(f"🚀 Launch {g_key}", key=f"btn_{g_key}", disabled=not can_start):
                        g["started"] = True; g["start_time"] = time.time(); st.rerun()
                else:
                    st.success(f"In Battle: {g['mode']}")
                    st.progress(min(g["score"] / g["goal"], 1.0) if g["mode"] == "Match Up" else 0.0)
                    if st.button("Reset", key=f"res_{g_key}"): 
                        g["started"] = False; g["score"] = 0; st.rerun()

# --- 6. STUDENT GAMEPLAY ---
else:
    room = all_rooms[st.session_state.room_id]
    if st.session_state.my_group_key is None:
        st.header("Join a Team")
        sc = st.columns(4)
        for i in range(1, GROUP_COUNT + 1):
            gk = f"Group {i}"
            with sc[(i-1)%4]:
                if st.button(f"{room['groups'][gk]['display_name']}\n({len(room['groups'][gk]['players'])} Players)", key=f"join_{gk}"):
                    st.session_state.my_group_key = gk
                    room["groups"][gk]["players"][st.session_state.user_fullname] = {"ready": False}
                    st.rerun()
    else:
        g_data = room["groups"][st.session_state.my_group_key]
        if not g_data["started"]:
            st.header(f"Lobby: {g_data['display_name']}")
            st.info(f"Mode: **{g_data['mode']}** | Difficulty: **{g_data['diff']}**")
            st.write(f"Target Score: **{g_data['goal']}**")
            
            # Captain Logic
            if g_data["captain"] is None:
                if st.button("Nominate Captain"): g_data["captain"] = st.session_state.user_fullname; st.rerun()
            elif st.session_state.user_fullname == g_data["captain"]:
                pep = st.text_input("Pep Talk:", value=g_data["pep_talk"])
                if st.button("Save"): g_data["pep_talk"] = pep; st.rerun()
                if st.button("Resign"): g_data["captain"] = None; st.rerun()
            
            ready = g_data["players"][st.session_state.user_fullname]["ready"]
            if st.button("✅ READY" if not ready else "⏳ NOT READY"):
                g_data["players"][st.session_state.user_fullname]["ready"] = not ready; st.rerun()
        else:
            # Active Gameplay
            st.title(f"{g_data['mode']} Mode")
            st.write(f"Difficulty: **{g_data['diff']}**")
            st.subheader(f"📢 {g_data['pep_talk']}")
            
            if g_data['mode'] == "Match Up":
                st.write(f"### Progress: {g_data['score']} / {g_data['goal']}")
                st.progress(min(g_data['score'] / g_data['goal'], 1.0))
            
            st.write("Game is live! Work with your team.")
