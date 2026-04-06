import streamlit as st
import random
from fractions import Fraction

# --- 1. SETTINGS ---
TEACHER_PASSWORD = "mathrocks2026"
ROOM_OPTIONS = ["Period 1", "Period 2", "Period 3", "Period 4"]

# --- 2. SHARED DATA ---
@st.cache_resource
def get_all_rooms():
    rooms = {}
    for r in ROOM_OPTIONS:
        rooms[r] = {
            "scores": {"Alpha": 0, "Beta": 0},
            "player_data": {}, # Stores { "Name": {"score": 0, "team": "Alpha"} }
            "history": [],
            "game_started": False,
            "turn": "Alpha",
            "q": "4/8",
            "a": "1/2"
        }
    return rooms

all_rooms = get_all_rooms()

# --- 3. SESSION STATE ---
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "role" not in st.session_state:
    st.session_state.role = "Student"
if "room_id" not in st.session_state:
    st.session_state.room_id = None
if "my_team" not in st.session_state:
    st.session_state.my_team = None

st.set_page_config(page_title="Fraction Battle Royale", layout="wide")

# --- LOGIN LOGIC ---
if st.session_state.user_name is None:
    st.title("🛡️ Fraction Battle Royale")
    t1, t2 = st.tabs(["Student Join", "Teacher Login"])
    
    with t1:
        s_room = st.selectbox("Select your Class:", ["Select..."] + ROOM_OPTIONS)
        s_first = st.text_input("First Name")
        s_last = st.text_input("Last Name")
        if st.button("Join Game"):
            if s_room != "Select..." and s_first and s_last:
                st.session_state.room_id = s_room
                st.session_state.user_name = f"{s_first} {s_last}"
                st.session_state.role = "Student"
                st.rerun()

    with t2:
        t_pass = st.text_input("Teacher Password", type="password")
        if st.button("Login"):
            if t_pass == TEACHER_PASSWORD:
                st.session_state.user_name = "Teacher"
                st.session_state.role = "Teacher"
                st.rerun()

# --- TEACHER DASHBOARD ---
elif st.session_state.role == "Teacher":
    st.title("👨‍🏫 Teacher Command Center")
    cols = st.columns(len(ROOM_OPTIONS))
    for i, r_name in enumerate(ROOM_OPTIONS):
        with cols[i]:
            room = all_rooms[r_name]
            st.subheader(r_name)
            st.write(f"Total Players: {len(room['player_data'])}")
            if st.button(f"Start {r_name}", key=f"s_{r_name}"): room["game_started"] = True
            if st.button(f"Reset {r_name}", key=f"r_{r_name}"):
                room["game_started"] = False
                room["scores"] = {"Alpha": 0, "Beta": 0}
                room["player_data"] = {}
                st.rerun()

# --- STUDENT GAMEPLAY ---
else:
    room = all_rooms[st.session_state.room_id]
    
    # Select Team
    if st.session_state.my_team is None:
        st.header(f"Join a Team - {st.session_state.room_id}")
        c1, c2 = st.columns(2)
        if c1.button("Join Alpha"):
            st.session_state.my_team = "Alpha"
            room["player_data"][st.session_state.user_name] = {"score": 0, "team": "Alpha"}
            st.rerun()
        if c2.button("Join Beta"):
            st.session_state.my_team = "Beta"
            room["player_data"][st.session_state.user_name] = {"score": 0, "team": "Beta"}
            st.rerun()

    # Waiting Lobby
    elif not room["game_started"]:
        st.header("⏳ Lobby: Waiting for Teacher")
        st.write(f"Logged in as: **{st.session_state.user_name}** (Team {st.session_state.my_team})")
        st.button("Refresh")

    # The Game
    else:
        # Scoreboard
        st.title(f"🏆 {st.session_state.room_id} Battle")
        tc1, tc2 = st.columns(2)
        tc1.metric("TEAM ALPHA", room["scores"]["Alpha"])
        tc2.metric("TEAM BETA", room["scores"]["Beta"])
        
        st.divider()

        # Gameplay & Sidebar Leaderboard
        game_col, leader_col = st.columns([2, 1])

        with game_col:
            if room["turn"] == st.session_state.my_team:
                st.success(f"🌟 {st.session_state.user_name}, IT'S YOUR TURN!")
                st.write(f"### Reduce: **{room['q']}**")
                ans = st.text_input("Your Answer:")
                if st.button("Submit"):
                    try:
                        if Fraction(ans) == Fraction(room["a"]):
                            room["scores"][st.session_state.my_team] += 10
                            room["player_data"][st.session_state.user_name]["score"] += 10
                            msg = f"✅ {st.session_state.user_name} scored! (+10)"
                        else:
                            room["scores"][st.session_state.my_team] -= 5
                            room["player_data"][st.session_state.user_name]["score"] -= 5
                            msg = f"❌ {st.session_state.user_name} missed. (-5)"
                        
                        room["history"].append(msg)
                        room["turn"] = "Beta" if room["turn"] == "Alpha" else "Alpha"
                        # Next Question
                        cf = random.randint(2, 10); n = random.randint(1, 5); d = random.randint(6, 12)
                        room["q"] = f"{n*cf}/{d*cf}"; room["a"] = str(Fraction(n, d))
                        st.rerun()
                    except: st.error("Use 1/2 format")
            else:
                st.warning(f"Waiting for Team {room['turn']}...")
                st.button("Refresh Board")

        with leader_col:
            st.subheader("🥇 Top Players")
            # Sort players by score
            sorted_players = sorted
