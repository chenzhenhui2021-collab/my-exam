import streamlit as st
import random
import re
import json
import os
from datetime import datetime

# --- 1. 页面配置与专属图标 ---
st.set_page_config(page_title="冰冰加油站", page_icon="🦁", layout="centered")

# --- 2. 深度美化界面 (修复隐身文字 + 浪漫粉色调) ---
st.markdown("""
    <style>
    /* 强制整体背景 */
    .stApp { background-color: #fff9fb !important; }
    
    /* 专属加油语样式 */
    .bing-cheer {
        color: #ff4b7d !important;
        font-weight: bold;
        font-size: 1.2rem;
        text-align: center;
        padding: 15px;
        background: #ffffff;
        border-radius: 15px;
        border: 2px dashed #ffb6c1;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(255,182,193,0.3);
    }
    
    /* 答题卡片：强制白底黑字 */
    .question-box {
        background-color: #ffffff !important;
        color: #1f1f1f !important;
        padding: 20px;
        border-radius: 15px;
        border-left: 8px solid #ffb6c1;
        margin-bottom: 20px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.05);
    }

    /* 选项文字：强制黑色 */
    .stRadio [data-testid="stMarkdownContainer"] p {
        color: #000000 !important;
        font-size: 1.1rem !important;
    }

    /* 覆盖所有可能变白的文字 */
    h1, h2, h3, p, span, label, .stMarkdown {
        color: #333333 !important;
    }

    /* 按钮美化 */
    .stButton button {
        width: 100%;
        border-radius: 20px;
        font-weight: bold;
        height: 3em;
        background-color: #ffb6c1 !important;
        color: white !important;
        border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 核心逻辑：解析题库 + 插入彩蛋 ---
@st.cache_data
def load_bank():
    file_name = "题库.txt"
    bank = []
    if not os.path.exists(file_name):
        return []
    
    content = ""
    for enc in ['utf-8', 'gbk', 'gb18030']:
        try:
            with open(file_name, 'r', encoding=enc) as f:
                content = f.read()
            if content.strip(): break
        except: continue
    
    # 正则解析
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
    
    # ✨ 这里就是给冰冰的彩蛋题目 ✨
    egg_question = {
        "id": "9999",
        "title": "【本场考试最重要的一题】谁是考场里最可爱、最优秀、且一定会高分通过考试的人？",
        "options": {
            "A": "黄冰同学",
            "B": "超努力的冰冰",
            "C": "最棒的冰冰🦁",
            "D": "以上全是，没得反驳！"
        },
        "answer": "D"
    }
    bank.append(egg_question)
    return bank

# --- 4. 鼓励语库 ---
ENCOURAGEMENTS = [
    "冰冰加油！你是最棒的 🦁",
    "每一题的坚持，都是冰冰在发光 🌟",
    "哇！这题也难不倒冰冰，厉害！😘",
    "坚持住，黄冰同学，终点就在前面！🚀",
    "冰冰累不累？考完带你去吃好吃的 🍦",
    "不管考多少分，冰冰在我心里都是 100 分 💖"
]

# --- 5. 状态管理 ---
if 'exam_started' not in st.session_state: st.session_state.exam_started = False
if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
if 'page' not in st.session_state: st.session_state.page = 0

bank_data = load_bank()

# --- 6. 界面流程 ---
if not st.session_state.exam_started and not st.session_state.get('show_result'):
    st.title("🦁 冰冰专属模拟考场")
    st.markdown("<div class='bing-cheer'>黄冰同学，准备好开始挑战了吗？我会一直陪着你的！✨</div>", unsafe_allow_html=True)
    
    if st.button("开始新一轮挑战 (100题)", type="primary"):
        # 随机抽99题，再把彩蛋题必填进去凑成100题
        normal_questions = random.sample([q for q in bank_data if q['id'] != "9999"], 99)
        egg_q = [q for q in bank_data if q['id'] == "9999"]
        current_exam = normal_questions + egg_q
        random.shuffle(current_exam) # 打乱顺序，让她猜不到彩蛋在哪
        
        st.session_state.current_exam = current_exam
        st.session_state.user_answers = {}
        st.session_state.page = 0
        st.session_state.exam_started = True
        st.rerun()

elif st.session_state.exam_started:
    q_idx = st.session_state.page
    q = st.session_state.current_exam[q_idx]
    
    # 动态鼓励
    cheer = random.choice(ENCOURAGEMENTS)
    st.markdown(f"<div class='bing-cheer'>✨ {cheer}</div>", unsafe_allow_html=True)
    
    st.progress((q_idx + 1) / 100)
    st.markdown(f"<div class='question-box'><b>第 {q_idx+1} 题：</b><br>{q['title']}</div>", unsafe_allow_html=True)
    
    opts = q['options']
    ans = st.radio("请选择：", [f"{k}. {v}" for k, v in opts.items()], key=f"q_{q_idx}")
    if ans: st.session_state.user_answers[q_idx] = ans[0]

    st.write("---")
    col1, col2 = st.columns(2)
    with col1:
        if q_idx > 0: st.button("⬅️ 上一题", on_click=lambda: setattr(st.session_state, 'page', st.session_state.page - 1))
    with col2:
        if q_idx < 99:
            st.button("下一题 ➡️", on_click=lambda: setattr(st.session_state, 'page', st.session_state.page + 1))
        else:
            if st.button("🏁 完成！看成绩！"):
                score = sum(1 for i, q in enumerate(st.session_state.current_exam) if st.session_state.user_answers.get(i) == q['answer'])
                st.session_state.final_score = score
                st.session_state.exam_started = False
                st.session_state.show_result = True
                st.rerun()

elif st.session_state.get('show_result'):
    s = st.session_state.final_score
    st.title("考试结束啦！")
    if s >= 60:
        st.balloons()
        st.success(f"🎉 厉害了我的冰！{s} 分！简直是天才少女！")
        st.markdown("<h3 style='text-align: center; color: #ff4b7d;'>走吧，带最优秀的黄冰同学庆祝去！🍔</h3>", unsafe_allow_html=True)
    else:
        st.snow()
        st.error(f"💔 呜呜，只有 {s} 分。没关系，冰冰不哭，咱们再试一次，你最棒了！")
    
    if st.button("再陪冰冰练一轮"):
        st.session_state.show_result = False
        st.rerun()
