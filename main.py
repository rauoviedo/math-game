import streamlit as st
import random
from fractions import Fraction

# --- 1. SETTINGS ---
TEACHER_PASSWORD = "mathrocks2026"
ROOM_OPTIONS = ["Period 1", "Period 2", "Period 3", "Period 4"]
GROUP_COUNT = 8  # Now supporting 8 groups per period

# --- 2. SHARED DATA STRUCTURE ---
@st.cache_resource
def get_all_rooms():
    rooms = {}
    for r in ROOM_OPTIONS:
        rooms[r] = {
            "groups": {f"Group {i}": {
                "score": 0, 
                "players": [], 
                "turn_idx": 0,
                "q": "6/8", 
                "a": "3/4"
            } for i in range(1, GROUP_COUNT + 1)},
            "game_started": False,
            "history": []
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
if "my_group" not in st.session_state:
    st.session_state.my_group = None

st.set_page_config(page_title="Fraction Group Battle", layout="wide")

# --- LOGIN LOGIC ---
if st.session_state.user_name is None:
    st.title("🔢 Fraction Group Challenge")
    t1, t2 = st.tabs(["Student Join", "Teacher Login"])
    
    with t1:
        s_room = st.selectbox("Select Class:", ["Select..."] + ROOM_OPTIONS)
        s_first = st.text_input("First Name")
        s_last = st.text_input("Last Name")
        if st.button("Join"):
            if s_room != "Select..." and s_first and s_last:
                st.session_state.room_id = s_room
                st.session_state.user_name = f"{s_first} {s_last}"
                st.session_state.role = "Student"
                st.rerun()

    with t2:
        t_pass = st.text_input("Password", type="password")
        if st.button("Login"):
            if t_pass == TEACHER_PASSWORD:
                st.session_state.user_name = "Teacher"
                st.session_state.role = "Teacher"
                st.rerun()

# --- TEACHER DASHBOARD ---
elif st.session_state.role == "Teacher":
    st.title("👨‍🏫 Teacher Command Center")
    
    # Select which period to view/manage
    view_room = st.selectbox("Manage Period:", ROOM_OPTIONS)
    room = all_rooms[view_room]
    
    # Validation: Ensure every group has at least 1 player
    ready_to_start = all(len(g["players"]) >= 1 for g in room["groups"].values())
    
    col_start, col_reset = st.columns(2)
    if col_start.button(f"🚀 START {view_room}", disabled=room["game_started"] or not ready_to_start):
        room["game_started"] = True
        st.rerun()
    if col_reset.button(f"🔄 RESET {view_room}"):
        all_rooms[view_room] = get_all_rooms()[view_room] # Reset specific room
        st.rerun()

    # Grid View of all 8 Groups
    st.write("### Group Status")
    g_cols = st.columns(4) # Two rows of 4
    for i in range(1, GROUP_COUNT + 1):
        g_name = f"Group {i}"
        with g_cols[(i-1)%4]:
            g_data = room["groups"][g_name]
            st.markdown(f"**{g_name}**")
            st.write(f"Players: {len(g_data['players'])}")
            st.write(f"Score: {g_data['score']}")
            if len(g_data['players']) == 0:
                st.error("Empty")

# --- STUDENT GAMEPLAY ---
else:
    room = all_rooms[st.session_state.room_id]
    
    # Choose Group
    if st.session_state.my_group is None:
        st.header(f"Select your Group - {st.session_state.room_id}")
        g_selection_cols = st.columns(4)
        for i in range(1, GROUP_COUNT + 1):
            g_name = f"Group {i}"
            with g_selection_cols[(i-1)%4]:
                if st.button(f"Join {g_name}"):
                    st.session_state.my_group = g_name
                    room["groups"][g_name]["players"].append(st.session_state.user_name)
                    st.rerun()

    # Lobby
    elif not room["game_started"]:
        st.header(f"⏳ {st.session_state.my_group} Waiting Room")
        st.write(f"Group Members: {', '.join(room['groups'][st.session_state.my_group]['players'])}")
        st.info("The teacher will start once every group has at least 1 player.")
        st.button("Refresh")

    # The Game
    else:
        g_data = room["groups"][st.session_state.my_group]
        current_player = g_data["players"][g_data["turn_idx"] % len(g_data["players"])]
        
        st.title(f"🏆 {st.session_state.my_group} - Score: {g_data['score']}")
        st.divider()

        if current_player == st.session_state.user_name:
            st.success(f"🌟 YOUR TURN, {st.session_state.user_name}!")
            st.write(f"### Reduce: **{g_data['q']}**")
            ans = st.text_input("Answer:")
            if st.button("Submit"):
                try:
                    if Fraction(ans) == Fraction(g_data["a"]):
                        g_data["score"] += 10
                        st.toast("Correct!")
                    else:
                        g_data["score"] -= 5
                        st.toast("Incorrect!")
                    
                    # Move to next player in group and get new Q
                    g_data["turn_idx"] += 1
                    cf = random.randint(2, 10); n = random.randint(1, 5); d = random.randint(6, 12)
                    g_data["q"] = f"{n*cf}/{d*cf}"; g_data["a"] = str(Fraction(n, d))
                    st.rerun()
                except: st.error("Use 1/2 format")
        else:
            st.warning(f"Waiting for **{current_player}** to answer...")
            st.button("Refresh My Group's Turn")
