"""
사내망 Jupyter에서 복사하여 사용할 템플릿 코드

이 코드를 Jupyter 노트북 셀에 복사하여 사용하세요.
"""

# ============================================================================
# Step 1: 환경 설정 확인
# ============================================================================

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

print("✅ 기본 패키지 로드 성공")
print(f"Pandas: {pd.__version__}, Numpy: {np.__version__}")


# ============================================================================
# Step 2: 데이터마트 연결
# ============================================================================

import sqlalchemy

# TODO: 실제 연결 정보로 수정하세요
connection_config = {
    'host': 'your-datamart-host.internal',
    'port': 5432,  # PostgreSQL 기본 포트
    'database': 'analytics',
    'user': 'your-username',
    'password': 'your-password'
}

# 연결 문자열 생성 (DB 종류에 따라 수정)
# PostgreSQL 예시:
conn_string = f"postgresql://{connection_config['user']}:{connection_config['password']}@{connection_config['host']}:{connection_config['port']}/{connection_config['database']}"

# MySQL 예시:
# conn_string = f"mysql+pymysql://{connection_config['user']}:{connection_config['password']}@{connection_config['host']}:{connection_config['port']}/{connection_config['database']}"

# MSSQL 예시:
# conn_string = f"mssql+pyodbc://{connection_config['user']}:{connection_config['password']}@{connection_config['host']}:{connection_config['port']}/{connection_config['database']}?driver=ODBC+Driver+17+for+SQL+Server"

try:
    engine = sqlalchemy.create_engine(conn_string)
    print("✅ 데이터베이스 연결 성공")
except Exception as e:
    print(f"❌ 연결 실패: {e}")


# ============================================================================
# Step 3: 데이터 로드 및 탐색
# ============================================================================

# TODO: 실제 테이블명과 컬럼명으로 수정하세요
query = """
    SELECT 
        date_column,
        category,
        metric1,
        metric2,
        metric3
    FROM your_schema.your_table
    WHERE date_column >= CURRENT_DATE - INTERVAL '30 days'
    LIMIT 1000
"""

# 데이터 로드
df = pd.read_sql(query, engine)
print(f"✅ 데이터 로드 성공: {len(df):,} rows × {len(df.columns)} columns")

# 기본 정보 확인
print("\n=== 데이터 개요 ===")
print(df.info())

print("\n=== 처음 5행 ===")
display(df.head())

print("\n=== 기초 통계 ===")
display(df.describe())

print("\n=== 결측치 확인 ===")
print(df.isnull().sum())


# ============================================================================
# Step 4: 데이터 전처리
# ============================================================================

def preprocess_data(df):
    """데이터 전처리 함수"""
    df = df.copy()
    
    # 1. 날짜 컬럼 변환
    if 'date_column' in df.columns:
        df['date_column'] = pd.to_datetime(df['date_column'])
    
    # 2. 결측치 처리
    df = df.dropna(subset=['중요한_컬럼'])  # TODO: 실제 컬럼명으로 수정
    
    # 3. 이상치 제거 (IQR 방법)
    for col in ['metric1', 'metric2']:  # TODO: 실제 컬럼명으로 수정
        if col in df.columns:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            df = df[(df[col] >= q1 - 1.5*iqr) & (df[col] <= q3 + 1.5*iqr)]
    
    # 4. 파생 변수 생성
    if 'date_column' in df.columns:
        df['year'] = df['date_column'].dt.year
        df['month'] = df['date_column'].dt.month
        df['year_month'] = df['date_column'].dt.to_period('M')
        df['weekday'] = df['date_column'].dt.day_name()
        df['hour'] = df['date_column'].dt.hour
    
    return df

# 전처리 실행
df_clean = preprocess_data(df)
print(f"✅ 전처리 완료: {len(df)} → {len(df_clean)} rows")


# ============================================================================
# Step 5: 데이터 집계 및 분석
# ============================================================================

# 시간대별 집계
time_series = df_clean.groupby('date_column').agg({
    'metric1': 'sum',
    'metric2': 'mean',
    'metric3': 'count'
}).reset_index()

print("\n=== 시간대별 집계 ===")
display(time_series.head())

# 카테고리별 집계
if 'category' in df_clean.columns:
    category_summary = df_clean.groupby('category').agg({
        'metric1': ['sum', 'mean', 'count']
    }).reset_index()
    
    print("\n=== 카테고리별 집계 ===")
    display(category_summary.head())


# ============================================================================
# Step 6: 시각화
# ============================================================================

# 1. 시계열 라인 차트
fig_timeseries = go.Figure()

fig_timeseries.add_trace(go.Scatter(
    x=time_series['date_column'],
    y=time_series['metric1'],
    mode='lines+markers',
    name='Metric 1',
    line=dict(color='#1f77b4', width=2),
    marker=dict(size=6)
))

fig_timeseries.update_layout(
    title='시간대별 Metric 추이',
    xaxis_title='날짜',
    yaxis_title='값',
    hovermode='x unified',
    template='plotly_white',
    height=400
)

fig_timeseries.show()


# 2. 카테고리별 막대 차트
if 'category' in df_clean.columns:
    category_agg = df_clean.groupby('category')['metric1'].sum().reset_index()
    
    fig_bar = px.bar(
        category_agg,
        x='category',
        y='metric1',
        title='카테고리별 Metric 분포',
        color='metric1',
        color_continuous_scale='Blues'
    )
    
    fig_bar.update_layout(height=400)
    fig_bar.show()


# 3. 히트맵 (요일별, 시간대별 패턴)
if 'weekday' in df_clean.columns and 'hour' in df_clean.columns:
    pivot_data = df_clean.pivot_table(
        values='metric1',
        index='hour',
        columns='weekday',
        aggfunc='mean'
    )
    
    # 요일 순서 정렬
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    pivot_data = pivot_data.reindex(columns=[d for d in weekday_order if d in pivot_data.columns])
    
    fig_heatmap = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=pivot_data.columns,
        y=pivot_data.index,
        colorscale='RdYlBu_r',
        hoverongaps=False
    ))
    
    fig_heatmap.update_layout(
        title='시간대별/요일별 패턴',
        xaxis_title='요일',
        yaxis_title='시간',
        height=500
    )
    
    fig_heatmap.show()


# ============================================================================
# Step 7: 최종 함수 정리 (Streamlit으로 복사할 코드)
# ============================================================================

def load_datamart_data(start_date, end_date):
    """
    데이터마트에서 데이터 로드
    
    Args:
        start_date (str): 시작일 (YYYY-MM-DD)
        end_date (str): 종료일 (YYYY-MM-DD)
    
    Returns:
        pd.DataFrame: 로드된 데이터
    """
    query = f"""
        SELECT 
            date_column,
            category,
            metric1,
            metric2,
            metric3
        FROM your_schema.your_table
        WHERE date_column BETWEEN '{start_date}' AND '{end_date}'
    """
    
    df = pd.read_sql(query, engine)
    return df


def calculate_key_metrics(df):
    """
    핵심 지표 계산
    
    Args:
        df (pd.DataFrame): 입력 데이터
    
    Returns:
        dict: 계산된 지표들
    """
    metrics = {
        'total_records': len(df),
        'metric1_sum': df['metric1'].sum() if 'metric1' in df.columns else 0,
        'metric2_avg': df['metric2'].mean() if 'metric2' in df.columns else 0,
        'date_range': {
            'start': df['date_column'].min() if 'date_column' in df.columns else None,
            'end': df['date_column'].max() if 'date_column' in df.columns else None
        }
    }
    return metrics


def create_timeseries_chart(df, metric_col, title="시계열 차트"):
    """
    시계열 차트 생성
    
    Args:
        df (pd.DataFrame): 입력 데이터
        metric_col (str): 표시할 지표 컬럼명
        title (str): 차트 제목
    
    Returns:
        go.Figure: Plotly 차트 객체
    """
    time_series = df.groupby('date_column')[metric_col].sum().reset_index()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=time_series['date_column'],
        y=time_series[metric_col],
        mode='lines+markers',
        name=metric_col,
        line=dict(width=2),
        marker=dict(size=6)
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title='날짜',
        yaxis_title='값',
        hovermode='x unified',
        template='plotly_white',
        height=400
    )
    
    return fig


# 함수 테스트
print("\n=== 함수 테스트 ===")
test_df = load_datamart_data('2024-01-01', '2024-12-31')
test_metrics = calculate_key_metrics(test_df)
print(f"지표: {test_metrics}")

test_df_clean = preprocess_data(test_df)
test_fig = create_timeseries_chart(test_df_clean, 'metric1', '테스트 차트')
test_fig.show()

print("\n✅ 모든 함수 동작 확인 완료!")
print("\n다음 단계:")
print("1. 이 함수들을 로컬 C:\\251213_pylon\\data\\datamart_connector.py로 복사")
print("2. Streamlit 페이지 생성")
print("3. 로컬에서 테스트")
print("4. development 브랜치에 커밋")

