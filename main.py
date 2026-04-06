import streamlit as st
import random
import time
import pandas as pd
from streamlit_autorefresh import st_autorefresh
from fractions import Fraction

# --- 1. LIVE REFRESH (Heartbeat) ---
st_autorefresh(interval=3000, limit=None, key="nexus_live_sync")

TEACHER_PASSWORD = "mathrocks2026"
ROOM_OPTIONS = ["Period 1", "Period 2", "Period 3", "Period 4"]
GROUP_COUNT = 8 

# --- 2. DATA STORAGE ---
@st.cache_resource
def get_all_rooms():
    rooms = {}
    for r in ROOM_OPTIONS:
        rooms[r] = {
            "groups": {f"Group {i}": {
                "display_name": f"Group {i}",
                "mode": "Match Up",
                "goal": 100,
                "captain": None,
                "pep_talk": "Let's win this!",
                "score": 0, 
                "players": {}, 
                "turn_idx": 0,
                "started": False,
                "start_time": None,
                "completed": False, # NEW: Track if they finished
                "q": "8/12", "a": "2/3",
                "history": [] 
            } for i in range(1, GROUP_COUNT + 1)}
        }
    return rooms

all_rooms = get_all_rooms()

# --- 3. SESSION STATE ---
if "user_fullname" not in st.session_state: st.session_state.user_fullname = None
if "room_id" not in st.session_state: st.session_state.room_id = None
if "my_group_key" not in st.session_state: st.session_state.my_group_key = None

st.set_page_config(page_title="Fraction Nexus", layout="wide")

# --- 4. NAVIGATION ---
if st.session_state.user_fullname:
    with st.sidebar:
        st.button("🔙 Logout", on_click=lambda: st.session_state.clear())

# --- 5. LOGIN ---
if st.session_state.user_fullname is None:
    st.title("🛡️ Fraction Nexus")
    s_room = st.selectbox("Select Class:", ["Select..."] + ROOM_OPTIONS)
    fn = st.text_input("First Name")
    ln = st.text_input("Last Name")
    if st.button("Join"):
        if s_room != "Select..." and fn and ln:
            st.session_state.room_id = s_room
            st.session_state.user_fullname = f"{fn.strip()} {ln.strip()}"
            st.rerun()

# --- 6. GAMEPLAY ---
else:
    room = all_rooms[st.session_state.room_id]
    
    if st.session_state.my_group_key is None:
        st.header("Step 1: Choose Your Group")
        sc = st.columns(4)
        for i in range(1, GROUP_COUNT + 1):
            gk = f"Group {i}"
            if sc[(i-1)%4].button(f"{gk} ({len(room['groups'][gk]['players'])})"):
                st.session_state.my_group_key = gk
                room["groups"][gk]["players"][st.session_state.user_fullname] = {"ready": False}
                st.rerun()
    
    else:
        g = room["groups"][st.session_state.my_group_key]

        # --- COMPLETION SCREEN ---
        if g["completed"]:
            st.balloons()
            st.title("🎊 GOAL REACHED! 🎊")
            st.header(f"Final Score: {g['score']}")
            st.write("### Team Contribution:")
            if g["history"]:
                df = pd.DataFrame(g["history"])
                stats = df.groupby('name')['correct'].agg(['count', 'sum']).reset_index()
                stats.columns = ['Player', 'Attempts', 'Correct Answers']
                st.table(stats)
            st.info("Wait for the Teacher to reset the room for a new round.")
            if st.button("Back to Lobby"):
                g.update({"completed": False, "started": False, "score": 0, "history": []})
                st.rerun()

        # --- LOBBY ---
        elif not g["started"]:
            st.title(f"Lobby: {g['display_name']}")
            ready = g["players"][st.session_state.user_fullname]["ready"]
            if st.button("READY" if not ready else "WAITING..."):
                g["players"][st.session_state.user_fullname]["ready"] = not ready
                st.rerun()
            
            if not g["captain"]:
                if st.button("Become Captain"): g["captain"] = st.session_state.user_fullname; st.rerun()
            elif st.session_state.user_fullname == g["captain"]:
                if st.button("🚀 START GAME", disabled=not all(p["ready"] for p in g["players"].values())):
                    g["started"] = True; g["start_time"] = time.time(); st.rerun()

        # --- ACTIVE GAME ---
        else:
            # Check if Goal was hit by someone else
            if g["score"] >= g["goal"]:
                g["completed"] = True
                st.rerun()

            p_list = list(g["players"].keys())
            current_p = p_list[g["turn_idx"] % len(p_list)]
            
            c1, c2 = st.columns([2, 1])
            
            with c1:
                st.header(f"Score: {g['score']} / {g['goal']}")
                st.progress(min(g["score"] / g["goal"], 1.0))
                
                if current_p == st.session_state.user_fullname:
                    st.success("⭐ YOUR TURN!")
                    st.write(f"## Simplify: {g['q']}")
                    ans = st.text_input("Answer:")
                    if st.button("Submit"):
                        try:
                            is_correct = Fraction(ans) == Fraction(g['a'])
                            g["score"] += 10 if is_correct else -5
                            g["history"].append({"name": st.session_state.user_fullname, "correct": is_correct, "time": time.time()})
                            g["turn_idx"] += 1
                            # Next Question
                            cf = random.randint(2, 5); n = random.randint(1, 5); d = random.randint(6, 10)
                            g["q"], g["a"] = f"{n*cf}/{d*cf}", f"{Fraction(n, d)}"
                            st.rerun()
                        except: st.error("Use x/y format!")
                else:
                    st.info(f"⏳ {current_p} is solving...")

            with c2:
                st.write("### 📡 Live Team Feed")
                if g["history"]:
                    # Show the last 5 actions from teammates
                    for event in reversed(g["history"][-5:]):
                        icon = "✅" if event['correct'] else "❌"
                        st.write(f"{icon} **{event['name']}**")
                else:
                    st.write("Waiting for the first move...")
