import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime

# =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
# Section 1: Page Configuration & Styling
# =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
st.set_page_config(
    page_title="해수면 상승과 고등학생 식생활 영향 분석",
    page_icon="🌊",
    layout="wide"
)

# Apply custom fonts and dark theme styles
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
    
    html, body, [class*="st-"], [class*="css-"] {
        font-family: 'Noto Sans KR', sans-serif;
    }
    h1 { font-size: 2.5em !important; font-weight: 700; }
    h2 { font-size: 1.75em !important; font-weight: 700; border-bottom: 2px solid #5DADE2; padding-bottom: .3em; margin-top: 2em; margin-bottom: 1em; }
    h3 { font-size: 1.25em !important; font-weight: 700; }
    .stMetric { background-color: #2E2E2E; border-radius: 10px; padding: 15px; border: 1px solid #444; }
    </style>
""", unsafe_allow_html=True)

# =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
# Section 2: Common Functions & Data Loading
# =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

def display_common_sections():
    """Display common informational sections at the bottom of each tab."""
    st.markdown("---")
    st.markdown("### 📖 데이터 출처 및 참고 자료")
    st.markdown("""
    - **해수면 상승 데이터**: Climate Change Tracker, Viva100, ESG Economy, Science Times
    - **해산물 생산량/가격**: Newsis, 연합뉴스
    - **해수온 및 어종 변화**: 경향신문, 뉴닉
    """)
    st.markdown("### 🔬 분석 방법론")
    st.markdown("""
    - **해수면 변화**: 위성 고도계 측정 및 장기 추세 분석 기반 데이터 시뮬레이션
    - **기후변화 영향**: 기온·염도 변화와 어획량 자료의 상관 분석 기반 데이터 시뮬레이션
    - **해산물 가격 동향**: 국내 주요 어종 가격 변동 통계 비교 기반 데이터 시뮬레이션
    - **청소년 식생활 영향**: 학교 급식 및 소비 패턴 사례 조사 기반 데이터 시뮬레이션
    """)
    st.markdown("### 🌍 주요 연구 결과 및 시사점")
    st.markdown("""
    1.  **데이터 분석 결과**: 한국 연안의 해수면이 지속적으로 상승하며, 이는 국내 주요 어종의 어획량 감소로 직접 이어짐.
    2.  **연쇄 효과**: 어획량 감소는 해산물 가격 상승을 유발하여 학생들의 해산물 접근성을 악화시키고, 식단 구성을 변화시킴.
    3.  **건강 문제**: 해산물 섭취 감소는 성장기 청소년의 필수 영양소 부족을 초래하여, 장기적으로 학습 능력 저하 및 건강권 문제로 확대될 수 있음.
    """)
    st.markdown("### ⚠️ 연구의 한계 및 주의사항")
    st.warning("이 대시보드의 일부 데이터는 뉴스 및 연구기관의 추정치를 기반으로 한 교육 목적의 시뮬레이션입니다. 실제 학술 연구 및 정책 활용 시에는 **NOAA, NASA, IPCC, KOSIS** 등의 공식 자료를 반드시 병행해야 합니다.")
    st.markdown("### 🌈 맺음말")
    st.markdown("""
    해수면 상승은 더 이상 바닷가 어촌만의 문제가 아닙니다.
    
    이는 곧 학교와 식탁, 그리고 청소년의 건강에 직접 연결된 현재진행형 과제입니다.
    하지만 대응 방법은 있습니다. 작은 실천(식습관 관리·에너지 절약)과 사회적 노력이 함께 모인다면, 기후 위기의 파급효과를 줄일 수 있습니다.
    
    👉 **고등학생인 지금부터라도 식생활과 환경을 연결하는 인식을 갖고 행동하는 것이 미래를 지키는 첫걸음입니다.**
    """)

@st.cache_data
def synthesize_data():
    """Generate a comprehensive set of virtual data for the dashboard."""
    datasets = {}
    current_year = datetime.now().year
    
    # 1. Korea Sea Level Data
    base_years = np.arange(1990, current_year + 1)
    national_base_rise = np.linspace(0, 107, len(base_years))
    national_values = national_base_rise + np.random.randn(len(base_years)).cumsum() * 0.5
    datasets['korea_sea_level'] = pd.DataFrame({"date": pd.to_datetime([f"{y}-01-01" for y in base_years]), "value": national_values, "year": base_years})

    # 2. Fisheries Data
    years_fish = np.arange(2010, current_year + 1)
    datasets['fish_distribution_change'] = pd.concat([
        pd.DataFrame({"year": years_fish, "어종": "명태", "어획량": np.linspace(100, 10, len(years_fish)) * np.random.uniform(0.8, 1.2, len(years_fish))}),
        pd.DataFrame({"year": years_fish, "어종": "방어", "어획량": np.linspace(30, 90, len(years_fish)) * np.random.uniform(0.8, 1.2, len(years_fish))})
    ])
    
    seafood_data = pd.DataFrame()
    trends = {'멸치': (220, 150), '오징어': (150, 40), '고등어': (180, 110), '꽃게': (30, 15), '낙지': (50, 25)}
    for name, (start, end) in trends.items():
        catch = np.linspace(start, end, len(years_fish)) * np.random.uniform(0.85, 1.15, len(years_fish))
        seafood_data = pd.concat([seafood_data, pd.DataFrame({'year': years_fish, '어종': name, '어획량 (천 톤)': np.clip(catch, 0, None)})])
    datasets['main_seafood_catch'] = seafood_data
    
    total_catch = seafood_data.groupby('year')['어획량 (천 톤)'].sum().reset_index()
    initial_catch = total_catch.iloc[0]['어획량 (천 톤)']
    total_catch['가격 지수'] = (initial_catch / total_catch['어획량 (천 톤)']) * 100 + np.random.randn(len(total_catch)) * 2
    datasets['main_seafood_economics'] = total_catch

    # 3. Student Nutrition Data
    years_nutrition = np.arange(2010, current_year + 1)
    datasets['student_nutrition'] = pd.DataFrame({
        'year': years_nutrition,
        '주간 해산물 섭취량 (g)': np.linspace(500, 350, len(years_nutrition)) * np.random.uniform(0.95, 1.05, len(years_nutrition)),
        '단백질 섭취 기여도 (%)': np.linspace(18, 15, len(years_nutrition)) * np.random.uniform(0.98, 1.02, len(years_nutrition)),
        '오메가-3 섭취 기여도 (상대치)': np.linspace(100, 75, len(years_nutrition)) * np.random.uniform(0.95, 1.05, len(years_nutrition))
    })
    return datasets

# =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
# Section 3: Main Dashboard UI
# =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
datasets = synthesize_data()
chart_template = "plotly_dark"

st.title("📑 높아지는 바다: 해수면 상승으로 식생활이 고등학생에게 미치는 영향")
st.markdown("### 📖 문제 제기")
st.markdown("최근 30년간 한국 연안의 해수면은 평균 10cm 이상 상승했습니다. 기후변화로 인한 바닷물의 온도와 염도 변화는 어획량 감소를 불러왔고, 우리가 일상적으로 접하는 해산물 가격도 꾸준히 상승하고 있습니다. 이는 단순히 어부나 어시장의 문제를 넘어, 학교 급식과 가정 식탁을 통해 학생들의 식생활에 직접 연결됩니다. 특히 성장기 청소년에게 필수적인 단백질과 오메가-3 지방산의 주요 공급원이 해산물이라는 점에서, 해수면 상승은 고등학생의 건강과 학습 능력에도 파급효과를 미칠 수 있습니다.")
st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🌍 해수면 상승 현황", 
    "🎣 수산자원 변화 분석",
    "💸 식탁 물가와 가격 변동",
    "🥗 청소년 영양 문제",
    "💡 해결 방안 및 실천"
])

with tab1:
    st.header("🌍 한반도 주변 해수면 상승 현황")
    st.sidebar.header("🌊 해수면 데이터 옵션")
    year_range_sl = st.sidebar.slider("기간 선택 (해수면)", 1990, datetime.now().year, (1990, datetime.now().year))
    smoothing_sl = st.sidebar.checkbox("추세선 표시", value=True)
    
    sl_filtered = datasets['korea_sea_level'][(datasets['korea_sea_level']['year'] >= year_range_sl[0]) & (datasets['korea_sea_level']['year'] <= year_range_sl[1])]
    
    total_rise = sl_filtered['value'].iloc[-1] - sl_filtered['value'].iloc[0]
    avg_rise_per_year = total_rise / (sl_filtered['year'].max() - sl_filtered['year'].min())
    c1, c2, c3 = st.columns(3)
    c1.metric("총 상승량", f"{total_rise:.1f} mm", help="약 10.7 cm")
    c2.metric("연평균 상승률", f"{avg_rise_per_year:.2f} mm/yr")
    c3.metric("측정 기간", f"{len(sl_filtered)}년")

    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(x=sl_filtered['date'], y=sl_filtered['value'], mode='lines+markers', name='해수면 높이', line=dict(color='#5DADE2', width=2)))
    if smoothing_sl:
        z = np.polyfit(sl_filtered['year'], sl_filtered['value'], 1)
        p = np.poly1d(z)
        fig_line.add_trace(go.Scatter(x=sl_filtered['date'], y=p(sl_filtered['year']), mode='lines', name='추세선', line=dict(color='red', width=2, dash='dash')))
    fig_line.update_layout(title="한반도 연평균 해수면 높이 변화", template=chart_template)
    st.plotly_chart(fig_line, use_container_width=True)
    display_common_sections()

with tab2:
    st.header("🎣 수산자원 변화 분석")
    st.sidebar.header("🐟 수산자원 데이터 옵션")
    year_range_fish = st.sidebar.slider("기간 선택 (수산자원)", 2010, datetime.now().year, (2010, datetime.now().year))
    seafood_options = datasets['main_seafood_catch']['어종'].unique()
    selected_seafood = st.sidebar.multiselect("주요 해산물 선택", seafood_options, default=['멸치', '오징어', '고등어'])

    fish_dist_filtered = datasets['fish_distribution_change'][(datasets['fish_distribution_change']['year'] >= year_range_fish[0]) & (datasets['fish_distribution_change']['year'] <= year_range_fish[1])]
    seafood_catch_filtered = datasets['main_seafood_catch'][(datasets['main_seafood_catch']['어종'].isin(selected_seafood)) & (datasets['main_seafood_catch']['year'] >= year_range_fish[0]) & (datasets['main_seafood_catch']['year'] <= year_range_fish[1])]
    
    st.subheader("한반도 바다의 어종 변화: 명태는 가고, 방어가 온다")
    fig_dist = px.bar(fish_dist_filtered, x='year', y='어획량', color='어종', barmode='group', title="한류성 vs 난류성 어종 어획량 비교", color_discrete_map={'명태': '#5DADE2', '방어': '#E74C3C'}, template=chart_template)
    st.plotly_chart(fig_dist, use_container_width=True)
    
    st.subheader("주요 해산물 어획량 변화 추이")
    if selected_seafood:
        fig_catch = px.line(seafood_catch_filtered, x='year', y='어획량 (천 톤)', color='어종', title="선택 해산물 연간 어획량 추이", template=chart_template, markers=True)
        st.plotly_chart(fig_catch, use_container_width=True)
    else:
        st.warning("사이드바에서 분석할 해산물을 선택해주세요.")
    display_common_sections()

with tab3:
    st.header("💸 식탁 물가와 가격 변동")
    st.sidebar.header("💹 가격 데이터 옵션")
    year_range_eco = st.sidebar.slider("기간 선택 (가격)", 2010, datetime.now().year, (2010, datetime.now().year))
    seafood_eco_filtered = datasets['main_seafood_economics'][(datasets['main_seafood_economics']['year'] >= year_range_eco[0]) & (datasets['main_seafood_economics']['year'] <= year_range_eco[1])]

    st.subheader("어획량 감소와 해산물 가격 지수 상승")
    fig_eco = go.Figure()
    fig_eco.add_trace(go.Bar(x=seafood_eco_filtered['year'], y=seafood_eco_filtered['어획량 (천 톤)'], name='주요 해산물 어획량', marker_color='#5DADE2'))
    fig_eco.add_trace(go.Scatter(x=seafood_eco_filtered['year'], y=seafood_eco_filtered['가격 지수'], name='가격 지수', yaxis='y2', mode='lines+markers', line=dict(color='#F39C12')))
    fig_eco.update_layout(title="주요 해산물 총 어획량과 가격 지수 변화", template=chart_template, yaxis2=dict(title="가격 지수 (2010년=100)", overlaying='y', side='right'), legend=dict(x=0.01, y=0.99))
    st.plotly_chart(fig_eco, use_container_width=True)
    display_common_sections()

with tab4:
    st.header("🥗 청소년 영양 문제")
    st.sidebar.header("🧑‍⚕️ 영양 데이터 옵션")
    year_range_nut = st.sidebar.slider("기간 선택 (영양)", 2010, datetime.now().year, (2010, datetime.now().year))
    nutrition_filtered = datasets['student_nutrition'][(datasets['student_nutrition']['year'] >= year_range_nut[0]) & (datasets['student_nutrition']['year'] <= year_range_nut[1])]

    st.subheader("해산물 섭취 감소가 청소년 영양에 미치는 영향")
    fig_nut = go.Figure()
    fig_nut.add_trace(go.Bar(x=nutrition_filtered['year'], y=nutrition_filtered['주간 해산물 섭취량 (g)'], name='주간 해산물 섭취량 (g)', marker_color='#2ECC71'))
    fig_nut.add_trace(go.Scatter(x=nutrition_filtered['year'], y=nutrition_filtered['단백질 섭취 기여도 (%)'], name='단백질 기여도', yaxis='y2', mode='lines+markers', line=dict(color='#E67E22')))
    fig_nut.add_trace(go.Scatter(x=nutrition_filtered['year'], y=nutrition_filtered['오메가-3 섭취 기여도 (상대치)'], name='오메가-3 기여도', yaxis='y2', mode='lines+markers', line=dict(color='#9B59B6')))
    fig_nut.update_layout(title="청소년 해산물 섭취량과 주요 영양소 기여도 변화", template=chart_template, yaxis2=dict(title="영양소 섭취 기여도 (%)", overlaying='y', side='right', range=[0, 105]), legend=dict(x=0.01, y=0.99))
    st.plotly_chart(fig_nut, use_container_width=True)
    display_common_sections()

with tab5:
    st.header("💡 해결 방안 및 실천 과제")
    st.markdown("해수면 상승은 더 이상 외면할 수 없는 우리 모두의 문제입니다. 개인, 학교, 사회 각자의 위치에서 작은 실천으로 변화를 만들 수 있습니다.")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("#### 제언 1: 개인 차원")
        st.markdown("- **해산물 대체 단백질 섭취**: 콩, 두부, 해조류 등\n- **균형 잡힌 식단**으로 성장기 영양 불균형 보완")
    with c2:
        st.warning("#### 제언 2: 학교 차원")
        st.markdown("- **기후 친화적 급식 메뉴** 활용\n- 학생 대상 **기후-식생활 교육** 강화")
    with c3:
        st.error("#### 제언 3: 사회 차원")
        st.markdown("- **해양 생태계 보전 정책** 강화\n- **지속 가능한 어업** 및 대체 식품 연구 지원")
    display_common_sections()


