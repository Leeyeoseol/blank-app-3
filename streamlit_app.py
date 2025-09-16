import streamlit as st
import pandas as pd
import numpy as np
import requests
import datetime
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO
import time

# ---------------------------
# 페이지 및 폰트 설정
# ---------------------------
st.set_page_config(page_title="해수면 상승 종합 대시보드", layout="wide", initial_sidebar_state="expanded")

# Pretendard 폰트 설정 시도
try:
    import matplotlib.font_manager as fm
    import matplotlib.pyplot as plt
    import seaborn as sns
    fm.fontManager.addfont("./fonts/Pretendard-Bold.ttf")
    plt.rc('font', family='Pretendard')
    sns.set(font="Pretendard")
except Exception:
    pass

# ===========================
# 사이드바: 시나리오 설정
# ===========================
st.sidebar.header("⚙️ 미래 시나리오 설정")
scenario = st.sidebar.radio(
    "기후변화 시나리오를 선택하세요:",
    ('현 추세 유지 (RCP 4.5)', '상황 악화 (RCP 8.5)', '개선 노력 (RCP 2.6)'),
    help="선택한 시나리오에 따라 국내 데이터 및 미래 예측이 변경됩니다."
)

scenario_multipliers = {
    '현 추세 유지 (RCP 4.5)': {'sea': 1.0, 'warming': 1.0, 'future': 1.0},
    '상황 악화 (RCP 8.5)': {'sea': 1.5, 'warming': 1.5, 'future': 1.8},
    '개선 노력 (RCP 2.6)': {'sea': 0.7, 'warming': 0.6, 'future': 0.5}
}
multiplier = scenario_multipliers[scenario]


# ===========================
# 대시보드 제목 및 소개
# ===========================
st.title("🌊 높아지는 바다, 우리 식탁의 미래는?")
st.markdown("""
본 대시보드는 해수면 상승이라는 전 지구적 현상을 데이터로 분석하고, 이것이 한국의 수산업과 식생활에 미치는 영향을 다각도로 조명합니다.
**사이드바에서 미래 시나리오를 선택**하여 우리의 선택이 가져올 변화를 직접 확인해 보세요.
""")

with st.expander("📑 보고서 핵심 내용 살펴보기"):
    st.markdown("""
    #### 문제 제기
    최근 30년간 한국 연안의 해수면은 평균 10cm 이상 상승했습니다. 기후변화로 인해 바닷물의 온도가 변하면서 어획량이 감소하고, 우리가 일상적으로 접하는 수산물의 가격도 꾸준히 오르고 있습니다. 이러한 현상은 단순히 어업계의 문제가 아니라, 매일의 식생활과 건강에 직결되는 문제입니다.

    #### 변화하는 밥상
    경향신문 보도에 따르면, 한반도 주변 해수온은 전 지구 평균보다 2배 빠른 속도로 상승하고 있습니다. 그 결과, ‘명태는 사라지고 방어가 늘어났다’는 기사처럼 한국인의 밥상 구성이 바뀌고 있으며, 이는 청소년의 영양 불균형으로까지 이어질 수 있습니다.
    """)

# ===========================
# 1. 전 세계 해수면 변화 (Global View)
# ===========================
st.header("🌍 전 세계는 지금: 해수면 상승 현황")

@st.cache_data(ttl=3600)
def load_public_sea_level_data():
    """
    NOAA: 전 세계 평균 해수면 데이터 불러오기 (출처: https://www.ncei.noaa.gov/access/monitoring/data/sea-level-rise/gmsl/)
    """
    data_url = "https://www.star.nesdis.noaa.gov/sod/lsa/SeaLevelRise/slr/slr_sla_gbl_free_txj1j2_90.csv"
    try:
        r = requests.get(data_url, timeout=10)
        if r.status_code == 200:
            csv_data = r.text
            data_io = StringIO('\n'.join(csv_data.splitlines()[5:]))
            df = pd.read_csv(data_io, header=None, names=['year', 'altimeter_type', 'num_observations', 'num_weighted_obs', 'gmsl_variation_mm', 'gmsl_variation_sd', 'gmsl_variation_sm_mm', 'gmsl_variation_sm_sd', 'gmsl_GIA_mm', 'gmsl_GIA_sd', 'gmsl_GIA_sm_mm', 'gmsl_GIA_sm_sd'])
            df['date'] = pd.to_datetime(df['year'], format='%Y', errors='coerce')
            df = df[['date', 'gmsl_GIA_sm_mm']].rename(columns={"gmsl_GIA_sm_mm": "sea_level_mm"})
            df = df.dropna(subset=["date", "sea_level_mm"])
            df = df[df['date'].dt.date < datetime.date.today()].copy()
            first_value = df.loc[df['date'].idxmin(), 'sea_level_mm']
            df['sea_level_mm'] = df['sea_level_mm'] - first_value
            return df.sort_values("date").reset_index(drop=True)
    except Exception as e:
        st.warning(f"⚠️ 공식 데이터 로드 실패 ({e}). 예시 데이터를 사용합니다.")
    
    years = list(range(1993, datetime.datetime.now().year + 1))
    values = np.linspace(0, (len(years) - 1) * 3.4, len(years))
    return pd.DataFrame({"date": pd.to_datetime([f"{y}-01-01" for y in years]), "sea_level_mm": values})

df_public = load_public_sea_level_data()
last_data_point = df_public.iloc[-1]
total_rise = last_data_point['sea_level_mm']
total_years = last_data_point['date'].year - df_public.iloc[0]['date'].year
avg_annual_rise = total_rise / total_years

col1, col2, col3 = st.columns(3)
col1.metric("최근 측정 연도", f"{last_data_point['date'].year}년")
col2.metric("1993년 대비 총 상승량", f"{total_rise:.2f} mm")
col3.metric("연평균 상승량", f"{avg_annual_rise:.2f} mm/year", "가속화 추세")

fig_public = px.area(df_public, x="date", y="sea_level_mm", title="전 세계 평균 해수면 상승 추이 (1993년 기준)", labels={"date":"연도","sea_level_mm":"해수면 상승량 (mm)"}, markers=True)
st.plotly_chart(fig_public, use_container_width=True)

# ===========================
# 2. 한국의 바다와 식탁 변화 (Korea Focus)
# ===========================
st.header(f"🇰🇷 한반도에 미치는 영향: <{scenario.split(' ')[0]}> 시나리오")

# --- 시나리오 기반 가상 데이터 생성 ---
base_year = 1990
num_years = datetime.datetime.now().year - base_year + 1
user_dates = pd.to_datetime(pd.date_range(start=f"{base_year}-01-01", periods=num_years, freq="Y"))

sea_level_kr = np.linspace(0, 107 * (num_years / 35), num_years) * multiplier['sea']
fish_production = 100 - (np.linspace(0, 25 * (num_years / 35), num_years) * multiplier['warming']) + np.random.randn(num_years) * 3
fish_price = 100 + (np.linspace(0, 50 * (num_years / 35), num_years) * multiplier['warming']) + np.random.randn(num_years) * 5

df_user = pd.DataFrame({"date": user_dates, "sea_level_mm": sea_level_kr, "fish_production_index": fish_production, "fish_price_index": fish_price})

# --- 주요 어종 변화 시뮬레이션 ---
st.subheader("🐟 우리 식탁의 단골 생선, 어떻게 변할까?")
years_arr = df_user['date'].dt.year
warming_factor = np.linspace(0, 1, len(years_arr)) * multiplier['warming']
df_fish = pd.DataFrame({
    '연도': np.tile(years_arr, 3),
    '어종': ['명태 (한류성)'] * len(years_arr) + ['방어 (난류성)'] * len(years_arr) + ['꽃게'] * len(years_arr),
    '어획량 지수': np.clip(np.concatenate([
        100 - (warming_factor * 80 + np.random.randn(len(years_arr)) * 5),
        100 + (warming_factor * 50 + np.random.randn(len(years_arr)) * 5),
        100 - (warming_factor * 20 + np.sin(years_arr / 3) * 10 + np.random.randn(len(years_arr)) * 5)
    ]), 0, 200) # 0 미만, 200 초과 값 방지
})
fig_fish = px.line(df_fish, x='연도', y='어획량 지수', color='어종', title='주요 어종 어획량 변화 시뮬레이션 (1990년=100)', markers=True)
st.plotly_chart(fig_fish, use_container_width=True)

# ===========================
# 3. 미래 전망 및 지역별 영향
# ===========================
st.header("🔮 미래 전망과 지역별 영향")

# --- 시나리오 기반 미래 예측 ---
st.subheader(f"<{scenario.split(' ')[0]}> 시나리오에 따른 미래 해수면 예측")
projection_years = 50
future_dates = pd.date_range(start=last_data_point['date'], periods=projection_years + 1, freq='Y')
df_future = pd.DataFrame({'date': future_dates})

for sc, mult in scenario_multipliers.items():
    projected_rise = [last_data_point['sea_level_mm'] + avg_annual_rise * mult['future'] * i for i in range(projection_years + 1)]
    df_future[sc] = projected_rise

fig_future = go.Figure()
fig_future.add_trace(go.Scatter(x=df_public['date'], y=df_public['sea_level_mm'], name='관측 데이터', mode='lines', line=dict(color='black', width=3)))
for sc in scenario_multipliers:
    fig_future.add_trace(go.Scatter(
        x=df_future['date'], y=df_future[sc], name=sc.split(' (')[0], 
        line=dict(dash='dash', width=(4 if sc == scenario else 2)),
        visible=(True if sc == scenario else 'legendonly'),
        opacity=(1.0 if sc == scenario else 0.5)
    ))
fig_future.update_layout(title=f'시나리오별 전 세계 해수면 상승 예측', xaxis_title='연도', yaxis_title='해수면 상승량 (mm, 1993년 기준)', legend_title_text='시나리오')
st.plotly_chart(fig_future, use_container_width=True)

# --- 지도 시각화 ---
st.subheader("연안 지역별 예측 해수면 상승량")
selected_year = st.slider("지도 연도 선택", min_value=1990, max_value=2050, value=datetime.datetime.now().year, step=1)
map_sea_level = np.linspace(0, 107 * ((2050-1990+1) / 35), 2051-1990+1) * multiplier['sea']
coords = {"인천": {"lat": 37.4563, "lon": 126.7052}, "부산": {"lat": 35.1796, "lon": 129.0756}, "목포": {"lat": 34.8118, "lon": 126.3922}, "강릉": {"lat": 37.7519, "lon": 128.8761}, "제주": {"lat": 33.4996, "lon": 126.5312}}
base_level = map_sea_level[selected_year - 1990]
map_data = [{"city": city, "lat": c["lat"], "lon": c["lon"], "sea_level_mm": max(0, base_level + np.random.uniform(-5, 5))} for city, c in coords.items()]

fig_map = px.scatter_mapbox(pd.DataFrame(map_data), lat="lat", lon="lon", color="sea_level_mm", size="sea_level_mm",
    hover_name="city", hover_data={"sea_level_mm": ":.2f mm"}, color_continuous_scale=px.colors.sequential.OrRd,
    size_max=30, zoom=5.5, mapbox_style="carto-positron", title=f"[{scenario.split(' ')[0]}] {selected_year}년 예측 해수면 상승량")
fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, legend_title_text='상승량(mm)')
st.plotly_chart(fig_map, use_container_width=True)

# ===========================
# 4. 해결 방안 및 맺음말
# ===========================
st.header("💡 우리는 무엇을 할 수 있을까요?")
col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("🙋‍♀️ 개인")
    st.markdown("- **육류 소비 줄이기**: 탄소 배출이 많은 육류 대신 채소, 콩, 해조류 등 지속가능한 단백질원 섭취 늘리기\n- **에너지 절약**: 불필요한 전등 끄기, 대중교통 이용 등 일상 속 에너지 소비 줄이기\n- **기후변화에 관심 갖기**: 관련 뉴스나 보고서를 찾아보며 문제의 심각성을 인지하기")
with col2:
    st.subheader("🏫 학교/단체")
    st.markdown("- **기후 친화적 급식**: 로컬푸드, 제철 식재료를 활용하여 탄소 발자국이 적은 급식 메뉴 개발\n- **기후변화 교육**: 데이터 기반의 체계적인 교육을 통해 학생들이 문제 해결의 주체로 성장하도록 돕기\n- **캠페인 활동**: '잔반 없는 날', '에너지 절약 주간' 등 공동체 캠페인 전개")
with col3:
    st.subheader("🏛️ 정부/사회")
    st.markdown("- **해양생태계 보전**: 연안 습지 보호, 인공어초 설치 등 해양생태계 회복 정책 강화\n- **지속가능한 어업 지원**: 친환경 어업 기술 개발 지원 및 어업 규제 강화\n- **신재생에너지 전환**: 화석연료 의존도를 낮추고 태양광, 풍력 등 신재생에너지 비중 확대")

st.markdown("---")
st.success("""
**맺음말**: 해수면 상승은 더 이상 먼 미래나 바닷가만의 문제가 아닙니다. 오늘 우리가 먹는 수산물부터 미래 세대의 식생활까지, 우리 삶 전반에 영향을 미치는 현재진행형 과제입니다. **데이터를 통해 현실을 직시하고, 지속 가능한 미래를 위한 지혜로운 해결책을 함께 모색해야 할 때입니다.**
""")

