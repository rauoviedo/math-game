import streamlit as st
import random
import time
from datetime import datetime
from fractions import Fraction

# --- 1. SETTINGS ---
# Updated to a simpler, more reliable string
TEACHER_PASSWORD = "mathrocks2026" 
ROOM_OPTIONS = ["Period 1", "Period 2", "Period 3", "Period 4"]
GROUP_COUNT = 8 

# --- 2. SHARED DATA (Persistent across reruns) ---
@st.cache_resource
def get_all_rooms():
    rooms = {}
    for r in ROOM_OPTIONS:
        rooms[r] = {
            "mode": "Match Up",
            "session_active": True,
            "groups": {f"Group {i}": {
                "display_name": f"Group {i}",
                "captain": None,
                "pep_talk": "",
                "score": 0, 
                "streak": 0,
                "players": {}, 
                "turn_idx": 0,
                "started": False,
                "q": "10/15", "a": "2/3",
                "start_time": time.time(),
                "history": []
            } for i in range(1, GROUP_COUNT + 1)}
        }
    return rooms

all_rooms = get_all_rooms()

# --- 3. SESSION STATE ---
if "user_fullname" not in st.session_state:
    st.session_state.user_fullname = None
if "role" not in st.session_state:
    st.session_state.role = "Student" # Default is student
if "room_id" not in st.session_state:
    st.session_state.room_id = None
if "my_group_key" not in st.session_state:
    st.session_state.my_group_key = None

st.set_page_config(page_title="Fraction Nexus Admin", layout="wide")

# --- 4. LOGIN INTERFACE ---
if st.session_state.user_fullname is None:
    st.title("🎯 Fraction Nexus: Team Challenge")
    
    tab_student, tab_teacher = st.tabs(["👤 Student Join", "🔑 Teacher Access"])
    
    with tab_student:
        s_room = st.selectbox("Which Class?", ["Select..."] + ROOM_OPTIONS)
        col_f, col_l = st.columns(2)
        fname = col_f.text_input("First Name")
        lname = col_l.text_input("Last Name")
        
        if st.button("Enter Battleground", use_container_width=True):
            if s_room != "Select..." and fname and lname:
                st.session_state.room_id = s_room
                st.session_state.user_fullname = f"{fname.strip()} {lname.strip()}"
                st.session_state.role = "Student"
                st.rerun()
            else:
                st.error("Please select a class and enter your full name.")

    with tab_teacher:
        st.subheader("Administrative Login")
        # Added key for stability
        input_pass = st.text_input("Enter Password:", type="password", key="login_pass_input")
        
        if st.button("Unlock Dashboard", use_container_width=True):
            # Normalizing the password check (lowercase and no spaces)
            if input_pass.strip().lower() == TEACHER_PASSWORD.lower():
                st.session_state.user_fullname = "Teacher"
                st.session_state.role = "Teacher"
                # If you haven't picked a room yet, default to Period 1
                if not st.session_state.room_id:
                    st.session_state.room_id = "Period 1"
                st.success("Access Granted! Loading Dashboard...")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Incorrect Password. Please try again.")

# --- 5. TEACHER DASHBOARD ---
elif st.session_state.role == "Teacher":
    st.title(f"👨‍🏫 Control Center: {st.session_state.room_id}")
    
    # Allow teacher to switch rooms easily
    st.session_state.room_id = st.selectbox("Switch Class View:", ROOM_OPTIONS, index=ROOM_OPTIONS.index(st.session_state.room_id))
    room = all_rooms[st.session_state.room_id]
    
    # Log out button for Teacher
    if st.sidebar.button("Logout"):
        st.session_state.user_fullname = None
        st.session_state.role = "Student"
        st.rerun()

    # (Rest of Teacher logic for Mode, Players, and Start Buttons...)
    st.write(f"Current Mode: **{room['mode']}**")
    # ... code continues as before ...

# --- 6. STUDENT GAMEPLAY ---
else:
    # (Student group selection and game logic...)
    st.write(f"Logged in as: {st.session_state.user_fullname}")
    if st.sidebar.button("Leave Room / Logout"):
        st.session_state.user_fullname = None
        st.rerun()
