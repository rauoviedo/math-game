import streamlit as st
import random
from fractions import Fraction

# --- SHARED CLASSROOM DATA ---
@st.cache_resource
def get_global_state():
    return {
        "scores": {"Alpha": 0, "Beta": 0},
        "history": [],
        "last_player": "No one yet",
        "turn": "Alpha",
        "q": "4/10",
        "a": "2/5"
    }

state = get_global_state()

# --- INDIVIDUAL STUDENT SESSION ---
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "my_team" not in st.session_state:
    st.session_state.my_team = None

st.title("🛡️ Fraction Team Battle")

# STEP 1: LOGIN
if st.session_state.user_name is None:
    st.subheader("Student Sign-In")
    first = st.text_input("First Name")
    last = st.text_input("Last Name")
    if st.button("Join Game"):
        if first and last:
            st.session_state.user_name = f"{first} {last}"
            st.rerun()

# STEP 2: TEAM SELECTION
elif st.session_state.my_team is None:
    st.subheader(f"Welcome, {st.session_state.user_name}!")
    c_a, c_b = st.columns(2)
    if c_a.button("Join Alpha"):
        st.session_state.my_team = "Alpha"
        st.rerun()
    if c_b.button("Join Beta"):
        st.session_state.my_team = "Beta"
        st.rerun()

# STEP 3: GAMEPLAY
else:
    # Top Stats
    col1, col2, col3 = st.columns(3)
    col1.metric("Alpha", state["scores"]["Alpha"])
    col2.metric("Beta", state["scores"]["Beta"])
    col3.write(f"🏃 **Last move by:** \n{state['last_player']}")

    st.divider()

    # THE TURN ANNOUNCEMENT
    if state["turn"] == st.session_state.my_team:
        st.success(f"🌟 **IT IS YOUR TURN, {st.session_state.user_name}!**")
        st.write(f"### Reduce: **{state['q']}**")
        
        ans = st.text_input("Simplest form:", key="play_input")
        
        if st.button("Submit Answer"):
            try:
                if Fraction(ans) == Fraction(state["a"]):
                    state["scores"][st.session_state.my_team] += 10
                    msg = f"✅ {st.session_state.user_name} (Team {st.session_state.my_team}) got it!"
                else:
                    state["scores"][st.session_state.my_team] -= 5
                    msg = f"❌ {st.session_state.user_name} (Team {st.session_state.my_team}) missed it."
                
                # Update shared history and turn
                state["history"].append(msg)
                state["last_player"] = st.session_state.user_name
                state["turn"] = "Beta" if state["turn"] == "Alpha" else "Alpha"
                
                # Generate next question
                cf = random.randint(2, 10)
                n, d = random.randint(1, 6), random.randint(7, 12)
                state["q"] = f"{n*cf}/{d*cf}"
                state["a"] = str(Fraction(n, d))
                st.rerun()
            except:
                st.warning("Please enter a fraction (e.g., 1/2)")
    else:
        # WAITING MESSAGE
        st.warning(f"⏳ **Waiting for Team {state['turn']} to answer...**")
        st.info(f"👉 **{state['last_player']}** just finished. It is now the other team's turn to continue the series!")
        
        if st.button("🔄 Refresh for New Question"):
            st.rerun()

    # Sidebar Activity Log
    st.sidebar.header("Match History")
    for event in reversed(state["history"]):
        st.sidebar.write(event)
