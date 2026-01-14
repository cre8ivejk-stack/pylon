# 사내망 Jupyter 워크플로우 (간단 버전)

## 📍 현재 상황
- ✅ 사내망 Jupyter에 `playground-pylon-test4` 클론 완료
- ✅ 로컬 PC에도 동일한 프로젝트 존재
- ✅ `development` 브랜치에서 작업 중

---

## 🎯 작업 방식

### 방식 1: Jupyter 노트북으로 실험 → Python 파일로 정리 (추천)

```
[사내망 Jupyter 환경]
pylon-test4/
├── notebooks/
│   ├── experiment_01.ipynb  ← 여기서 데이터 연동 실험
│   ├── experiment_02.ipynb  ← 차트 프로토타이핑
│   └── experiment_03.ipynb  ← 최종 검증
│
├── data/
│   └── datamart_connector.py  ← 검증된 코드를 여기 정리
│
└── pages/
    └── 4_📊_Datamart_Analysis.py  ← 새 페이지 여기 생성
```

#### Step 1: 사내망 Jupyter에서 노트북 생성

```bash
# 사내망 Jupyter에서
cd pylon-test4/notebooks/
# 새 노트북 생성: experiment_datamart.ipynb
```

#### Step 2: 노트북에서 개발 및 테스트

```python
# Cell 1: 데이터 로드 실험
import pandas as pd
import sqlalchemy

conn_string = "postgresql://user:pass@datamart-host:5432/db"
engine = sqlalchemy.create_engine(conn_string)

query = "SELECT * FROM your_table LIMIT 100"
df = pd.read_sql(query, engine)
df.head()
```

```python
# Cell 2: 전처리 실험
df['date'] = pd.to_datetime(df['date'])
df_clean = df.dropna()
# ... 계속 실험
```

```python
# Cell 3: 차트 실험
import plotly.graph_objects as go

fig = go.Figure()
fig.add_trace(go.Scatter(x=df['date'], y=df['value']))
fig.show()
```

#### Step 3: 검증 완료 후 Python 파일로 정리

노트북에서 잘 작동하는 코드를 정리:

```bash
# 같은 사내망 Jupyter 환경에서
# data/datamart_connector.py 파일 생성/수정
```

```python
# data/datamart_connector.py

import pandas as pd
import sqlalchemy
import streamlit as st

@st.cache_data(ttl=3600)
def load_datamart_data(start_date: str, end_date: str) -> pd.DataFrame:
    """Jupyter 노트북에서 검증된 로직을 그대로 복사"""
    conn_string = st.secrets.get("datamart", {}).get("connection_string")
    
    query = f"""
        SELECT * FROM your_table
        WHERE date BETWEEN '{start_date}' AND '{end_date}'
    """
    
    engine = sqlalchemy.create_engine(conn_string)
    df = pd.read_sql(query, engine)
    return df

def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """Jupyter에서 검증된 전처리 로직"""
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    # ... 검증된 로직
    return df
```

#### Step 4: 새 Streamlit 페이지 생성

```bash
# 같은 사내망 Jupyter 환경에서
# pages/4_📊_Datamart_Analysis.py 파일 생성
```

```python
# pages/4_📊_Datamart_Analysis.py

import streamlit as st
from data.datamart_connector import load_datamart_data, preprocess_data
from components.layout import create_header

st.set_page_config(page_title="데이터마트 분석", layout="wide")
create_header()

st.title("📊 데이터마트 분석")

# 날짜 선택
start_date = st.date_input("시작일")
end_date = st.date_input("종료일")

# 데이터 로드
df = load_datamart_data(str(start_date), str(end_date))
df = preprocess_data(df)

# 표시
st.dataframe(df)
```

#### Step 5: Git에 커밋 (중요!)

```bash
# 사내망 Jupyter 터미널에서
cd pylon-test4/

# development 브랜치 확인
git branch

# notebooks/ 폴더는 커밋하지 않음 (실험용)
# .py 파일만 커밋
git add data/datamart_connector.py
git add pages/4_📊_Datamart_Analysis.py

git commit -m "feat: 데이터마트 연동 추가"

# development 브랜치에 push (자동 배포 안 됨!)
git push pylon-test4 development
```

#### Step 6: 로컬 PC에서 동기화 (선택사항)

```bash
# 로컬 PC에서 (C:\251213_pylon)
git pull pylon-test4 development
```

#### Step 7: 테스트 완료 후 배포

```bash
# 사내망 Jupyter 또는 로컬 PC에서
git checkout master
git merge development
git push pylon-test4 master  # ← 이때 자동 배포!
```

---

### 방식 2: 사내망 Jupyter에서 바로 .py 파일 작성

노트북 없이 바로 Python 파일을 작성해도 됩니다:

```bash
# 사내망 Jupyter 환경에서
cd pylon-test4/data/
# datamart_connector.py 생성 및 편집

cd ../pages/
# 4_📊_Datamart_Analysis.py 생성 및 편집
```

단, 이 경우 실험하기 어려우므로 방식 1 추천!

---

## 🔄 전체 워크플로우 정리

```
┌─────────────────────────────────┐
│  사내망 Jupyter 환경             │
│  pylon-test4/ (클론됨)          │
└─────────────────────────────────┘
         │
         ▼
  notebooks/*.ipynb에서 실험
  - 데이터마트 연결 테스트
  - 쿼리 작성 및 데이터 확인
  - 전처리 로직 개발
  - 차트 프로토타이핑
         │
         ▼
  검증 완료된 코드를
  data/*.py, pages/*.py로 정리
         │
         ▼
  git add, commit, push
  (development 브랜치)
         │
         ▼
  ┌─────────────┐
  │ 로컬 PC에서 │ (선택사항)
  │ git pull    │
  │ 로컬 테스트 │
  └─────────────┘
         │
         ▼
  테스트 완료 후
  master에 merge & push
         │
         ▼
  ⚡ 자동 배포!
```

---

## 💡 핵심 포인트

### ✅ notebooks/ 폴더의 역할
- **실험실**: 자유롭게 시도, 에러 걱정 없음
- **Git 제외**: .gitignore에 설정됨
- **빠른 반복**: 셀 단위로 즉시 테스트

### ✅ .py 파일의 역할
- **최종 코드**: 검증된 것만 정리
- **Git 추적**: 버전 관리됨
- **운영 배포**: Streamlit 앱에서 사용

### ✅ 브랜치 전략
- **development**: 안전한 개발 공간 (자동 배포 ❌)
- **master**: 운영 버전 (자동 배포 ⚡)

---

## 🎯 당장 시작하기

### 1. 사내망 Jupyter 접속

### 2. 터미널에서 브랜치 확인
```bash
cd pylon-test4/
git status
git branch  # development 브랜치인지 확인
```

### 3. 첫 노트북 생성
```bash
cd notebooks/
# 새 노트북: datamart_test.ipynb 생성
```

### 4. 첫 셀에 코드 입력
```python
import pandas as pd
print("✅ 환경 준비 완료!")
print(f"Pandas 버전: {pd.__version__}")

# 사내 데이터마트 연결 테스트
# TODO: 실제 연결 정보 입력
```

---

## ❓ 자주 묻는 질문

### Q1: 노트북 파일은 Git에 올라가나요?
**A:** 아니오. `.gitignore`에 `notebooks/` 폴더가 제외되어 있어서 커밋되지 않습니다.

### Q2: 사내망에서 작업한 걸 로컬 PC로 가져와야 하나요?
**A:** 선택사항입니다. 사내망에서 `git push`만 하면 로컬에서 `git pull`로 가져올 수 있습니다.

### Q3: Streamlit 앱은 어디서 실행하나요?
**A:** 
- 개발 중: 사내망 Jupyter에서 실행 가능 (`streamlit run app.py`)
- 최종 배포: master 브랜치 push → Playground 자동 배포

### Q4: development 브랜치에 push하면 배포되나요?
**A:** 아니오! development 브랜치는 자동 배포 안 됩니다. master에 merge할 때만 배포됩니다.

---

## 🚀 시작하세요!

지금 바로 사내망 Jupyter에 접속하여 작업을 시작하시면 됩니다!

