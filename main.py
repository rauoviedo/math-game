import streamlit as st
import random
import time
from datetime import datetime
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
            "mode": "Battle", 
            "session_active": True,
            "groups": {f"Group {i}": {
                "display_name": f"Group {i}",
                "captain": None,
                "pep_talk": "",
                "score": 0, 
                "players": {}, # {"Name": {"ready": bool, "joined": "time"}}
                "turn_idx": 0,
                "started": False,
                "q": "12/20", "a": "3/5",
                "start_time": time.time(),
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

# --- LOGIN ---
if st.session_state.user_fullname is None:
    st.title("🛡️ Fraction Nexus")
    t1, t2 = st.tabs(["Student Entry", "Teacher Admin"])
    with t1:
        s_room = st.selectbox("Class Period:", ["Select..."] + ROOM_OPTIONS)
        c_fn, c_ln = st.columns(2)
        s_first = c_fn.text_input("First Name")
        s_last = c_ln.text_input("Last Name")
        if st.button("Join Session", use_container_width=True):
            if s_room != "Select..." and s_first and s_last:
                st.session_state.room_id = s_room
                st.session_state.user_fullname = f"{s_first.strip()} {s_last.strip()}"
                st.rerun()
    with t2:
        t_pass = st.text_input("Admin Password", type="password")
        if st.button("Access Dashboard"):
            if t_pass == TEACHER_PASSWORD:
                st.session_state.user_fullname = "Teacher"; st.session_state.role = "Teacher"; st.rerun()

# --- TEACHER DASHBOARD ---
elif st.session_state.get("role") == "Teacher":
    st.title(f"👨‍🏫 Teacher Dashboard - {st.session_state.room_id}")
    room = all_rooms[st.session_state.room_id]
    
    st.divider()
    g_cols = st.columns(4)
    for i in range(1, GROUP_COUNT + 1):
        g_key = f"Group {i}"
        g = room["groups"][g_key]
        with g_cols[(i-1)%4]:
            with st.container(border=True):
                player_count = len(g["players"])
                st.subheader(f"{g['display_name']}")
                st.write(f"👥 **Players: {player_count}**")
                
                num_ready = sum(1 for p in g["players"].values() if p["ready"])
                has_pep = len(g["pep_talk"].strip()) >= 3
                
                if not g["started"]:
                    can_start = (player_count > 0 and num_ready == player_count and g["captain"] and has_pep)
                    st.button(f"🚀 Start Match", key=f"s_{g_key}", disabled=not can_start, 
                              on_click=lambda g=g: g.update({"started": True, "start_time": time.time()}))
                    if player_count > 0:
                        st.caption(f"Ready: {num_ready}/{player_count}")
                else:
                    st.success("Match in Progress")
                    if st.button("Reset Group", key=f"res_{g_key}"): g["started"] = False; st.rerun()

# --- STUDENT GAMEPLAY ---
else:
    room = all_rooms[st.session_state.room_id]
    
    # 1. Select Team (Showing Player Counts)
    if st.session_state.my_group_key is None:
        st.header("Join a Team")
        cols = st.columns(4)
        for i in range(1, GROUP_COUNT + 1):
            g_key = f"Group {i}"
            g_data = room["groups"][g_key]
            p_count = len(g_data["players"])
            with cols[(i-1)%4]:
                if st.button(f"{g_data['display_name']}\n({p_count} Players)", key=f"j_{g_key}", use_container_width=True):
                    st.session_state.my_group_key = g_key
                    now = datetime.now().strftime("%H:%M")
                    g_data["players"][st.session_state.user_fullname] = {"ready": False, "joined": now}
                    st.rerun()
    
    # 2. Lobby & Ready Up
    else:
        g_data = room["groups"][st.session_state.my_group_key]
        is_cap = (st.session_state.user_fullname == g_data["captain"])

        if not g_data["started"]:
            st.header(f"Team Lobby: {g_data['display_name']}")
            st.write(f"👥 **Current Team Size: {len(g_data['players'])}**")
            
            # Captain Logic
            if g_data["captain"] is None:
                if st.button("🗳️ Nominate Myself as Captain", use_container_width=True):
                    g_data["captain"] = st.session_state.user_fullname; st.rerun()
            elif is_cap:
                st.success("🌟 YOU ARE THE CAPTAIN")
                pep = st.text_input("Team Pep Talk:", value=g_data["pep_talk"])
                if st.button("Save Message"): g_data["pep_talk"] = pep; st.rerun()
                if st.button("❌ Resign as Captain", type="secondary"):
                    g_data["captain"] = None; g_data["pep_talk"] = ""; st.rerun()
            else:
                st.info(f"Captain: {g_data['captain']}")

            # Ready Button
            p_info = g_data["players"][st.session_state.user_fullname]
            if st.button("✅ I AM READY" if not p_info["ready"] else "⏳ WAIT, NOT READY"):
                p_info["ready"] = not p_info["ready"]; st.rerun()
            
            st.divider()
            st.write("**Who's here:**")
            for name, info in g_data["players"].items():
                status = "✅" if info["ready"] else "⏳"
                st.write(f"{status} {name}")
            
            st.button("🔄 Refresh")
        else:
            # Active Match
            st.info(f"📢 Captain's Word: {g_data['pep_talk']}")
            st.title(f"Score: {g_data['score']}")
            st.write(f"Players in match: {len(g_data['players'])}")
            # ... Fraction Logic would follow ...
