# Jupyter 개발 가이드 (사내망 환경)

## 🎯 목표
사내망 Jupyter에서 데이터마트 연동을 개발하고, 검증된 코드를 Streamlit 앱에 통합

---

## 📝 사내망 Jupyter에서 할 일

### Step 1: 프로젝트 이해 및 기존 코드 파악

#### 1-1. 업로드할 파일들
사내망 Jupyter로 다음 파일들을 복사:

```
업로드 필수:
- data/ 폴더 (기존 데이터 로더)
- components/ 폴더 (레이아웃, 차트 컴포넌트)
- utils/ 폴더 (유틸리티 함수)
```

또는 간단하게 필요한 함수만 Jupyter 노트북에 복사해도 됩니다.

#### 1-2. 첫 번째 노트북: 환경 확인

```python
# 01_setup_check.ipynb

# 패키지 확인
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

print("✅ 기본 패키지 로드 성공")

# 사내 데이터마트 연결 테스트
# TODO: 사내 데이터마트 연결 정보로 수정
try:
    # 예시: PostgreSQL, Oracle, MSSQL 등
    import sqlalchemy
    # connection_string = "postgresql://user:password@host:port/database"
    # engine = sqlalchemy.create_engine(connection_string)
    print("✅ 데이터베이스 패키지 사용 가능")
except Exception as e:
    print(f"⚠️ DB 연결 설정 필요: {e}")
```

---

### Step 2: 데이터마트 연동 및 탐색

#### 2-1. 데이터 로드 테스트

```python
# 02_datamart_connection.ipynb

import pandas as pd
import sqlalchemy

# 사내 데이터마트 연결 설정
# ⚠️ 실제 연결 정보로 수정하세요
connection_config = {
    'host': 'your-datamart-host',
    'port': 5432,
    'database': 'analytics',
    'user': 'your-username',
    'password': 'your-password'
}

# 연결 문자열 생성
conn_string = f"postgresql://{connection_config['user']}:{connection_config['password']}@{connection_config['host']}:{connection_config['port']}/{connection_config['database']}"

engine = sqlalchemy.create_engine(conn_string)

# 테스트 쿼리
query = """
    SELECT *
    FROM your_table
    LIMIT 10
"""

df = pd.read_sql(query, engine)
print(f"✅ 데이터 로드 성공: {len(df)} rows")
df.head()
```

#### 2-2. 데이터 탐색

```python
# 데이터 기본 정보
print("=== 데이터 개요 ===")
print(f"행 수: {len(df):,}")
print(f"열 수: {len(df.columns)}")
print(f"\n컬럼 목록:\n{df.columns.tolist()}")

# 데이터 타입 확인
print("\n=== 데이터 타입 ===")
print(df.dtypes)

# 결측치 확인
print("\n=== 결측치 ===")
print(df.isnull().sum())

# 기초 통계
print("\n=== 기초 통계 ===")
df.describe()
```

---

### Step 3: 데이터 처리 로직 개발

#### 3-1. 데이터 전처리

```python
# 03_data_processing.ipynb

# 날짜 컬럼 처리
if 'date_column' in df.columns:
    df['date_column'] = pd.to_datetime(df['date_column'])

# 데이터 정제
df_clean = df.copy()

# 1. 결측치 처리
df_clean = df_clean.dropna(subset=['중요한_컬럼'])

# 2. 이상치 제거 (예시)
q1 = df_clean['metric'].quantile(0.25)
q3 = df_clean['metric'].quantile(0.75)
iqr = q3 - q1
df_clean = df_clean[
    (df_clean['metric'] >= q1 - 1.5*iqr) & 
    (df_clean['metric'] <= q3 + 1.5*iqr)
]

# 3. 파생 변수 생성
df_clean['year_month'] = df_clean['date_column'].dt.to_period('M')
df_clean['weekday'] = df_clean['date_column'].dt.day_name()

print(f"✅ 전처리 완료: {len(df_clean)} rows")
```

#### 3-2. 집계 및 분석

```python
# 시간대별 집계
time_series = df_clean.groupby('date_column').agg({
    'metric1': 'sum',
    'metric2': 'mean',
    'metric3': 'count'
}).reset_index()

# 카테고리별 집계
category_summary = df_clean.groupby('category').agg({
    'value': ['sum', 'mean', 'count']
}).reset_index()

print("✅ 집계 완료")
time_series.head()
```

---

### Step 4: 시각화 프로토타이핑

#### 4-1. Plotly 차트 개발

```python
# 04_visualization.ipynb

import plotly.graph_objects as go
import plotly.express as px

# 1. 시계열 차트
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
    title='시간대별 추이',
    xaxis_title='날짜',
    yaxis_title='값',
    hovermode='x unified',
    template='plotly_white'
)

fig_timeseries.show()

# 2. 막대 차트
fig_bar = px.bar(
    category_summary,
    x='category',
    y='value',
    title='카테고리별 분포',
    color='value',
    color_continuous_scale='Blues'
)

fig_bar.show()

# 3. 히트맵 (요일별, 시간대별 패턴)
df_pivot = df_clean.pivot_table(
    values='metric',
    index=df_clean['date_column'].dt.hour,
    columns=df_clean['date_column'].dt.day_name(),
    aggfunc='mean'
)

fig_heatmap = go.Figure(data=go.Heatmap(
    z=df_pivot.values,
    x=df_pivot.columns,
    y=df_pivot.index,
    colorscale='RdYlBu_r'
))

fig_heatmap.update_layout(
    title='시간대별 패턴',
    xaxis_title='요일',
    yaxis_title='시간'
)

fig_heatmap.show()
```

---

### Step 5: 최종 함수 정리 (Streamlit 통합 준비)

#### 5-1. 재사용 가능한 함수로 정리

```python
# 05_final_functions.ipynb

# 이 함수들을 나중에 Streamlit 앱으로 복사할 예정

def load_datamart_data(start_date, end_date):
    """데이터마트에서 데이터 로드"""
    query = f"""
        SELECT *
        FROM your_table
        WHERE date_column BETWEEN '{start_date}' AND '{end_date}'
    """
    df = pd.read_sql(query, engine)
    return df

def preprocess_data(df):
    """데이터 전처리"""
    df = df.copy()
    df['date_column'] = pd.to_datetime(df['date_column'])
    # ... 전처리 로직
    return df

def create_timeseries_chart(df, metric_name):
    """시계열 차트 생성"""
    fig = go.Figure()
    # ... 차트 로직
    return fig

def calculate_metrics(df):
    """핵심 지표 계산"""
    metrics = {
        'total': df['value'].sum(),
        'average': df['value'].mean(),
        'count': len(df)
    }
    return metrics

# 테스트
df = load_datamart_data('2024-01-01', '2024-12-31')
df_processed = preprocess_data(df)
metrics = calculate_metrics(df_processed)
fig = create_timeseries_chart(df_processed, 'metric1')

print("✅ 모든 함수 동작 확인 완료")
print(f"지표: {metrics}")
fig.show()
```

---

## 🔄 로컬 Streamlit 통합 프로세스

### Step 6: 검증된 코드를 로컬로 가져오기

사내망 Jupyter에서 검증 완료 후:

#### 6-1. 로컬에서 모듈 생성

```python
# C:\251213_pylon\data\datamart_connector.py 생성

import pandas as pd
import sqlalchemy
import streamlit as st
from typing import Dict, Any

@st.cache_data(ttl=3600)  # 1시간 캐싱
def load_datamart_data(start_date: str, end_date: str) -> pd.DataFrame:
    """
    사내 데이터마트에서 데이터 로드
    
    Args:
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)
    
    Returns:
        DataFrame: 로드된 데이터
    """
    # Jupyter에서 검증된 함수 복사
    # ...
    pass

def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """데이터 전처리 (Jupyter에서 검증된 로직)"""
    # ...
    pass

def calculate_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """핵심 지표 계산 (Jupyter에서 검증된 로직)"""
    # ...
    pass
```

#### 6-2. 새 페이지 생성

```python
# C:\251213_pylon\pages\4_📊_Datamart_Analysis.py 생성

import streamlit as st
from data.datamart_connector import (
    load_datamart_data,
    preprocess_data,
    calculate_metrics
)
from components.charts import create_timeseries_chart
from components.layout import create_header, create_metric_card

st.set_page_config(page_title="데이터마트 분석", layout="wide")
create_header()

st.title("📊 데이터마트 분석")

# 날짜 선택
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("시작일", value=pd.Timestamp.now() - pd.Timedelta(days=30))
with col2:
    end_date = st.date_input("종료일", value=pd.Timestamp.now())

# 데이터 로드
with st.spinner("데이터 로딩 중..."):
    df = load_datamart_data(str(start_date), str(end_date))
    df = preprocess_data(df)

if not df.empty:
    # 지표 표시
    metrics = calculate_metrics(df)
    col1, col2, col3 = st.columns(3)
    with col1:
        create_metric_card("총계", f"{metrics['total']:,.0f}", "📈")
    with col2:
        create_metric_card("평균", f"{metrics['average']:,.1f}", "📊")
    with col3:
        create_metric_card("건수", f"{metrics['count']:,}", "🔢")
    
    # 차트 표시
    fig = create_timeseries_chart(df, 'metric1')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("데이터가 없습니다.")
```

#### 6-3. 로컬 테스트

```bash
# development 브랜치에서 실행
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속하여 테스트

---

## ✅ 체크리스트

### Jupyter 개발 단계
- [ ] 데이터마트 연결 성공
- [ ] 데이터 로드 및 탐색 완료
- [ ] 전처리 로직 개발 및 검증
- [ ] 차트 프로토타입 완성
- [ ] 함수로 정리 및 테스트

### Streamlit 통합 단계
- [ ] `data/datamart_connector.py` 생성
- [ ] `pages/4_📊_Datamart_Analysis.py` 생성
- [ ] 로컬 Streamlit 테스트 완료
- [ ] 에러 없이 정상 작동 확인

### 배포 단계
- [ ] `development` 브랜치에 커밋
- [ ] `master` 브랜치에 merge
- [ ] `pylon-test4`에 push
- [ ] 사내 Playground에서 동작 확인

---

## 💡 팁

1. **Jupyter에서 자주 저장**: 세션 타임아웃에 대비
2. **함수 단위로 개발**: 나중에 Streamlit에 복사하기 쉬움
3. **충분히 테스트**: Jupyter에서 완벽히 검증 후 이동
4. **문서화**: 주석과 docstring 작성 (나중에 본인이 볼 때도 편함)
5. **데이터 샘플링**: 큰 데이터는 일부만 로드해서 빠르게 개발

---

## 🚨 주의사항

- **비밀번호 노출 금지**: 연결 정보는 변수로 분리, Git에 커밋하지 않기
- **쿼리 최적화**: 필요한 데이터만 SELECT
- **캐싱 활용**: Streamlit의 `@st.cache_data` 사용
- **에러 처리**: try-except로 안전하게 처리


