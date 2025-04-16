import streamlit as st
import json
import bcrypt
import random
import time
from collections import Counter
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="百家送你花 僅供參考 Le關心你", layout="wide")
USER_FILE = Path("users.json")

# 載入使用者資料
try:
    with open(USER_FILE, "r") as f:
        users = json.load(f)
except FileNotFoundError:
    users = {}

# 初始化登入狀態
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# 登入流程
if not st.session_state.authenticated:
    tab1 = st.tabs(["🔐 登入"])[0]
    with tab1:
        with st.form("login_form"):
            username = st.text_input("帳號")
            password = st.text_input("密碼", type="password")
            submitted = st.form_submit_button("登入")

        if submitted:
            if username in users and bcrypt.checkpw(password.encode(), users[username]["password"].encode()):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.role = users[username].get("role", "user")
                users[username]["last_login"] = datetime.now().isoformat()
                with open(USER_FILE, "w") as f:
                    json.dump(users, f)
                st.success(f"✅ 歡迎 {username}！登入成功。")
                st.experimental_rerun()
            else:
                st.error("❌ 帳號或密碼錯誤，請再試一次")
    st.stop()

# ===== 功能模組 =====
def show_simulator_tab():
    st.title("🎲 百家送你花 僅供參考 Le關心你")
    if "deck" not in st.session_state:
        deck = []
        for _ in range(8):
            for card in range(1, 14):
                for _ in range(4):
                    deck.append(card)
        random.shuffle(deck)
        
        st.session_state.deck = deck
        st.session_state.used_cards = []
        st.session_state.round_count = 0

    st.write(f"目前剩餘牌數：{len(st.session_state.deck)} 張")

    if st.checkbox("顯示剩餘牌分布"):
        count_remain = Counter(st.session_state.deck)
        for num in range(1, 14):
            name = {1: "A", 11: "J", 12: "Q", 13: "K"}.get(num, str(num))
            st.write(f"{name}: {count_remain[num]} 張")

    st.divider()
    cards_input = st.text_input("請輸入本局開過的牌（空白隔開，例如：1 3 13 6 3）")

    if st.button("模擬下一局勝率"):
        try:
            cards = list(map(int, cards_input.strip().split()))
            if not all(1 <= card <= 13 for card in cards):
                st.error("請輸入1到13之間的數字！")
            else:
                st.session_state.round_count += 1
                st.session_state.used_cards.extend(cards)
                deck = []
                for _ in range(8):
                    for card in range(1, 14):
                        for _ in range(4):
                            deck.append(card)
                for card in st.session_state.used_cards:
                    if card in deck:
                        deck.remove(card)
                st.session_state.deck = deck

                if len(st.session_state.deck) < 6:
                    st.warning("剩餘牌數過少，無法繼續模擬。")
                else:
                    st.success(f"開始模擬第 {st.session_state.round_count} 局...請稍等")

                    start_time = time.time()
                    result = simulate_with_draw_split(st.session_state.deck, simulations_per_round=50000, rounds=3)
                    end_time = time.time()
                    duration = end_time - start_time

                    banker_odds = 100 / (result['Banker Win Rate'] * 100)
                    player_odds = 100 / (result['Player Win Rate'] * 100)
                    tie_odds = 100 / (result['Tie Rate'] * 100)
                    adjusted_banker_rate = result['Banker Win Rate'] * 0.95

                    banker_expectation = adjusted_banker_rate + result['Player Win Rate'] * -1
                    player_expectation = result['Player Win Rate'] * 1 + result['Banker Win Rate'] * -1
                    tie_expectation = result['Tie Rate'] * 8 + (1 - result['Tie Rate']) * -1

                    st.subheader("模擬結果")
                    st.write(f"莊勝率: {result['Banker Win Rate']*100:.2f}% (賠率 {banker_odds:.2f})")
                    st.write(f"閒勝率: {result['Player Win Rate']*100:.2f}% (賠率 {player_odds:.2f})")
                    st.write(f"和勝率: {result['Tie Rate']*100:.2f}% (賠率 {tie_odds:.2f})")
                    st.write(f"模擬耗時：{duration:.2f}秒")
                    st.write(f"調整後莊勝率（扣抽水5%）：{adjusted_banker_rate*100:.2f}%")

                    st.subheader("抽水後期望值")
                    st.write(f"下注莊家，期望值: {banker_expectation*100:.2f}%")
                    st.write(f"下注閒家，期望值: {player_expectation*100:.2f}%")
                    st.write(f"下注和局，期望值: {tie_expectation*100:.2f}%")
        except:
            st.error("輸入格式錯誤，請重新輸入！")

def simulate_with_draw_split(deck, simulations_per_round=10000, rounds=10):
    total_player_win = 0
    total_banker_win = 0
    total_tie = 0

    for _ in range(rounds):
        player_win = 0
        banker_win = 0
        tie = 0

        temp_deck = deck.copy()
        for _ in range(simulations_per_round):
            if len(temp_deck) < 6:
                temp_deck = deck.copy()
            random.shuffle(temp_deck)

            player_cards = [temp_deck.pop(), temp_deck.pop()]
            banker_cards = [temp_deck.pop(), temp_deck.pop()]

            def baccarat_value(card):
                return 0 if card >= 10 else card

            player_total = (baccarat_value(player_cards[0]) + baccarat_value(player_cards[1])) % 10
            banker_total = (baccarat_value(banker_cards[0]) + baccarat_value(banker_cards[1])) % 10

            player_third_card = None
            if player_total <= 5:
                player_third_card = baccarat_value(temp_deck.pop())
                player_total = (player_total + player_third_card) % 10

            def banker_should_draw(bt, ptc):
                if bt >= 7:
                    return False
                if bt <= 2:
                    return True
                if bt == 3:
                    return ptc != 8
                if bt == 4:
                    return 2 <= ptc <= 7
                if bt == 5:
                    return 4 <= ptc <= 7
                if bt == 6:
                    return 6 <= ptc <= 7
                return False

            if player_third_card is None:
                if banker_total <= 5:
                    banker_total = (banker_total + baccarat_value(temp_deck.pop())) % 10
            else:
                if banker_should_draw(banker_total, player_third_card):
                    banker_total = (banker_total + baccarat_value(temp_deck.pop())) % 10

            if player_total > banker_total:
                player_win += 1
            elif banker_total > player_total:
                banker_win += 1
            else:
                tie += 1

        total_player_win += player_win
        total_banker_win += banker_win
        total_tie += tie

    total = total_player_win + total_banker_win + total_tie
    return {
        "Player Win Rate": total_player_win / total,
        "Banker Win Rate": total_banker_win / total,
        "Tie Rate": total_tie / total
    }

# 顯示主畫面
if st.session_state.role == "admin":
    tab1, tab2 = st.tabs(["👤 帳號管理後台", "🎲 百家樂模擬區"])
    with tab2:
        show_simulator_tab()
    with tab1:
        st.header("🔧 帳號管理後台")

        st.subheader("📋 所有帳號")
        if users:
            for user, data in users.items():
                created_time = data.get("created_at", "(未記錄)")
                last_login = data.get("last_login", "(從未登入)")
                st.write(f"👤 `{user}` - 權限：{data.get('role', 'user')} - 建立：{created_time} - 最後登入：{last_login}")
        else:
            st.write("目前尚無使用者資料。")

        st.divider()

        st.subheader("➕ 新增帳號")
        with st.form("add_user_form"):
            new_user = st.text_input("新帳號")
            new_pass = st.text_input("新密碼", type="password")
            submit_add = st.form_submit_button("新增帳號")
            if submit_add:
                if new_user in users:
                    st.warning("❗ 此帳號已存在")
                elif len(new_pass) < 6:
                    st.warning("❗ 密碼請至少6位數")
                else:
                    hashed_pw = bcrypt.hashpw(new_pass.encode(), bcrypt.gensalt()).decode()
                    users[new_user] = {
                        "password": hashed_pw,
                        "role": "user",
                        "created_at": datetime.now().isoformat()
                    }
                    with open(USER_FILE, "w") as f:
                        json.dump(users, f)
                    st.success(f"✅ 已新增帳號 `{new_user}`")

        st.subheader("🗑️ 刪除帳號")
        deletable_users = [u for u in users if u != st.session_state.username]
        if deletable_users:
            with st.form("delete_user_form"):
                del_user = st.selectbox("選擇帳號刪除", deletable_users)
                submit_del = st.form_submit_button("刪除帳號")
                if submit_del:
                    users.pop(del_user)
                    with open(USER_FILE, "w") as f:
                        json.dump(users, f)
                    st.success(f"✅ `{del_user}` 已被刪除")
        else:
            st.info("（無可刪除的其他帳號）")

else:
    show_simulator_tab()
