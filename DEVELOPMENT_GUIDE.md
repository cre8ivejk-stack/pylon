# PYLON 개발 가이드

## 개발 환경 설정

### 1. 브랜치 전략

```
main/master (운영)
    └── development (개발) ← 여기서 작업
```

**중요:** 
- `development` 브랜치에서만 개발 작업 진행
- `master` 브랜치에 push → pylon-test4 자동 배포
- 테스트 완료 후에만 `master`로 merge

### 2. Jupyter 환경 시작

```bash
# 개발 브랜치로 전환 (아직 안 했다면)
git checkout development

# Jupyter 패키지 설치 (처음 한 번만)
.\Scripts\pip.exe install -r requirements.txt

# Jupyter Lab 실행 (추천)
.\Scripts\jupyter.exe lab

# 또는 Jupyter Notebook 실행
.\Scripts\jupyter.exe notebook
```

브라우저에서 자동으로 열립니다: `http://localhost:8888`

### 3. 개발 워크플로우

#### Phase 1: 데이터 탐색 및 프로토타이핑 (Jupyter)

```
notebooks/
├── 01_data_exploration.ipynb      # 데이터마트 연결 테스트
├── 02_data_processing.ipynb       # 데이터 전처리 로직
├── 03_visualization_tests.ipynb   # 차트 프로토타입
└── 04_integration.ipynb           # 최종 통합 테스트
```

**작업 예시:**
```python
# notebooks/01_data_exploration.ipynb
import pandas as pd
import streamlit as st
import sys
sys.path.append('..')  # 상위 디렉토리 접근

# 기존 유틸리티 함수 재사용
from components.layout import create_header
from data.loader import load_data

# 사내 데이터마트 연결 테스트
df = pd.read_sql(query, connection)
df.head()
```

#### Phase 2: 코드 모듈화

Jupyter에서 검증된 코드를 Python 모듈로 정리:

```
data/
├── datamart_connector.py  # 데이터마트 연결 로직
└── datamart_queries.py    # SQL 쿼리 모음

pages/
└── datamart_analysis.py   # 새로운 분석 페이지
```

#### Phase 3: Streamlit 로컬 테스트

```bash
# 로컬에서 앱 실행 및 테스트
.\Scripts\streamlit.exe run app.py
```

브라우저에서 확인: `http://localhost:8501`

#### Phase 4: 배포 (테스트 완료 후에만!)

```bash
# 개발 브랜치 커밋
git add .
git commit -m "feat: 데이터마트 연동 추가"
git push pylon-test4 development

# 테스트 완료 후 master로 merge
git checkout master
git merge development
git push pylon-test4 master  # ⚠️ 자동 배포 시작!
```

## Git Remote 구성

```bash
# 현재 설정된 저장소
git remote -v
```

- **origin**: `cre8ivejk-stack/pylon` (백업/참고용)
- **pylon-test4**: `PGPRIVATE/playground-pylon-test4` (사내 운영)

## 주의사항

### ⚠️ 절대 하지 말 것
1. `master` 브랜치에서 직접 개발
2. 테스트 안 된 코드를 `master`에 merge
3. `notebooks/` 폴더를 Git에 커밋 (실험용 코드만 포함)

### ✅ 권장 사항
1. 자주 커밋 (development 브랜치)
2. 의미 있는 커밋 메시지 작성
   ```
   feat: 새 기능 추가
   fix: 버그 수정
   refactor: 코드 리팩토링
   docs: 문서 수정
   style: 코드 포맷팅
   ```
3. Jupyter에서 충분히 검증 후 Python 모듈로 이동

## 데이터마트 연동 예시

### 1. 데이터 로더 생성

```python
# data/datamart_connector.py
import pandas as pd
import streamlit as st
from typing import Optional

@st.cache_data(ttl=3600)  # 1시간 캐싱
def load_datamart_data(query: str) -> pd.DataFrame:
    """사내 데이터마트에서 데이터 로드"""
    # 연결 설정 (secrets.toml에서 관리)
    connection_string = st.secrets.get("datamart", {}).get("connection_string")
    
    if not connection_string:
        st.warning("데이터마트 연결 정보가 없습니다.")
        return pd.DataFrame()
    
    try:
        df = pd.read_sql(query, connection_string)
        return df
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return pd.DataFrame()
```

### 2. Secrets 설정

`.streamlit/secrets.toml` (Git에 커밋하지 않음):

```toml
[datamart]
connection_string = "postgresql://user:password@host:port/database"

# 또는 여러 환경 설정
[datamart.dev]
host = "dev-datamart.internal"
port = 5432
database = "analytics"

[datamart.prod]
host = "prod-datamart.internal"
port = 5432
database = "analytics"
```

### 3. 새 페이지 추가

```python
# pages/3_📊_Datamart_Analysis.py
import streamlit as st
import pandas as pd
from data.datamart_connector import load_datamart_data
from components.layout import create_header, create_metric_card

st.set_page_config(page_title="데이터마트 분석", layout="wide")
create_header()

st.title("📊 데이터마트 분석")

# 데이터 로드
query = """
    SELECT 
        date,
        metric_name,
        value
    FROM analytics.metrics
    WHERE date >= CURRENT_DATE - INTERVAL '30 days'
"""

df = load_datamart_data(query)

if not df.empty:
    # 메트릭 표시
    col1, col2, col3 = st.columns(3)
    with col1:
        create_metric_card("총 레코드", len(df), "📈")
    
    # 차트 표시
    st.plotly_chart(create_chart(df), use_container_width=True)
else:
    st.info("데이터를 불러올 수 없습니다.")
```

## 디버깅 팁

### Jupyter에서 Streamlit 컴포넌트 테스트

Jupyter에서는 Streamlit의 `st.*` 함수가 작동하지 않으므로:

```python
# Jupyter에서 실행 중인지 확인
try:
    import streamlit as st
    IN_STREAMLIT = True
except ImportError:
    IN_STREAMLIT = False

# 조건부 실행
if IN_STREAMLIT:
    st.write("Streamlit에서 실행 중")
else:
    print("Jupyter에서 실행 중")
```

### 로그 확인

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("디버그 메시지")
logger.info("정보 메시지")
logger.error("에러 메시지")
```

## 성능 최적화

1. **데이터 캐싱**: `@st.cache_data` 사용
2. **쿼리 최적화**: 필요한 컬럼만 SELECT
3. **페이지네이션**: 대용량 데이터는 페이지 단위로 로드
4. **Lazy Loading**: 탭/확장 패널 활용

## 참고 자료

- [Streamlit 공식 문서](https://docs.streamlit.io)
- [Plotly 차트 예시](https://plotly.com/python/)
- [Pandas 최적화](https://pandas.pydata.org/docs/user_guide/enhancingperf.html)

---

**문의**: 개발 중 문제 발생 시 팀에 문의하세요.

