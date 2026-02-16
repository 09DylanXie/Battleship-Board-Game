import streamlit as st
import random

# --- CONFIGURATION ---
st.set_page_config(page_title="My Battleship Dashboard", layout="wide", page_icon="⚓")

# --- RULES & CONSTANTS ---
STARTING_GOLD = 150
STARTING_STEEL = 10
BASE_GOLD_INCOME = 20
BASE_STEEL_INCOME = 2

# Unit Stats
UNITS = {
    "Aircraft Carrier": {"gold": 100, "steel": 5, "turns": 3, "desc": "Range 7, 3x Air Rolls (1-6)"},
    "Battleship":       {"gold": 80,  "steel": 7, "turns": 2, "desc": "Range 5, Dmg 1-10"},
    "Cruiser":          {"gold": 50,  "steel": 5, "turns": 1, "desc": "Range 3, Dmg 1-5 + Torp (7)"},
    "Destroyer":        {"gold": 30,  "steel": 3, "turns": 0, "desc": "Range 2, Dmg 1-3 + Torp (7)"},
    "Submarine":        {"gold": 30,  "steel": 1, "turns": 0, "desc": "Torpedo (5 dmg), Hidden"},
}

BUILDINGS = {
    "Gold Mine":     {"gold": 20, "limit": 3, "effect": "+10 Gold/turn"},
    "Steel Factory": {"gold": 40, "limit": 3, "effect": "+1 Steel/turn"},
    "Shipyard":      {"gold": 100,"limit": 1, "effect": "Cheaper/Faster Ships"}
}

# --- INITIALIZATION ---
if 'gold' not in st.session_state:
    st.session_state.gold = STARTING_GOLD
if 'steel' not in st.session_state:
    st.session_state.steel = STARTING_STEEL
if 'turn' not in st.session_state:
    st.session_state.turn = 1
if 'queue' not in st.session_state:
    st.session_state.queue = [] # List of {name, turns_left}
if 'buildings' not in st.session_state:
    st.session_state.buildings = {"Gold Mine": 0, "Steel Factory": 0, "Shipyard": 0}
if 'fleet' not in st.session_state:
    # Starting Fleet: 1 Base, 2 Destroyers
    st.session_state.fleet = {"Base": 1, "Destroyer": 2, "Aircraft Carrier": 0, "Battleship": 0, "Cruiser": 0, "Submarine": 0}
if 'logs' not in st.session_state:
    st.session_state.logs = ["Game Started. Good luck, Commander."]

if 'roll_results' not in st.session_state:
    st.session_state.roll_results = {}

# --- FUNCTIONS ---
def log(msg):
    st.session_state.logs.insert(0, f"Turn {st.session_state.turn}: {msg}")

def end_turn():
    # 1. Process Income
    gold_gain = BASE_GOLD_INCOME + (st.session_state.buildings["Gold Mine"] * 10)
    steel_gain = BASE_STEEL_INCOME + (st.session_state.buildings["Steel Factory"] * 1)
    
    st.session_state.gold += gold_gain
    st.session_state.steel += steel_gain
    
    # 2. Process Build Queue
    completed = []
    new_queue = []
    for item in st.session_state.queue:
        item['turns_left'] -= 1
        if item['turns_left'] <= 0:
            completed.append(item['name'])
            st.session_state.fleet[item['name']] += 1
        else:
            new_queue.append(item)
    
    st.session_state.queue = new_queue
    
    # 3. Log Updates
    log(f"Collected +{gold_gain} Gold, +{steel_gain} Steel.")
    if completed:
        log(f"✅ Deployment Complete: {', '.join(completed)}")
        
    st.session_state.turn += 1

# --- MAIN UI ---
st.title("⚓ Personal Command Center")

# Top Dashboard
col1, col2, col3, col4 = st.columns(4)
col1.metric("Gold", st.session_state.gold)
col2.metric("Steel", st.session_state.steel)
col3.metric("Turn", st.session_state.turn)

with col4:
    if st.button("End Turn ➡️", type="primary", use_container_width=True):
        end_turn()
        st.rerun()
    st.caption("🏆 Win: Destroy all enemy bases")

st.divider()

# Main Tabs
tab1, tab2, tab3 = st.tabs(["⚔️ Combat Computer", "🏗️ Production", "📋 Fleet & Logs"])

# --- TAB 1: COMBAT ---
with tab1:
    st.caption("Press a button to roll immediately.")

    # -- Section: Heavy Ships --
    st.markdown("#### Heavy Firepower")
    
    # Row 1: Carrier
    r1c1, r1c2 = st.columns([1, 2])
    with r1c1:
        if st.button("✈️ Aircraft Carrier"):
            rolls = [random.randint(1, 6) for _ in range(3)]
            total = sum(rolls)
            msg = f"🎲 Rolls: {rolls} = **{total} Total**"
            st.session_state.roll_results['carrier'] = msg
            log(f"Carrier: {rolls} = {total} Dmg")
    with r1c2:
        if 'carrier' in st.session_state.roll_results:
            st.markdown(st.session_state.roll_results['carrier'])

    # Row 2: Battleship
    r2c1, r2c2 = st.columns([1, 2])
    with r2c1:
        if st.button("🔥 Battleship"):
            dmg = random.randint(1, 10)
            msg = f"💥 Cannon Hit: **{dmg} Damage**"
            st.session_state.roll_results['battleship'] = msg
            log(f"Battleship: {dmg} Dmg")
    with r2c2:
        if 'battleship' in st.session_state.roll_results:
            st.markdown(st.session_state.roll_results['battleship'])

    # Row 3: Base
    r3c1, r3c2 = st.columns([1, 2])
    with r3c1:
        if st.button("🏯 Base Defense"):
            rolls = [random.randint(1, 5) for _ in range(3)]
            total = sum(rolls)
            msg = f"🛡️ Rolls: {rolls} = **{total} Total**"
            st.session_state.roll_results['base'] = msg
            log(f"Base: {rolls} = {total} Dmg")
    with r3c2:
        if 'base' in st.session_state.roll_results:
            st.markdown(st.session_state.roll_results['base'])

    st.divider()

    # -- Section: Light Ships & Torps --
    st.markdown("#### Light Ships & Torpedoes")
    
    # Row 4: Cruiser/Destroyer Guns
    r4c1, r4c2, r4c3 = st.columns([1.5, 1, 2])
    with r4c1:
        ship_type = st.radio("Class", ["Cruiser (d5)", "Destroyer (d3)"], horizontal=True, label_visibility="collapsed")
    with r4c2:
        if st.button("Fire Gun"):
            limit = 5 if "Cruiser" in ship_type else 3
            dmg = random.randint(1, limit)
            msg = f"🔫 Hit: **{dmg} Damage**"
            st.session_state.roll_results['light_gun'] = msg
            log(f"{ship_type.split()[0]} Gun: {dmg} Dmg")
    with r4c3:
        if 'light_gun' in st.session_state.roll_results:
             st.markdown(st.session_state.roll_results['light_gun'])
    
    # Row 5: Heavy Torpedo
    r5c1, r5c2 = st.columns([1, 2])
    with r5c1:
        if st.button("🚀 Heavy Torpedo"):
            msg = "💥 **7 Damage** (Fixed)"
            st.session_state.roll_results['h_torp'] = msg
            log("Heavy Torpedo: 7 Dmg")
    with r5c2:
        if 'h_torp' in st.session_state.roll_results:
            st.markdown(st.session_state.roll_results['h_torp'])

    # Row 6: Sub Torpedo
    r6c1, r6c2 = st.columns([1, 2])
    with r6c1:
        if st.button("🌊 Sub Torpedo"):
            msg = "💧 **5 Damage** (Fixed)"
            st.session_state.roll_results['s_torp'] = msg
            log("Sub Torpedo: 5 Dmg")
    with r6c2:
        if 's_torp' in st.session_state.roll_results:
            st.markdown(st.session_state.roll_results['s_torp'])


# --- TAB 2: PRODUCTION ---
with tab2:
    prod_col1, prod_col2 = st.columns(2)
    
    # Logic for Shipyard Discount
    has_shipyard = st.session_state.buildings["Shipyard"] > 0
    discount_g = 20 if has_shipyard else 0
    discount_t = 1 if has_shipyard else 0

    with prod_col1:
        st.subheader("Purchase Units")
        unit = st.selectbox("Select Unit", list(UNITS.keys()))
        stats = UNITS[unit]
        
        final_gold = max(0, stats['gold'] - discount_g)
        final_turns = max(0, stats['turns'] - discount_t)
        
        st.info(f"Cost: {final_gold} Gold, {stats['steel']} Steel\n\nReady in: {final_turns} turns")
        
        if st.button(f"Build {unit}"):
            if st.session_state.gold >= final_gold and st.session_state.steel >= stats['steel']:
                st.session_state.gold -= final_gold
                st.session_state.steel -= stats['steel']
                if final_turns == 0:
                    st.session_state.fleet[unit] += 1
                    log(f"Built {unit} (Instant)")
                else:
                    st.session_state.queue.append({'name': unit, 'turns_left': final_turns})
                    log(f"Started {unit} construction")
                st.rerun()
            else:
                st.error("Insufficient Funds!")

    with prod_col2:
        st.subheader("Infrastructure")
        b_name = st.selectbox("Select Building", list(BUILDINGS.keys()))
        b_stats = BUILDINGS[b_name]
        
        curr = st.session_state.buildings[b_name]
        st.write(f"Owned: {curr} / {b_stats['limit']}")
        st.write(f"Cost: {b_stats['gold']} Gold")
        
        if st.button(f"Construct {b_name}"):
            if curr < b_stats['limit']:
                if st.session_state.gold >= b_stats['gold']:
                    st.session_state.gold -= b_stats['gold']
                    st.session_state.buildings[b_name] += 1
                    log(f"Constructed {b_name}")
                    st.rerun()
                else:
                    st.error("Need more Gold")
            else:
                st.error("Max limit reached")
        
        # New Section: Buildings Built Summary
        st.markdown("---")
        st.caption("Buildings Built:")
        for b, count in st.session_state.buildings.items():
            st.write(f"**{b}:** {count}")

# --- TAB 3: FLEET & LOGS ---
with tab3:
    st.subheader("Active Fleet")
    fleet_data = {k: v for k, v in st.session_state.fleet.items() if v > 0}
    if fleet_data:
        st.json(fleet_data)
    else:
        st.write("Fleet destroyed!")

    st.subheader("Construction Queue")
    if st.session_state.queue:
        for q in st.session_state.queue:
            st.progress(1.0, text=f"🏗️ {q['name']}: {q['turns_left']} turns remaining")
    else:
        st.caption("No active construction.")
        
    st.divider()
    st.subheader("Mission Log")
    for l in st.session_state.logs:
        st.text(l)

# --- SIDEBAR: GLOBAL ACTIONS ---
with st.sidebar:
    st.header("Actions")
    if st.button("💥 Enemy Ship Destroyed (+30g)"):
        st.session_state.gold += 30
        log("Victory at sea! +30 Gold reward.")
        st.rerun()
    
    st.divider()
    if st.button("RESET GAME", type="primary"):
        st.session_state.clear()
        st.rerun()