import streamlit as st
import random
import re
import json
import os
from datetime import datetime

# --- 1. 页面配置 ---
st.set_page_config(page_title="冰冰加油：冲刺 2.9", page_icon="💖", layout="centered")

# --- 2. 深度样式定制 ---
st.markdown("""
    <style>
    .stApp { background-color: #fff9fb !important; }
    .bing-cheer {
        color: #ff4b7d !important; font-weight: bold; font-size: 1.1rem; text-align: center;
        padding: 12px; background: #ffffff; border-radius: 15px; border: 2px dashed #ffb6c1;
        margin-bottom: 15px; box-shadow: 0 4px 10px rgba(255,182,193,0.2);
    }
    .question-box {
        background-color: #ffffff !important; color: #333333 !important;
        padding: 20px; border-radius: 15px; border-left: 8px solid #ffb6c1; margin-bottom: 20px;
    }
    .history-card {
        padding: 10px; border-radius: 10px; background: #ffffff; 
        border: 1px solid #ffeef2; margin-bottom: 8px; font-size: 0.9rem;
    }
    /* 强制黑色文字，防止隐身 */
    .stRadio [data-testid="stMarkdownContainer"] p { color: #000000 !important; font-size: 1.1rem !important; }
    h1, h2, h3, p, span, label, .stMarkdown { color: #333333 !important; }
    .stButton button {
        width: 100%; border-radius: 20px; font-weight: bold; height: 3em;
        background-color: #ffb6c1 !important; color: white !important; border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 数据存储管理 ---
PROGRESS_FILE = "progress.json"    # 记录哪些题做对了（不再出现）
WRONG_FILE = "wrong_questions.json" # 记录错题
HISTORY_FILE = "exam_history.json"  # 记录每一场考试成绩

def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f: return json.load(f)
        except: return default
    return default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

# --- 4. 题库解析逻辑 ---
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
    # 表白彩蛋
    bank.append({"id": "BING_LOVE", "title": "【必考题】冰冰最近复习这么辛苦，考完试最想做的一件事是什么？", 
                 "options": {"A": "吃顿好的", "B": "美美睡一觉", "C": "出去旅游", "D": "以上都要，且由某人买单"}, "answer": "D"})
    return bank

# --- 5. 初始化数据 ---
all_bank = load_bank()
progress = load_json(PROGRESS_FILE, {"passed_ids": []})
wrong_data = load_json(WRONG_FILE, {})
history_data = load_json(HISTORY_FILE, [])

if 'mode' not in st.session_state: st.session_state.mode = "home"
if 'page' not in st.session_state: st.session_state.page = 0
if 'user_answers' not in st.session_state: st.session_state.user_answers = {}

# --- 6. 首页：增加历史记录展示 ---
if st.session_state.mode == "home":
    st.title("🦁 冰冰冲刺宝典")
    
    # 考试倒计时
    days_left = (datetime(2026, 2, 9) - datetime.now()).days
    st.markdown(f"<div class='bing-cheer'>黄冰同学，目前已消灭 {len(progress['passed_ids'])}/{len(all_bank)} 道题！<br>距离 2月9日 考试仅剩 {max(0, days_left)} 天，冰冰必胜！</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 开始模拟考 (100题)"):
            # 优先选没做过的
            available = [q for q in all_bank if q['id'] not in progress["passed_ids"] or q['id'] == "BING_LOVE"]
            st.session_state.current_exam = random.sample(available if len(available)>=100 else all_bank, 100)
            st.session_state.mode = "exam"; st.session_state.page = 0; st.session_state.user_answers = {}; st.rerun()
    with col2:
        if st.button(f"📖 错题复习 ({len(wrong_data)})"):
            if not wrong_data: st.balloons(); st.success("没有错题，冰冰太棒了！")
            else:
                st.session_state.current_exam = [q for q in all_bank if q['id'] in wrong_data]
                st.session_state.mode = "review"; st.session_state.page = 0; st.rerun()

    # --- 历史足迹板块 ---
    st.write("---")
    st.subheader("📊 冰冰的成长足迹 (最近10场)")
    if not history_data:
        st.write("还没有考试记录哦，冰冰快开始第一场吧！")
    else:
        for record in reversed(history_data[-10:]):
            color = "#52c41a" if record['score'] >= 60 else "#ff4b7d"
            st.markdown(f"""
            <div class='history-card'>
                📅 {record['time']} | 模式: {record['mode']} <br>
                得分: <span style='color:{color}; font-weight:bold;'>{record['score']}分</span> 
                ({record['correct']}/{record['total']}题)
            </div>
            """, unsafe_allow_html=True)

# --- 7. 考试与复习界面 ---
elif st.session_state.mode in ["exam", "review"]:
    q_idx = st.session_state.page
    exam_list = st.session_state.current_exam
    q = exam_list[q_idx]
    
    st.markdown(f"<div class='bing-cheer'>正在进行：{st.session_state.mode == 'exam' and '模拟考' or '错题攻克'} · 冰冰加油！</div>", unsafe_allow_html=True)
    st.progress((q_idx + 1) / len(exam_list))
    st.markdown(f"<div class='question-box'><b>第 {q_idx+1} / {len(exam_list)} 题：</b><br>{q['title']}</div>", unsafe_allow_html=True)
    
    if st.session_state.mode == "review": st.info(f"💡 正确答案是：{q['answer']}")

    opts = q['options']
    ans = st.radio("选择你的答案：", [f"{k}. {v}" for k, v in opts.items()], key=f"q_{q['id']}_{q_idx}")
    if ans: st.session_state.user_answers[q_idx] = ans[0]

    st.write("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        if q_idx > 0: st.button("⬅️ 上一题", on_click=lambda: setattr(st.session_state, 'page', st.session_state.page - 1))
    with c3:
        if q_idx < len(exam_list) - 1:
            st.button("下一题 ➡️", on_click=lambda: setattr(st.session_state, 'page', st.session_state.page + 1))
        else:
            if st.button("🏁 完成交卷"):
                # 计算分数并记录
                score_count = 0
                new_passed = set(progress["passed_ids"])
                for i, q_obj in enumerate(exam_list):
                    u_ans = st.session_state.user_answers.get(i)
                    if u_ans == q_obj['answer']:
                        score_count += 1
                        new_passed.add(q_obj['id'])
                        if q_obj['id'] in wrong_data: del wrong_data[q_obj['id']]
                    else:
                        wrong_data[q_obj['id']] = {"time": str(datetime.now())}
                
                # 保存所有记录
                save_json(PROGRESS_FILE, {"passed_ids": list(new_passed)})
                save_json(WRONG_FILE, wrong_data)
                
                final_score = int((score_count / len(exam_list)) * 100)
                history_data.append({
                    "time": datetime.now().strftime("%m-%d %H:%M"),
                    "mode": "模拟考" if st.session_state.mode == "exam" else "错题集",
                    "score": final_score,
                    "correct": score_count,
                    "total": len(exam_list)
                })
                save_json(HISTORY_FILE, history_data)
                
                st.session_state.final_score = final_score
                st.session_state.mode = "result"; st.rerun()

# --- 8. 结果页 ---
elif st.session_state.mode == "result":
    s = st.session_state.final_score
    st.title("考试结束啦！")
    if s >= 60:
        st.balloons(); st.success(f"🎉 冰冰真棒！考了 {s} 分！通过了！")
    else:
        st.snow(); st.error(f"💔 哎呀，得分 {s}。别灰心，错题已经帮你存进小本本了，咱们再练练！")
    
    if st.button("回首页查看记录"):
        st.session_state.mode = "home"; st.rerun()
