import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from io import StringIO
from datetime import datetime
import numpy as np

# -------------------------------------------------------
# 페이지 설정
# -------------------------------------------------------
st.set_page_config(page_title="해수면 상승 & 절약 챌린지", layout="wide")

# (선택) Pretendard 폰트 적용 시도 (로컬 환경에 폰트가 있어야 동작)
try:
    st.markdown(
        """
        <style>
        @font-face {
            font-family: 'Pretendard';
            src: url('/fonts/Pretendard-Bold.ttf');
        }
        html, body, [class*="css"] {
            font-family: 'Pretendard', sans-serif;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
except Exception:
    pass

# -------------------------------------------------------
# NOAA 데이터 로드 (캐시)
# -------------------------------------------------------
@st.cache_data
def load_noaa_data():
    url = "https://datahub.io/core/sea-level-rise/r/csiro_recons_gmsl_mo_2015.csv"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        df = pd.read_csv(StringIO(r.text))

        # 컬럼명 정리 (데이터셋에 따라 컬럼명이 다를 수 있어서 보정)
        if "Time" in df.columns and "GMSL" in df.columns:
            df = df.rename(columns={"Time": "date", "GMSL": "value"})
        elif "date" in df.columns and "value" in df.columns:
            pass
        else:
            # fallback: 첫 두 컬럼을 date/value로 가정
            cols = df.columns.tolist()
            if len(cols) >= 2:
                df = df.rename(columns={cols[0]: "date", cols[1]: "value"})

        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date", "value"])
        df = df[df["date"] <= datetime.today()]  # 미래 데이터 제거
        df["year"] = df["date"].dt.year
        return df
    except Exception:
        # 실패 시 예시 데이터 리턴
        data = {
            "date": pd.date_range("2000-01-01", periods=120, freq="M"),
            "value": np.linspace(0, 80, 120) + np.random.normal(scale=1.5, size=120)
        }
        df = pd.DataFrame(data)
        df["year"] = df["date"].dt.year
        return df

df_monthly = load_noaa_data()

# -------------------------------------------------------
# 사이드바: 분석 옵션
# -------------------------------------------------------
st.sidebar.header("🔍 분석 옵션")

min_year = int(df_monthly["year"].min())
max_year = int(df_monthly["year"].max())
default_start = max(min_year, 1990)

year_range = st.sidebar.slider("분석 기간", min_year, max_year, (default_start, max_year))
window = st.sidebar.slider("이동평균 윈도우 (년)", 1, 10, 5)
show_trend = st.sidebar.checkbox("추세선 표시 (선형)", value=True)

# -------------------------------------------------------
# 해수면 데이터: 연도별 집계 & 시각화
# -------------------------------------------------------
st.header("📊 전 세계 해수면 상승 추이 (연도별 평균 + 범위)")

df_filtered = df_monthly[(df_monthly["year"] >= year_range[0]) & (df_monthly["year"] <= year_range[1])]
df_yearly = df_filtered.groupby("year")["value"].agg(["mean", "min", "max"]).reset_index().sort_values("year")
df_yearly = df_yearly.rename(columns={"mean": "avg"})

# 이동평균 (년 단위)
df_yearly["moving_avg"] = df_yearly["avg"].rolling(window=window, min_periods=1).mean()

# 추세선 (선형 회귀)
if len(df_yearly) >= 2:
    coeffs = np.polyfit(df_yearly["year"].astype(float), df_yearly["avg"].astype(float), 1)
    slope, intercept = coeffs[0], coeffs[1]
    df_yearly["trend"] = df_yearly["year"] * slope + intercept
else:
    df_yearly["trend"] = df_yearly["avg"]

# 막대 그래프 (평균) + 에러바(최솟값/최댓값)
fig = px.bar(
    df_yearly,
    x="year",
    y="avg",
    error_y=(df_yearly["max"] - df_yearly["avg"]),
    error_y_minus=(df_yearly["avg"] - df_yearly["min"]),
    labels={"year": "연도", "avg": "해수면 높이 (mm)"},
    title=f"연도별 평균 해수면 높이 ({year_range[0]} - {year_range[1]})"
)

# 이동평균 선 추가
fig.add_trace(
    go.Scatter(
        x=df_yearly["year"],
        y=df_yearly["moving_avg"],
        mode="lines",
        name=f"{window}년 이동평균",
        line=dict(width=3, dash="dash")
    )
)

# 추세선 추가 (옵션)
if show_trend:
    fig.add_trace(
        go.Scatter(
            x=df_yearly["year"],
            y=df_yearly["trend"],
            mode="lines",
            name=f"선형 추세선 ({slope:.3f} mm/년)",
            line=dict(width=2, dash="dot")
        )
    )

fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

st.plotly_chart(fig, use_container_width=True)

# 데이터 다운로드 (연도별)
csv = df_yearly.to_csv(index=False)
st.download_button("📥 연도별 데이터 다운로드 (CSV)", csv, "sea_level_yearly.csv", mime="text/csv")

# -------------------------------------------------------
# 체크리스트 UI
# -------------------------------------------------------
st.header("✅ 나의 기후행동 체크리스트")
st.write("아래 10가지 절약 미션을 체크해보세요! 체크할수록 게이지가 올라갑니다 ⚡")

missions = [
    "하루 한 번 이상 플러그 뽑기",
    "계단 이용하기 (가능한 범위에서)",
    "SNS에 환경 관련 내용 공유하기",
    "대중교통 이용하기",
    "종이 대신 디지털 메모 사용하기",
    "일회용컵 대신 텀블러 사용하기",
    "친구들과 기후변화 이야기 나누기",
    "중고 물품 재사용하기",
    "음식물 쓰레기 줄이기",
    "환경 다큐멘터리나 뉴스 관심 갖기"
]

if "checked" not in st.session_state:
    st.session_state.checked = [False] * len(missions)

cols = st.columns(2)
for i, mission in enumerate(missions):
    with cols[i % 2]:
        st.session_state.checked[i] = st.checkbox(mission, value=st.session_state.checked[i])

completed = sum(st.session_state.checked)
progress = completed / len(missions)
progress_percent = int(progress * 100)

# 프로그레스 바 (0~100)
st.progress(progress_percent)
st.write(f"실천 수: {completed}/{len(missions)}  ·  현재 달성률: **{progress_percent}%**")

# 0% / 60% / 80% 피드백
if progress_percent == 0:
    st.warning("🙃 아직 하나도 체크하지 않았어요. 작은 것부터 하나씩 시작해봐요 — 시작이 반입니다!")
elif progress_percent >= 80:
    st.balloons()
    st.success("🎉 멋져요! 80% 이상 달성했습니다 — 당신의 작은 실천이 큰 변화를 만듭니다!")
elif progress_percent >= 60:
    st.info("👍 잘하고 있어요! 조금만 더 하면 큰 변화를 만들 수 있어요 — 계속 응원합니다!")
else:
    st.info("💡 좋은 출발이에요. 꾸준히 이어가면 큰 변화를 만들 수 있어요.")

# (선택) 추가 설명/저장 기능 등은 원하시면 더 붙여드릴게요.
