import streamlit as st
import random
import re
import json
import os
from datetime import datetime

# --- 1. 页面配置 ---
st.set_page_config(page_title="冰冰冲刺宝典", page_icon="🦁", layout="centered")

# --- 2. 样式美化 (粉色温情 + 答题卡片) ---
st.markdown("""
    <style>
    .stApp { background-color: #fff9fb !important; }
    .bing-cheer {
        color: #ff4b7d !important;
        font-weight: bold;
        font-size: 1.1rem;
        text-align: center;
        padding: 12px;
        background: #ffffff;
        border-radius: 15px;
        border: 2px dashed #ffb6c1;
        margin-bottom: 15px;
        box-shadow: 0 4px 10px rgba(255,182,193,0.2);
    }
    .question-box {
        background-color: #ffffff !important;
        color: #333333 !important;
        padding: 20px;
        border-radius: 15px;
        border-left: 8px solid #ffb6c1;
        margin-bottom: 20px;
    }
    .stRadio [data-testid="stMarkdownContainer"] p { color: #000000 !important; font-size: 1.1rem !important; }
    h1, h2, h3, p, span, label { color: #333333 !important; }
    .stButton button {
        width: 100%; border-radius: 20px; font-weight: bold; height: 3em;
        background-color: #ffb6c1 !important; color: white !important; border: none !important;
    }
    .wrong-text { color: #ff4d4f; font-weight: bold; }
    .right-text { color: #52c41a; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 数据读写逻辑 ---
PROGRESS_FILE = "progress.json"
WRONG_FILE = "wrong_questions.json"

def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f: return json.load(f)
    return default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False)

# --- 4. 解析题库 + 彩蛋 ---
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
    
    # 彩蛋题
    bank.append({"id": "BING_99", "title": "【必答题】谁是世界上最可爱且一定会通过考试的小仙女？", 
                 "options": {"A": "黄冰", "B": "冰冰", "C": "超棒的冰冰🦁", "D": "以上全是"}, "answer": "D"})
    return bank

# --- 5. 状态管理 ---
if 'mode' not in st.session_state: st.session_state.mode = "home" # home, exam, review
if 'page' not in st.session_state: st.session_state.page = 0
if 'user_answers' not in st.session_state: st.session_state.user_answers = {}

all_bank = load_bank()
progress = load_json(PROGRESS_FILE, {"passed_ids": []})
wrong_data = load_json(WRONG_FILE, {}) # {id: {"user_ans": "A", "time": "..."}}

# --- 6. 首页逻辑 ---
if st.session_state.mode == "home":
    st.title("🦁 冰冰冲刺宝典")
    passed_count = len(progress["passed_ids"])
    total_count = len(all_bank)
    
    st.markdown(f"<div class='bing-cheer'>黄冰同学，目前已消灭 {passed_count}/{total_count} 道题！<br>距离 9 号考试还有 { (datetime(2026,2,9)-datetime.now()).days } 天，加油！</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 开始模拟考试 (100道新题)"):
            # 过滤掉已经做对的题 (彩蛋题除外，每次都出)
            available = [q for q in all_bank if q['id'] not in progress["passed_ids"] or q['id'] == "BING_99"]
            if len(available) < 100:
                st.session_state.current_exam = random.sample(all_bank, 100)
            else:
                st.session_state.current_exam = random.sample(available, 100)
            st.session_state.mode = "exam"; st.session_state.page = 0; st.session_state.user_answers = {}; st.rerun()
            
    with col2:
        if st.button(f"📖 进入错题集 ({len(wrong_data)} 题)"):
            if not wrong_data: st.warning("冰冰目前还没有错题哦，太棒了！")
            else:
                st.session_state.current_exam = [q for q in all_bank if q['id'] in wrong_data]
                st.session_state.mode = "review"; st.session_state.page = 0; st.rerun()

    if st.button("🗑️ 重置所有进度 (重新开始)"):
        if st.checkbox("确认清空冰冰的所有记录吗？"):
            save_json(PROGRESS_FILE, {"passed_ids": []}); save_json(WRONG_FILE, {})
            st.rerun()

# --- 7. 考试/复习 逻辑 ---
elif st.session_state.mode in ["exam", "review"]:
    q_idx = st.session_state.page
    exam_list = st.session_state.current_exam
    q = exam_list[q_idx]
    
    cheers = ["冰冰加油！🦁", "这题肯定难不倒你 ✨", "你是最棒的，黄冰！🌟", "再坚持一下下 🚀"]
    st.markdown(f"<div class='bing-cheer'>{random.choice(cheers)}</div>", unsafe_allow_html=True)
    
    st.progress((q_idx + 1) / len(exam_list))
    st.markdown(f"<div class='question-box'><b>第 {q_idx+1} 题：</b><br>{q['title']}</div>", unsafe_allow_html=True)
    
    # 选项显示
    opts = q['options']
    formatted_opts = [f"{k}. {v}" for k, v in opts.items()]
    
    # 复习模式显示上次错误
    if st.session_state.mode == "review":
        st.info(f"💡 正确答案是：{q['answer']}")
    
    ans = st.radio("请选择：", formatted_opts, key=f"ans_{q['id']}_{q_idx}")
    if ans: st.session_state.user_answers[q_idx] = ans[0]

    st.write("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        if q_idx > 0: st.button("⬅️ 上一题", on_click=lambda: setattr(st.session_state, 'page', st.session_state.page - 1))
    with c3:
        if q_idx < len(exam_list) - 1:
            st.button("下一题 ➡️", on_click=lambda: setattr(st.session_state, 'page', st.session_state.page + 1))
        else:
            if st.button("🏁 完成提交"):
                # 交卷逻辑
                new_passed = set(progress["passed_ids"])
                score = 0
                for i, q_obj in enumerate(exam_list):
                    u_ans = st.session_state.user_answers.get(i)
                    if u_ans == q_obj['answer']:
                        score += 1
                        new_passed.add(q_obj['id'])
                        if q_obj['id'] in wrong_data: del wrong_data[q_obj['id']] # 答对了，从错题集移除
                    else:
                        wrong_data[q_obj['id']] = {"user_ans": u_ans, "time": str(datetime.now())}
                
                save_json(PROGRESS_FILE, {"passed_ids": list(new_passed)})
                save_json(WRONG_FILE, wrong_data)
                st.session_state.final_score = (score / len(exam_list)) * 100
                st.session_state.mode = "result"; st.rerun()

# --- 8. 结果页 ---
elif st.session_state.mode == "result":
    s = int(st.session_state.final_score)
    st.title("考试成绩报告")
    if s >= 60:
        st.balloons(); st.success(f"🎉 太牛了！冰冰考了 {s} 分！通过了！")
    else:
        st.snow(); st.error(f"💔 哎呀只有 {s} 分。没关系，错题已经帮你记下了，咱们练练错题！")
    
    if st.button("回首页"):
        st.session_state.mode = "home"; st.rerun()
