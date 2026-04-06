import streamlit as st
import random
from fractions import Fraction

# --- 1. DEFINE YOUR ROOMS HERE ---
# You can change these names to match your actual class periods
ROOM_OPTIONS = ["Select a Room", "Period 1", "Period 2", "Period 3", "Period 4", "After School Club"]

# --- 2. MULTI-ROOM SHARED DATA ---
@st.cache_resource
def get_all_rooms():
    return {}

all_rooms = get_all_rooms()

def initialize_room(room_id):
    if room_id not in all_rooms:
        all_rooms[room_id] = {
            "scores": {"Alpha": 0, "Beta": 0},
            "players": {"Alpha": [], "Beta": []},
            "history": [],
            "game_started": False,
            "turn": "Alpha",
            "q": "15/20",
            "a": "3/4"
        }
    return all_rooms[room_id]

# --- 3. INDIVIDUAL STUDENT SESSION ---
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "my_team" not in st.session_state:
    st.session_state.my_team = None
if "room_id" not in st.session_state:
    st.session_state.room_id = None
if "is_teacher" not in st.session_state:
    st.session_state.is_teacher = False

st.set_page_config(page_title="Fraction Battle Royale", layout="centered")
st.title("🛡️ Fraction Team Battle")

# STEP 1: LOGIN & ROOM SELECTION
if st.session_state.user_name is None:
    st.subheader("📝 Join Your Class")
    
    # Dropdown for Rooms
    selected_room = st.selectbox("Which class are you in?", ROOM_OPTIONS)
    
    first = st.text_input("First Name")
    last = st.text_input("Last Name")
    
    # Hidden Teacher Access (Type 'Admin' in Last Name to be the teacher)
    is_teacher_check = st.checkbox("I am the teacher")
    
    if st.button("Enter Lobby"):
        if selected_room != "Select a Room" and first and last:
            st.session_state.room_id = selected_room
            st.session_state.user_name = f"{first} {last}"
            st.session_state.is_teacher = is_teacher_check
            initialize_room(selected_room)
            st.rerun()
        else:
            st.error("Please select a room and enter your full name!")

else:
    # Connect to the specific room's data
    room = all_rooms[st.session_state.room_id]

    # STEP 2: TEAM SELECTION
    if st.session_state.my_team is None:
        st.subheader(f"Class: {st.session_state.room_id}")
        st.write(f"Hello {st.session_state.user_name}, pick a team:")
        c_a, c_b = st.columns(2)
        if c_a.button("Join Team Alpha"):
            st.session_state.my_team = "Alpha"
            if st.session_state.user_name not in room["players"]["Alpha"]:
                room["players"]["Alpha"].append(st.session_state.user_name)
            st.rerun()
        if c_b.button("Join Team Beta"):
            st.session_state.my_team = "Beta"
            if st.session_state.user_name not in room["players"]["Beta"]:
                room["players"]["Beta"].append(st.session_state.user_name)
            st.rerun()

    # STEP 3: THE WAITING ROOM
    elif not room["game_started"]:
        st.header(f"⏳ {st.session_state.room_id} Lobby")
        st.write("---")
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("🚩 Team Alpha")
            for p in room["players"]["Alpha"]:
                st.write(f"• {p}")
        with col_b:
            st.subheader("🚩 Team Beta")
            for p in room["players"]["Beta"]:
                st.write(f"• {p}")
        
        st.write("---")
        
        # Only the "Teacher" session sees the Start button
        if st.session_state.is_teacher:
            if st.button("🚀 START THE MATCH"):
                room["game_started"] = True
                st.rerun()
        else:
            st.info("Waiting for your teacher to start the game...")
            if st.button("🔄 Refresh Roster"):
                st.rerun()

    # STEP 4: ACTIVE GAMEPLAY
    else:
        st.subheader(f"Room: {st.session_state.room_id}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Alpha", f"{room['scores']['Alpha']} pts")
        c2.metric("Beta", f"{room['scores']['Beta']} pts")
        c3.write(f"**Your Team:** \n{st.session_state.my_team}")

        st.divider()

        if room["turn"] == st.session_state.my_team:
            st.success(f"🌟 YOUR TURN, {st.session_state.user_name}!")
            st.write(f"### Reduce this:  **{room['q']}**")
            ans = st.text_input("Enter simplest form:", key="play_input")
            
            if st.button("Submit"):
                try:
                    if Fraction(ans) == Fraction(room["a"]):
                        room["scores"][st.session_state.my_team] += 10
                        msg = f"✅ {st.session_state.user_name} (Team {st.session_state.my_team}) got it!"
                    else:
                        room["scores"][st.session_state.my_team] -= 5
                        msg = f"❌ {st.session_state.user_name} (Team {st.session_state.my_team}) missed."
                    
                    room["history"].append(msg)
                    room["turn"] = "Beta" if room["turn"] == "Alpha" else "Alpha"
                    
                    # New Question Generation
                    cf = random.randint(2, 10)
                    n, d = random.randint(1, 5), random.randint(6, 12)
                    room["q"] = f"{n*cf}/{d*cf}"
                    room["a"] = str(Fraction(n, d))
                    st.rerun()
                except:
                    st.error("Please enter a valid fraction (e.g. 1/2)")
        else:
            st.warning(f"⏳ **Next up to continue the series: Team {room['turn']}**")
            st.button("🔄 Refresh Scoreboard")
                
        st.sidebar.header("Class History")
        for event in reversed(room["history"]):
            st.sidebar.write(event)
            
        if st.sidebar.button("🚪 Leave Room"):
            st.session_state.my_team = None
            st.session_state.user_name = None
            st.rerun()
