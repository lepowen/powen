import streamlit as st
import bcrypt
import json
import uuid
from datetime import datetime
from collections import Counter
import random
import time

USER_FILE = "users.json"

# 百家樂模擬區功能定義
def show_simulator_tab():
    st.header("🎲 百家樂模擬區")
    st.write("這裡是模擬功能區，將進行 100 萬次百家樂模擬，分為 10 輪計算。")

    def create_deck():
        deck = []
        for _ in range(8):
            for card in range(1, 14):
                deck.extend([card] * 4)
        return deck

    def baccarat_value(card):
        return 0 if card >= 10 else card

    def total_value(cards):
        return sum(baccarat_value(c) for c in cards) % 10

    def player_should_draw(total):
        return total <= 5

    def banker_should_draw(banker_total, player_third_card):
        if banker_total >= 7:
            return False
        if banker_total <= 2:
            return True
        if banker_total == 3:
            return player_third_card != 8
        if banker_total == 4:
            return 2 <= player_third_card <= 7
        if banker_total == 5:
            return 4 <= player_third_card <= 7
        if banker_total == 6:
            return 6 <= player_third_card <= 7
        return False

    def simulate_baccarat_game(deck):
        player_cards = [deck.pop(), deck.pop()]
        banker_cards = [deck.pop(), deck.pop()]

        player_total = total_value(player_cards)
        banker_total = total_value(banker_cards)

        if player_total in [8, 9] or banker_total in [8, 9]:
            return player_total, banker_total

        player_third = None
        if player_should_draw(player_total):
            player_third = deck.pop()
            player_cards.append(player_third)

        if player_third is not None:
            if banker_should_draw(banker_total, player_third):
                banker_cards.append(deck.pop())
        elif banker_total <= 5:
            banker_cards.append(deck.pop())

        return total_value(player_cards), total_value(banker_cards)

    def run_simulation():
        player_wins = 0
        banker_wins = 0
        ties = 0
        rounds = 10
        sims_per_round = 100000

        for _ in range(rounds):
            deck = create_deck()
            random.shuffle(deck)
            for _ in range(sims_per_round):
                if len(deck) < 10:
                    deck = create_deck()
                    random.shuffle(deck)
                player_score, banker_score = simulate_baccarat_game(deck)
                if player_score > banker_score:
                    player_wins += 1
                elif player_score < banker_score:
                    banker_wins += 1
                else:
                    ties += 1

        total_games = player_wins + banker_wins + ties
        st.write(f"模擬完成：共 {total_games:,} 局")
        st.write(f"閒家贏：{player_wins:,} 局 ({player_wins/total_games:.2%})")
        st.write(f"莊家贏：{banker_wins:,} 局 ({banker_wins/total_games:.2%})")
        st.write(f"和局：{ties:,} 局 ({ties/total_games:.2%})")

    if st.button("開始模擬"):
        with st.spinner("模擬中，請稍候..."):
            run_simulation()

    # 主系統登入與分頁邏輯
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

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
                with USER_FILE.open("w") as f:
                    json.dump(users, f)
                st.success(f"✅ 歡迎 {username}！登入成功。")
                st.experimental_rerun()
            else:
                st.error("❌ 帳號或密碼錯誤，請再試一次")

    else:
    with open(USER_FILE, "r") as f:
        users = json.load(f)

    if st.session_state.role == "admin":
        tab1, tab2 = st.tabs(["👤 帳號管理後台", "🎲 百家樂模擬區"])
        with tab1:
            st.header("👥 帳號管理後台")
            st.subheader("📋 所有帳號")
            for user, data in users.items():
                created = data.get("created_at", "(未記錄)")
                last_login = data.get("last_login", "(從未登入)")
                st.write(f"🔹 {user}，權限：{data.get('role', 'user')} - 裝置：{data.get('device_id', '未綁定')} - 建立：{created} - 最後登入：{last_login}")
            st.subheader("➕ 新增帳號")
            with st.form("add_user"):
                new_user = st.text_input("新增帳號")
                new_pass = st.text_input("密碼", type="password")
                new_role = st.selectbox("權限等級", ["user", "admin"])
                submit_add = st.form_submit_button("新增")
                if submit_add:
                    if new_user in users:
                        st.warning("⚠️ 此帳號已存在")
                    elif len(new_pass) < 6:
                        st.warning("⚠️ 密碼請至少6位數")
                    else:
                        hashed_pw = bcrypt.hashpw(new_pass.encode(), bcrypt.gensalt()).decode()
                        users[new_user] = {
                            "password": hashed_pw,
                            "role": new_role,
                            "created_at": datetime.now().isoformat()
                        }
                        with open(USER_FILE, "w") as f:
                            json.dump(users, f)
                        st.success(f"✅ 使用者 {new_user} 已新增成功")
                        st.experimental_rerun()
        with tab2:
            show_simulator_tab()
    else:
        tab2 = st.tabs(["🎲 百家樂模擬區"])[0]
        with tab2:
            show_simulator_tab()
