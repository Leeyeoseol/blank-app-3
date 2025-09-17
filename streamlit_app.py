import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.express as px
import plotly.graph_objects as go
import requests
import json

# =====================================================================================
# 1. 페이지 및 폰트 설정
# =====================================================================================
st.set_page_config(
    page_title="기후변화 국내 영향 대시보드",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Pretendard 폰트 적용 시도
try:
    import matplotlib.font_manager as fm
    import matplotlib.pyplot as plt
    font_path = "./fonts/Pretendard-Bold.ttf"
    fm.fontManager.addfont(font_path)
    plt.rc('font', family='Pretendard')
    st.markdown(f"""
        <style>
        @font-face {{
            font-family: 'Pretendard';
            src: url('{font_path}') format('truetype');
        }}
        html, body, [class*="st-"], [class*="css-"] {{ font-family: 'Pretendard', sans-serif; }}
        </style>""", unsafe_allow_html=True)
except Exception:
    pass

# =====================================================================================
# 2. 데이터 합성 및 대시보드 구현
# =====================================================================================

@st.cache_data
def synthesize_user_data():
    """프롬프트 입력을 기반으로 데이터프레임을 합성합니다."""
    datasets = {}
    current_year = datetime.datetime.now().year

    # 1. 한국 해수면 상승 데이터
    years_kr = np.arange(1990, current_year + 1)
    base_rise = np.linspace(0, (len(years_kr) - 1) * 3.05, len(years_kr))
    df_kr_sea = pd.DataFrame({"date": pd.to_datetime([f"{y}-01-01" for y in years_kr]), "value": base_rise + np.random.randn(len(years_kr)).cumsum() * 0.5, "year": years_kr})
    datasets['korea_sea_level'] = df_kr_sea

    # 2. 어종 변화 (명태 vs 방어) 데이터
    years_fish = np.arange(2015, current_year + 1)
    df_fish = pd.DataFrame({"year": years_fish, "어종": "명태", "어획량": np.linspace(100, 10, len(years_fish)) * np.random.uniform(0.8, 1.2, len(years_fish))})
    df_fish = pd.concat([df_fish, pd.DataFrame({"year": years_fish, "어종": "방어", "어획량": np.linspace(30, 90, len(years_fish)) * np.random.uniform(0.8, 1.2, len(years_fish))})])
    datasets['fish_change'] = df_fish

    # 3. 낙지 어획량과 가격 변화 데이터
    years_oct = np.arange(2018, current_year + 1)
    catch = np.linspace(120, 50, len(years_oct)) * np.random.uniform(0.9, 1.1, len(years_oct))
    price = 1 / catch * 5000 + np.random.randn(len(years_oct)) * 10
    df_octopus = pd.DataFrame({"date": pd.to_datetime([f"{y}-01-01" for y in years_oct]), "어획량 (톤)": catch, "평균 가격 (원)": price, "year": years_oct})
    datasets['octopus_economics'] = df_octopus
    
    # 4. 지도 시각화를 위한 지역별 데이터
    map_data = {
        'province': ['Seoul', 'Busan', 'Daegu', 'Incheon', 'Gwangju', 'Daejeon', 'Ulsan', 'Gyeonggi-do', 'Gangwon-do', 'Chungcheongbuk-do', 'Chungcheongnam-do', 'Jeollabuk-do', 'Jeollanam-do', 'Gyeongsangbuk-do', 'Gyeongsangnam-do', 'Jeju-do'],
        'name_kor': ['서울특별시', '부산광역시', '대구광역시', '인천광역시', '광주광역시', '대전광역시', '울산광역시', '경기도', '강원도', '충청북도', '충청남도', '전라북도', '전라남도', '경상북도', '경상남도', '제주특별자치도'],
        '해수면 상승 (cm)': [9.5, 12.1, 10.0, 11.2, 10.2, 9.8, 11.8, 10.8, 9.8, 9.2, 11.0, 10.7, 10.5, 11.2, 11.5, 12.5],
        '주요 어업 영향': ['내륙', '고수온 양식업 피해', '내륙', '서해안 꽃게 어획량 급감', '내륙', '내륙', '고수온 및 어종 변화', '해안선 침식', '동해안 명태 어장 소실', '내륙', '서해안 어업 타격', '새만금 연안 생태계 변화', '서남해안 수산자원 변동', '동해안 오징어 어획량 감소', '남해안 어종 변화', '아열대성 어종 출현 증가']
    }
    datasets['regional_impact'] = pd.DataFrame(map_data)

    # 5. 주요 수산물 7종 어획량 데이터
    years_detail = np.arange(2010, current_year + 1)
    df_seafood = pd.DataFrame()
    
    seafood_trends = {
        '명태': np.linspace(80, 5, len(years_detail)) * np.random.uniform(0.7, 1.3, len(years_detail)),
        '오징어': np.sin(np.linspace(0, 5*np.pi, len(years_detail)))*20 + np.linspace(70, 25, len(years_detail)),
        '꽃게': np.sin(np.linspace(0, 8*np.pi, len(years_detail)))*5 + 20,
        '낙지': np.linspace(40, 20, len(years_detail)) * np.random.uniform(0.8, 1.2, len(years_detail)),
        '멸치': np.sin(np.linspace(0, 10*np.pi, len(years_detail)))*30 + np.linspace(220, 180, len(years_detail)),
        '고등어': np.sin(np.linspace(0, 6*np.pi, len(years_detail)))*25 + 150,
        '새우': np.linspace(50, 75, len(years_detail)) * np.random.uniform(0.9, 1.1, len(years_detail))
    }
    if 2024 in years_detail:
        crab_idx_2024 = list(years_detail).index(2024)
        crab_idx_start = list(years_detail).index(2019)
        min_val = seafood_trends['꽃게'][crab_idx_start:crab_idx_2024+1].min()
        seafood_trends['꽃게'][crab_idx_2024] = min_val * 0.9

    for name, data in seafood_trends.items():
        temp_df = pd.DataFrame({'year': years_detail, '어종': name, '어획량 (천 톤)': np.clip(data, 0, None)})
        df_seafood = pd.concat([df_seafood, temp_df])
        
    datasets['detailed_catch'] = df_seafood

    return datasets

# --- 대한민국 지도 GeoJSON 로드 ---
@st.cache_data
def load_korea_geojson():
    url = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2018/json/skorea-provinces-2018-geo.json"
    response = requests.get(url)
    return response.json()

# --- 대시보드 타이틀 ---
st.title("🗺️ 기후변화가 국내 해양 생태계에 미치는 영향")
st.markdown("---")
st.info("이 대시보드는 제공된 뉴스 기사 및 연구 자료를 바탕으로 구성한 **가상 데이터**를 시각화합니다.")

# --- 데이터 및 GeoJSON 로드 ---
datasets = synthesize_user_data()
korea_geojson = load_korea_geojson()
df_sea_level = datasets['korea_sea_level']; df_fish_change = datasets['fish_change']
df_octopus = datasets['octopus_economics']; df_regional = datasets['regional_impact']
df_detailed_catch = datasets['detailed_catch']

# --- 사이드바 옵션 ---
with st.sidebar:
    st.header("⚙️ 표시 옵션")
    min_year, max_year = df_sea_level['year'].min(), df_sea_level['year'].max()
    selected_years = st.slider("분석 연도 범위 선택", min_year, max_year, (2015, max_year))

# --- 데이터 필터링 ---
sea_level_filtered = df_sea_level[(df_sea_level['year'] >= selected_years[0]) & (df_sea_level['year'] <= selected_years[1])]
fish_change_filtered = df_fish_change[(df_fish_change['year'] >= selected_years[0]) & (df_fish_change['year'] <= selected_years[1])]
octopus_filtered = df_octopus[(df_octopus['year'] >= selected_years[0]) & (df_octopus['year'] <= selected_years[1])]
detailed_catch_filtered = df_detailed_catch[(df_detailed_catch['year'] >= selected_years[0]) & (df_detailed_catch['year'] <= selected_years[1])]

# --- 대시보드 UI (탭) ---
tabs = ["지역 및 전체 변화", "주요 어종 변화", "수산물 가격 변동", "주요 수산물 어획량"]
tab1, tab2, tab3, tab4 = st.tabs(tabs)

with tab1:
    st.subheader("📍 국내 시/도별 해수면 상승 영향")
    fig_map = px.choropleth_mapbox(df_regional, geojson=korea_geojson, locations='province', featureidkey="properties.name_eng", color='해수면 상승 (cm)', color_continuous_scale="Blues", mapbox_style="carto-positron", zoom=5.5, center={"lat": 36.3, "lon": 127.8}, opacity=0.6, hover_name='name_kor', hover_data={'주요 어업 영향': True, 'province': False})
    fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, title_text="시/도별 누적 해수면 상승 및 어업 영향 (35년 누적 가상 데이터)")
    st.plotly_chart(fig_map, use_container_width=True)

    st.markdown("---") # 구분선 추가
    
    st.subheader("📈 한반도 주변 해수면 상승 추이")
    if not sea_level_filtered.empty:
        c1, c2 = st.columns(2); c1.metric("🌊 35년간 총 상승량 (1990~2024)", "10.7 cm"); c2.metric("📊 연평균 상승률", "약 3.05 mm/yr")
        fig_line = px.line(sea_level_filtered, x='date', y='value', title=f"{selected_years[0]}년-{selected_years[1]}년 한반도 연평균 해수면 높이 변화", labels={'date': '연도', 'value': '상대적 높이 (mm)'}, template="plotly_white")
        st.plotly_chart(fig_line, use_container_width=True)
        st.download_button("📥 데이터 다운로드", sea_level_filtered.to_csv(index=False, encoding='utf-8-sig'), "korea_sea_level.csv", key="sl")
    else: st.warning("선택된 연도 범위에 데이터가 없습니다.")

with tab2:
    st.subheader("🎣 명태는 가고, 방어가 온다?")
    if not fish_change_filtered.empty:
        fig = px.bar(fish_change_filtered, x='year', y='어획량', color='어종', barmode='group', title=f"{selected_years[0]}년-{selected_years[1]}년 주요 어종 연간 어획량 변화 (가상)", labels={'year': '연도', '어획량': '어획량 (상대치)'}, color_discrete_map={'명태': '#3498db', '방어': '#e74c3c'}, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
        st.download_button("📥 데이터 다운로드", fish_change_filtered.to_csv(index=False, encoding='utf-8-sig'), "fish_change.csv", key="fc")
    else: st.warning("선택된 연도 범위에 데이터가 없습니다.")

with tab3:
    st.subheader("🐙 어획량 감소와 낙지 가격의 상관관계")
    if not octopus_filtered.empty:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=octopus_filtered['date'], y=octopus_filtered['어획량 (톤)'], name='어획량', yaxis='y1', marker_color='#3498db'))
        fig.add_trace(go.Scatter(x=octopus_filtered['date'], y=octopus_filtered['평균 가격 (원)'], name='평균 가격', yaxis='y2', mode='lines+markers', line=dict(color='#e74c3c')))
        fig.update_layout(title_text=f"{selected_years[0]}년-{selected_years[1]}년 낙지 어획량과 평균 가격 변화", template="plotly_white", xaxis_title="연도", yaxis=dict(title="어획량 (톤)"), yaxis2=dict(title="평균 가격 (원)", overlaying='y', side='right'), legend=dict(x=0.05, y=1.15, orientation='h'))
        st.plotly_chart(fig, use_container_width=True)
        st.download_button("📥 데이터 다운로드", octopus_filtered.to_csv(index=False, encoding='utf-8-sig'), "octopus_economics.csv", key="oe")
    else: st.warning("선택된 연도 범위에 데이터가 없습니다.")

with tab4:
    st.subheader("🦑 주요 수산물 어획량 변화 추이")
    if not detailed_catch_filtered.empty:
        fig = px.line(
            detailed_catch_filtered, 
            x='year', 
            y='어획량 (천 톤)', 
            color='어종',
            title=f"{selected_years[0]}년-{selected_years[1]}년 주요 수산물 어획량 추이",
            labels={'year': '연도', '어획량 (천 톤)': '어획량 (천 톤)', '어종': '수산물'},
            markers=True,
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.download_button("📥 데이터 다운로드", detailed_catch_filtered.to_csv(index=False, encoding='utf-8-sig'), "detailed_catch.csv", key="dc")
    else:
        st.warning("선택된 연도 범위에 데이터가 없습니다.")