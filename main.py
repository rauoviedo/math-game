import streamlit as st
import random
from fractions import Fraction

# --- 1. SETTINGS ---
TEACHER_PASSWORD = "mathrocks2026"
ROOM_OPTIONS = ["Period 1", "Period 2", "Period 3", "Period 4"]
GROUP_COUNT = 8 

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
                "q": "9/15", "a": "3/5",
                "message": "" # Message for the group
            } for i in range(1, GROUP_COUNT + 1)},
            "global_msg": "" # Message for the whole class
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
if "my_group_key" not in st.session_state:
    st.session_state.my_group_key = None

st.set_page_config(page_title="Teacher Master Control", layout="wide")

# --- LOGIN ---
if st.session_state.user_name is None:
    st.title("🛡️ Fraction Command Center")
    t1, t2 = st.tabs(["Student Join", "Teacher Login"])
    with t1:
        s_room = st.selectbox("Select Class:", ["Select..."] + ROOM_OPTIONS)
        s_first = st.text_input("First Name")
        s_last = st.text_input("Last Name")
        if st.button("Join Game"):
            if s_room != "Select..." and s_first and s_last:
                st.session_state.room_id = s_room
                st.session_state.user_name = f"{s_first} {s_last}"
                st.rerun()
    with t2:
        t_pass = st.text_input("Password", type="password")
        if st.button("Login as Teacher"):
            if t_pass == TEACHER_PASSWORD:
                st.session_state.user_name = "Teacher"; st.session_state.role = "Teacher"
                st.rerun()

# --- TEACHER DASHBOARD (Master Control) ---
elif st.session_state.role == "Teacher":
    st.title("👨‍🏫 Teacher Master Dashboard")
    view_room = st.selectbox("Manage Period:", ROOM_OPTIONS)
    room = all_rooms[view_room]
    
    # Global Messaging
    new_global = st.text_input("📢 Send Message to WHOLE CLASS:")
    if st.button("Send Global Message"):
        room["global_msg"] = new_global
        st.success("Message Sent!")

    st.divider()
    
    # 8-Group Management Grid
    g_cols = st.columns(4)
    for i in range(1, GROUP_COUNT + 1):
        g_key = f"Group {i}"
        g = room["groups"][g_key]
        with g_cols[(i-1)%4]:
            with st.expander(f"⚙️ {g['display_name']}", expanded=True):
                st.write(f"**Score:** {g['score']}")
                
                # Start/Reset Controls
                if not g["started"]:
                    if st.button(f"🚀 Start {g_key}", key=f"start_{g_key}"):
                        g["started"] = True
                        st.rerun()
                else:
                    st.success("Game Live")

                # Player Management (Remove Names)
                st.write("**Players:**")
                for p in g["players"]:
                    pc1, pc2 = st.columns([3, 1])
                    pc1.write(f"• {p}")
                    if pc2.button("❌", key=f"kick_{p}_{g_key}"):
                        g["players"].remove(p)
                        if g["leader"] == p: g["leader"] = None
                        st.rerun()
                
                # Group Specific Message
                g_msg = st.text_input("Group Msg:", key=f"msg_input_{g_key}")
                if st.button("Send", key=f"send_{g_key}"):
                    g["message"] = g_msg

# --- STUDENT GAMEPLAY ---
else:
    room = all_rooms[st.session_state.room_id]
    
    # Check if student was kicked
    all_players_in_room = []
    for g in room["groups"].values(): all_players_in_room.extend(g["players"])
    if st.session_state.user_name not in all_players_in_room and st.session_state.my_group_key is not None:
        st.error("You have been removed from the group by the teacher.")
        if st.button("Back to Login"):
            st.session_state.user_name = None; st.session_state.my_group_key = None
            st.rerun()
        st.stop()

    # SHOW GLOBAL ANNOUNCEMENTS
    if room["global_msg"]:
        st.warning(f"📢 **TEACHER MESSAGE:** {room['global_msg']}")

    # CHOOSE GROUP
    if st.session_state.my_group_key is None:
        st.header(f"Join a Group")
        cols = st.columns(4)
        for i in range(1, GROUP_COUNT + 1):
            g_key = f"Group {i}"
            g_data = room["groups"][g_key]
            with cols[(i-1)%4]:
                if st.button(f"Join {g_data['display_name']}", key=f"join_{g_key}"):
                    st.session_state.my_group_key = g_key
                    if g_data["leader"] is None: g_data["leader"] = st.session_state.user_name
                    g_data["players"].append(st.session_state.user_name)
                    st.rerun()

    # LOBBY / GAMEPLAY
    else:
        g_data = room["groups"][st.session_state.my_group_key]
        
        # Group Message
        if g_data["message"]:
            st.info(f"💬 **GROUP NOTICE:** {g_data['message']}")

        if not g_data["started"]:
            st.header(f"🏠 Lobby: {g_data['display_name']}")
            if st.session_state.user_name == g_data["leader"]:
                new_name = st.text_input("Edit Group Name:", value=g_data["display_name"])
                if st.button("Save Name"): 
                    g_data["display_name"] = new_name
                    st.rerun()
            st.write("Wait for the teacher to click START.")
            st.write(f"Roster: {', '.join(g_data['players'])}")
            st.button("Refresh")
        else:
            # Standard fraction turn logic
            current_player = g_data["players"][g_data["turn_idx"] % len(g_data["players"])]
            st.subheader(f"🏆 {g_data['display_name']} | Score: {g_data['score']}")
            if current_player == st.session_state.user_name:
                st.success("🎯 YOUR TURN!")
                st.write(f"### Simplify: **{g_data['q']}**")
                ans = st.text_input("Answer:")
                if st.button("Submit"):
                    try:
                        if Fraction(ans) == Fraction(g_data['a']): g_data['score'] += 10
                        else: g_data['score'] -= 5
                        g_data['turn_idx'] += 1
                        cf = random.randint(2, 9); n = random.randint(1, 5); d = random.randint(6, 12)
                        g_data["q"] = f"{n*cf}/{d*cf}"; g_data["a"] = str(Fraction(n, d))
                        st.rerun()
                    except: st.error("Format: 1/2")
            else:
                st.warning(f"Waiting for {current_player}...")
                st.button("Refresh")
