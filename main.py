import streamlit as st
import random
from fractions import Fraction

# --- 1. SETTINGS ---
TEACHER_PASSWORD = "mathrocks2026"  # Change this to your preferred password
ROOM_OPTIONS = ["Period 1", "Period 2", "Period 3", "Period 4", "Test Room"]

# --- 2. SHARED DATA ---
@st.cache_resource
def get_all_rooms():
    # Initialize all rooms immediately
    rooms = {}
    for r in ROOM_OPTIONS:
        rooms[r] = {
            "scores": {"Alpha": 0, "Beta": 0},
            "players": {"Alpha": [], "Beta": []},
            "history": [],
            "game_started": False,
            "turn": "Alpha",
            "q": "10/15",
            "a": "2/3"
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

st.set_page_config(page_title="Math Battle: Teacher Edition", layout="wide")

# --- STEP 1: LOGIN SCREEN ---
if st.session_state.user_name is None:
    st.title("🛡️ Fraction Battle Royale")
    
    tab1, tab2 = st.tabs(["Student Join", "Teacher Login"])
    
    with tab1:
        s_room = st.selectbox("Select your Class:", ["Select..."] + ROOM_OPTIONS)
        s_first = st.text_input("First Name")
        s_last = st.text_input("Last Name")
        if st.button("Join as Student"):
            if s_room != "Select..." and s_first and s_last:
                st.session_state.room_id = s_room
                st.session_state.user_name = f"{s_first} {s_last}"
                st.session_state.role = "Student"
                st.rerun()
            else:
                st.error("Please fill in all student details.")

    with tab2:
        st.subheader("Teacher Access")
        t_pass = st.text_input("Teacher Password", type="password")
        if st.button("Login to Dashboard"):
            if t_pass == TEACHER_PASSWORD:
                st.session_state.user_name = "Teacher"
                st.session_state.role = "Teacher"
                st.rerun()
            else:
                st.error("Incorrect Password")

# --- STEP 2: TEACHER DASHBOARD ---
elif st.session_state.role == "Teacher":
    st.title("👨‍🏫 Teacher Command Center")
    st.write("Monitor and start your classes from here.")
    
    cols = st.columns(len(ROOM_OPTIONS))
    
    for i, r_name in enumerate(ROOM_OPTIONS):
        with cols[i]:
            room = all_rooms[r_name]
            st.subheader(r_name)
            st.write(f"👥 Alpha: {len(room['players']['Alpha'])}")
            st.write(f"👥 Beta: {len(room['players']['Beta'])}")
            
            if not room["game_started"]:
                if st.button(f"Start {r_name}", key=f"start_{r_name}"):
                    room["game_started"] = True
                    st.success(f"{r_name} Started!")
            else:
                st.write(f"🏆 Score: {room['scores']['Alpha']} - {room['scores']['Beta']}")
                if st.button(f"Reset {r_name}", key=f"reset_{r_name}"):
                    room["game_started"] = False
                    room["scores"] = {"Alpha": 0, "Beta": 0}
                    room["players"] = {"Alpha": [], "Beta": []}
                    st.rerun()
    
    if st.button("Logout"):
        st.session_state.user_name = None
        st.rerun()

# --- STEP 3: STUDENT GAMEPLAY ---
else:
    room = all_rooms[st.session_state.room_id]
    
    # Student Team Choice
    if st.session_state.my_team is None:
        st.header(f"Welcome to {st.session_state.room_id}")
        c1, c2 = st.columns(2)
        if c1.button("Join Alpha"):
            st.session_state.my_team = "Alpha"
            room["players"]["Alpha"].append(st.session_state.user_name)
            st.rerun()
        if c2.button("Join Beta"):
            st.session_state.my_team = "Beta"
            room["players"]["Beta"].append(st.session_state.user_name)
            st.rerun()

    # Waiting Room
    elif not room["game_started"]:
        st.header("⏳ Waiting for Teacher...")
        st.write(f"You are on **Team {st.session_state.my_team}**.")
        st.write("The match will begin once your teacher hits 'Start' on their dashboard.")
        st.button("🔄 Refresh")

    # The Actual Game
    else:
        st.header(f"Class: {st.session_state.room_id}")
        sc1, sc2 = st.columns(2)
        sc1.metric("Alpha", room["scores"]["Alpha"])
        sc2.metric("Beta", room["scores"]["Beta"])
        
        st.divider()
        
        if room["turn"] == st.session_state.my_team:
            st.success(f"🌟 {st.session_state.user_name}, it is your turn!")
            st.write(f"## Reduce: **{room['q']}**")
            ans = st.text_input("Answer:")
            if st.button("Submit"):
                try:
                    if Fraction(ans) == Fraction(room["a"]):
                        room["scores"][st.session_state.my_team] += 10
                    else:
                        room["scores"][st.session_state.my_team] -= 5
                    
                    room["turn"] = "Beta" if room["turn"] == "Alpha" else "Alpha"
                    # New Q
                    cf = random.randint(2, 10); n = random.randint(1, 5); d = random.randint(6, 12)
                    room["q"] = f"{n*cf}/{d*cf}"; room["a"] = str(Fraction(n, d))
                    st.rerun()
                except: st.error("Use 1/2 format")
        else:
            st.warning(f"Waiting for Team {room['turn']}...")
            st.button("Refresh")
