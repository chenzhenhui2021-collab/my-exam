import streamlit as st
import random
import re
import json
import os
from datetime import datetime

# --- 页面配置 ---
st.set_page_config(page_title="安全生产模拟考试", page_icon="📝", layout="centered")

# --- 深度美化界面 (修复手机端文字隐身问题) ---
st.markdown("""
    <style>
    /* 强制整体背景和文字颜色，防止深色模式干扰 */
    .stApp {
        background-color: #f8f9fa !important;
    }
    
    /* 答题卡片：强制白底黑字 */
    .question-box {
        background-color: #ffffff !important;
        color: #1f1f1f !important;  /* 强制深灰色文字 */
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #1890ff;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    /* 选项文字：强制黑色 */
    .stRadio [data-testid="stMarkdownContainer"] p {
        color: #000000 !important;
        font-size: 1.15rem !important;
        line-height: 1.6;
    }

    /* 标题颜色 */
    h1, h2, h3, p, span, label {
        color: #1f1f1f !important;
    }

    /* 按钮样式保持不变 */
    .stButton button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
        background-color: #ffffff;
        color: #1f1f1f;
        border: 1px solid #d9d9d9;
    }
    
    /* 进度条文字颜色 */
    .stCaption {
        color: #595959 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 核心逻辑：严谨解析题库 ---
@st.cache_data
def load_bank():
    file_name = "题库.txt"
    if not os.path.exists(file_name):
        st.error(f"未找到文件: {file_name}")
        return []
    
    content = ""
    # 按照优先级尝试多种编码
    encodings = ['utf-8', 'gbk', 'gb18030', 'utf-16']
    for enc in encodings:
        try:
            with open(file_name, 'r', encoding=enc) as f:
                content = f.read()
            if content.strip(): # 如果读到了内容，就跳出循环
                break
        except Exception:
            continue
    
    if not content:
        st.error("题库文件读取失败，请检查文件格式或编码。")
        return []

    # 这里的正则保持不变...
    pattern = re.compile(r'(\d+)\.(.*?)(?=(?:\d+\.)|(?:\Z))', re.S)
    matches = pattern.findall(content)
    
    bank = []
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
    
    return bank

# --- 历史记录 ---
def save_history(score, passed):
    record = {"time": datetime.now().strftime("%m-%d %H:%M"), "score": score, "result": "及格" if passed else "不及格"}
    history = []
    if os.path.exists("history.json"):
        try:
            with open("history.json", "r", encoding="utf-8") as f: history = json.load(f)
        except: pass
    history.append(record)
    with open("history.json", "w", encoding="utf-8") as f: json.dump(history, f, ensure_ascii=False)

# --- 状态管理 ---
if 'exam_started' not in st.session_state: st.session_state.exam_started = False
if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
if 'page' not in st.session_state: st.session_state.page = 0

bank = load_bank()

# --- 导航逻辑 ---
def next_page(): st.session_state.page += 1
def prev_page(): st.session_state.page -= 1

# --- 页面显示 ---
if not st.session_state.exam_started and not st.session_state.get('show_result'):
    st.title("🏗️ 安全生产考核模拟")
    st.write(f"已准备好题库，共 {len(bank)} 道题目。")
    
    if st.button("开始正式考试 (随机100题)", type="primary"):
        if len(bank) >= 100:
            st.session_state.current_exam = random.sample(bank, 100)
        else:
            st.session_state.current_exam = bank.copy()
            random.shuffle(st.session_state.current_exam)
        st.session_state.user_answers = {}
        st.session_state.page = 0
        st.session_state.exam_started = True
        st.rerun()

    if os.path.exists("history.json"):
        with st.expander("📊 查看往期成绩"):
            with open("history.json", "r", encoding="utf-8") as f:
                history = json.load(f)
                for h in reversed(history[-10:]): # 只显示最近10条
                    st.write(f"`{h['time']}` — **{h['score']}分** ({h['result']})")

elif st.session_state.exam_started:
    q_idx = st.session_state.page
    exam_list = st.session_state.current_exam
    q = exam_list[q_idx]
    
    # 顶部进度
    st.caption(f"进度: {q_idx + 1} / {len(exam_list)}")
    st.progress((q_idx + 1) / len(exam_list))
    
    # 题干显示区域
    st.markdown(f"""<div class='question-box'><b>题目：</b><br>{q['title']}</div>""", unsafe_allow_html=True)
    
    # 选项显示
    opts = q['options']
    formatted_opts = [f"{k}. {v}" for k, v in opts.items()]
    
    # 获取之前选过的索引
    prev_ans = st.session_state.user_answers.get(q_idx)
    default_idx = None
    if prev_ans:
        try: default_idx = list(opts.keys()).index(prev_ans)
        except: pass

    # 选项
    ans = st.radio("选择你的答案：", formatted_opts, index=default_idx, key=f"radio_{q_idx}")
    if ans:
        st.session_state.user_answers[q_idx] = ans[0]

    st.write("---")
    
    # 底部导航按钮
    col1, col2 = st.columns(2)
    with col1:
        if q_idx > 0:
            st.button("⬅️ 上一题", on_click=prev_page)
    with col2:
        if q_idx < len(exam_list) - 1:
            st.button("下一题 ➡️", on_click=next_page)
        else:
            if st.button("🏁 提交试卷", type="primary"):
                score = sum(1 for i, q in enumerate(exam_list) if st.session_state.user_answers.get(i) == q['answer'])
                st.session_state.final_score = score
                st.session_state.exam_started = False
                st.session_state.show_result = True
                save_history(score, score >= 60)
                st.rerun()

elif st.session_state.get('show_result'):
    st.balloons() if st.session_state.final_score >= 60 else st.snow()
    st.title("考试成绩报告")
    score = st.session_state.final_score
    
    if score >= 60:
        st.success(f"🎉 恭喜！你通过了考试。\n\n得分：{score} / 100")
    else:
        st.error(f"💔 很遗憾，未及格。\n\n得分：{score} / 100")
        
    if st.button("再考一次"):
        st.session_state.show_result = False
        st.rerun()

