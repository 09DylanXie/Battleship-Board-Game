import streamlit as st
import random
import uuid

# --- CONFIGURATION ---
st.set_page_config(page_title="Battleship Command v18", layout="wide", page_icon="⚓")

# --- RULES & CONSTANTS ---
STARTING_GOLD = 150
STARTING_STEEL = 10
STARTING_GEMS = 0
BASE_GOLD_INCOME = 20
BASE_STEEL_INCOME = 2
FLEET_CAP_ACTIVE = 7
FLEET_CAP_RESERVE = 3
BASE_MAX_HP = 30 

# Unit Stats (Added Decoy)
UNITS = {
    "Aircraft Carrier": {"gold": 110, "steel": 8, "turns": 3, "hp": 7,  "limit": 2, "desc": "Range 4, 1x(3-10) or 2x(1-5)"}, 
    "Battleship":       {"gold": 90,  "steel": 7, "turns": 2, "hp": 13, "limit": 3, "desc": "Range 3, Dmg 2-7"}, 
    "Cruiser":          {"gold": 60,  "steel": 5, "turns": 1, "hp": 9,  "limit": 4, "desc": "Range 2, Dmg 2-4"}, 
    "Destroyer":        {"gold": 40,  "steel": 4, "turns": 0, "hp": 5,  "limit": 5, "desc": "Range 2, Dmg 1-3, Torp(5), Mine Gems"}, 
    "Submarine":        {"gold": 30,  "steel": 2, "turns": 0, "hp": 3,  "limit": 2, "desc": "Torpedo (7 dmg), Hidden"}, 
    "Decoy":            {"gold": 20,  "steel": 0, "turns": 0, "hp": 1,  "limit": 1, "desc": "Fake ship. Destroyed upon reveal."}, 
}

BUILDINGS = {
    "Gold Mine": {
        "gold": 20, "steel": 2, "limit": 4, 
        "effect": "+10 Gold/turn", 
        "desc": "Deep earth mining infrastructure to fund the war effort."
    },
    "Steel Factory": {
        "gold": 40, "steel": 1, "limit": 3,  # Increased limit from 2 to 3
        "effect": "+1 Steel/turn", 
        "desc": "Heavy industrial processing for ship armor and hulls."
    },
    "Base Defense": {
        "gold": 50, "steel": 0, "limit": 2, 
        "effect": "+1 Bomber (2-4 Dmg)", 
        "desc": "Scramble interceptors to defend the homeland."
    },
    "Shipyard": {
        "gold": 80, "steel": 3, "limit": 1, 
        "effect": "Unlocks Repairs", 
        "desc": "Allows repairing ships (3HP) within 1 tile of base."
    }
}

# --- INITIALIZATION ---
if 'gold' not in st.session_state: st.session_state.gold = STARTING_GOLD
if 'steel' not in st.session_state: st.session_state.steel = STARTING_STEEL
if 'gems' not in st.session_state: st.session_state.gems = STARTING_GEMS
if 'turn' not in st.session_state: st.session_state.turn = 1
if 'base_hp' not in st.session_state: st.session_state.base_hp = BASE_MAX_HP
if 'queue' not in st.session_state: st.session_state.queue = [] 
if 'buildings' not in st.session_state:
    st.session_state.buildings = {"Gold Mine": 0, "Steel Factory": 0, "Shipyard": 0, "Base Defense": 0}
if 'logs' not in st.session_state:
    st.session_state.logs = ["Game Started. Good luck, Commander."]
if 'roll_results' not in st.session_state:
    st.session_state.roll_results = {}

# --- DYNAMIC NUMBERING HELPER ---
def get_next_ship_number(fleet_list, u_type, limit):
    used = [s['num'] for s in fleet_list if s['type'] == u_type]
    for i in range(1, limit + 1):
        if i not in used:
            return i
    return limit + 1

def create_player_ship(u_type, status="Active"):
    num = get_next_ship_number(st.session_state.fleet_list, u_type, UNITS[u_type]["limit"])
    # Don't add a number for the decoy since there's only ever 1
    name_display = f"{u_type} {num}" if u_type != "Decoy" else u_type
    
    return {
        "id": str(uuid.uuid4()), 
        "type": u_type, 
        "num": num,
        "name": name_display,
        "status": status,
        "hp": UNITS[u_type]["hp"],
        "max_hp": UNITS[u_type]["hp"],
        "mined_this_turn": False
    }

if 'fleet_list' not in st.session_state:
    st.session_state.fleet_list = []
    st.session_state.fleet_list.append(create_player_ship("Destroyer", "Active"))

# Enemy State Initialization
if 'enemies' not in st.session_state:
    st.session_state.enemies = {
        "Enemy 1": {"base_hp": 30, "ships": []},
        "Enemy 2": {"base_hp": 30, "ships": []},
        "Enemy 3": {"base_hp": 30, "ships": []}
    }

# --- FUNCTIONS ---
def log(msg):
    st.session_state.logs.insert(0, f"Turn {st.session_state.turn}: {msg}")

def end_turn():
    gold_gain = BASE_GOLD_INCOME + (st.session_state.buildings["Gold Mine"] * 10)
    steel_gain = BASE_STEEL_INCOME + (st.session_state.buildings["Steel Factory"] * 1)
    
    st.session_state.gold += gold_gain
    st.session_state.steel += steel_gain
    
    completed = []
    new_queue = []
    for item in st.session_state.queue:
        item['turns_left'] -= 1
        if item['turns_left'] <= 0:
            completed.append(item['type'])
            active_count = sum(1 for s in st.session_state.fleet_list if s['status'] == "Active")
            status = "Active" if active_count < FLEET_CAP_ACTIVE else "Reserve"
            st.session_state.fleet_list.append(create_player_ship(item['type'], status))
        else:
            new_queue.append(item)
    
    st.session_state.queue = new_queue
    
    # Reset Destroyer mining status
    for ship in st.session_state.fleet_list:
        if ship['type'] == 'Destroyer':
            ship['mined_this_turn'] = False
    
    log(f"Collected +{gold_gain} Gold, +{steel_gain} Steel.")
    if completed:
        log(f"✅ Deployment Complete: {', '.join(completed)}")
        
    st.session_state.turn += 1

def delete_ship(ship_id):
    st.session_state.fleet_list = [s for s in st.session_state.fleet_list if s['id'] != ship_id]
    log("Ship sunk/scrapped.")

def toggle_ship_status(ship_id):
    ship = next((s for s in st.session_state.fleet_list if s['id'] == ship_id), None)
    if not ship: return

    active_count = sum(1 for s in st.session_state.fleet_list if s['status'] == "Active")
    reserve_count = sum(1 for s in st.session_state.fleet_list if s['status'] == "Reserve")

    if ship['status'] == "Active":
        if reserve_count < FLEET_CAP_RESERVE:
            ship['status'] = "Reserve"
            log(f"⚓ {ship['name']} moved to Reserve.")
        else:
            st.error("Reserve Fleet Full!")
    elif ship['status'] == "Reserve":
        if active_count < FLEET_CAP_ACTIVE:
            ship['status'] = "Active"
            log(f"⚔️ {ship['name']} deployed to Active.")
        else:
            st.error("Active Fleet Full!")

# --- MAIN UI ---
st.title("⚓ Battleship Command v18")

# Dashboard
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Gold", st.session_state.gold)
col2.metric("Steel", st.session_state.steel)
col3.metric("Gems", st.session_state.gems)
col4.metric("Turn", st.session_state.turn)
with col5:
    if st.button("End Turn ➡️", type="primary", use_container_width=True):
        end_turn()
        st.rerun()

st.divider()

# Tabs
tab_combat, tab_health, tab_ships, tab_enemy, tab_shop, tab_infra = st.tabs([
    "⚔️ Combat", "🏥 Damage Control", "⚓ Fleet", "🔴 Enemy", "💎 Shop", "🏗️ Infrastructure"
])

# --- TAB 1: COMBAT ---
with tab_combat:
    # --- MOUNTAIN MINING ---
    st.markdown("### ⛰️ Mountain Operations")
    
    available_miners = [s for s in st.session_state.fleet_list if s['type'] == 'Destroyer' and s['status'] == 'Active' and not s.get('mined_this_turn', False)]
    
    m_col1, m_col2 = st.columns([1, 2])
    with m_col1:
        st.write(f"**Available Destroyers to Mine:** {len(available_miners)}")
        if st.button("⛏️ Mine Mountain (Uses 1 Destroyer)", disabled=len(available_miners) == 0):
            available_miners[0]['mined_this_turn'] = True
            st.session_state.gems += 1
            log(f"{available_miners[0]['name']} extracted 1 Gem from the mountains.")
            st.toast("Mined 1 Gem!")
            st.rerun()
    with m_col2:
        st.caption("Destroyers can mine 1 Gem per turn when adjacent to a mountain tile.")

    st.divider()

    # --- AIRCRAFT CARRIER ---
    st.markdown("### ✈️ Aircraft Carrier")
    c_mode = st.radio("Carrier Mode", ["Focused (3-10 Dmg)", "Split (2x 1-5 Dmg)"], horizontal=True)
    c_col1, c_col2 = st.columns(2)
    
    if "Focused" in c_mode:
        with c_col1:
            if st.button("Launch Strike"):
                dmg = random.randint(3, 10)
                st.session_state.roll_results['carrier'] = f"🎯 Carrier Hit: **{dmg}**"
                log(f"Carrier Focused: {dmg}")
    else:
        with c_col1:
            if st.button("Sqd A"):
                dmg = random.randint(1, 5)
                st.session_state.roll_results['carrier_a'] = f"🛩️ A: **{dmg}**"
                log(f"Carrier A: {dmg}")
            if 'carrier_a' in st.session_state.roll_results: st.caption(st.session_state.roll_results['carrier_a'])
        with c_col2:
            if st.button("Sqd B"):
                dmg = random.randint(1, 5)
                st.session_state.roll_results['carrier_b'] = f"🛩️ B: **{dmg}**"
                log(f"Carrier B: {dmg}")
            if 'carrier_b' in st.session_state.roll_results: st.caption(st.session_state.roll_results['carrier_b'])
            
    if "Focused" in c_mode and 'carrier' in st.session_state.roll_results:
        st.info(st.session_state.roll_results['carrier'])

    st.divider()

    # --- BASE DEFENSE ---
    st.markdown("### 🏯 Base Defense")
    bombers = st.session_state.buildings["Base Defense"]
    
    if bombers == 0:
        st.caption("No bombers active. Buy upgrades.")
    elif bombers == 1:
        if st.button("Launch Scramble (2-4 Dmg)"):
            dmg = random.randint(2, 4)
            st.session_state.roll_results['base'] = f"🛡️ Intercept: **{dmg}**"
            log(f"Base Defense: {dmg}")
        if 'base' in st.session_state.roll_results: st.info(st.session_state.roll_results['base'])
    else: 
        b_mode = st.radio("Defense Mode", ["Focused (2x combined)", "Split (2x 2-4 Dmg)"], horizontal=True)
        bd1, bd2 = st.columns(2)
        
        if "Focused" in b_mode:
            with bd1:
                if st.button("Combined Sortie"):
                    dmg = random.randint(2, 4) + random.randint(2, 4)
                    st.session_state.roll_results['base_focus'] = f"🛡️ Combined Hit: **{dmg}**"
                    log(f"Base Focused: {dmg}")
            if 'base_focus' in st.session_state.roll_results: st.info(st.session_state.roll_results['base_focus'])
        else:
            with bd1:
                if st.button("Bomber 1"):
                    dmg = random.randint(2, 4)
                    st.session_state.roll_results['base_1'] = f"🛡️ B1: **{dmg}**"
                    log(f"Base B1: {dmg}")
                if 'base_1' in st.session_state.roll_results: st.caption(st.session_state.roll_results['base_1'])
            with bd2:
                if st.button("Bomber 2"):
                    dmg = random.randint(2, 4)
                    st.session_state.roll_results['base_2'] = f"🛡️ B2: **{dmg}**"
                    log(f"Base B2: {dmg}")
                if 'base_2' in st.session_state.roll_results: st.caption(st.session_state.roll_results['base_2'])

    st.divider()
    
    # --- HEAVY & LIGHT ---
    st.markdown("### Surface Fleet")
    col_surf1, col_surf2, col_surf3 = st.columns(3)
    with col_surf1:
        if st.button("🔥 Battleship"):
            dmg = random.randint(2, 7)
            st.session_state.roll_results['bb'] = f"💥 **{dmg}**"
            log(f"Battleship Fired: {dmg}")
    with col_surf2:
        if st.button("🔫 Cruiser"):
            dmg = random.randint(2, 4)
            st.session_state.roll_results['cr'] = f"🔫 **{dmg}**"
            log(f"Cruiser Fired: {dmg}")
    with col_surf3:
        if st.button("🔫 Destroyer"):
            dmg = random.randint(1, 3)
            st.session_state.roll_results['dd'] = f"🔫 **{dmg}**"
            log(f"Destroyer Fired: {dmg}")
            
    if 'bb' in st.session_state.roll_results: st.caption(f"BB (2-7): {st.session_state.roll_results['bb']}")
    if 'cr' in st.session_state.roll_results: st.caption(f"CA (2-4): {st.session_state.roll_results['cr']}")
    if 'dd' in st.session_state.roll_results: st.caption(f"DD (1-3): {st.session_state.roll_results['dd']}")

    st.divider()
    st.markdown("### Torpedoes")
    t1, t2 = st.columns(2)
    with t1: 
        if st.button("🚀 Dest. Torp (5)"): 
            st.toast("5 Damage")
            log("Destroyer Torpedo Fired (5 Dmg)")
    with t2:
        if st.button("🌊 Sub Torp (7)"): 
            st.toast("7 Damage")
            log("Submarine Torpedo Fired (7 Dmg)")


# --- TAB 2: HEALTH TRACKER ---
with tab_health:
    st.subheader("🏥 Damage Control Center")
    
    bh_col1, bh_col2 = st.columns([1, 3])
    with bh_col1:
        st.metric("Base HP", f"{st.session_state.base_hp} / {BASE_MAX_HP}")
    with bh_col2:
        st.write("") 
        st.progress(st.session_state.base_hp / BASE_MAX_HP)
        hb1, hb2, hb3 = st.columns(3)
        if hb1.button("➖ Hit (-1)", key="b_minus"): 
            st.session_state.base_hp = max(0, st.session_state.base_hp - 1)
            st.rerun()
        if hb2.button("💥 Crit (-5)", key="b_crit"): 
            st.session_state.base_hp = max(0, st.session_state.base_hp - 5)
            st.rerun()
        if hb3.button("➕ Repair (+1)", key="b_plus"):
            st.session_state.base_hp = min(BASE_MAX_HP, st.session_state.base_hp + 1)
            st.rerun()

    st.divider()
    
    st.markdown("#### Fleet Status")
    active_ships = [s for s in st.session_state.fleet_list if s['status'] == "Active"]
    
    if not active_ships:
        st.info("No Active Ships to track.")
    else:
        for ship in active_ships:
            with st.container(border=True):
                hc1, hc2, hc3 = st.columns([2, 3, 2])
                with hc1:
                    st.markdown(f"**{ship['name']}**")
                    st.caption(UNITS[ship['type']]['desc'])
                    if ship['hp'] <= 0: st.error("DESTROYED")
                    elif ship['hp'] <= ship['max_hp'] * 0.3: st.warning("CRITICAL")
                    else: st.success("OPERATIONAL")
                with hc2:
                    pct = max(0.0, ship['hp'] / ship['max_hp'])
                    st.progress(pct, text=f"{ship['hp']} / {ship['max_hp']} HP")
                with hc3:
                    sub1, sub2, sub3, sub4 = st.columns(4)
                    if sub1.button("-1", key=f"dmg_{ship['id']}"):
                        ship['hp'] = max(0, ship['hp'] - 1)
                        st.rerun()
                    if sub2.button("-3", key=f"crit_{ship['id']}"):
                        ship['hp'] = max(0, ship['hp'] - 3)
                        st.rerun()
                    if sub3.button("+1", key=f"rep_{ship['id']}"):
                        ship['hp'] = min(ship['max_hp'], ship['hp'] + 1)
                        st.rerun()
                    if sub4.button("☠️", key=f"kill_hp_{ship['id']}", help="Mark as Sunk"):
                        delete_ship(ship['id'])
                        st.rerun()


# --- TAB 3: FLEET COMMAND ---
with tab_ships:
    col_fleet, col_yard = st.columns([1.5, 1])

    with col_fleet:
        st.subheader("Fleet Command")
        active_s = [s for s in st.session_state.fleet_list if s['status'] == "Active"]
        reserve_s = [s for s in st.session_state.fleet_list if s['status'] == "Reserve"]
        
        st.info(f"Active ({len(active_s)}/{FLEET_CAP_ACTIVE})")
        for ship in active_s:
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.markdown(f"**{ship['name']}** (HP: {ship['hp']})")
                if c2.button("Recall", key=f"r_{ship['id']}"):
                    toggle_ship_status(ship['id'])
                    st.rerun()
                if c3.button("Sunk", key=f"k_{ship['id']}"):
                    delete_ship(ship['id'])
                    st.rerun()

        st.warning(f"Reserve ({len(reserve_s)}/{FLEET_CAP_RESERVE})")
        for ship in reserve_s:
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.markdown(f"**{ship['name']}** (HP: {ship['hp']})")
                if c2.button("Deploy", key=f"d_{ship['id']}"):
                    toggle_ship_status(ship['id'])
                    st.rerun()
                if c3.button("Scrap", key=f"sc_{ship['id']}"):
                    delete_ship(ship['id'])
                    st.rerun()

    with col_yard:
        st.subheader("Shipyard")
        u = st.selectbox("Build Blueprint", list(UNITS.keys()))
        s = UNITS[u]
        
        curr_built = len([ship for ship in st.session_state.fleet_list if ship['type'] == u])
        curr_queued = len([q for q in st.session_state.queue if q['type'] == u])
        total_u = curr_built + curr_queued
        limit_u = s['limit']
        
        st.caption(f"Cost: {s['gold']}G {s['steel']}S | {s['turns']} Turns")
        st.write(f"**Owned/Queued:** {total_u} / {limit_u}")
        
        # --- GEM RUSHING LOGIC ---
        rush_turns = 0
        if s['turns'] > 0:
            max_possible_rush = min(st.session_state.gems // 2, s['turns'])
            rush_turns = st.number_input(
                "Rush Construction (2 Gems per Turn)", 
                min_value=0, 
                max_value=int(max_possible_rush), 
                value=0
            )
            if rush_turns > 0:
                st.info(f"Rushing {rush_turns} turns for **{rush_turns * 2} Gems**.")
        
        can_afford_g = st.session_state.gold >= s['gold']
        can_afford_s = st.session_state.steel >= s['steel']
        can_afford_gems = st.session_state.gems >= (rush_turns * 2)
        is_maxed = total_u >= limit_u
        
        if st.button(f"Commission {u}", type="primary", disabled=is_maxed):
            if can_afford_g and can_afford_s and can_afford_gems:
                st.session_state.gold -= s['gold']
                st.session_state.steel -= s['steel']
                st.session_state.gems -= (rush_turns * 2)
                
                final_turns = s['turns'] - rush_turns
                
                if final_turns == 0:
                    st.session_state.fleet_list.append(create_player_ship(u, "Active"))
                    log(f"Rushed construction of {u} instantly!")
                else:
                    st.session_state.queue.append({'type': u, 'turns_left': final_turns})
                    log(f"Started construction of {u} ({final_turns} turns remaining).")
                st.rerun()
            else:
                st.error("Insufficient Funds or Gems!")
        
        if st.session_state.queue:
            st.divider()
            for q in st.session_state.queue:
                st.write(f"🏗️ {q['type']}: {q['turns_left']} turns")


# --- TAB 4: ENEMY TRACKER ---
with tab_enemy:
    st.subheader("🔴 Enemy Intelligence")
    e_tabs = st.tabs(["Enemy 1", "Enemy 2", "Enemy 3"])
    
    for i, e_name in enumerate(["Enemy 1", "Enemy 2", "Enemy 3"]):
        with e_tabs[i]:
            enemy_data = st.session_state.enemies[e_name]
            
            st.markdown(f"#### {e_name} Base HP: {enemy_data['base_hp']} / {BASE_MAX_HP}")
            e_bh1, e_bh2 = st.columns([3, 1])
            with e_bh1:
                st.progress(enemy_data['base_hp'] / BASE_MAX_HP)
            with e_bh2:
                eh1, eh2 = st.columns(2)
                if eh1.button("-1", key=f"e_bm_{e_name}"):
                    enemy_data['base_hp'] = max(0, enemy_data['base_hp'] - 1)
                    st.rerun()
                if eh2.button("+1", key=f"e_bp_{e_name}"):
                    enemy_data['base_hp'] = min(BASE_MAX_HP, enemy_data['base_hp'] + 1)
                    st.rerun()
            
            st.divider()
            
            st.markdown("#### Add Spotted Ship")
            esp1, esp2 = st.columns([2, 1])
            with esp1:
                e_unit = st.selectbox("Ship Type", list(UNITS.keys()), key=f"sel_{e_name}", label_visibility="collapsed")
            with esp2:
                e_limit = UNITS[e_unit]['limit']
                curr_e_ships = len([s for s in enemy_data['ships'] if s['type'] == e_unit])
                
                if st.button("Spawn", key=f"spawn_{e_name}", disabled=(curr_e_ships >= e_limit)):
                    num = get_next_ship_number(enemy_data['ships'], e_unit, e_limit)
                    name_display = f"{e_unit} {num}" if e_unit != "Decoy" else e_unit
                    
                    enemy_data['ships'].append({
                        "id": str(uuid.uuid4()),
                        "type": e_unit,
                        "num": num,
                        "name": name_display,
                        "hp": UNITS[e_unit]['hp'],
                        "max_hp": UNITS[e_unit]['hp']
                    })
                    st.rerun()
            
            if not enemy_data['ships']:
                st.caption("No ships tracked for this enemy.")
            else:
                for ship in enemy_data['ships']:
                    with st.container(border=True):
                        ec1, ec2, ec3 = st.columns([2, 3, 2])
                        with ec1:
                            st.markdown(f"**{ship['name']}**")
                            st.caption(UNITS[ship['type']]['desc'])
                        with ec2:
                            pct = max(0.0, ship['hp'] / ship['max_hp'])
                            st.progress(pct, text=f"{ship['hp']} / {ship['max_hp']} HP")
                        with ec3:
                            es1, es2, es3 = st.columns(3)
                            if es1.button("-1", key=f"e_dmg_{ship['id']}"):
                                ship['hp'] = max(0, ship['hp'] - 1)
                                st.rerun()
                            if es2.button("+1", key=f"e_rep_{ship['id']}"):
                                ship['hp'] = min(ship['max_hp'], ship['hp'] + 1)
                                st.rerun()
                            if es3.button("☠️", key=f"e_kill_{ship['id']}"):
                                enemy_data['ships'] = [s for s in enemy_data['ships'] if s['id'] != ship['id']]
                                st.rerun()


# --- TAB 5: SHOP ---
with tab_shop:
    st.subheader("💎 Black Market Gem Exchange")
    st.caption("Trade rare mountain gems to off-the-grid smugglers for resources.")
    
    st.metric("Current Gems", st.session_state.gems)
    
    s1, s2 = st.columns(2)
    with s1:
        with st.container(border=True):
            st.markdown("#### 💰 Buy Gold")
            st.write("**Cost:** 1 Gem")
            st.write("**Receive:** 30 Gold")
            if st.button("Trade for Gold", use_container_width=True, disabled=st.session_state.gems < 1):
                st.session_state.gems -= 1
                st.session_state.gold += 30
                log("Traded 1 Gem for 30 Gold.")
                st.rerun()
                
    with s2:
        with st.container(border=True):
            st.markdown("#### 🏗️ Buy Steel")
            st.write("**Cost:** 1 Gem")
            st.write("**Receive:** 3 Steel")
            if st.button("Trade for Steel", use_container_width=True, disabled=st.session_state.gems < 1):
                st.session_state.gems -= 1
                st.session_state.steel += 3
                log("Traded 1 Gem for 3 Steel.")
                st.rerun()


# --- TAB 6: INFRASTRUCTURE ---
with tab_infra:
    st.subheader("Resource Management")
    
    for b_name, b_data in BUILDINGS.items():
        curr = st.session_state.buildings.get(b_name, 0)
        limit = b_data['limit']
        
        with st.container(border=True):
            ic1, ic2, ic3 = st.columns([2, 2, 1])
            with ic1:
                st.markdown(f"#### {b_name}")
                st.caption(b_data['desc'])
            with ic2:
                st.write(f"**Effect:** {b_data['effect']}")
                cost_str = f"{b_data['gold']}G"
                if b_data['steel'] > 0: cost_str += f" | {b_data['steel']}S"
                st.write(f"**Cost:** {cost_str}")
                st.write(f"**Owned:** {curr} / {limit}")
            with ic3:
                can_afford_g = st.session_state.gold >= b_data['gold']
                can_afford_s = st.session_state.steel >= b_data['steel']
                not_maxed = curr < limit
                if st.button(f"Buy", key=f"buy_{b_name}", disabled=not (can_afford_g and can_afford_s and not_maxed)):
                    st.session_state.gold -= b_data['gold']
                    st.session_state.steel -= b_data['steel']
                    st.session_state.buildings[b_name] += 1
                    log(f"Constructed {b_name}")
                    st.rerun()
    
    st.divider()
    st.markdown("### 📋 Infrastructure Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gold Mines", st.session_state.buildings["Gold Mine"])
    c2.metric("Steel Factories", st.session_state.buildings["Steel Factory"])
    c3.metric("Base Defenses", st.session_state.buildings["Base Defense"])
    c4.metric("Shipyard", "Operational" if st.session_state.buildings["Shipyard"] else "None")


# --- SIDEBAR ---
with st.sidebar:
    st.header("Actions")
    if st.button("💥 Enemy Destroyed (+20g)"):
        st.session_state.gold += 20
        st.rerun()
    st.divider()
    if st.button("RESET GAME", type="primary"):
        st.session_state.clear()
        st.rerun()