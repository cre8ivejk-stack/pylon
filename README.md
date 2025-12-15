# PYLON - SKT Network센터 Energy Operations Platform

**Energy Operations Backbone** - Decision → Action → Validation 라이프사이클을 지원하는 에너지 운영 플랫폼

## 개요

PYLON은 단순 대시보드가 아닌, 의사결정부터 조치 실행, 검증까지 전체 운영 라이프사이클을 지원하는 Streamlit 기반 운영 플랫폼입니다.

### 주요 기능

- **Energy Intelligence**: 계획 대비 실적, 청구서 vs 실사용량 분석
- **Performance & Risk Control**: 과제 성과 관리, 전기요금 리스크 모니터링
- **Optimization & Action**: 계약전력 최적화, 요금제 변경 추천, 이상 탐지
- **Validation & IDEA**: 3G Phase-Out 효과 검증, 솔루션 실증 실험 관리
- **Action 관리**: 조치 생성/추적/완료 라이프사이클

## 설치 및 실행

### 1. 환경 설정

```bash
# Python 3.9+ 권장
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 실행

```bash
streamlit run app.py
```

브라우저가 자동으로 열리며 `http://localhost:8501`로 접속됩니다.

## 폴더 구조

```
pylon/
├── README.md              # 이 파일
├── requirements.txt       # Python 의존성
├── app.py                # 메인 진입점
├── data/                 # 데이터 저장 폴더 (자동 생성)
│   ├── sample_*.parquet  # 샘플 데이터 (첫 실행시 생성)
│   ├── actions.parquet   # 조치 이력
│   └── experiments.parquet # 실험 이력
├── src/                  # 핵심 로직
│   ├── data_access.py    # 데이터 접근 레이어
│   ├── sample_data.py    # 샘플 데이터 생성
│   ├── models.py         # 데이터 모델
│   ├── analytics.py      # 분석 로직
│   ├── actions.py        # Action 관리
│   └── experiments.py    # 실험 관리
├── pages/                # Streamlit 페이지
│   ├── 1_energy_intelligence.py
│   ├── 2_performance_risk.py
│   ├── 3_optimization.py
│   └── 4_validation.py
├── components/           # 재사용 가능 컴포넌트
│   ├── global_controls.py
│   ├── action_inbox.py
│   └── widget_card.py
└── tests/               # 단위 테스트
    └── test_analytics.py
```

## 데이터 소스

### 샘플 데이터 사용 (기본)

첫 실행시 `data/` 폴더에 샘플 데이터가 자동 생성됩니다. 앱을 즉시 사용할 수 있습니다.

### 실제 데이터 연동

사이드바에서 "데이터 소스" 섹션을 통해 CSV/Parquet 파일을 업로드할 수 있습니다.

필요한 데이터 스키마:

#### bills (청구서 데이터)
- `yymm`: str, 년월 (예: "2401")
- `site_id`: str, 국소 ID
- `kwh_bill`: float, 청구 전력량 (kWh)
- `cost_bill`: float, 청구 금액 (원)
- `contract_type`: str, 계약 유형 ("정액" / "종량")
- `contract_power_kw`: float, 계약전력 (kW)
- `region`: str, 지역

#### actual (실사용량 데이터)
- `yymm`: str, 년월
- `site_id`: str, 국소 ID
- `kwh_actual`: float, 실제 사용량 (kWh)
- `cost_actual_est`: float, 실제 추정 금액 (원)
- `data_source`: str, 데이터 출처 ("EMS" / "PRB" / "EST")
- `confidence`: float, 신뢰도 (0~1)

#### plan (계획 데이터)
- `yymm`: str, 년월
- `site_id`: str, 국소 ID (optional)
- `kwh_plan`: float, 계획 전력량 (kWh)
- `cost_plan`: float, 계획 금액 (원)

#### traffic (트래픽 데이터)
- `yymm`: str, 년월
- `site_id`: str, 국소 ID
- `gb_traffic`: float, 트래픽 (GB)

#### site_master (국소 마스터)
- `site_id`: str, 국소 ID
- `site_name`: str, 국소명
- `region`: str, 지역 (예: "수도권", "충청")
- `site_type`: str, 설비 유형 (예: "기지국", "통합국")
- `voltage`: str, 전압 (예: "고압", "저압")
- `contract_type`: str, 계약 유형

## 주요 기능 설명

### Action 라이프사이클

1. **조치 생성**: 각 위젯에서 "조치 생성" 버튼 클릭
2. **Action Inbox**: 상단에서 본인에게 할당된 조치 확인
3. **상태 업데이트**: TODO → DOING → DONE
4. **검증**: 완료된 조치의 효과 측정

### Governance 배지

화면 상단에 거버넌스 결과가 배지로 표시됩니다:
- **Official 기준**: 현재 적용중인 기준 버전
- **Plan Locked**: 계획 Lock 여부
- **Data Freshness**: 데이터 신선도

## 테스트

```bash
pytest tests/
```

## 개발 참고사항

- **캐싱**: 대용량 데이터는 `@st.cache_data`로 캐싱됩니다
- **한글 지원**: UI 라벨은 한글, 차트 라벨은 영문 fallback 가능
- **타입 힌팅**: 모든 함수에 타입 힌팅 적용
- **에러 핸들링**: 누락 컬럼, 빈 데이터셋에 대한 robust 처리

## 향후 실제 데이터 연동시

`src/data_access.py`의 `DataAccessLayer` 클래스를 수정하여 실제 데이터베이스 연결로 대체:
- SQL 쿼리 연동 (Oracle, PostgreSQL 등)
- API 호출 (EMS, PRB 시스템)
- Parquet/Delta Lake 연동

## 라이선스

Internal Use Only - SKT

## 문의

Network센터 Energy팀




