# PYLON 배포 가이드

## 빠른 시작 (Quick Start)

### 1단계: 환경 설정

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 가상환경 활성화 (Linux/Mac)
source venv/bin/activate
```

### 2단계: 의존성 설치

```bash
pip install -r requirements.txt
```

### 3단계: 앱 실행

```bash
streamlit run app.py
```

브라우저가 자동으로 `http://localhost:8501`로 열립니다.

## 프로젝트 구조

```
pylon/
├── app.py                          # 메인 진입점
├── requirements.txt                # Python 의존성
├── README.md                       # 프로젝트 문서
├── DEPLOYMENT_GUIDE.md            # 이 파일
├── .gitignore                     # Git 제외 파일
│
├── src/                           # 핵심 비즈니스 로직
│   ├── __init__.py
│   ├── models.py                  # 데이터 모델 (Action, Experiment 등)
│   ├── data_access.py             # 데이터 접근 레이어
│   ├── sample_data.py             # 샘플 데이터 생성
│   ├── analytics.py               # 분석 및 계산 함수
│   ├── actions.py                 # Action 관리 시스템
│   └── experiments.py             # 실험 관리 시스템
│
├── components/                    # 재사용 가능 UI 컴포넌트
│   ├── __init__.py
│   ├── global_controls.py         # 전역 필터 및 거버넌스 배지
│   ├── action_inbox.py            # Action Inbox 컴포넌트
│   └── widget_card.py             # Widget 카드 컴포넌트
│
├── pages/                         # Streamlit 페이지 (메뉴)
│   ├── __init__.py
│   ├── 1_energy_intelligence.py   # Energy Intelligence 메뉴
│   ├── 2_performance_risk.py      # Performance & Risk 메뉴
│   ├── 3_optimization.py          # Optimization & Action 메뉴
│   └── 4_validation.py            # Validation & IDEA 메뉴
│
├── tests/                         # 단위 테스트
│   ├── __init__.py
│   └── test_analytics.py          # Analytics 모듈 테스트
│
└── data/                          # 데이터 파일 (자동 생성)
    ├── .gitkeep
    ├── sample_*.parquet           # 샘플 데이터 (첫 실행시 생성)
    ├── actions.parquet            # Action 이력
    └── experiments.parquet        # 실험 이력
```

## 기능 개요

### 1. Energy Intelligence (⚡)

**위치**: `pages/1_energy_intelligence.py`

#### 하위 메뉴:
- **Overview**: 전체 에너지 사용 현황, KPI 타일, 주요 변동 Top 5
- **계획 대비 실적**: 월별 추이 차트, Variance 분석 테이블
- **청구서 vs 실사용량**: 오차 분포, 분류별 현황, 조사 필요 국소

#### 주요 기능:
- 전력량/비용 KPI 표시
- YoY 비교
- Bill vs Actual 오차 분석 및 분류
- 조사 필요 국소에 대한 Action 생성

---

### 2. Performance & Risk (📊)

**위치**: `pages/2_performance_risk.py`

#### 하위 메뉴:
- **과제별 성과 관리**: 프로젝트별 목표/실적, 달성률
- **전기요금 Risk Monitoring**: Risk Score 계산, High Risk 국소 탐지

#### 주요 기능:
- Risk Score = Impact × Likelihood × Confidence
- 리스크 히트맵 (지역 × 계약유형)
- High Risk 국소 Action 생성

---

### 3. Optimization & Action (🎯)

**위치**: `pages/3_optimization.py`

#### 하위 메뉴:
- **계약전력 최적화**: 감설/증설 권고
- **이상 국소 탐지**: Z-score 기반 이상 패턴 탐지
- **사용량 0 국소**: 연속 0 사용 국소 탐지

#### 주요 기능:
- 계약전력 최적화 권고 (6개월 사용 패턴 분석)
- 이상 탐지 (Z-score > 2.0)
- 사용량 0 국소 지역별 분포

---

### 4. Validation & IDEA (🔬)

**위치**: `pages/4_validation.py`

#### 하위 메뉴:
- **3G Phase-Out 효과 검증**: Before/After 비교, 트래픽 정규화
- **솔루션 실증 (IDEA)**: 실험 등록/관리, 상태 추적

#### 주요 기능:
- 효과 검증 (Before/After 비교)
- 실험 CRUD (Create/Read/Update/Delete)
- 검증 완료 Action 생성

---

## Action 라이프사이클

### Action 생성
각 위젯에서 "⚡ 조치 생성" 버튼 클릭 → 자동으로 Action ID 부여 → `data/actions.parquet`에 저장

### Action 추적
- **Action Inbox**: 메인 화면 또는 사이드바에서 확인
- **상태**: TODO → DOING → DONE
- **필터**: 담당자별, 카테고리별, 지연 여부

### Action 카테고리
- 계약전력 최적화
- 요금제 변경
- 이상 조사
- 사용량 0 조사
- 청구서 불일치
- 효과 검증
- 기타

---

## 데이터 스키마

### bills (청구서)
```python
{
    'yymm': str,              # 년월 (예: "2401")
    'site_id': str,           # 국소 ID
    'kwh_bill': float,        # 청구 전력량 (kWh)
    'cost_bill': float,       # 청구 금액 (원)
    'contract_type': str,     # 계약 유형 ("정액" / "종량")
    'contract_power_kw': float,  # 계약전력 (kW)
    'region': str             # 지역
}
```

### actual (실사용량)
```python
{
    'yymm': str,
    'site_id': str,
    'kwh_actual': float,      # 실제 사용량 (kWh)
    'cost_actual_est': float, # 실제 추정 금액 (원)
    'data_source': str,       # "EMS" / "PRB" / "EST"
    'confidence': float       # 신뢰도 (0~1)
}
```

### plan (계획)
```python
{
    'yymm': str,
    'site_id': str,           # Optional
    'kwh_plan': float,
    'cost_plan': float
}
```

### traffic (트래픽)
```python
{
    'yymm': str,
    'site_id': str,
    'gb_traffic': float       # 트래픽 (GB)
}
```

### site_master (국소 마스터)
```python
{
    'site_id': str,
    'site_name': str,
    'region': str,            # "수도권", "충청", "호남", "영남", "강원"
    'site_type': str,         # "기지국", "통합국", "사옥", "중계국"
    'voltage': str,           # "저압", "고압"
    'contract_type': str      # "정액", "종량"
}
```

---

## 핵심 분석 로직

### 1. Risk Score 계산
```python
risk_score = (impact / 10_000_000) × likelihood × confidence
```
- **impact**: 비용 차이 절댓값
- **likelihood**: 과거 이상 발생 빈도 (0~1)
- **confidence**: 데이터 신뢰도 (0~1)

### 2. Plan Variance
```python
variance = actual - plan
variance_pct = (variance / plan) × 100
achievement_rate = (actual / plan) × 100
```

### 3. Bill vs Actual Error
```python
error_pct = ((actual - bill) / bill) × 100
```

### 4. 계약전력 권고
```python
demand_est = kwh / 720  # 시간당 평균 수요
recommended_kw = max(demand_est) × safety_margin (1.15)
savings = (current_kw - recommended_kw) × 8000  # 기본요금
```

---

## 테스트 실행

```bash
# 전체 테스트
pytest tests/ -v

# 특정 모듈 테스트
pytest tests/test_analytics.py -v

# 커버리지 리포트
pytest tests/ --cov=src --cov-report=html
```

---

## 실제 데이터 연동

### 방법 1: 파일 업로드
메인 화면 하단 "📁 데이터 소스 관리" 섹션에서 CSV/Parquet 파일 업로드

### 방법 2: 데이터베이스 연동
`src/data_access.py`의 `DataAccessLayer` 클래스 수정:

```python
# 예시: PostgreSQL 연동
import psycopg2
import pandas as pd

class DataAccessLayer:
    def __init__(self, db_config):
        self.conn = psycopg2.connect(**db_config)
    
    def load_bills(self):
        query = "SELECT * FROM bills WHERE yymm >= '2401'"
        return pd.read_sql(query, self.conn)
```

### 방법 3: API 연동
```python
import requests

def load_bills_from_api():
    response = requests.get("https://api.skt.com/energy/bills")
    data = response.json()
    return pd.DataFrame(data)
```

---

## 성능 최적화

### 캐싱
- `@st.cache_data`: 데이터 로드 함수에 자동 캐싱 적용됨
- 캐시 TTL: 1시간 (3600초)

### 대용량 데이터 처리
- Parquet 파일 사용 (CSV 대비 10배 빠름)
- 필터링 먼저 수행 후 집계
- 필요한 컬럼만 선택

---

## 문제 해결

### 1. 샘플 데이터가 생성되지 않음
```bash
# data 폴더 삭제 후 재실행
rm -rf data
mkdir data
streamlit run app.py
```

### 2. Plotly 차트가 표시되지 않음
```bash
pip install --upgrade plotly
```

### 3. 한글 깨짐
- Streamlit은 UTF-8을 기본 사용
- CSV 업로드 시 UTF-8-BOM 또는 EUC-KR 인코딩 확인

### 4. 메모리 부족
- 데이터 필터링 범위 축소 (기간/지역)
- Parquet 파일 사용
- 샘플 데이터 개수 줄이기 (`src/sample_data.py`에서 `n_sites` 조정)

---

## 커스터마이징

### 거버넌스 배지 변경
`src/models.py`의 `GovernanceBadge` 클래스 수정

### 컬러 테마 변경
`.streamlit/config.toml` 파일 생성:
```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
```

---

## 프로덕션 배포

### Streamlit Cloud
```bash
# GitHub에 push 후
# streamlit.io에서 Connect Repository
```

### Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501"]
```

### 온프레미스
```bash
# systemd service 생성
sudo nano /etc/systemd/system/pylon.service

[Unit]
Description=PYLON Energy Platform
After=network.target

[Service]
User=pylon
WorkingDirectory=/opt/pylon
ExecStart=/opt/pylon/venv/bin/streamlit run app.py --server.port=8501
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 라이선스

Internal Use Only - SKT

## 문의

Network센터 Energy팀






