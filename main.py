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
                "leader": None,
                "score": 0, 
                "players": {}, # {"Full Name": {"ready": bool, "joined": "timestamp"}}
                "turn_idx": 0,
                "started": False,
                "q": "24/36", "a": "2/3",
                "start_time": time.time(),
                "history": [] # [{"name": "", "correct": bool, "time_taken": 0, "timestamp": ""}]
            } for i in range(1, GROUP_COUNT + 1)}
        }
    return rooms

all_rooms = get_all_rooms()

# --- 3. SESSION STATE ---
if "user_fullname" not in st.session_state: st.session_state.user_fullname = None
if "role" not in st.session_state: st.session_state.role = "Student"
if "room_id" not in st.session_state: st.session_state.room_id = None
if "my_group_key" not in st.session_state: st.session_state.my_group_key = None

st.set_page_config(page_title="Fraction Nexus Admin", layout="wide")

# --- LOGIN (With First/Last Name) ---
if st.session_state.user_fullname is None:
    st.title("🛡️ Fraction Nexus Login")
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
                st.session_state.user_fullname = "Teacher"; st.session_state.role = "Teacher"
                st.rerun()

# --- TEACHER DASHBOARD (With Timestamps) ---
elif st.session_state.role == "Teacher":
    st.title(f"👨‍🏫 Admin Panel - {st.session_state.room_id}")
    room = all_rooms[st.session_state.room_id or "Period 1"]
    
    # Global Controls
    room["mode"] = st.segmented_control("Game Mode:", ["Battle", "Team Fusion", "Practice"], default=room["mode"])
    room["session_active"] = st.toggle("Session Online", value=room["session_active"])
    
    st.divider()
    
    g_cols = st.columns(4)
    for i in range(1, GROUP_COUNT + 1):
        g_key = f"Group {i}"
        g = room["groups"][g_key]
        with g_cols[(i-1)%4]:
            with st.container(border=True):
                st.subheader(g["display_name"])
                # Show Roster with Join Times
                for name, data in g["players"].items():
                    st.caption(f"👤 {name} (Joined: {data['joined']})")
                
                if not g["started"]:
                    num_ready = sum(1 for p in g["players"].values() if p["ready"])
                    total = len(g["players"])
                    if st.button(f"Start {g_key}", key=f"s_{g_key}", disabled=(total == 0 or num_ready < total)):
                        g["started"] = True; g["start_time"] = time.time(); st.rerun()
                else:
                    st.write(f"**Score:** {g['score']}")
                    if st.expander("Detailed Log"):
                        for h in reversed(g["history"][-5:]):
                            st.write(f"{h['timestamp']} - {h['name']} {'✅' if h['correct'] else '❌'}")

# --- STUDENT GAMEPLAY ---
else:
    room = all_rooms[st.session_state.room_id]
    if not room["session_active"]:
        st.warning("Session Paused by Teacher."); st.stop()

    # Practice Mode Logic
    if room["mode"] == "Practice":
        st.title("🧘 Individual Training")
        st.write(f"Welcome, {st.session_state.user_fullname}")
        # Practice questions here...
        st.stop()

    # Group Selection
    if st.session_state.my_group_key is None:
        st.header("Select Your Group")
        cols = st.columns(4)
        for i in range(1, GROUP_COUNT + 1):
            g_key = f"Group {i}"
            if st.button(f"Join {room['groups'][g_key]['display_name']}", key=f"j_{g_key}"):
                st.session_state.my_group_key = g_key
                now = datetime.now().strftime("%H:%M:%S")
                room["groups"][g_key]["players"][st.session_state.user_fullname] = {"ready": False, "joined": now}
                st.rerun()
    
    # Group Lobby / Game
    else:
        g_data = room["groups"][st.session_state.my_group_key]
        if not g_data["started"]:
            st.header(f"Lobby: {g_data['display_name']}")
            is_ready = g_data["players"][st.session_state.user_fullname]["ready"]
            if st.button("READY UP" if not is_ready else "UNREADY", use_container_width=True):
                g_data["players"][st.session_state.user_fullname]["ready"] = not is_ready
                st.rerun()
            st.write("Wait for the teacher to start.")
        else:
            # Active Battle/Fusion Gameplay
            # Note: Logic to handle turn-based questions
            st.title(f"Score: {g_data['score']}")
            # Inside the answer submission logic:
            # current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # g_data["history"].append({"name": st.session_state.user_fullname, "timestamp": current_time, ...})
