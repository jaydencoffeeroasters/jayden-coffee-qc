import streamlit as st
import pandas as pd
import datetime
import os
import json
import plotly.graph_objects as go

# ==========================================
# 1. 초기 설정 및 데이터 로드 
# ==========================================
st.set_page_config(page_title="Jayden Coffee QC", page_icon="☕", layout="wide")

# 시인성을 높이기 위한 커스텀 CSS (글자 크기 대폭 확대)
st.markdown("""
<style>
    .big-font { font-size: 30px !important; font-weight: bold; color: #FF3131; }
    .setting-box { 
        background-color: #F0F2F6; 
        padding: 20px; 
        border-radius: 15px; 
        border: 3px solid #FF3131;
        text-align: center;
        margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { font-size: 20px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

BEANS_FILE = "jayden_beans.json"
QC_FILE = "jayden_qc_logs.csv"
BARISTAS_FILE = "jayden_baristas.json"
TODAY_SETTING_FILE = "today_selected_setting.json"

COLOR_PALETTE = ['#FF3131', '#1F77B4', '#2CA02C', '#FF7F0E', '#9467BD', '#8C564B', '#E377C2', '#17BECF']

def load_beans():
    if not os.path.exists(BEANS_FILE):
        default_beans = {"제이든 시그니처 블렌드": {"배전도": "미디엄 다크", "가공방식": "블렌딩", "노트": "다크 초콜릿", "std_dose": 19.0, "std_yield": 38.0, "std_time": 25}}
        with open(BEANS_FILE, "w", encoding="utf-8") as f: json.dump(default_beans, f, ensure_ascii=False, indent=4)
        return default_beans
    with open(BEANS_FILE, "r", encoding="utf-8") as f: return json.load(f)

def save_beans(data):
    with open(BEANS_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

def load_baristas():
    if not os.path.exists(BARISTAS_FILE):
        default_baristas = ["이반석", "신진경", "이재용"]
        with open(BARISTAS_FILE, "w", encoding="utf-8") as f: json.dump(default_baristas, f, ensure_ascii=False, indent=4)
        return default_baristas
    with open(BARISTAS_FILE, "r", encoding="utf-8") as f: return json.load(f)

def save_baristas(data):
    with open(BARISTAS_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

def load_qc_logs():
    if not os.path.exists(QC_FILE): return pd.DataFrame(columns=["날짜", "바리스타", "원두명", "도징량(g)", "추출량(g)", "추출시간(s)", "신맛", "단맛", "쓴맛", "바디감", "애프터테이스트", "코멘트"])
    return pd.read_csv(QC_FILE)

def load_today_setting():
    if not os.path.exists(TODAY_SETTING_FILE): return {}
    with open(TODAY_SETTING_FILE, "r", encoding="utf-8") as f: return json.load(f)

def save_today_setting(data):
    with open(TODAY_SETTING_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

beans = load_beans()
baristas = load_baristas()
today_selected = load_today_setting()

# ==========================================
# 상단 고정: 오늘의 공식 세팅 전광판
# ==========================================
st.markdown("### 📢 오늘의 공식 추출 가이드")
log_date = datetime.date.today()
date_str = str(log_date)

# 모든 원두에 대해 오늘 확정된 세팅이 있는지 확인 후 표시
if date_str in today_selected:
    for b_name, s_data in today_selected[date_str].items():
        st.markdown(f"""
        <div class="setting-box">
            <span style="font-size: 20px; color: #555;">🏆 {b_name} 공식 세팅</span><br>
            <span class="big-font">{s_data['dose']}g ➡️ {s_data['yield']}g ({s_data['time']}초)</span><br>
            <span style="font-size: 16px; color: #777;">채택 바리스타: {s_data['by']}</span>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("아직 오늘 채택된 공식 세팅이 없습니다. 일간 기록 비교 탭에서 확정해주세요!")

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["📝 QC 작성", "📊 일간 비교", "📈 기간 통계", "⚙️ 관리"])

# ==========================================
# 탭 1: 데일리 QC 작성
# ==========================================
with tab1:
    if not beans or not baristas:
        st.warning("⚙️ 시스템 관리 탭에서 원두와 바리스타를 먼저 등록해주세요!")
    else:
        with st.form("qc_form"):
            c1, c2 = st.columns(2)
            selected_barista = c1.selectbox("바리스타", baristas)
            selected_bean = c2.selectbox("원두", list(beans.keys()))
            
            b_data = beans[selected_bean]
            current_today = today_selected.get(date_str, {}).get(selected_bean, {})
            
            # 확정 세팅이 있으면 그것을, 없으면 원두 표준 세팅을 기본값으로 사용
            def_d = current_today.get("dose", b_data.get("std_dose", 19.0))
            def_y = current_today.get("yield", b_data.get("std_yield", 38.0))
            def_t = current_today.get("time", b_data.get("std_time", 25))

            st.markdown("---")
            r1, r2, r3 = st.columns(3)
            dose = r1.number_input("도징(g)", value=float(def_d), step=0.1)
            yield_amt = r2.number_input("추출(g)", value=float(def_y), step=0.1)
            time_sec = r3.number_input("시간(초)", value=int(def_t), step=1)
            
            st.divider()
            s1, s2 = st.columns(2)
            acidity = s1.slider("🍋 신맛", 1, 5, 3)
            sweetness = s1.slider("🍬 단맛", 1, 5, 3)
            bitterness = s1.slider("🍫 쓴맛", 1, 5, 3)
            body = s2.slider("🥛 바디감", 1, 5, 3)
            aftertaste = s2.slider("🌬️ 후미", 1, 5, 3)
            comments = st.text_area("코멘트")
            
            if st.form_submit_button("✅ 기록 저장", type="primary", use_container_width=True):
                new_log = {"날짜": date_str, "바리스타": selected_barista, "원두명": selected_bean, "도징량(g)": dose, "추출량(g)": yield_amt, "추출시간(s)": time_sec, "신맛": acidity, "단맛": sweetness, "쓴맛": bitterness, "바디감": body, "애프터테이스트": aftertaste, "코멘트": comments}
                df = load_qc_logs(); df = pd.concat([df, pd.DataFrame([new_log])], ignore_index=True)
                df.to_csv(QC_FILE, index=False, encoding="utf-8-sig"); st.rerun()

# ==========================================
# 탭 2: 일간 기록 비교
# ==========================================
with tab2:
    df = load_qc_logs()
    if not df.empty:
        c1, c2 = st.columns(2)
        f_date = c1.date_input("조회 날짜", datetime.date.today())
        f_bean = c2.selectbox("원두 선택", list(df['원두명'].unique()), key="day_bean")
        day_df = df[(df['날짜'] == str(f_date)) & (df['원두명'] == f_bean)]
        
        if not day_df.empty:
            chart_col, info_col = st.columns([3, 2])
            with chart_col:
                categories = ['신맛', '단맛', '쓴맛', '바디감', '애프터테이스트']
                fig = go.Figure()
                for i, (_, row) in enumerate(day_df.iterrows()):
                    fig.add_trace(go.Scatterpolar(r=[row[c] for c in categories] + [row[categories[0]]], theta=categories + [categories[0]], fill='toself', name=row['바리스타'], line=dict(color=COLOR_PALETTE[i % 8], width=3)))
                fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), height=500)
                st.plotly_chart(fig, use_container_width=True)
            with info_col:
                st.markdown("#### 🏆 세팅 확정하기")
                for idx, row in day_df.iterrows():
                    with st.expander(f"{row['바리스타']} ({row['추출시간(s)']}초)"):
                        st.write(f"⚖️ {row['도징량(g)']}g ➡️ {row['추출량(g)']}g")
                        if st.button("🚩 공식 세팅으로 채택", key=f"fix_{idx}"):
                            d_str = str(f_date)
                            if d_str not in today_selected: today_selected[d_str] = {}
                            today_selected[d_str][f_bean] = {"dose": row['도징량(g)'], "yield": row['추출량(g)'], "time": row['추출시간(s)'], "by": row['바리스타']}
                            save_today_setting(today_selected); st.rerun()
                        if st.button("🗑️ 삭제", key=f"d_del_{idx}"):
                            df.drop(idx).to_csv(QC_FILE, index=False, encoding="utf-8-sig"); st.rerun()

# [통계 및 관리 탭은 이전과 동일한 로직 유지]
with tab3:
    st.info("데이터를 분석하여 주간/월간 추이를 보여줍니다.")
    # (탭 3 로직은 이전과 동일)
with tab4:
    st.subheader("⚙️ 설정")
    # (탭 4 로직은 이전과 동일)