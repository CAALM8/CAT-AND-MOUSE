# Streamlit 试玩版：猫抓芝士（轻量版）
# 保存为 app.py，然后运行：
#    pip install streamlit
#    streamlit run app.py

import streamlit as st
import random

# ====== 配置（可修改） ======
TRACK_LEN = 10  # 位置 0..TRACK_LEN-1
CHEESE_POS = 5
HOLE_POS = 0
MAX_MOUSE_HP = 3
MAX_CAT_HP = 4
MAX_TRAPS = 3

# ====== Session state 初始化 ======
if 'inited' not in st.session_state:
    st.session_state.inited = True
    st.session_state.mouse_pos = 0
    st.session_state.cat_pos = TRACK_LEN - 1
    st.session_state.mouse_hp = MAX_MOUSE_HP
    st.session_state.cat_hp = MAX_CAT_HP
    st.session_state.has_cheese = False
    st.session_state.traps = []  # list of positions
    st.session_state.traps_left = MAX_TRAPS
    st.session_state.turn = 'mouse'  # 'mouse' or 'cat'
    st.session_state.log = []
    st.session_state.mouse_balloon = 1  # 气球卡数量
    st.session_state.mouse_banana = 1   # 香蕉皮卡数量
    st.session_state.cat_broom = 1      # 扫帚卡数量
    st.session_state.cat_skip = False   # 是否被香蕉影响跳过
    st.session_state.cat_broom_active = False
    st.session_state.game_over = False

# ====== 工具函数 ======

def reset_game():
    st.session_state.mouse_pos = 0
    st.session_state.cat_pos = TRACK_LEN - 1
    st.session_state.mouse_hp = MAX_MOUSE_HP
    st.session_state.cat_hp = MAX_CAT_HP
    st.session_state.has_cheese = False
    st.session_state.traps = []
    st.session_state.traps_left = MAX_TRAPS
    st.session_state.turn = 'mouse'
    st.session_state.log = []
    st.session_state.mouse_balloon = 1
    st.session_state.mouse_banana = 1
    st.session_state.cat_broom = 1
    st.session_state.cat_skip = False
    st.session_state.cat_broom_active = False
    st.session_state.game_over = False


def log(msg):
    st.session_state.log.insert(0, msg)


def roll_dice():
    return random.randint(1, 3)


def render_board():
    # Render a simple horizontal board with emojis
    row = []
    for i in range(TRACK_LEN):
        cell = ''
        if st.session_state.mouse_pos == i and st.session_state.cat_pos == i:
            cell = '🐱🐭'  # same cell
        elif st.session_state.mouse_pos == i:
            cell = '🐭'
        elif st.session_state.cat_pos == i:
            cell = '🐱'
        elif i == CHEESE_POS and not st.session_state.has_cheese:
            cell = '🧀'
        elif i == HOLE_POS:
            cell = '🕳️'
        elif i in st.session_state.traps:
            cell = '🪤'
        else:
            cell = '▫️'
        row.append(cell)
    # show as columns
    cols = st.columns(TRACK_LEN)
    for idx, c in enumerate(cols):
        c.markdown(f"**{idx}**")
        c.write(row[idx])


# ====== 游戏逻辑核心 ======

def mouse_move(steps):
    # Mouse movement: if has cheese -> move toward HOLE_POS (decreasing index)
    if st.session_state.has_cheese:
        target = max(HOLE_POS, st.session_state.mouse_pos - steps)
    else:
        target = min(TRACK_LEN - 1, st.session_state.mouse_pos + steps)
    log(f"老鼠移动：{st.session_state.mouse_pos} ➜ {target}（步数：{steps}）")
    st.session_state.mouse_pos = target

    # 检查是否踩到陷阱
    if st.session_state.mouse_pos in st.session_state.traps:
        # 如果有气球可用并选择自动使用，则免疫一次陷阱（否则扣血）
        if st.session_state.mouse_balloon > 0 and st.session_state.auto_use_balloon:
            st.session_state.mouse_balloon -= 1
            st.session_state.traps.remove(st.session_state.mouse_pos)
            log("老鼠用气球躲过了陷阱（自动使用）🎈")
        else:
            st.session_state.mouse_hp -= 1
            log(f"老鼠踩到捕鼠夹！-1 生命（剩余：{st.session_state.mouse_hp}）🪤")

    # 检查是否到达奶酪
    if (not st.session_state.has_cheese) and (st.session_state.mouse_pos == CHEESE_POS):
        st.session_state.has_cheese = True
        log("老鼠拿到奶酪！现在往鼠洞逃跑 🧀➡️🕳️")

    # 如果带着奶酪回到鼠洞，老鼠胜利
    if st.session_state.has_cheese and st.session_state.mouse_pos == HOLE_POS:
        st.session_state.game_over = True
        log("老鼠成功带着芝士回到老鼠洞，老鼠胜利！🏆")


def cat_move(steps):
    # Cat movement: move toward mouse by default
    # For simplicity，猫朝着老鼠方向移动steps，若猫选择指定移动则此处也是执行
    if st.session_state.cat_pos > st.session_state.mouse_pos:
        newpos = max(0, st.session_state.cat_pos - steps)
    else:
        newpos = min(TRACK_LEN - 1, st.session_state.cat_pos + steps)
    log(f"猫移动：{st.session_state.cat_pos} ➜ {newpos}（步数：{steps}）")
    st.session_state.cat_pos = newpos

    # 检查是否踩到香蕉（我们用陷阱位置存香蕉也是可以；但这里简化：香蕉仅在老鼠使用时记录在 banana_pos）
    if hasattr(st.session_state, 'banana_pos') and st.session_state.cat_pos == st.session_state.banana_pos:
        st.session_state.cat_skip = True
        log("汤姆踩到香蕉皮，下一回合跳过（尴尬）🍌")
        # banana disappears
        del st.session_state.banana_pos

    # 如果在同一格，攻击
    dist = abs(st.session_state.cat_pos - st.session_state.mouse_pos)
    attack_range = 1
    if st.session_state.cat_broom_active:
        attack_range = 2
    if dist <= attack_range:
        # 成功攻击
        st.session_state.mouse_hp -= 1
        log(f"猫攻击到老鼠！老鼠 -1 生命（剩余：{st.session_state.mouse_hp}）😾")

    # 清理 broom 状态（只延续本回合）
    st.session_state.cat_broom_active = False

    # 猫攻击后若老鼠生命归0，猫胜
    if st.session_state.mouse_hp <= 0:
        st.session_state.game_over = True
        log("老鼠生命耗尽，猫胜利！😼")


# ====== UI ======

st.title('🐱🐭 试玩：猫抓芝士（轻量版）')
st.markdown('简化的回合制对抗桌游，适合放到 Streamlit 做试玩 Demo。')

# 左侧：游戏信息与操作
left, right = st.columns([2, 1])

with left:
    render_board()

    st.markdown('---')
    st.write(f"**回合**：{st.session_state.turn.upper()}")
    st.write(f"老鼠生命：{st.session_state.mouse_hp}  |  带芝士：{st.session_state.has_cheese}  |  气球：{st.session_state.mouse_balloon}  |  香蕉：{st.session_state.mouse_banana}")
    st.write(f"猫位置：{st.session_state.cat_pos}  |  捕鼠夹剩余可放：{st.session_state.traps_left}  |  扫帚：{st.session_state.cat_broom}")

    st.markdown('---')

    if st.session_state.game_over:
        st.error('游戏结束')
        if st.button('重新开始'):
            reset_game()
    else:
        if st.session_state.turn == 'mouse':
            st.subheader('老鼠行动')
            # 自动使用气球开关
            st.session_state.auto_use_balloon = st.checkbox('自动使用气球躲避陷阱（若有）', value=True)

            if st.button('掷骰并移动（老鼠）'):
                steps = roll_dice()
                mouse_move(steps)
                # 轮到猫
                if not st.session_state.game_over:
                    st.session_state.turn = 'cat'

            # 卡牌：气球、香蕉
            cols = st.columns(2)
            with cols[0]:
                if st.session_state.mouse_balloon > 0:
                    if st.button('使用气球（消耗1）'):
                        # 使用气球：本回合移动额外+2并避免一次陷阱
                        steps = roll_dice() + 2
                        st.session_state.mouse_balloon -= 1
                        log(f"老鼠用气球：掷骰并额外+2（本次步数 {steps}）🎈")
                        mouse_move(steps)
                        if not st.session_state.game_over:
                            st.session_state.turn = 'cat'
                else:
                    st.write('气球：无')
            with cols[1]:
                if st.session_state.mouse_banana > 0:
                    if st.button('使用香蕉皮（放在当前位置）'):
                        st.session_state.mouse_banana -= 1
                        st.session_state.banana_pos = st.session_state.mouse_pos
                        log(f"老鼠在位置 {st.session_state.mouse_pos} 放了香蕉皮 🍌")
                else:
                    st.write('香蕉：无')

        else:
            st.subheader('猫行动')
            if st.session_state.cat_skip:
                st.warning('汤姆本回合被香蕉影响，跳过行动 🫨')
                st.session_state.cat_skip = False
                st.session_state.turn = 'mouse'
            else:
                if st.button('掷骰并自动追击（猫）'):
                    steps = roll_dice()
                    cat_move(steps)
                    if not st.session_state.game_over:
                        st.session_state.turn = 'mouse'

                # 猫放捕鼠夹
                if st.session_state.traps_left > 0:
                    if st.button('放置捕鼠夹（当前位置+1格）'):
                        # 放在猫朝向老鼠的下一个格子
                        direction = -1 if st.session_state.cat_pos > st.session_state.mouse_pos else 1
                        pos = st.session_state.cat_pos + direction
                        pos = max(0, min(TRACK_LEN - 1, pos))
                        if pos not in st.session_state.traps:
                            st.session_state.traps.append(pos)
                            st.session_state.traps_left -= 1
                            log(f"猫放置捕鼠夹在位置 {pos} 🪤")
                        else:
                            log('该位置已有捕鼠夹')

                # 猫使用扫帚
                if st.session_state.cat_broom > 0:
                    if st.button('使用扫帚（本回合攻击范围扩大）'):
                        st.session_state.cat_broom -= 1
                        st.session_state.cat_broom_active = True
                        log('猫使用扫帚，本回合攻击范围扩大🧹')
                        # 猫可立即尝试移动并攻击
                        steps = roll_dice()
                        cat_move(steps)
                        if not st.session_state.game_over:
                            st.session_state.turn = 'mouse'

# 右侧：日志和规则
with right:
    st.subheader('游戏日志（最新在上）')
    for entry in st.session_state.log[:10]:
        st.write('- ' + entry)

    st.markdown('---')
    st.subheader('快速说明')
    st.write('1. 老鼠从鼠洞（位置 0）出发，目标：拿到奶酪（位置 5）并返回鼠洞。')
    st.write('2. 猫从地图末端追逐，目标：在老鼠回洞前使其生命耗尽。')
    st.write('3. 双方通过掷骰移动（1-3 步），并可使用各自的道具卡。')
    st.write('4. 你可以把这个文件命名为 app.py 上传到 GitHub，使用 streamlit run app.py 运行试玩。')

    st.markdown('---')
    st.write('（这是一个简化试玩版，欢迎让我帮你扩展成更复杂的规则、AI 或多人在线版本）')

# Footer: 状态提示
if st.session_state.game_over:
    st.balloons()
    st.success('游戏结束！可以点击「重新开始」开始新局。')

