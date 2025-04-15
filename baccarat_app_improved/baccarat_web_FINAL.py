import random
import time
import json
import bcrypt
from collections import Counter
import streamlit as st
from pathlib import Path
import uuid
from datetime import datetime

st.set_page_config(page_title="百家樂模擬器", layout="centered")

USER_FILE = Path("users.json")

if not USER_FILE.exists():
    USER_FILE.write_text(json.dumps({}))

with USER_FILE.open("r") as f:
    users = json.load(f)

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
                    client_id = st.session_state.get("device_id")
                    if not client_id:
                        client_id = str(uuid.uuid4())  # ✅ 要放在這裡
                    st.session_state.device_id = client_id
                    users[username]["last_login"] = datetime.now().isoformat()
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.role = users[username].get("role", "user")
                    with USER_FILE.open("w") as f:
                        json.dump(users, f)
                    st.success(f"✅ 歡迎 {username}！登入成功。")
                    st.experimental_rerun()
                else:
                    st.error("❌ 帳號或密碼錯誤，請再試一次")
        st.stop()
st.sidebar.success(f"🎉 歡迎 {st.session_state.username}，祝你模擬順利！")

# 密碼修改功能
st.sidebar.write("🔑 修改密碼")
with st.sidebar.form("change_password"):
    old_pass = st.text_input("舊密碼", type="password")
    new_pass = st.text_input("新密碼", type="password")
    confirm_new = st.text_input("確認新密碼", type="password")
    submitted = st.form_submit_button("確認修改")
    if submitted:
        if not bcrypt.checkpw(old_pass.encode(), users[st.session_state.username]["password"].encode()):
            st.sidebar.error("❌ 舊密碼錯誤")
        elif new_pass != confirm_new:
            st.sidebar.error("❌ 新密碼與確認不一致")
        elif len(new_pass) < 6:
            st.sidebar.warning("⚠️ 新密碼請設定至少6位數")
        else:
            users[st.session_state.username]["password"] = bcrypt.hashpw(new_pass.encode(), bcrypt.gensalt()).decode()
            with USER_FILE.open("w") as f:
                json.dump(users, f)
            st.sidebar.success("✅ 密碼修改成功")

# 管理員 sees tab1 (後台) + tab2 (模擬)，一般使用者 only sees tab2
if st.session_state.role == "admin":
    tab1, tab2 = st.tabs(["🔧 帳號管理後台", "🎲 百家樂模擬區"])
    with tab1:
        st.header("🔧 帳號管理後台")
        st.subheader("📋 所有帳號")
        for user, data in users.items():
            created_time = data.get("created_at", "(未記錄)")
            last_login = data.get("last_login", "(從未登入)")
            st.write(
                f"👤 `{user}` - 權限：{data.get('role', 'user')} - 裝置：{data.get('device_id', '未綁定')} - 建立：{created_time} - 最後登入：{last_login}"
            )

        st.subheader("➕ 新增帳號")
        with st.form("add_user"):
            new_user = st.text_input("新帳號")
            new_pass = st.text_input("新密碼", type="password")
            new_role = st.selectbox("權限等級", ["user", "admin"])
            submit_add = st.form_submit_button("新增")
            if submit_add:
                if new_user in users:
                    st.warning("❗ 此帳號已存在")
                elif len(new_pass) < 6:
                    st.warning("❗ 密碼請至少6位數")
                else:
                    hashed_pw = bcrypt.hashpw(new_pass.encode(), bcrypt.gensalt()).decode()
                    users[new_user] = {
                        "password": hashed_pw,
                        "role": new_role,
                        "created_at": datetime.now().isoformat()
                    }
                    with USER_FILE.open("w") as f:
                        json.dump(users, f)
                    st.success(f"✅ 已新增帳號 `{new_user}`")

        st.subheader("🗑️ 刪除帳號")
        with st.form("delete_user"):
            del_user = st.selectbox("選擇帳號刪除", [u for u in users if u != st.session_state.username])
            submit_del = st.form_submit_button("刪除")
            if submit_del:
                users.pop(del_user)
                with USER_FILE.open("w") as f:
                    json.dump(users, f)
                st.success(f"✅ `{del_user}` 已被刪除")
else:
    tab2 = st.tabs(["🎲 百家樂模擬區"])[0]
    with tab2:
        show_simulator_tab()

def show_simulator_tab():
    from collections import Counter
    import time

    st.header("🎰 百家樂模擬區")
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
            if player_total > banker_total:
                return "Player"
            elif banker_total > player_total:
                return "Banker"
            else:
                return "Tie"

        player_third_card = None
        if player_should_draw(player_total):
            player_third_card = deck.pop()
            player_cards.append(player_third_card)

        if player_third_card is not None:
            if banker_should_draw(banker_total, baccarat_value(player_third_card)):
                banker_cards.append(deck.pop())
        else:
            if banker_total <= 5:
                banker_cards.append(deck.pop())

        player_total = total_value(player_cards)
        banker_total = total_value(banker_cards)

        if player_total > banker_total:
            return "Player"
        elif banker_total > player_total:
            return "Banker"
        else:
            return "Tie"

    if st.button("開始模擬 100 萬局（分10輪）"):
        all_results = Counter()
        start_time = time.time()

        for round_num in range(10):
            deck = create_deck()
            random.shuffle(deck)
            result_counter = Counter()
            for _ in range(100000):
                if len(deck) < 10:
                    deck = create_deck()
                    random.shuffle(deck)
                result = simulate_baccarat_game(deck)
                result_counter[result] += 1
            st.write(f"第 {round_num+1} 輪結果：莊家 {result_counter['Banker']}、閒家 {result_counter['Player']}、和局 {result_counter['Tie']}")
            all_results += result_counter

        end_time = time.time()
        st.subheader("💯 總結結果（100 萬局）")
        st.write(f"👤 玩家勝：{all_results['Player']:,} 局")
        st.write(f"🏦 莊家勝：{all_results['Banker']:,} 局")
        st.write(f"🤝 和局：{all_results['Tie']:,} 局")
        st.write(f"⏱️ 總耗時：{end_time - start_time:.2f} 秒")
    def create_deck():
        deck = []
        for _ in range(8):
            for card in range(1, 14):
                for _ in range(4):
                    deck.append(card)
        return deck

    def baccarat_value(card):
        return 0 if card >= 10 else card

    def update_deck(deck, used_cards):
        deck_counter = Counter(deck)
        used_counter = Counter(used_cards)
        for card, count in used_counter.items():
            if deck_counter[card] >= count:
                deck_counter[card] -= count
        new_deck = []
        for card, count in deck_counter.items():
            new_deck.extend([card] * count)
        return new_deck

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
    def simulate_with_draw_split(deck, simulations_per_round=10000, rounds=10):
        total_player_win = 0
        total_banker_win = 0
        total_tie = 0

        for _ in range(rounds):
            temp_deck = deck.copy()
            for _ in range(simulations_per_round):
                if len(temp_deck) < 6:
                    temp_deck = deck.copy()
                random.shuffle(temp_deck)

                player_cards = [temp_deck.pop(), temp_deck.pop()]
                banker_cards = [temp_deck.pop(), temp_deck.pop()]

                player_total = (baccarat_value(player_cards[0]) + baccarat_value(player_cards[1])) % 10
                banker_total = (baccarat_value(banker_cards[0]) + baccarat_value(banker_cards[1])) % 10

                player_third_card = None

                if player_should_draw(player_total):
                    player_third_card = baccarat_value(temp_deck.pop())
                    player_total = (player_total + player_third_card) % 10

                if player_third_card is None:
                    if banker_total <= 5:
                        banker_third_card = baccarat_value(temp_deck.pop())
                        banker_total = (banker_total + banker_third_card) % 10
                else:
                    if banker_should_draw(banker_total, player_third_card):
                        banker_third_card = baccarat_value(temp_deck.pop())
                        banker_total = (banker_total + banker_third_card) % 10

                if player_total > banker_total:
                    total_player_win += 1
                elif banker_total > player_total:
                    total_banker_win += 1
                else:
                    total_tie += 1

        total = total_player_win + total_banker_win + total_tie
        return {
            "Player Win Rate": total_player_win / total,
            "Banker Win Rate": total_banker_win / total,
            "Tie Rate": total_tie / total
        }
    if "deck" not in st.session_state:
        deck = create_deck()
        random.shuffle(deck)
        for _ in range(8):
            deck.pop()
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
                st.session_state.deck = create_deck()
                st.session_state.deck = update_deck(st.session_state.deck, st.session_state.used_cards)

                if len(st.session_state.deck) < 6:
                    st.warning("剩餘牌數過少，無法繼續模擬。")
                else:
                    st.success(f"開始模擬第 {st.session_state.round_count} 局...請稍等")
                    start_time = time.time()
                    result = simulate_with_draw_split(st.session_state.deck, simulations_per_round=10000, rounds=10)
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

                    expectations = [banker_expectation, player_expectation]
                    names = ["莊家", "閒家"]
                    best_index = expectations.index(max(expectations))
                    suggestion = names[best_index]

                    st.subheader("建議下注")
                    st.success(f"➡️ 建議下注：{suggestion}")

                    best = max(expectations)
                    worst = min(expectations)
                    confidence_gap = best - worst

                    if confidence_gap < 0.002:
                        confidence = "低信心"
                        emotion = "局勢普通，小心觀望！"
                    elif confidence_gap < 0.005:
                        confidence = "中信心"
                        emotion = "機會還不錯，穩穩來！"
                    else:
                        confidence = "高信心"
                        emotion = "這局信心爆棚，建議大膽出手！"

                    st.write(f"📈 信心等級：{confidence}")
                    st.info(f"💬 {emotion}")

                    if best < 0:
                        st.warning("⚠️ 溫馨提醒：這局整體期望值偏負，可以考慮休息一下～")
        except:
            st.error("輸入格式錯誤，請重新輸入！")
