import streamlit as st
import random
import time
from datetime import datetime
from fractions import Fraction

# --- 1. CONFIGURATION & PASSWORD ---
TEACHER_PASSWORD = "mathrocks2026"
ROOM_OPTIONS = ["Period 1", "Period 2", "Period 3", "Period 4"]
GROUP_COUNT = 8 
WINNING_SCORE = 100

# --- 2. SHARED DATA STORAGE ---
@st.cache_resource
def get_all_rooms():
    rooms = {}
    for r in ROOM_OPTIONS:
        rooms[r] = {
            "mode": "Match Up", # Default: Match Up, Study in Groups, Streak Alive
            "session_active": True,
            "groups": {f"Group {i}": {
                "display_name": f"Group {i}",
                "captain": None,
                "pep_talk": "",
                "score": 0, 
                "streak": 0,
                "players": {}, # {"Full Name": {"ready": bool, "joined": "timestamp"}}
                "turn_idx": 0,
                "started": False,
                "q": "12/16", "a": "3/4",
                "start_time": time.time(),
                "history": [] # Individual records
            } for i in range(1, GROUP_COUNT + 1)}
        }
    return rooms

all_rooms = get_all_rooms()

# --- 3. SESSION STATE MANAGEMENT ---
if "user_fullname" not in st.session_state: st.session_state.user_fullname = None
if "role" not in st.session_state: st.session_state.role = "Student"
if "room_id" not in st.session_state: st.session_state.room_id = None
if "my_group_key" not in st.session_state: st.session_state.my_group_key = None

st.set_page_config(page_title="Fraction Nexus", layout="wide", page_icon="🎯")

# --- 4. LOGIN SYSTEM ---
if st.session_state.user_fullname is None:
    st.title("🛡️ Fraction Nexus: Battle & Study")
    st.write("Welcome! Please log in to join your class.")
    
    t1, t2 = st.tabs(["👤 Student Join", "🔑 Teacher Access"])
    
    with t1:
        s_room = st.selectbox("Select Class Period:", ["Select..."] + ROOM_OPTIONS)
        c1, c2 = st.columns(2)
        fname = c1.text_input("First Name")
        lname = c2.text_input("Last Name")
        if st.button("Join Session", use_container_width=True):
            if s_room != "Select..." and fname and lname:
                st.session_state.room_id = s_room
                st.session_state.user_fullname = f"{fname.strip()} {lname.strip()}"
                st.session_state.role = "Student"
                st.rerun()
            else:
                st.error("Please fill in all fields.")

    with t2:
        st.subheader("Administrative Login")
        input_pass = st.text_input("Enter Teacher Password:", type="password")
        if st.button("Unlock Dashboard", use_container_width=True):
            if input_pass.strip().lower() == TEACHER_PASSWORD.lower():
                st.session_state.user_fullname = "Teacher"
                st.session_state.role = "Teacher"
                if not st.session_state.room_id: st.session_state.room_id = "Period 1"
                st.success("Access Granted!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Incorrect Password.")

# --- 5. TEACHER DASHBOARD ---
elif st.session_state.role == "Teacher":
    st.title(f"👨‍🏫 Admin: {st.session_state.room_id}")
    room = all_rooms[st.session_state.room_id]
    
    # Global Mode Controls
    c_m1, c_m2, c_m3 = st.columns(3)
    if c_m1.button("⚔️ Mode: Match Up"): room["mode"] = "Match Up"
    if c_m2.button("📚 Mode: Study Groups"): room["mode"] = "Study in Groups"
    if c_m3.button("🔥 Mode: Streak Alive"): room["mode"] = "Streak Alive"
    
    st.info(f"Active Mode: **{room['mode']}**")
    
    st.divider()
    g_cols = st.columns(4)
    for i in range(1, GROUP_COUNT + 1):
        g_key = f"Group {i}"
        g = room["groups"][g_key]
        with g_cols[(i-1)%4]:
            with st.container(border=True):
                st.subheader(f"{g['display_name']}")
                p_count = len(g["players"])
                st.write(f"Players: **{p_count}**")
                
                num_ready = sum(1 for p in g["players"].values() if p["ready"])
                has_pep = len(g["pep_talk"].strip()) >= 3
                
                if not g["started"]:
                    can_start = (p_count > 0 and num_ready == p_count and g["captain"] and has_pep)
                    st.button(f"🚀 Start {g_key}", key=f"s_{g_key}", disabled=not can_start)
                    if st.session_state.get(f"s_{g_key}"): # Trigger start
                        g["started"] = True; g["start_time"] = time.time(); st.rerun()
                    
                    if p_count > 0:
                        st.caption(f"Ready: {num_ready}/{p_count}")
                        if not g["captain"]: st.error("Need Captain")
                        elif not has_pep: st.warning("Need Pep Talk")
                else:
                    st.success("LIVE")
                    st.write(f"Score/Streak: {g['score'] if room['mode'] != 'Streak Alive' else g['streak']}")
                    if st.button("End/Reset", key=f"r_{g_key}"):
                        g["started"] = False; g["score"] = 0; g["streak"] = 0; st.rerun()

    if st.sidebar.button("Logout Admin"):
        st.session_state.user_fullname = None; st.rerun()

# --- 6. STUDENT GAMEPLAY ---
else:
    room = all_rooms[st.session_state.room_id]
    
    # --- Step 1: Join a Group ---
    if st.session_state.my_group_key is None:
        st.header("Step 1: Choose Your Team")
        cols = st.columns(4)
        for i in range(1, GROUP_COUNT + 1):
            g_key = f"Group {i}"
            count = len(room["groups"][g_key]["players"])
            with cols[(i-1)%4]:
                if st.button(f"{room['groups'][g_key]['display_name']}\n({count} Players)", key=f"j_{g_key}", use_container_width=True):
                    st.session_state.my_group_key = g_key
                    room["groups"][g_key]["players"][st.session_state.user_fullname] = {
                        "ready": False, "joined": datetime.now().strftime("%H:%M:%S")
                    }
                    st.rerun()
    
    # --- Step 2: Group Lobby ---
    else:
        g_data = room["groups"][st.session_state.my_group_key]
        
        if not g_data["started"]:
            st.header(f"Lobby: {g_data['display_name']}")
            st.info(f"Today's Mission: **{room['mode']}**")
            
            # Captain Election & Resignation
            if g_data["captain"] is None:
                if st.button("🗳️ Nominate Myself as Captain", use_container_width=True):
                    g_data["captain"] = st.session_state.user_fullname; st.rerun()
            elif st.session_state.user_fullname == g_data["captain"]:
                st.success("🌟 You are the Team Captain!")
                pep = st.text_input("Enter an encouraging phrase for your team:", value=g_data["pep_talk"])
                if st.button("Save Pep Talk"): g_data["pep_talk"] = pep; st.rerun()
                if st.button("❌ Never mind, I do not want to be a captain", type="secondary"):
                    g_data["captain"] = None; g_data["pep_talk"] = ""; st.rerun()
            else:
                st.write(f"**Captain:** {g_data['captain']}")
                if g_data["pep_talk"]: st.write(f"📢 _{g_data['pep_talk']}_")

            # Ready Status
            p_state = g_data["players"][st.session_state.user_fullname]
            if st.button("✅ I AM READY" if not p_state["ready"] else "⏳ WAIT, NOT READY", use_container_width=True):
                p_state["ready"] = not p_state["ready"]; st.rerun()
            
            st.divider()
            st.write(f"**Team Roster ({len(g_data['players'])} Players):**")
            for name, info in g_data["players"].items():
                st.write(f"{'✅' if info['ready'] else '⏳'} {name}")
            
            st.button("🔄 Refresh Lobby")

        # --- Step 3: Active Gameplay ---
        else:
            st.title(f"🚀 Mode: {room['mode']}")
            st.subheader(f"💪 {g_data['captain']}'s Message: {g_data['pep_talk']}")
            
            # Turn Logic
            player_list = list(g_data["players"].keys())
            current_p = player_list[g_data["turn_idx"] % len(player_list)]
            elapsed = int(time.time() - g_data["start_time"])
            
            c_game, c_hist = st.columns([2, 1])
            
            with c_game:
                if room["mode"] == "Match Up": st.write(f"### Score: {g_data['score']}/100")
                elif room["mode"] == "Streak Alive": st.write(f"### 🔥 Current Streak: {g_data['streak']}")
                
                if current_p == st.session_state.user_fullname:
                    st.success("🎯 YOUR TURN!")
                    st.write(f"## Reduce: **{g_data['q']}**")
                    ans = st.text_input("Your Answer (e.g. 1/2):", key="ans_input")
                    if st.button("Submit Answer"):
                        try:
                            correct = Fraction(ans) == Fraction(g_data['a'])
                            # Point Logic based on Mode
                            if room["mode"] == "Streak Alive":
                                g_data["streak"] = (g_data["streak"] + 1) if correct else 0
                            else:
                                points = 10 if correct else -5
                                if room["mode"] == "Study in Groups" and not correct: points = 0
                                g_data["score"] += points
                            
                            # Record History
                            g_data["history"].append({
                                "name": st.session_state.user_fullname,
                                "timestamp": datetime.now().strftime("%H:%M:%S"),
                                "correct": correct
                            })
                            
                            # Next Question
                            g_data["turn_idx"] += 1
                            g_data["start_time"] = time.time()
                            cf = random.randint(2, 9); n = random.randint(1, 5); d = random.randint(6, 12)
                            g_data["q"] = f"{n*cf}/{d*cf}"; g_data["a"] = str(Fraction(n, d))
                            st.rerun()
                        except: st.error("Please use format like 1/2")
                else:
                    st.warning(f"Waiting for {current_p} to solve...")
                    time.sleep(2); st.rerun()

            with c_hist:
                st.write("📜 **Recent Activity**")
                for h in reversed(g_data["history"][-10:]):
                    st.write(f"{h['timestamp']} - {h['name']} {'✅' if h['correct'] else '❌'}")

    if st.sidebar.button("Leave Group"):
        if st.session_state.user_fullname in g_data["players"]:
            del g_data["players"][st.session_state.user_fullname]
            if g_data["captain"] == st.session_state.user_fullname: g_data["captain"] = None
        st.session_state.my_group_key = None; st.rerun()
