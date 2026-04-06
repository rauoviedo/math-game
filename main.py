import streamlit as st
import random
import time
import pandas as pd
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
from fractions import Fraction

# --- 1. SETTINGS & LIVE HEARTBEAT ---
# Automatically refreshes the page every 3 seconds to show new players/scores
st_autorefresh(interval=3000, limit=None, key="nexus_heartbeat")

TEACHER_PASSWORD = "mathrocks2026"
ROOM_OPTIONS = ["Period 1", "Period 2", "Period 3", "Period 4"]
GROUP_COUNT = 8 

# --- 2. SHARED SERVER DATA ---
@st.cache_resource
def get_all_rooms():
    rooms = {}
    for r in ROOM_OPTIONS:
        rooms[r] = {
            "groups": {f"Group {i}": {
                "display_name": f"Group {i}",
                "mode": "Match Up",
                "goal": 100,
                "diff": "Medium",
                "captain": None,
                "pep_talk": "",
                "score": 0, 
                "streak": 0,
                "players": {}, # Storage: {"Name": {"ready": bool}}
                "turn_idx": 0,
                "started": False,
                "start_time": None,
                "q": "10/15", "a": "2/3",
                "history": [] 
            } for i in range(1, GROUP_COUNT + 1)}
        }
    return rooms

all_rooms = get_all_rooms()

# --- 3. INDIVIDUAL SESSION STATE ---
if "user_fullname" not in st.session_state: st.session_state.user_fullname = None
if "role" not in st.session_state: st.session_state.role = "Student"
if "room_id" not in st.session_state: st.session_state.room_id = None
if "my_group_key" not in st.session_state: st.session_state.my_group_key = None

st.set_page_config(page_title="Fraction Nexus", layout="wide", page_icon="🎯")

# --- 4. NAVIGATION & RECOVERY LOGIC ---
def reset_session():
    st.session_state.user_fullname = None
    st.session_state.room_id = None
    st.session_state.my_group_key = None
    st.session_state.role = "Student"
    st.rerun()

# Sidebar Navigation
if st.session_state.user_fullname:
    with st.sidebar:
        st.write(f"👤 **{st.session_state.user_fullname}**")
        st.write(f"🏫 {st.session_state.room_id}")
        if st.button("🔙 Return to Home / Logout"):
            reset_session()
        st.divider()

# --- 5. LOGIN & RECONNECT ---
if st.session_state.user_fullname is None:
    st.title("🛡️ Fraction Nexus")
    t1, t2 = st.tabs(["👤 Student Join", "🔑 Teacher Access"])
    
    with t1:
        s_room = st.selectbox("Select Class:", ["Select..."] + ROOM_OPTIONS)
        c1, c2 = st.columns(2)
        fn, ln = c1.text_input("First Name"), c2.text_input("Last Name")
        if st.button("Enter Battleground", use_container_width=True):
            if s_room != "Select..." and fn and ln:
                name = f"{fn.strip()} {ln.strip()}"
                st.session_state.room_id = s_room
                st.session_state.user_fullname = name
                # Reconnect Check
                for gk, gd in all_rooms[s_room]["groups"].items():
                    if name in gd["players"]:
                        st.session_state.my_group_key = gk
                st.rerun()

    with t2:
        pw = st.text_input("Teacher Password:", type="password")
        if st.button("Unlock Admin Dashboard"):
            if pw.strip().lower() == TEACHER_PASSWORD:
                st.session_state.user_fullname, st.session_state.role = "Teacher", "Teacher"
                if not st.session_state.room_id: st.session_state.room_id = "Period 1"
                st.rerun()

# --- 6. TEACHER DASHBOARD ---
elif st.session_state.role == "Teacher":
    st.title(f"👨‍🏫 Control Center: {st.session_state.room_id}")
    room = all_rooms[st.session_state.room_id]

    with st.expander("⚙️ Global Match Settings"):
        col_g, col_m, col_d = st.columns(3)
        g_goal = col_g.number_input("Goal Score:", 10, 500, 100)
        g_mode = col_m.selectbox("Game Mode:", ["Match Up", "Study in Groups", "Streak Alive"])
        g_diff = col_d.selectbox("Difficulty:", ["Easy", "Medium", "Hard"], index=1)
        if st.button("Sync All Groups"):
            for g in room["groups"].values():
                g.update({"goal": g_goal, "mode": g_mode, "diff": g_diff})
            st.success("Settings Updated Live!")

    st.divider()
    t_cols = st.columns(4)
    for i in range(1, GROUP_COUNT + 1):
        gk = f"Group {i}"
        g = room["groups"][gk]
        with t_cols[(i-1)%4]:
            with st.container(border=True):
                st.subheader(gk)
                st.write(f"Players: **{len(g['players'])}**")
                if g["started"]:
                    st.success(f"LIVE | Score: {g['score']}")
                    if st.button("🛑 Stop & Log", key=f"stop_{gk}"):
                        if g["history"]:
                            df = pd.DataFrame(g["history"])
                            st.table(df.groupby('name')['correct'].sum())
                        g.update({"started": False, "score": 0, "history": []})
                        st.rerun()
                else:
                    st.info("Waiting in Lobby...")

# --- 7. STUDENT GAMEPLAY ---
else:
    room = all_rooms[st.session_state.room_id]
    
    # Select Group
    if st.session_state.my_group_key is None:
        st.header("Step 1: Choose Your Team")
        sc = st.columns(4)
        for i in range(1, GROUP_COUNT + 1):
            gk = f"Group {i}"
            count = len(room["groups"][gk]["players"])
            with sc[(i-1)%4]:
                if st.button(f"{gk}\n({count} Players)", key=f"sel_{gk}"):
                    st.session_state.my_group_key = gk
                    room["groups"][gk]["players"][st.session_state.user_fullname] = {"ready": False}
                    st.rerun()
    
    # Gameplay / Lobby
    else:
        g_data = room["groups"][st.session_state.my_group_key]
        
        # Accidental Logout Recovery
        if st.session_state.user_fullname not in g_data["players"]:
            g_data["players"][st.session_state.user_fullname] = {"ready": False}

        if not g_data["started"]:
            st.header(f"Lobby: {g_data['display_name']}")
            
            if st.button("⬅️ Leave Group"):
                del g_data["players"][st.session_state.user_fullname]
                if g_data["captain"] == st.session_state.user_fullname: g_data["captain"] = None
                st.session_state.my_group_key = None
                st.rerun()

            # Live Roster
            with st.expander("👥 Team Roster (Updates Live)", expanded=True):
                for name, info in g_data["players"].items():
                    st.write(f"{'✅' if info['ready'] else '⏳'} {name} {'👑' if name == g_data['captain'] else ''}")
            
            # Captain Controls
            if st.session_state.user_fullname == g_data["captain"]:
                st.success("🌟 You are the Captain!")
                pep = st.text_input("Enter Pep Talk:", value=g_data["pep_talk"])
                if st.button("Save Talk"): g_data["pep_talk"] = pep; st.rerun()
                
                num_ready = sum(1 for p in g_data["players"].values() if p["ready"])
                can_start = (num_ready == len(g_data["players"]) and len(g_data["players"]) > 0 and len(g_data["pep_talk"]) > 2)
                if st.button("🚀 START MATCH", type="primary", disabled=not can_start):
                    g_data["started"] = True; g_data["start_time"] = time.time(); st.rerun()
            elif not g_data["captain"]:
                if st.button("🗳️ Become Captain"): g_data["captain"] = st.session_state.user_fullname; st.rerun()
            
            # Ready Button
            is_ready = g_data["players"][st.session_state.user_fullname]["ready"]
            if st.button("✅ I AM READY" if not is_ready else "⏳ NOT READY", use_container_width=True):
                g_data["players"][st.session_state.user_fullname]["ready"] = not is_ready
                st.rerun()

        # Countdown Screen
        elif time.time() - g_data["start_time"] < 5:
            remain = 5 - int(time.time() - g_data["start_time"])
            st.title(f"🚀 Starting in... {remain}")
            st.subheader(f"📢 {g_data['captain']}: {g_data['pep_talk']}")
            time.sleep(1); st.rerun()

        # Active Match
        else:
            player_list = list(g_data["players"].keys())
            current_p = player_list[g_data["turn_idx"] % len(player_list)]
            
            st.title(f"Score: {g_data['score']} / {g_data['goal']}")
            st.subheader(f"📢 {g_data['pep_talk']}")
            
            if current_p == st.session_state.user_fullname:
                st.success("🎯 YOUR TURN!")
                st.write(f"## Reduce: **{g_data['q']}**")
                ans = st.text_input("Answer (x/y):", key="math_ans")
                if st.button("Submit"):
                    try:
                        correct = Fraction(ans) == Fraction(g_data['a'])
                        if correct: g_data["score"] += 10
                        else: g_data["score"] -= 5
                        g_data["history"].append({"name": st.session_state.user_fullname, "correct": correct})
                        g_data["turn_idx"] += 1
                        # New Question
                        cf = random.randint(2, 10); n = random.randint(1, 6); d = random.randint(7, 12)
                        g_data["q"], g_data["a"] = f"{n*cf}/{d*cf}", f"{Fraction(n, d)}"
                        st.rerun()
                    except: st.error("Use 1/2 format!")
            else:
                st.warning(f"Waiting for {current_p}...")
