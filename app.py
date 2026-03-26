import streamlit as st
import pandas as pd
import datetime
import os
import json
import plotly.graph_objects as go

# ==========================================
# 1. 초기 설정 및 CSS (시인성 강화)
# ==========================================
st.set_page_config(page_title="Jayden Coffee QC", page_icon="☕", layout="wide")

st.markdown("""
<style>
    .big-font { font-size: 32px !important; font-weight: bold; color: #FF3131; }
    .setting-box { 
        background-color: #F8F9FA; 
        padding: 25px; 
        border-radius: 15px; 
        border: 4px solid #FF3131;
        text-align: center;
        margin-bottom: 25px;
    }
    .stTabs [data-baseweb="tab"] { font-size: 20px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# 파일 경로
BEANS_FILE = "jayden_beans.json"
QC_FILE = "jayden_qc_logs.csv"
BARISTAS_FILE = "jayden_baristas.json"
TODAY_SETTING_FILE = "today_selected_setting.json"

COLOR_PALETTE = ['#FF3131', '#1F77B4', '#2CA02C', '#FF7F0E', '#9467BD', '#8C564B', '#E377C2', '#17BECF']

# ==========================================
# 2. 데이터 관리 함수
# ==========================================
def load_json(file, default):
    if not os.path.exists(file):
        with open(file, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=4)
        return default
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except: return default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_qc_logs():
    if not os.path.exists(QC_FILE):
        return pd.DataFrame(columns=["날짜", "바리스타", "원두명", "도징량(g)", "추출량(g)", "추출시간(s)", "신맛", "단맛", "쓴맛", "바디감", "애프터테이스트", "코멘트"])
    try:
        df = pd.read_csv(QC_FILE)
        numeric_cols = ["도징량(g)", "추출량(g)", "추출시간(s)", "신맛", "단맛", "쓴맛", "바디감", "애프터테이스트"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame(columns=["날짜", "바리스타", "원두명", "도징량(g)", "추출량(g)", "추출시간(s)", "신맛", "단맛", "쓴맛", "바디감", "애프터테이스트", "코멘트"])

beans = load_json(BEANS_FILE, {"제이든 블렌드": {"배전도": "미디엄 다크", "가공방식": "블렌딩", "노트": "초콜릿"}})
baristas = load_json(BARISTAS_FILE, ["이반석", "신진경", "이재용"])
today_selected = load_json(TODAY_SETTING_FILE, {})

# ==========================================
# 3. 메인 화면 및 탭 구성
# ==========================================
st.markdown("### 📢 오늘의 공식 추출 가이드")
today_str = str(datetime.date.today())

if today_str in today_selected and today_selected[today_str]:
    for b_name, s_data in today_selected[today_str].items():
        st.markdown(f"""
        <div class="setting-box">
            <span style="font-size: 22px; color: #333;">🏆 {b_name} 확정 세팅</span><br>
            <span class="big-font">{s_data['dose']}g ➡️ {s_data['yield']}g ({s_data['time']}초)</span><br>
            <span style="font-size: 16px; color: #666;">채택 바리스타: {s_data['by']}</span>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("오늘 채택된 공식 세팅이 없습니다. [📊 일간 비교]에서 확정해주세요.")

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["📝 QC 작성", "📊 일간 비교", "📈 기간 통계", "⚙️ 시스템 관리"])

# 탭 1: QC 작성 (표준값 설정 없이 기본 19/38/25 적용)
with tab1:
    if not beans or not baristas:
        st.warning("⚙️ 관리 탭에서 원두와 바리스타를 등록해주세요.")
    else:
        with st.form("form_qc_entry"):
            c1, c2 = st.columns(2)
            sel_barista = c1.selectbox("바리스타", baristas)
            sel_bean = c2.selectbox("원두 선택", list(beans.keys()))
            
            # 확정 세팅이 있으면 가져오고 없으면 기본 19/38/25
            today_cfg = today_selected.get(today_str, {}).get(sel_bean, {})
            d_init = float(today_cfg.get("dose", 19.0))
            y_init = float(today_cfg.get("yield", 38.0))
            t_init = int(today_cfg.get("time", 25))

            r1, r2, r3 = st.columns(3)
            in_dose = r1.number_input("도징(g)", value=d_init, step=0.1)
            in_yield = r2.number_input("추출(g)", value=y_init, step=0.1)
            in_time = r3.number_input("시간(초)", value=t_init, step=1)
            
            st.divider()
            s1, s2 = st.columns(2)
            v_acid = s1.slider("🍋 신맛", 1, 5, 3); v_sweet = s1.slider("🍬 단맛", 1, 5, 3); v_bitter = s1.slider("🍫 쓴맛", 1, 5, 3)
            v_body = s2.slider("🥛 바디감", 1, 5, 3); v_after = s2.slider("🌬️ 후미", 1, 5, 3)
            v_comm = st.text_area("코멘트")
            
            if st.form_submit_button("✅ 기록 저장", type="primary", use_container_width=True):
                df = load_qc_logs()
                new_row = {"날짜": today_str, "바리스타": sel_barista, "원두명": sel_bean, "도징량(g)": in_dose, "추출량(g)": in_yield, "추출시간(s)": in_time, "신맛": v_acid, "단맛": v_sweet, "쓴맛": v_bitter, "바디감": v_body, "애프터테이스트": v_after, "코멘트": v_comm}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                df.to_csv(QC_FILE, index=False, encoding="utf-8-sig"); st.rerun()

# 탭 2: 일간 비교 (중복 ID 에러 방지)
with tab2:
    df_day = load_qc_logs()
    if not df_day.empty:
        f1, f2 = st.columns(2)
        t_date = f1.date_input("날짜 선택", datetime.date.today(), key="day_date")
        t_bean = f2.selectbox("원두 선택", list(df_day['원두명'].unique()), key="day_bean")
        day_df = df_day[(df_day['날짜'] == str(t_date)) & (df_day['원두명'] == t_bean)]
        
        if not day_df.empty:
            cl, cr = st.columns([3, 2])
            cats = ['신맛', '단맛', '쓴맛', '바디감', '애프터테이스트']
            with cl:
                fig_day = go.Figure()
                for i, (idx, r) in enumerate(day_df.iterrows()):
                    fig_day.add_trace(go.Scatterpolar(r=[r[c] for c in cats]+[r[cats[0]]], theta=cats+[cats[0]], fill='toself', name=r['바리스타'], line=dict(color=COLOR_PALETTE[i%8], width=3)))
                fig_day.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), height=500)
                st.plotly_chart(fig_day, use_container_width=True, key=f"plotly_day_{t_bean}")
            with cr:
                for idx, r in day_df.iterrows():
                    with st.expander(f"{r['바리스타']} ({r['추출시간(s)']}초)"):
                        if st.button("🚩 공식 채택", key=f"fix_btn_{idx}"):
                            d_key = str(t_date)
                            if d_key not in today_selected: today_selected[d_key] = {}
                            today_selected[d_key][t_bean] = {"dose": r['도징량(g)'], "yield": r['추출량(g)'], "time": r['추출시간(s)'], "by": r['바리스타']}
                            save_json(TODAY_SETTING_FILE, today_selected); st.rerun()
                        if st.button("🗑️ 삭제", key=f"del_btn_{idx}"):
                            df_day.drop(idx).to_csv(QC_FILE, index=False, encoding="utf-8-sig"); st.rerun()

# 탭 3: 기간 통계 (ValueError 에러 방지)
with tab3:
    df_stat = load_qc_logs()
    if not df_stat.empty:
        df_stat['dt'] = pd.to_datetime(df_stat['날짜']).dt.date
        dr = st.date_input("조회 기간", [datetime.date.today()-datetime.timedelta(days=7), datetime.date.today()])
        if len(dr) == 2:
            p_df = df_stat[(df_stat['dt'] >= dr[0]) & (df_stat['dt'] <= dr[1])]
            if not p_df.empty:
                p_bean = st.selectbox("분석할 원두", list(p_df['원두명'].unique()), key="sb_stat_bean")
                p_df_b = p_df[p_df['원두명'] == p_bean]
                if not p_df_b.empty:
                    m = ['신맛', '단맛', '쓴맛', '바디감', '애프터테이스트']
                    avg_df = p_df_b.groupby('바리스타')[m].mean().reset_index()
                    sl, sr = st.columns([3, 2])
                    with sl:
                        fig_st = go.Figure()
                        for i, (_, row) in enumerate(avg_df.iterrows()):
                            v = [row[c] for c in m]
                            fig_st.add_trace(go.Scatterpolar(r=v+[v[0]], theta=m+[m[0]], fill='toself', name=row['바리스타'], line=dict(color=COLOR_PALETTE[i%8], width=3)))
                        fig_st.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), height=450)
                        st.plotly_chart(fig_st, use_container_width=True, key=f"plotly_stat_{p_bean}")
                    with sr:
                        st.write("**평균 점수**")
                        st.dataframe(avg_df.set_index('바리스타').astype(float).style.format("{:.1f}"), use_container_width=True)

# 탭 4: 시스템 관리 (원두 수정 시 도징/추출/시간 입력 삭제)
with tab4:
    m1, m2 = st.columns(2)
    with m1:
        st.subheader("🧑‍🍳 바리스타 관리")
        with st.form("f_add_b", clear_on_submit=True):
            nb = st.text_input("새 바리스타")
            if st.form_submit_button("추가"):
                if nb and nb not in baristas: baristas.append(nb); save_json(BARISTAS_FILE, baristas); st.rerun()
        for b in baristas:
            c_n, c_d = st.columns([3, 1])
            c_n.write(f"• {b}")
            if c_d.button("X", key=f"db_{b}"): baristas.remove(b); save_json(BARISTAS_FILE, baristas); st.rerun()
    with m2:
        st.subheader("📦 원두 관리")
        work = st.radio("작업 상태", ["신규 등록", "정보 수정"], horizontal=True)
        target = st.selectbox("원두 선택", list(beans.keys())) if work == "정보 수정" else ""
        cur = beans.get(target, {"배전도": "미디엄", "가공방식": "워시드", "노트": ""})
        
        with st.form("f_bean"):
            nm = st.text_input("원두명", value=target if work == "정보 수정" else "")
            c_ro, c_pr = st.columns(2)
            ro = c_ro.selectbox("배전도", ["라이트", "미디엄", "다크"], index=1)
            pr = c_pr.selectbox("가공방식", ["네츄럴", "워시드", "무산소", "이스트발효", "허니", "블렌딩"], index=1)
            nt = st.text_input("커핑 노트", value=cur.get('노트', ""))
            
            # ⭐ 대표님 요청: 도징량, 추출량, 시간 설정 항목 삭제됨
            
            if st.form_submit_button("원두 정보 저장"):
                if nm:
                    beans[nm] = {"배전도": ro, "가공방식": pr, "노트": nt}
                    if work == "정보 수정" and target != nm:
                        if target in beans: del beans[target]
                    save_json(BEANS_FILE, beans); st.rerun()
                else: st.error("원두명을 입력하세요.")
        
        for bn in list(beans.keys()):
            col_bn, col_bd = st.columns([3, 1])
            col_bn.write(f"☕ {bn}")
            if col_bd.button("X", key=f"del_bn_{bn}"):
                del beans[bn]; save_json(BEANS_FILE, beans); st.rerun()