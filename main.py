import streamlit as st
import random
import time
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
            "groups": {f"Group {i}": {
                "display_name": f"Group {i}",
                "leader": None,
                "score": 0, 
                "players": [], 
                "turn_idx": 0,
                "started": False,
                "q": "12/18", "a": "2/3",
                "start_time": time.time(),
                "history": []
            } for i in range(1, GROUP_COUNT + 1)},
            "timer_enabled": True,
            "global_msg": ""
        }
    return rooms

all_rooms = get_all_rooms()

# --- 3. SESSION STATE ---
if "user_name" not in st.session_state: st.session_state.user_name = None
if "role" not in st.session_state: st.session_state.role = "Student"
if "room_id" not in st.session_state: st.session_state.room_id = None
if "my_group_key" not in st.session_state: st.session_state.my_group_key = None

st.set_page_config(page_title="Fraction Battle Royale", layout="wide")

# --- LOGIN SCREEN ---
if st.session_state.user_name is None:
    st.title("🛡️ Fraction Battle Royale")
    t1, t2 = st.tabs(["Student Join", "Teacher Login"])
    
    with t1:
        s_room = st.selectbox("Select Class:", ["Select..."] + ROOM_OPTIONS)
        s_first = st.text_input("First Name")
        s_last = st.text_input("Last Name")
        if st.button("Join Game", use_container_width=True):
            if s_room != "Select..." and s_first and s_last:
                st.session_state.room_id = s_room
                st.session_state.user_name = f"{s_first} {s_last}"
                st.rerun()
            else:
                st.error("Please fill in all fields.")

    with t2:
        st.subheader("Teacher Access")
        t_pass = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if t_pass == TEACHER_PASSWORD:
                st.session_state.user_name = "Teacher"; st.session_state.role = "Teacher"
                st.rerun()

# --- TEACHER DASHBOARD ---
elif st.session_state.role == "Teacher":
    st.title("👨‍🏫 Teacher Command Center")
    view_room = st.selectbox("Manage Period:", ROOM_OPTIONS)
    room = all_rooms[view_room]
    
    room["timer_enabled"] = st.toggle("Enable Speed Bonus (under 10s)", value=room["timer_enabled"])
    
    st.divider()
    g_cols = st.columns(4)
    for i in range(1, GROUP_COUNT + 1):
        g_key = f"Group {i}"
        g = room["groups"][g_key]
        with g_cols[(i-1)%4]:
            with st.container(border=True):
                st.subheader(g["display_name"])
                st.progress(min(g["score"] / WINNING_SCORE, 1.0))
                st.write(f"**Score:** {g['score']}/{WINNING_SCORE}")
                
                if not g["started"]:
                    if st.button(f"🚀 Start {g_key}", key=f"s_{g_key}"):
                        g["started"] = True
                        g["start_time"] = time.time()
                        st.rerun()
                
                # Kick players / Show Roster
                for p in g["players"]:
                    c1, c2 = st.columns([3, 1])
                    c1.write(p)
                    if c2.button("❌", key=f"k_{p}_{g_key}"):
                        g["players"].remove(p)
                        st.rerun()

# --- STUDENT GAMEPLAY ---
else:
    room = all_rooms[st.session_state.room_id]
    
    # 1. Join a Group
    if st.session_state.my_group_key is None:
        st.header("Pick Your Group")
        cols = st.columns(4)
        for i in range(1, GROUP_COUNT + 1):
            g_key = f"Group {i}"
            g_disp = room["groups"][g_key]["display_name"]
            with cols[(i-1)%4]:
                if st.button(f"Join {g_disp}", key=f"j_{g_key}", use_container_width=True):
                    st.session_state.my_group_key = g_key
                    if room["groups"][g_key]["leader"] is None:
                        room["groups"][g_key]["leader"] = st.session_state.user_name
                    room["groups"][g_key]["players"].append(st.session_state.user_name)
                    st.rerun()

    # 2. Main Game Logic
    else:
        g_data = room["groups"][st.session_state.my_group_key]
        
        # Winner Check
        if g_data["score"] >= WINNING_SCORE:
            st.balloons()
            st.title(f"🏆 {g_data['display_name']} WINS!")
            st.header(f"Final Score: {g_data['score']}")
            st.stop()

        if not g_data["started"]:
            st.header(f"Waiting Area: {g_data['display_name']}")
            if st.session_state.user_name == g_data["leader"]:
                new_n = st.text_input("Edit Group Name:", value=g_data["display_name"])
                if st.button("Save Name"): 
                    g_data["display_name"] = new_n
                    st.rerun()
            st.info("The teacher will start the match shortly.")
            st.write(f"Group Members: {', '.join(g_data['players'])}")
            st.button("Refresh")
        else:
            # Active Turn
            current_player = g_data["players"][g_data["turn_idx"] % len(g_data["players"])]
            elapsed = int(time.time() - g_data["start_time"])
            
            game_col, hist_col = st.columns([2, 1])
            
            with game_col:
                st.subheader(f"Group: {g_data['display_name']}")
                st.progress(min(g_data["score"] / WINNING_SCORE, 1.0))
                st.write(f"Points: **{g_data['score']} / {WINNING_SCORE}**")
                
                if current_player == st.session_state.user_name:
                    st.success("✨ IT IS YOUR TURN!")
                    st.write(f"## Simplify: **{g_data['q']}**")
                    ans = st.text_input("Enter fraction (e.g. 1/2):")
                    
                    if st.button("Submit Answer", use_container_width=True):
                        try:
                            if Fraction(ans) == Fraction(g_data['a']):
                                pts = 15 if (room["timer_enabled"] and elapsed < 10) else 10
                                g_data['score'] += pts
                                g_data["history"].append({"name": st.session_state.user_name, "correct": True, "time": elapsed})
                            else:
                                g_data['score'] -= 5
                                g_data["history"].append({"name": st.session_state.user_name, "correct": False, "time": elapsed})
                            
                            g_data['turn_idx'] += 1
                            g_data["start_time"] = time.time()
                            cf = random.randint(2, 9); n = random.randint(1, 5); d = random.randint(6, 12)
                            g_data["q"] = f"{n*cf}/{d*cf}"; g_data["a"] = str(Fraction(n, d))
                            st.rerun()
                        except: st.error("Please use the 1/2 format.")
                else:
                    st.warning(f"Waiting for {current_player}...")
                    if room["timer_enabled"]: st.write(f"Current Timer: {elapsed}s")
                    time.sleep(1)
                    st.rerun()

            with hist_col:
                st.subheader("📜 Group History")
                for entry in reversed(g_data["history"]):
                    icon = "✅" if entry["correct"] else "❌"
                    color = "green" if entry["correct"] else "red"
                    st.markdown(f"**{entry['name']}** {icon} ({entry['time']}s)")
