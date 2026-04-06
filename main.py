import streamlit as st
import random
import time
from fractions import Fraction

# --- 1. SETTINGS ---
TEACHER_PASSWORD = "mathrocks2026"
ROOM_OPTIONS = ["Period 1", "Period 2", "Period 3", "Period 4"]
GROUP_COUNT = 8 
WINNING_SCORE = 100 # Per group in Battle
COOP_GOAL = 800     # Total for Class in Team Fusion

# --- 2. SHARED DATA ---
@st.cache_resource
def get_all_rooms():
    rooms = {}
    for r in ROOM_OPTIONS:
        rooms[r] = {
            "mode": "Battle", # Options: Battle, Team Fusion, Practice
            "groups": {f"Group {i}": {
                "display_name": f"Group {i}",
                "leader": None,
                "score": 0, 
                "players": {}, # {"Name": is_ready}
                "turn_idx": 0,
                "started": False,
                "q": "20/30", "a": "2/3",
                "start_time": time.time(),
                "history": []
            } for i in range(1, GROUP_COUNT + 1)},
            "session_active": True,
            "timer_enabled": True
        }
    return rooms

all_rooms = get_all_rooms()

# --- 3. SESSION STATE ---
if "user_name" not in st.session_state: st.session_state.user_name = None
if "role" not in st.session_state: st.session_state.role = "Student"
if "room_id" not in st.session_state: st.session_state.room_id = None
if "my_group_key" not in st.session_state: st.session_state.my_group_key = None
if "personal_score" not in st.session_state: st.session_state.personal_score = 0

st.set_page_config(page_title="Fraction Nexus", layout="wide")

# --- LOGIN (Simplified) ---
if st.session_state.user_name is None:
    st.title("🛡️ Fraction Nexus")
    t1, t2 = st.tabs(["Student Join", "Teacher Login"])
    with t1:
        s_room = st.selectbox("Select Class:", ["Select..."] + ROOM_OPTIONS)
        s_name = st.text_input("Your Name")
        if st.button("Join"):
            if s_room != "Select..." and s_name:
                st.session_state.room_id = s_room; st.session_state.user_name = s_name; st.rerun()
    with t2:
        t_pass = st.text_input("Password", type="password")
        if st.button("Login"):
            if t_pass == TEACHER_PASSWORD:
                st.session_state.user_name = "Teacher"; st.session_state.role = "Teacher"; st.rerun()

# --- TEACHER DASHBOARD ---
elif st.session_state.role == "Teacher":
    st.title("👨‍🏫 Grandmaster Control")
    view_room = st.selectbox("Manage Period:", ROOM_OPTIONS)
    room = all_rooms[view_room]
    
    # MODE SELECTOR
    st.info(f"Current Mode: **{room['mode']}**")
    new_mode = st.radio("Switch Game Mode:", ["Battle", "Team Fusion", "Practice"], horizontal=True)
    if new_mode != room["mode"]:
        room["mode"] = new_mode; st.rerun()

    c1, c2 = st.columns(2)
    with c1: room["session_active"] = st.toggle("🟢 Session Active", value=room["session_active"])
    with c2: room["timer_enabled"] = st.toggle("⏱️ Speed Bonus", value=room["timer_enabled"])
    
    if room["mode"] == "Team Fusion":
        total_class_score = sum(g["score"] for g in room["groups"].values())
        st.header(f"🌍 Class Fusion Progress: {total_class_score} / {COOP_GOAL}")
        st.progress(min(total_class_score / COOP_GOAL, 1.0))

    st.divider()
    g_cols = st.columns(4)
    for i in range(1, GROUP_COUNT + 1):
        g_key = f"Group {i}"
        g = room["groups"][g_key]
        with g_cols[(i-1)%4]:
            with st.container(border=True):
                st.subheader(g["display_name"])
                num_ready = sum(1 for r in g["players"].values() if r)
                total_p = len(g["players"])
                
                if room["mode"] != "Practice":
                    if not g["started"]:
                        st.button(f"🚀 Start {g_key}", key=f"s_{g_key}", disabled=(num_ready == 0 or num_ready < total_p), on_click=lambda g=g: g.update({"started": True, "start_time": time.time()}))
                    else:
                        st.write(f"Score: {g['score']}")
                        if st.button("End Group", key=f"stop_{g_key}"): g["started"] = False; st.rerun()

# --- STUDENT GAMEPLAY ---
else:
    room = all_rooms[st.session_state.room_id]
    if not room["session_active"]: st.error("PAUSED"); st.stop()

    # --- MODE 3: INDIVIDUAL PRACTICE ---
    if room["mode"] == "Practice":
        st.title("🧘 Individual Training")
        st.metric("Personal High Score", st.session_state.personal_score)
        st.write("## Simplify: **12/15**") # Example static for brevity
        ans = st.text_input("Answer:")
        if st.button("Check"):
            if ans == "4/5":
                st.session_state.personal_score += 10; st.success("Correct!"); time.sleep(1); st.rerun()
            else: st.error("Try again!")

    # --- MODE 1 & 2: BATTLE & TEAM FUSION ---
    elif st.session_state.my_group_key is None:
        st.header("Select Your Group")
        cols = st.columns(4)
        for i in range(1, GROUP_COUNT + 1):
            g_key = f"Group {i}"
            if st.button(f"Join {room['groups'][g_key]['display_name']}", key=f"j_{g_key}"):
                st.session_state.my_group_key = g_key
                g_ptr = room["groups"][g_key]
                if g_ptr["leader"] is None: g_ptr["leader"] = st.session_state.user_name
                g_ptr["players"][st.session_state.user_name] = False; st.rerun()
    
    else:
        g_data = room["groups"][st.session_state.my_group_key]
        if not g_data["started"]:
            st.header(f"Lobby: {g_data['display_name']}")
            ready = g_data["players"][st.session_state.user_name]
            if st.button("READY" if not ready else "WAITING", use_container_width=True):
                g_data["players"][st.session_state.user_name] = not ready; st.rerun()
            st.write("Status:", "✅ Ready" if ready else "⏳ Click to Ready Up")
        else:
            # Active Gameplay
            player_keys = list(g_data["players"].keys())
            current_player = player_keys[g_data["turn_idx"] % len(player_keys)]
            elapsed = int(time.time() - g_data["start_time"])
            
            if room["mode"] == "Team Fusion":
                total_fusion = sum(g["score"] for g in room["groups"].values())
                st.info(f"🌍 Global Class Score: {total_fusion} / {COOP_GOAL}")
                st.progress(min(total_fusion / COOP_GOAL, 1.0))
            
            st.subheader(f"Group Score: {g_data['score']}")
            if current_player == st.session_state.user_name:
                st.success("YOUR TURN!")
                st.write(f"### Simplify: {g_data['q']}")
                ans = st.text_input("Answer:")
                if st.button("Submit"):
                    try:
                        correct = Fraction(ans) == Fraction(g_data['a'])
                        pts = (15 if elapsed < 10 else 10) if correct else -5
                        g_data['score'] += pts
                        g_data['turn_idx'] += 1; g_data["start_time"] = time.time()
                        # New Question Logic here...
                        st.rerun()
                    except: st.error("Use 1/2 format")
            else:
                st.warning(f"Waiting for {current_player}...")
                time.sleep(1); st.rerun()
