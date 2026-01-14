# 사내망 전용 개발 워크플로우 (보안 환경)

## 🔒 보안 제약 사항
- ❌ 사내 데이터를 외부(로컬 PC)로 반출 불가
- ❌ 로컬 PC에서 데이터마트 접근 불가
- ✅ 사내망 Jupyter에서만 데이터 접근 가능
- ✅ Playground에 배포해야 확인 가능

---

## 🎯 최적 워크플로우

### 핵심 전략: Jupyter에서 최대한 검증 후 배포

```
[사내망 Jupyter 환경]
    ↓
1. 노트북에서 충분히 개발 및 검증 (90%)
   - 데이터 로드 확인
   - 전처리 로직 검증
   - 차트가 제대로 나오는지 확인
    ↓
2. .py 파일로 정리 (신중하게)
    ↓
3. development 브랜치에 push
    ↓
4. Streamlit 테스트가 필요하다면?
   → 옵션 A: 사내망 Jupyter에서 Streamlit 실행 시도
   → 옵션 B: master 배포 전 최종 리뷰
    ↓
5. master에 merge & push
    ↓
[Playground 자동 배포]
    ↓
6. 사내망에서 Playground 앱 접속하여 확인
```

---

## 📋 상세 단계

### Step 1: 사내망 Jupyter에서 철저히 검증

#### 노트북에서 할 일 (매우 중요!)

```python
# notebooks/datamart_dev.ipynb

# ============================================
# 1. 데이터 로드 검증
# ============================================

import pandas as pd
import sqlalchemy

conn = "postgresql://user:pass@host/db"
engine = sqlalchemy.create_engine(conn)

# 실제 쿼리 테스트
query = """
    SELECT *
    FROM your_table
    WHERE date_column >= '2024-01-01'
    LIMIT 100
"""

df = pd.read_sql(query, engine)
print(f"✅ 데이터 로드: {len(df)} rows")
df.head()

# ============================================
# 2. 전처리 검증
# ============================================

def preprocess_data(df):
    df = df.copy()
    df['date_column'] = pd.to_datetime(df['date_column'])
    df = df.dropna(subset=['important_col'])
    return df

df_clean = preprocess_data(df)
print(f"✅ 전처리: {len(df)} → {len(df_clean)} rows")
df_clean.info()

# ============================================
# 3. 차트 검증 (매우 중요!)
# ============================================

import plotly.graph_objects as go

def create_chart(df):
    """Streamlit에 들어갈 차트 미리 테스트"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['date_column'],
        y=df['value'],
        mode='lines+markers',
        name='값'
    ))
    
    fig.update_layout(
        title='시계열 차트',
        xaxis_title='날짜',
        yaxis_title='값',
        height=400,
        template='plotly_white'
    )
    
    return fig

# 차트가 제대로 나오는지 확인!
fig = create_chart(df_clean)
fig.show()  # Jupyter에서 바로 확인

# ============================================
# 4. 집계 로직 검증
# ============================================

# Streamlit에서 보여줄 지표 계산
metrics = {
    'total_records': len(df_clean),
    'sum_value': df_clean['value'].sum(),
    'avg_value': df_clean['value'].mean(),
    'date_range': f"{df_clean['date_column'].min()} ~ {df_clean['date_column'].max()}"
}

print("=== 핵심 지표 ===")
for key, val in metrics.items():
    print(f"{key}: {val}")

# ============================================
# 5. 에러 처리 테스트
# ============================================

# 빈 데이터 상황 테스트
empty_df = pd.DataFrame()
try:
    result = preprocess_data(empty_df)
    print("✅ 빈 데이터 처리 OK")
except Exception as e:
    print(f"❌ 에러 발생: {e}")
    # 함수 수정 필요!

# ============================================
# 6. 최종 통합 테스트
# ============================================

def full_pipeline(start_date, end_date):
    """전체 파이프라인 한번에 실행"""
    # 로드
    query = f"""
        SELECT * FROM your_table
        WHERE date_column BETWEEN '{start_date}' AND '{end_date}'
    """
    df = pd.read_sql(query, engine)
    
    # 전처리
    df = preprocess_data(df)
    
    # 지표 계산
    metrics = {
        'total': len(df),
        'sum': df['value'].sum()
    }
    
    # 차트 생성
    fig = create_chart(df)
    
    return df, metrics, fig

# 여러 날짜 범위로 테스트
test_df, test_metrics, test_fig = full_pipeline('2024-01-01', '2024-01-31')
print(f"✅ 통합 테스트 완료: {test_metrics}")
test_fig.show()

print("\n🎉 모든 검증 완료! .py 파일로 옮길 준비 됨")
```

---

### Step 2: .py 파일로 신중하게 정리

노트북에서 **완벽히 검증된 코드만** 복사

#### `data/datamart_connector.py`

```python
"""
사내 데이터마트 연결
※ Jupyter 노트북에서 완전히 검증됨
"""

import pandas as pd
import sqlalchemy
import streamlit as st

@st.cache_data(ttl=3600)
def load_datamart_data(start_date: str, end_date: str) -> pd.DataFrame:
    """
    데이터마트에서 데이터 로드
    ※ Jupyter에서 검증된 쿼리 사용
    """
    # Secrets에서 연결 정보 가져오기
    config = st.secrets.get("datamart", {})
    
    if not config:
        st.error("데이터마트 연결 정보가 없습니다.")
        return pd.DataFrame()
    
    conn_string = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
    
    try:
        engine = sqlalchemy.create_engine(conn_string)
        
        # Jupyter에서 검증된 쿼리 그대로 복사
        query = f"""
            SELECT *
            FROM your_table
            WHERE date_column BETWEEN '{start_date}' AND '{end_date}'
        """
        
        df = pd.read_sql(query, engine)
        return df
    
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return pd.DataFrame()

def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    데이터 전처리
    ※ Jupyter에서 검증된 로직
    """
    if df.empty:
        return df
    
    df = df.copy()
    # Jupyter에서 검증된 로직 그대로 복사
    df['date_column'] = pd.to_datetime(df['date_column'])
    df = df.dropna(subset=['important_col'])
    return df

def calculate_metrics(df: pd.DataFrame) -> dict:
    """
    핵심 지표 계산
    ※ Jupyter에서 검증된 로직
    """
    if df.empty:
        return {
            'total_records': 0,
            'sum_value': 0,
            'avg_value': 0
        }
    
    return {
        'total_records': len(df),
        'sum_value': df['value'].sum(),
        'avg_value': df['value'].mean()
    }
```

#### `components/datamart_charts.py`

```python
"""
데이터마트 시각화
※ Jupyter 노트북에서 완전히 검증됨
"""

import plotly.graph_objects as go
import pandas as pd

def create_timeseries_chart(df: pd.DataFrame) -> go.Figure:
    """
    시계열 차트
    ※ Jupyter에서 검증됨 - 차트가 제대로 나오는 것 확인됨
    """
    fig = go.Figure()
    
    # Jupyter에서 검증된 차트 코드 그대로 복사
    fig.add_trace(go.Scatter(
        x=df['date_column'],
        y=df['value'],
        mode='lines+markers',
        name='값'
    ))
    
    fig.update_layout(
        title='시계열 차트',
        xaxis_title='날짜',
        yaxis_title='값',
        height=400,
        template='plotly_white'
    )
    
    return fig
```

#### `pages/4_📊_Datamart_Analysis.py`

```python
"""
데이터마트 분석 페이지
※ 로직은 Jupyter에서 모두 검증됨
"""

import streamlit as st
import pandas as pd
from datetime import timedelta

from data.datamart_connector import (
    load_datamart_data,
    preprocess_data,
    calculate_metrics
)
from components.datamart_charts import create_timeseries_chart
from components.layout import create_header, create_metric_card

st.set_page_config(
    page_title="데이터마트 분석",
    page_icon="📊",
    layout="wide"
)

create_header()

st.title("📊 데이터마트 분석")

# 사이드바
with st.sidebar:
    st.header("필터")
    end_date = st.date_input("종료일", value=pd.Timestamp.now())
    start_date = st.date_input("시작일", value=end_date - timedelta(days=30))
    load_btn = st.button("데이터 로드", type="primary")

# 데이터 로드
if load_btn:
    with st.spinner("데이터 로딩 중..."):
        df = load_datamart_data(str(start_date), str(end_date))
        
        if df.empty:
            st.warning("데이터가 없습니다.")
            st.stop()
        
        # 전처리 (Jupyter에서 검증됨)
        df = preprocess_data(df)
        st.session_state['df'] = df
        st.success("✅ 데이터 로드 완료")

# 표시
if 'df' in st.session_state:
    df = st.session_state['df']
    
    # 지표 (Jupyter에서 검증됨)
    metrics = calculate_metrics(df)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        create_metric_card("총 레코드", f"{metrics['total_records']:,}", "📊")
    with col2:
        create_metric_card("합계", f"{metrics['sum_value']:,.0f}", "📈")
    with col3:
        create_metric_card("평균", f"{metrics['avg_value']:,.1f}", "📉")
    
    # 차트 (Jupyter에서 검증됨)
    st.subheader("시계열 추이")
    fig = create_timeseries_chart(df)
    st.plotly_chart(fig, use_container_width=True)
    
    # 테이블
    with st.expander("📋 데이터 테이블"):
        st.dataframe(df, use_container_width=True)
else:
    st.info("👈 사이드바에서 날짜를 선택하고 데이터를 로드하세요.")
```

---

### Step 3: Secrets 파일 준비

**중요!** Playground에 배포하기 전에 secrets 설정 필요

`.streamlit/secrets.toml` (로컬에는 샘플, Playground에는 실제 값)

```toml
[datamart]
host = "datamart-host.internal"
port = 5432
database = "analytics"
user = "your-username"
password = "your-password"
```

---

### Step 4: Git 커밋 및 배포

```bash
# 사내망 Jupyter 터미널
cd pylon-test4/

# 파일 확인
git status

# 스테이징
git add data/datamart_connector.py
git add components/datamart_charts.py
git add pages/4_📊_Datamart_Analysis.py

# 커밋 (신중하게!)
git commit -m "feat: 데이터마트 연동 추가

- 데이터 로드 함수 (Jupyter 검증 완료)
- 전처리 로직 (Jupyter 검증 완료)
- 시계열 차트 (Jupyter 검증 완료)
- 새 페이지 추가"

# development에 먼저 push (안전)
git push pylon-test4 development

# 코드 리뷰 (직접 확인)
# 문제없다고 판단되면...

# master에 merge
git checkout master
git merge development

# 배포! (자동 빌드 시작)
git push pylon-test4 master
```

---

### Step 5: Playground에서 확인

1. Playground 빌드 완료 대기 (시간 소요)
2. 사내망에서 Playground 앱 접속
3. 새 페이지 "📊 데이터마트 분석" 확인
4. 날짜 선택 → 데이터 로드 → 결과 확인

**문제 발견 시:**
```bash
# 사내망 Jupyter로 돌아가서
git checkout development
# 노트북에서 다시 디버깅...
```

---

## 💡 핵심 팁

### ✅ Jupyter에서 철저히 검증하기

1. **데이터 로드**: 쿼리가 제대로 작동하는가?
2. **전처리**: 빈 데이터, NULL, 이상치 처리 확인
3. **차트**: `fig.show()`로 실제로 보이는지 확인
4. **지표**: 계산 결과가 맞는지 확인
5. **에러 케이스**: 다양한 상황 테스트

### ✅ 배포 전 체크리스트

- [ ] Jupyter에서 모든 함수 테스트 완료
- [ ] 차트가 제대로 나오는 것 확인
- [ ] 에러 처리 코드 추가
- [ ] Secrets 파일 준비 (Playground)
- [ ] 코드 최종 리뷰
- [ ] development 브랜치에 먼저 push
- [ ] 문제없으면 master에 merge

### ✅ 빠른 반복을 위한 팁

```python
# Jupyter 노트북에서 가능한 한 많이 테스트

# 1. Mock Streamlit (Jupyter에서 테스트)
class MockST:
    """Streamlit 함수 모의 객체"""
    def error(self, msg): print(f"ERROR: {msg}")
    def warning(self, msg): print(f"WARNING: {msg}")
    def success(self, msg): print(f"SUCCESS: {msg}")

# Streamlit 없이 테스트
st_mock = MockST()

# 2. 함수를 독립적으로 만들기
def load_data_pure(conn_string, start_date, end_date):
    """Streamlit 의존성 없는 순수 함수"""
    engine = sqlalchemy.create_engine(conn_string)
    query = f"SELECT ... WHERE date BETWEEN '{start_date}' AND '{end_date}'"
    return pd.read_sql(query, engine)

# Jupyter에서 직접 테스트 가능
df = load_data_pure(conn_string, '2024-01-01', '2024-01-31')
```

---

## 🔄 전체 워크플로우

```
[사내망 Jupyter 노트북]
  ↓ 90% 시간 투자
  - 데이터 로드 검증
  - 전처리 검증
  - 차트 검증
  - 지표 검증
  - 에러 케이스 테스트
  ↓
[.py 파일로 정리]
  ↓ 신중하게
  - 검증된 코드만 복사
  - 주석 추가
  ↓
[Git Push]
  ↓ development → master
  ↓
[Playground 배포]
  ↓ 자동 빌드
  ↓
[사내망에서 확인]
  ✅ 성공 → 완료
  ❌ 실패 → Jupyter로 돌아가서 수정
```

---

## ⚠️ 주의사항

1. **배포 전 Jupyter에서 충분히 테스트** (90% 이상 확신)
2. **development 브랜치 활용** (바로 master 금지)
3. **에러 처리 철저히** (빈 데이터, 연결 실패 등)
4. **Secrets 관리** (Playground에 미리 설정)
5. **커밋 메시지 상세히** (나중에 롤백 시 도움)

---

## 🚀 시작하기

```bash
# 사내망 Jupyter
cd pylon-test4/
mkdir notebooks
git checkout development
```

```python
# notebooks/datamart_dev.ipynb
import pandas as pd
print("✅ 시작!")

# 여기서 충분히 개발하고 검증하세요!
# 배포는 확신이 들 때만!
```

