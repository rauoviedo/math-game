import streamlit as st
import random
from fractions import Fraction

# --- SHARED CLASSROOM DATA ---
@st.cache_resource
def get_global_state():
    return {
        "scores": {"Alpha": 0, "Beta": 0},
        "turn": "Alpha",
        "q": "6/8",
        "a": "3/4"
    }

state = get_global_state()

# --- STUDENT SESSION (Individual Device) ---
if "my_team" not in st.session_state:
    st.session_state.my_team = None

st.title("🛡️ Fraction Team Battle")

# STEP 1: JOIN A TEAM
if st.session_state.my_team is None:
    st.subheader("Welcome! Choose your side:")
    col_a, col_b = st.columns(2)
    if col_a.button("Join Team Alpha"):
        st.session_state.my_team = "Alpha"
        st.rerun()
    if col_b.button("Join Team Beta"):
        st.session_state.my_team = "Beta"
        st.rerun()

# STEP 2: THE GAME
else:
    # Scoreboard (Visible to all)
    c1, c2 = st.columns(2)
    c1.metric("Team Alpha", f"{state['scores']['Alpha']} pts")
    c2.metric("Team Beta", f"{state['scores']['Beta']} pts")
    
    st.divider()
    st.write(f"You are on **Team {st.session_state.my_team}**")
    
    # Logic: Only show input if it's your team's turn
    if state["turn"] == st.session_state.my_team:
        st.info(f"### IT IS YOUR TURN! \n## Reduce: **{state['q']}**")
        ans = st.text_input("Enter simplest form (e.g. 1/2):")
        
        if st.button("Submit for my Team"):
            if ans == state["a"]:
                state["scores"][st.session_state.my_team] += 10
                st.toast("Correct! +10 Points", icon="✅")
            else:
                state["scores"][st.session_state.my_team] -= 5
                st.toast("Wrong! -5 Points", icon="❌")
            
            # Switch turn and generate new Q
            state["turn"] = "Beta" if state["turn"] == "Alpha" else "Alpha"
            cf = random.randint(2, 6)
            n, d = random.randint(1, 4), random.randint(5, 10)
            state["q"] = f"{n*cf}/{d*cf}"
            state["a"] = str(Fraction(n, d))
            st.rerun()
    else:
        st.warning(f"Wait! It is Team {state['turn']}'s turn. Watch the scores!")
        if st.button("Refresh Scoreboard"):
            st.rerun()
