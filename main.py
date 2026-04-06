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
                "players": {}, # {"Name": {"ready": bool}}
                "turn_idx": 0,
                "started": False,
                "q": "10/20", "a": "1/2",
                "start_time": time.time(),
                "history": [] # [{"name": "John", "correct": True, "ts": "10:00"}]
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

    with st.expander("⚙️ GLOBAL SETUP & LEADERBOARD"):
        c_goal, c_diff, c_mode = st.columns(3)
        goal = c_goal.number_input("Target Score:", 10, 500, 100)
        diff = c_diff.selectbox("Difficulty:", ["Easy", "Medium", "Hard"], index=1)
        mode = c_mode.selectbox("Mode:", ["Match Up", "Study in Groups", "Streak Alive"])
        if st.button("Sync All Groups"):
            for g in room["groups"].values():
                g.update({"goal": goal, "diff": diff, "mode": mode})
            st.success("Settings Pushed!")

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
                    st.success(f"Mode: {g['mode']}")
                    st.metric("Score", g["score"] if g["mode"] != "Streak Alive" else g["streak"])
                    
                    if st.button("🛑 End Round", key=f"end_{g_key}"):
                        # LOGGING LOGIC
                        if g["history"]:
                            st.write("### Round Results")
                            df = pd.DataFrame(g["history"])
                            stats = df.groupby('name')['correct'].agg(['count', 'sum']).reset_index()
                            stats.columns = ['Player', 'Attempts', 'Correct']
                            stats['Accuracy'] = (stats['Correct'] / stats['Attempts'] * 100).round(1).astype(str) + '%'
                            st.table(stats)
                            if st.button("Clear & Reset Group"):
                                g.update({"started": False, "score": 0, "streak": 0, "history": []})
                                st.rerun()
                        else:
                            g.update({"started": False, "score": 0, "streak": 0}); st.rerun()

# --- 6. STUDENT GAMEPLAY ---
else:
    room = all_rooms[st.session_state.room_id]
    if st.session_state.my_group_key is None:
        st.header("Join a Team")
        sc = st.columns(2 if len(ROOM_OPTIONS) < 5 else 4)
        for i in range(1, GROUP_COUNT + 1):
            gk = f"Group {i}"
            with sc[(i-1)%len(sc)]:
                if st.button(f"{room['groups'][gk]['display_name']} ({len(room['groups'][gk]['players'])})", key=f"j_{gk}", use_container_width=True):
                    st.session_state.my_group_key = gk
                    room["groups"][gk]["players"][st.session_state.user_fullname] = {"ready": False}
                    st.rerun()
    else:
        g_data = room["groups"][st.session_state.my_group_key]
        if not g_data["started"]:
            st.header(f"Lobby: {g_data['display_name']}")
            st.write(f"**Mode:** {g_data['mode']} | **Goal:** {g_data['goal']}")
            
            if not g_data["captain"]:
                if st.button("🗳️ Become Captain"): g_data["captain"] = st.session_state.user_fullname; st.rerun()
            elif st.session_state.user_fullname == g_data["captain"]:
                pep = st.text_input("Encouraging Message:", value=g_data["pep_talk"])
                if st.button("Save Message"): g_data["pep_talk"] = pep; st.rerun()
                if st.button("Resign"): g_data["captain"] = None; st.rerun()
            else:
                st.info(f"Captain: {g_data['captain']}")
            
            ready = g_data["players"][st.session_state.user_fullname]["ready"]
            if st.button("✅ READY" if not ready else "⏳ UNREADY", use_container_width=True):
                g_data["players"][st.session_state.user_fullname]["ready"] = not ready; st.rerun()
        else:
            # Active Gameplay
            player_list = list(g_data["players"].keys())
            current_p = player_list[g_data["turn_idx"] % len(player_list)]
            
            st.subheader(f"💪 {g_data['pep_talk']}")
            st.write(f"### Score: {g_data['score']} / {g_data['goal']}")
            
            if current_p == st.session_state.user_fullname:
                st.success("🌟 YOUR TURN!")
                st.write(f"## Reduce: **{g_data['q']}**")
                ans = st.text_input("Answer (e.g., 1/2):")
                if st.button("Submit"):
                    try:
                        correct = Fraction(ans) == Fraction(g_data['a'])
                        if correct: g_data["score"] += 10; g_data["streak"] += 1
                        else: g_data["score"] -= 5; g_data["streak"] = 0
                        
                        g_data["history"].append({"name": st.session_state.user_fullname, "correct": correct})
                        g_data["turn_idx"] += 1
                        # Generate next
                        cf = random.randint(2, 10); n = random.randint(1, 6); d = random.randint(7, 12)
                        g_data["q"], g_data["a"] = f"{n*cf}/{d*cf}", f"{Fraction(n, d)}"
                        st.rerun()
                    except: st.error("Use the 1/2 format!")
            else:
                st.warning(f"Waiting for {current_p}...")
                time.sleep(3); st.rerun()
