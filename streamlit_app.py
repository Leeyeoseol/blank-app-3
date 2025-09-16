import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime
import os
from sklearn.linear_model import LinearRegression

# --- 폰트 설정 ---
# GitHub Codespaces 환경에 폰트가 없을 수 있으므로, 파일 존재 여부를 확인합니다.
def get_font_path():
    """시스템에 Pretendard 폰트가 있는지 확인하고 경로를 반환"""
    font_path = '/fonts/Pretendard-Bold.ttf'
    return font_path if os.path.exists(font_path) else None

FONT_PATH = get_font_path()
FONT_FAMILY = "Pretendard" if FONT_PATH else "sans-serif"


# --- 데이터 로딩 및 전처리 함수 (캐싱 적용) ---

@st.cache_data
def load_sea_level_data():
    """
    NOAA에서 제공하는 전 세계 평균 해수면 데이터를 로드합니다.
    데이터 출처(URL): https://www.star.nesdis.noaa.gov/sod/lsa/SeaLevelRise/slr/index.php
    실패 시 예시 데이터를 사용합니다.
    """
    url = "https://www.star.nesdis.noaa.gov/sod/lsa/SeaLevelRise/api/gbl/noaa/data.json"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data)
        
        # 데이터 포맷 변경에 따른 파싱 로직 수정
        # 'year' 컬럼(소수점 연도)을 datetime으로 변환
        df['year_int'] = df['year'].astype(int)
        df['remainder'] = df['year'] - df['year_int']
        
        # 윤년을 고려하여 일수 계산
        is_leap = (df['year_int'] % 4 == 0) & ((df['year_int'] % 100 != 0) | (df['year_int'] % 400 == 0))
        days_in_year = np.where(is_leap, 366, 365)
        df['day_of_year'] = (df['remainder'] * days_in_year).round().astype(int) + 1
        df['day_of_year'] = df['day_of_year'].clip(1, 366) # 계산 오류 방지
        
        # YYYY + DayOfYear 형식으로 변환하여 날짜 생성
        df['date_str'] = df['year_int'].astype(str) + df['day_of_year'].astype(str).str.zfill(3)
        df['date'] = pd.to_datetime(df['date_str'], format='%Y%j', errors='coerce')

        df.rename(columns={'mean': 'value'}, inplace=True)
        
        df = df[['date', 'value']].copy()
        df.dropna(subset=['date', 'value'], inplace=True)
        
    except (requests.exceptions.RequestException, ValueError, KeyError) as e:
        st.error(f"⚠️ 공식 데이터를 불러오는 데 실패했습니다: {e}. 예시 데이터로 대시보드를 구성합니다.")
        dates = pd.to_datetime(pd.date_range(start='1993-01-01', end='2024-12-31', freq='M'))
        values = np.linspace(0, 105, len(dates)) + np.random.normal(0, 2.5, len(dates))
        df = pd.DataFrame({'date': dates, 'value': values})

    today = pd.to_datetime(datetime.now().date())
    df = df[df['date'] < today].copy()
    
    df.drop_duplicates(subset=['date'], inplace=True, keep='first')
    df.sort_values('date', inplace=True)
    df.reset_index(drop=True, inplace=True)
    
    return df

@st.cache_data
def load_fisheries_data():
    """
    사용자 입력 자료를 바탕으로 국내 어획량 변화 예시 데이터를 생성합니다.
    """
    data = {
        'year': range(2018, 2025),
        '꽃게': [15000, 14500, 13000, 12000, 11500, 10000, 9500],
        '낙지': [6500, 6200, 5800, 5500, 5000, 4800, 4500],
        '명태': [1000, 800, 500, 300, 200, 100, 50],
        '방어': [8000, 8500, 9000, 9800, 11000, 12000, 13500]
    }
    df = pd.DataFrame(data)
    df_melted = df.melt(id_vars='year', var_name='group', value_name='value')
    df_melted['date'] = pd.to_datetime(df_melted['year'], format='%Y')
    
    return df_melted[['date', 'group', 'value']]

# --- 헬퍼 함수 ---
def to_csv(df):
    """데이터프레임을 CSV로 변환"""
    return df.to_csv(index=False).encode('utf-8-sig')


# --- 1. 공식 데이터 대시보드 ---
def public_data_dashboard():
    st.header("🌊 공식 데이터 기반 해수면 & 어업생산량 대시보드")
    st.markdown("""
    [미국 해양대기청(NOAA)](https://www.star.nesdis.noaa.gov/sod/lsa/SeaLevelRise/index.php)의 위성 관측 데이터와 국내 어획량 통계(예시)를 바탕으로 해수면 상승과 우리 식탁의 관계를 탐색합니다.
    """)

    # 데이터 로드
    sea_level_df = load_sea_level_data()
    fisheries_df = load_fisheries_data()

    # --- 사이드바 필터 ---
    st.sidebar.header("📈 표시 옵션")
    
    min_date = sea_level_df['date'].min().to_pydatetime()
    max_date = sea_level_df['date'].max().to_pydatetime()
    start_date, end_date = st.sidebar.slider(
        "해수면 데이터 기간 선택",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM"
    )
    
    smoothing_window = st.sidebar.slider("해수면 데이터 스무딩 (이동 평균 월)", 1, 24, 6, help="데이터의 추세를 부드럽게 보기 위한 기능입니다.")
    show_trendline = st.sidebar.checkbox("해수면 상승 추세선 표시", value=True)
    
    st.sidebar.markdown("---")
    
    species_options = fisheries_df['group'].unique()
    selected_species = st.sidebar.multiselect("어종 선택", options=species_options, default=species_options)

    # --- 데이터 필터링 및 전처리 ---
    filtered_sea_level_df = sea_level_df[
        (sea_level_df['date'] >= pd.to_datetime(start_date)) & 
        (sea_level_df['date'] <= pd.to_datetime(end_date))
    ].copy()
    
    filtered_sea_level_df['value_smoothed'] = filtered_sea_level_df['value'].rolling(window=smoothing_window, min_periods=1).mean()

    filtered_fisheries_df = fisheries_df[fisheries_df['group'].isin(selected_species)]

    # --- 화면 구성 ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("전 세계 평균 해수면 변화")
        
        fig_sea = px.area(
            filtered_sea_level_df, 
            x='date', 
            y='value_smoothed',
            labels={'date': '연도', 'value_smoothed': '해수면 높이 변화 (mm)'},
            hover_data={'value_smoothed': ':.2f mm'}
        )
        
        # 추세선 추가 (scikit-learn 사용)
        if show_trendline and not filtered_sea_level_df.empty:
            X = filtered_sea_level_df['date'].map(datetime.toordinal).values.reshape(-1, 1)
            y = filtered_sea_level_df['value_smoothed'].values
            
            model = LinearRegression()
            model.fit(X, y)
            trend_values = model.predict(X)
            
            fig_sea.add_trace(go.Scatter(
                x=filtered_sea_level_df['date'], 
                y=trend_values,
                mode='lines',
                name='상승 추세선',
                line=dict(color='red', dash='dash')
            ))

        fig_sea.update_layout(
            font_family=FONT_FAMILY,
            xaxis_title="연도",
            yaxis_title="해수면 높이 변화 (mm, 기준값 대비)"
        )
        st.plotly_chart(fig_sea, use_container_width=True)

        st.download_button(
            label="📈 해수면 데이터 다운로드 (CSV)",
            data=to_csv(filtered_sea_level_df[['date', 'value_smoothed']]),
            file_name="sea_level_data.csv",
            mime="text/csv",
        )

    with col2:
        st.subheader("국내 주요 어종 어획량 변화 (예시)")
        
        fig_fish = px.line(
            filtered_fisheries_df,
            x='date', y='value', color='group',
            labels={'date': '연도', 'value': '어획량 (톤)', 'group': '어종'},
            markers=True
        )
        fig_fish.update_layout(
            font_family=FONT_FAMILY,
            xaxis_title="연도", yaxis_title="어획량 (톤)"
        )
        st.plotly_chart(fig_fish, use_container_width=True)
        
        st.download_button(
            label="🐟 어획량 데이터 다운로드 (CSV)",
            data=to_csv(filtered_fisheries_df),
            file_name="fisheries_data.csv",
            mime="text/csv",
        )
    st.info("💡 어획량 데이터는 제공된 기사 내용을 바탕으로 생성된 예시 데이터입니다.")


# --- 2. 사용자 입력 기반 대시보드 ---
def user_input_dashboard():
    st.header("📑 기사/자료 기반 해수면 상승 영향 분석")
    st.markdown("제공해주신 자료들의 핵심 내용을 시각화하고 분석합니다.")
    
    st.subheader("1. 해수면 상승 주요 데이터 요약")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("연평균 상승 (전 세계)", "4.8 mm/yr", delta="상승 가속화", delta_color="inverse")
    col2.metric("최근 20년 상승 (전 세계)", "7 cm", "총 70 mm", delta_color="off")
    col3.metric("최근 35년간 상승 (한국)", "10.7 cm", "지구 평균보다 빠른 속도", delta_color="inverse")

    st.subheader("2. 수산업 및 식생활에 미치는 영향")
    
    df_fish_impact = pd.DataFrame({
        '어종': ['명태', '꽃게', '낙지', '방어'],
        '변화': ['급감', '감소', '감소', '증가'],
        '관련 내용': [
            '기후변화로 인한 밥상 변화의 대표 사례', 
            '6년 만에 최저 어획량 기록',
            '어획량 감소로 인한 가격 급등',
            '난류성 어종으로, 한반도 해역에서 어획량 증가'
        ]
    })

    change_map = {'급감': -2, '감소': -1, '증가': 1}
    df_fish_impact['change_value'] = df_fish_impact['변화'].map(change_map)
    
    fig = px.bar(
        df_fish_impact.sort_values('change_value'), 
        x='어종', y='change_value', color='변화',
        color_discrete_map={'급감': '#d62728', '감소': '#FF7F0E', '증가': '#1f77b4'},
        labels={'change_value': '변화 방향 및 정도', '어종': '어종'},
        hover_data=['관련 내용']
    )
    fig.update_layout(
        font_family=FONT_FAMILY,
        yaxis_title="변화 방향",
        showlegend=False,
        yaxis=dict(tickvals=[-2, -1, 1], ticktext=['급감', '감소', '증가'])
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    ---
    ### 영향의 연쇄 작용
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center; font-size: 1.1em;">
        <b>기후변화 (지구 온난화)</b> ➡️ <b>해수온/해수면 상승</b> ➡️ <b>해양 생태계 교란</b> ➡️ <b>어획량 변화</b> ➡️ <b>수산물 가격 변동</b> ➡️ <b>우리 식생활에 직접적 영향</b>
    </div>
    """, unsafe_allow_html=True)
        
# --- 메인 앱 로직 ---
def main():
    st.set_page_config(page_title="해수면 상승 영향 대시보드", layout="wide", initial_sidebar_state="expanded")
    
    st.title("기후변화와 우리 식탁: 해수면 상승 영향 대시보드")

    st.sidebar.title("항해사 🧭")
    app_mode = st.sidebar.radio(
        "확인할 대시보드를 선택하세요.",
        ["공식 데이터 기반 대시보드", "사용자 입력 기반 분석"],
        captions=["NOAA 실시간 데이터", "제공된 자료 요약"]
    )

    if app_mode == "공식 데이터 기반 대시보드":
        public_data_dashboard()
    else:
        user_input_dashboard()

if __name__ == "__main__":
    main()


