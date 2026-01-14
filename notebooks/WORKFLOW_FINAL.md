# 실전 워크플로우 (최종 정리)

## 📍 현재 상황
- ✅ 사내망 Jupyter: 오늘 아침 버전 (notebooks 폴더 없음)
- ✅ Playground: 앱 정상 작동 중
- ❌ 사내망 Jupyter에서 streamlit 브라우저 실행 안 됨
  → 정상입니다! Jupyter 환경의 네트워크 제약

---

## 🎯 추천 워크플로우

### 방식: Jupyter에서 개발 → 로컬/Playground에서 테스트

```
[사내망 Jupyter]
  개발만 (빠른 반복)
  ├─ notebooks/*.ipynb로 실험
  ├─ 검증된 코드를 .py로 정리
  └─ git push
       │
       ▼
[로컬 PC 또는 Playground]
  테스트 및 확인
  ├─ git pull
  ├─ streamlit run app.py (로컬)
  └─ 또는 master push → Playground 자동 배포
```

---

## 📋 단계별 가이드

### Step 1: 사내망 Jupyter에서 환경 준비

```bash
# 사내망 Jupyter 터미널
cd pylon-test4/

# notebooks 폴더 생성
mkdir notebooks

# 브랜치 확인/전환
git branch -a
git checkout development  # 없으면 git checkout -b development
```

---

### Step 2: Jupyter 노트북으로 데이터 개발

#### 새 노트북 생성: `notebooks/datamart_dev.ipynb`

**Cell 1: 환경 확인**
```python
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys

print(f"✅ Python {sys.version}")
print(f"✅ Pandas {pd.__version__}")
print("환경 준비 완료!")
```

**Cell 2: 기존 프로젝트 구조 확인**
```python
import os

# 현재 프로젝트 구조 확인
print("프로젝트 구조:")
for root, dirs, files in os.walk('.'):
    level = root.replace('.', '').count(os.sep)
    indent = ' ' * 2 * level
    print(f'{indent}{os.path.basename(root)}/')
    subindent = ' ' * 2 * (level + 1)
    for file in files[:5]:  # 처음 5개만
        print(f'{subindent}{file}')
```

**Cell 3: 기존 유틸리티 함수 가져오기**
```python
# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, '..')

# 기존 컴포넌트 재사용 (선택사항)
try:
    from components.layout import create_header
    from data.loader import load_data
    print("✅ 기존 모듈 로드 성공")
except Exception as e:
    print(f"⚠️ 모듈 로드 실패 (정상): {e}")
    print("→ 필요한 함수만 직접 작성하면 됩니다")
```

**Cell 4: 데이터마트 연결**
```python
import sqlalchemy

# 실제 연결 정보로 수정
DB_CONFIG = {
    'host': 'your-datamart-host.internal',
    'port': 5432,
    'database': 'analytics',
    'user': 'your-username',
    'password': 'your-password'
}

# 연결 문자열 생성
conn_string = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

try:
    engine = sqlalchemy.create_engine(conn_string)
    print("✅ 데이터베이스 연결 성공")
except Exception as e:
    print(f"❌ 연결 실패: {e}")
```

**Cell 5: 데이터 로드 테스트**
```python
# 작은 샘플 데이터로 시작
query = """
    SELECT *
    FROM your_table
    LIMIT 100
"""

df = pd.read_sql(query, engine)
print(f"✅ 데이터 로드 성공: {len(df)} rows × {len(df.columns)} columns")

# 데이터 확인
display(df.head())
display(df.info())
```

**Cell 6: 데이터 탐색**
```python
# 기초 통계
print("=== 기초 통계 ===")
display(df.describe())

# 결측치 확인
print("\n=== 결측치 ===")
print(df.isnull().sum())

# 유니크 값 확인 (카테고리 컬럼)
for col in df.select_dtypes(include='object').columns:
    print(f"\n{col}: {df[col].nunique()} unique values")
    print(df[col].value_counts().head())
```

**Cell 7: 시각화 프로토타이핑**
```python
# 간단한 차트로 데이터 이해
fig = px.histogram(df, x='your_column', title='데이터 분포')
fig.show()

# 시계열이 있다면
if 'date_column' in df.columns:
    df['date_column'] = pd.to_datetime(df['date_column'])
    daily_agg = df.groupby('date_column')['value_column'].sum().reset_index()
    
    fig = px.line(daily_agg, x='date_column', y='value_column', title='시간대별 추이')
    fig.show()
```

**Cell 8: 함수로 정리**
```python
def load_datamart_data(start_date, end_date, engine):
    """검증된 데이터 로드 함수"""
    query = f"""
        SELECT *
        FROM your_table
        WHERE date_column BETWEEN '{start_date}' AND '{end_date}'
    """
    return pd.read_sql(query, engine)

def preprocess_data(df):
    """검증된 전처리 함수"""
    df = df.copy()
    df['date_column'] = pd.to_datetime(df['date_column'])
    df = df.dropna(subset=['important_column'])
    return df

def create_chart(df):
    """검증된 차트 생성 함수"""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['date_column'],
        y=df['value'],
        mode='lines+markers'
    ))
    fig.update_layout(title='차트 제목', height=400)
    return fig

# 테스트
test_df = load_datamart_data('2024-01-01', '2024-01-31', engine)
test_df = preprocess_data(test_df)
test_fig = create_chart(test_df)
test_fig.show()

print("✅ 모든 함수 검증 완료!")
```

---

### Step 3: Python 파일로 정리

#### 3-1. 데이터 커넥터 생성

사내망 Jupyter에서 파일 생성: `data/datamart_connector.py`

```python
"""
사내 데이터마트 연결 모듈
Jupyter 노트북에서 검증된 로직
"""

import pandas as pd
import sqlalchemy
import streamlit as st
from typing import Optional

@st.cache_data(ttl=3600)
def get_datamart_engine():
    """데이터마트 연결 엔진 생성"""
    config = st.secrets.get("datamart", {})
    
    if not config:
        st.warning("⚠️ 데이터마트 연결 정보가 없습니다.")
        return None
    
    conn_string = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
    return sqlalchemy.create_engine(conn_string)

@st.cache_data(ttl=3600)
def load_datamart_data(start_date: str, end_date: str) -> pd.DataFrame:
    """
    데이터마트에서 데이터 로드 (Jupyter에서 검증됨)
    
    Args:
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)
    
    Returns:
        DataFrame
    """
    engine = get_datamart_engine()
    if engine is None:
        return pd.DataFrame()
    
    # Jupyter에서 검증된 쿼리 복사
    query = f"""
        SELECT *
        FROM your_table
        WHERE date_column BETWEEN '{start_date}' AND '{end_date}'
    """
    
    try:
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return pd.DataFrame()

def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """데이터 전처리 (Jupyter에서 검증됨)"""
    if df.empty:
        return df
    
    df = df.copy()
    # Jupyter에서 검증된 전처리 로직 복사
    df['date_column'] = pd.to_datetime(df['date_column'])
    df = df.dropna(subset=['important_column'])
    return df
```

#### 3-2. 차트 모듈 생성 (선택사항)

`components/datamart_charts.py`

```python
"""데이터마트 시각화 (Jupyter에서 검증됨)"""

import plotly.graph_objects as go
import pandas as pd

def create_timeseries_chart(df: pd.DataFrame, title: str = "시계열 차트"):
    """Jupyter에서 검증된 차트"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['date_column'],
        y=df['value'],
        mode='lines+markers',
        line=dict(width=2),
        marker=dict(size=6)
    ))
    
    fig.update_layout(
        title=title,
        height=400,
        hovermode='x unified',
        template='plotly_white'
    )
    
    return fig
```

#### 3-3. Streamlit 페이지 생성

`pages/4_📊_Datamart_Analysis.py`

```python
"""
데이터마트 분석 페이지
"""

import streamlit as st
import pandas as pd
from datetime import timedelta

from data.datamart_connector import load_datamart_data, preprocess_data
from components.datamart_charts import create_timeseries_chart
from components.layout import create_header, create_metric_card

# 페이지 설정
st.set_page_config(
    page_title="데이터마트 분석",
    page_icon="📊",
    layout="wide"
)

create_header()

st.title("📊 데이터마트 분석")
st.markdown("사내 데이터마트 실시간 분석 대시보드")

# 사이드바: 필터
with st.sidebar:
    st.header("필터")
    
    # 날짜 선택
    end_date = st.date_input(
        "종료일",
        value=pd.Timestamp.now()
    )
    start_date = st.date_input(
        "시작일",
        value=end_date - timedelta(days=30)
    )
    
    load_button = st.button("데이터 로드", type="primary")

# 메인 컨텐츠
if load_button:
    with st.spinner("데이터 로딩 중..."):
        # 데이터 로드
        df = load_datamart_data(str(start_date), str(end_date))
        
        if df.empty:
            st.warning("데이터가 없습니다.")
            st.stop()
        
        # 전처리
        df = preprocess_data(df)
        
        # 세션에 저장
        st.session_state['datamart_df'] = df

# 데이터가 있으면 표시
if 'datamart_df' in st.session_state:
    df = st.session_state['datamart_df']
    
    # 핵심 지표
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        create_metric_card("총 레코드", f"{len(df):,}", "📊")
    with col2:
        total = df['value'].sum() if 'value' in df.columns else 0
        create_metric_card("합계", f"{total:,.0f}", "📈")
    with col3:
        avg = df['value'].mean() if 'value' in df.columns else 0
        create_metric_card("평균", f"{avg:,.1f}", "📉")
    with col4:
        create_metric_card("기간", f"{(df['date_column'].max() - df['date_column'].min()).days}일", "📅")
    
    # 차트
    st.subheader("시간대별 추이")
    fig = create_timeseries_chart(df)
    st.plotly_chart(fig, use_container_width=True)
    
    # 데이터 테이블
    with st.expander("📋 원본 데이터 보기"):
        st.dataframe(df, use_container_width=True)
else:
    st.info("👈 사이드바에서 날짜를 선택하고 '데이터 로드' 버튼을 클릭하세요.")
```

---

### Step 4: Git 커밋 (사내망 Jupyter)

```bash
# 사내망 Jupyter 터미널
cd pylon-test4/

# 상태 확인
git status

# .py 파일만 추가 (notebooks는 자동 제외됨)
git add data/datamart_connector.py
git add components/datamart_charts.py  # 생성했다면
git add pages/4_📊_Datamart_Analysis.py

git commit -m "feat: 데이터마트 연동 기능 추가"

# development 브랜치에 push
git push pylon-test4 development
```

---

### Step 5: 로컬 PC에서 테스트

```bash
# 로컬 PC (C:\251213_pylon)
cd C:\251213_pylon

# 변경사항 가져오기
git pull pylon-test4 development

# Streamlit 실행
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속하여 새 페이지 확인

---

### Step 6: Playground 배포

로컬 테스트 완료 후:

```bash
# master로 merge
git checkout master
git merge development

# 배포 (자동 빌드 시작!)
git push pylon-test4 master
```

Playground에서 자동 빌드 완료 후 확인

---

## ✅ 요약

| 환경 | 역할 | Streamlit 실행 |
|------|------|----------------|
| **사내망 Jupyter** | 개발 (노트북 실험 + 코드 정리) | ❌ 불필요 |
| **로컬 PC** | 테스트 | ✅ `streamlit run app.py` |
| **Playground** | 운영 | ✅ 자동 배포 |

**핵심:**
1. 사내망 Jupyter = 개발만 (Streamlit 실행 안 해도 됨)
2. Jupyter 노트북에서 충분히 검증
3. .py 파일로 정리 후 Git push
4. 로컬 PC 또는 Playground에서 확인

---

## 🚀 지금 할 일

```bash
# 사내망 Jupyter에서
cd pylon-test4/
mkdir notebooks
# 새 노트북 생성: notebooks/datamart_dev.ipynb
```

첫 셀에:
```python
import pandas as pd
print("✅ 시작!")
```

이제 데이터마트 연결부터 시작하세요! 🎯

