import streamlit as st
import random
import re
import json
import os
from datetime import datetime

# --- 1. 页面配置 ---
st.set_page_config(page_title="冰冰加油站 🦁", page_icon="💖", layout="centered")

# --- 2. 极致可爱样式定制 ---
st.markdown("""
    <style>
    /* 整体背景：柔和粉色 */
    .stApp { background-color: #fff9fb !important; }
    
    /* 可爱对话框样式 */
    .bing-bubble {
        background-color: #ffffff;
        border: 2px solid #ffb6c1;
        border-radius: 20px;
        padding: 15px;
        position: relative;
        margin-bottom: 25px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(255,182,193,0.3);
    }
    .bing-bubble:after {
        content: '';
        position: absolute;
        bottom: -10px;
        left: 50%;
        margin-left: -10px;
        border-width: 10px 10px 0;
        border-style: solid;
        border-color: #ffb6c1 transparent transparent;
    }
    
    .cheer-text {
        color: #ff4b7d !important;
        font-weight: bold;
        font-size: 1.2rem;
        font-family: "Microsoft YaHei", sans-serif;
    }

    /* 答题卡片 */
    .question-box {
        background-color: #ffffff !important;
        color: #333333 !important;
        padding: 25px;
        border-radius: 20px;
        border-bottom: 5px solid #ffb6c1;
        margin-bottom: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }

    /* 历史记录小卡片 */
    .history-card {
        padding: 12px;
        border-radius: 15px;
        background: white;
        margin-bottom: 10px;
        border: 1px solid #ffeef2;
    }

    /* 强制黑色文字，防止深色模式隐身 */
    .stRadio [data-testid="stMarkdownContainer"] p { color: #000000 !important; font-size: 1.1rem !important; }
    h1, h2, h3, p, span, label, .stMarkdown { color: #444444 !important; }
    
    /* 按钮美化：圆润可爱 */
    .stButton button {
        width: 100%; border-radius: 25px; font-weight: bold; height: 3.5em;
        background: linear-gradient(135deg, #ffb6c1 0%, #ff80ab 100%) !important;
        color: white !important; border: none !important;
        box-shadow: 0 4px 10px rgba(255,128,171,0.3);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 数据读写逻辑 (保持不变) ---
PROGRESS_FILE = "progress.json"
WRONG_FILE = "wrong_questions.json"
HISTORY_FILE = "exam_history.json"

def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f: return json.load(f)
        except: return default
    return default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

# --- 4. 题库解析逻辑 (包含彩蛋) ---
@st.cache_data
def load_bank():
    file_name = "题库.txt"
    bank = []
    if not os.path.exists(file_name): return []
    content = ""
    for enc in ['utf-8', 'gbk', 'gb18030']:
        try:
            with open(file_name, 'r', encoding=enc) as f: content = f.read(); break
        except: continue
    
    pattern = re.compile(r'(\d+)\.(.*?)(?=(?:\d+\.)|(?:\Z))', re.S)
    matches = pattern.findall(content)
    for m_id, m_body in matches:
        ans_match = re.search(r'正确答案[:：]\s*([A-D])', m_body)
        if not ans_match: continue
        answer = ans_match.group(1)
        clean_body = re.sub(r'正确答案[:：].*', '', m_body, flags=re.S).strip()
        opt_pattern = re.compile(r'([A-D])\s*[\.．]\s*(.*?)(?=[A-D]\s*[\.．]|\Z)', re.S)
        opt_matches = opt_pattern.findall(clean_body)
        options = {k.strip(): v.strip() for k, v in opt_matches}
        title_part = clean_body.split('A.')[0].strip()
        title_part = re.sub(r'广东省建筑施工企业.*?题库', '', title_part).strip()
        if title_part and options:
            bank.append({"id": m_id, "title": title_part, "options": options, "answer": answer})
    
    # 彩蛋题必出
    bank.append({"id": "BING_99", "title": "【必考题】冰冰最近复习这么辛苦，某人想问：考完试冰冰想吃什么好吃的？", 
                 "options": {"A": "火锅大餐", "B": "甜甜的蛋糕", "C": "奶茶喝到饱", "D": "都要！某人全包！"}, "answer": "D"})
    return bank

# --- 5. 状态管理 ---
all_bank = load_bank()
progress = load_json(PROGRESS_FILE, {"passed_ids": []})
wrong_data = load_json(WRONG_FILE, {})
history_data = load_json(HISTORY_FILE, [])

if 'mode' not in st.session_state: st.session_state.mode = "home"
if 'page' not in st.session_state: st.session_state.page = 0
if 'user_answers' not in st.session_state: st.session_state.user_answers = {}

# --- 6. 可爱话术库 ---
CUTE_PHRASES = [
    "冰冰加油，你是最亮的一颗星！⭐",
    "这道题虽然难，但冰冰更厉害！🦁",
    "每一道题都在说：冰冰必胜！💪",
    "哇哦，冰冰思考的样子真认真！😘",
    "坚持住，黄冰同学，终点有大餐在等你！🍔",
    "冰冰累不累？抱抱你再接着冲！🤗",
    "离2月9日又近了一步，冰冰稳如泰山！🏰",
    "某人正在后台为你拼命打call！📢"
]

# --- 7. 首页逻辑 ---
if st.session_state.mode == "home":
    st.title("🦁 冰冰冲刺宝典")
    
    days_left = (datetime(2026, 2, 9) - datetime.now()).days
    st.markdown(f"""
    <div class='bing-bubble'>
        <span class='cheer-text'>
            黄冰同学，目前已消灭 {len(progress['passed_ids'])}/{len(all_bank)} 道题！<br>
            距离 2月9日 考试仅剩 {max(0, days_left)} 天，冰冰加油！✨
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 开始新考试"):
            available = [q for q in all_bank if q['id'] not in progress["passed_ids"] or q['id'] == "BING_99"]
            st.session_state.current_exam = random.sample(available if len(available)>=100 else all_bank, 100)
            st.session_state.mode = "exam"; st.session_state.page = 0; st.session_state.user_answers = {}; st.rerun()
    with col2:
        if st.button(f"📖 错题攻克 ({len(wrong_data)})"):
            if not wrong_data: st.balloons(); st.success("冰冰太棒了，目前没有错题！")
            else:
                st.session_state.current_exam = [q for q in all_bank if q['id'] in wrong_data]
                st.session_state.mode = "review"; st.session_state.page = 0; st.rerun()

    st.write("---")
    st.subheader("📊 冰冰的成长记录")
    if not history_data:
        st.write("点击开始考试，留下你的足迹吧~")
    else:
        for record in reversed(history_data[-8:]):
            st.markdown(f"""
            <div class='history-card'>
                📅 {record['time']} | <b>{record['score']}分</b> ({record['mode']})
            </div>
            """, unsafe_allow_html=True)

# --- 8. 答题界面：极致可爱化 ---
elif st.session_state.mode in ["exam", "review"]:
    q_idx = st.session_state.page
    q = st.session_state.current_exam[q_idx]
    
    # 顶部跳动的小加油语
    st.markdown(f"""
    <div class='bing-bubble'>
        <span class='cheer-text'>🦁 {random.choice(CUTE_PHRASES)}</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.progress((q_idx + 1) / len(st.session_state.current_exam))
    st.markdown(f"<div class='question-box'><b>第 {q_idx+1} 题：</b><br>{q['title']}</div>", unsafe_allow_html=True)
    
    if st.session_state.mode == "review": st.warning(f"💡 冰冰请记好，这题选：{q['answer']}")

    ans = st.radio("点击选项：", [f"{k}. {v}" for k, v in q['options'].items()], key=f"q_{q['id']}_{q_idx}")
    if ans: st.session_state.user_answers[q_idx] = ans[0]

    st.write("---")
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        if q_idx > 0: st.button("⬅️ 上一题", on_click=lambda: setattr(st.session_state, 'page', st.session_state.page - 1))
    with c3:
        if q_idx < len(st.session_state.current_exam) - 1:
            st.button("下一题 ➡️", on_click=lambda: setattr(st.session_state, 'page', st.session_state.page + 1))
        else:
            if st.button("🏁 完成交卷"):
                score_cnt = 0
                new_passed = set(progress["passed_ids"])
                for i, q_obj in enumerate(st.session_state.current_exam):
                    if st.session_state.user_answers.get(i) == q_obj['answer']:
                        score_cnt += 1
                        new_passed.add(q_obj['id'])
                        if q_obj['id'] in wrong_data: del wrong_data[q_obj['id']]
                    else:
                        wrong_data[q_obj['id']] = {"time": str(datetime.now())}
                
                save_json(PROGRESS_FILE, {"passed_ids": list(new_passed)})
                save_json(WRONG_FILE, wrong_data)
                
                f_score = int((score_cnt / len(st.session_state.current_exam)) * 100)
                history_data.append({"time": datetime.now().strftime("%m-%d %H:%M"), "mode": "模拟考", "score": f_score})
                save_json(HISTORY_FILE, history_data)
                
                st.session_state.final_score = f_score
                st.session_state.mode = "result"; st.rerun()

# --- 9. 结果页 ---
elif st.session_state.mode == "result":
    s = st.session_state.final_score
    st.title("考试报告单")
    if s >= 60:
        st.balloons()
        st.success(f"🎉 厉害了我的冰！{s} 分！你就是安全生产小天才！")
    else:
        st.snow()
        st.error(f"💔 得分 {s}。没关系，冰冰不哭，咱们再练练错题，某人陪你！")
    
    if st.button("回首页"):
        st.session_state.mode = "home"; st.rerun()
