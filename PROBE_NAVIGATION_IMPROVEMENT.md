# PROBE 네비게이션 개선 완료 요약

## 완료된 작업

### 1. 대화 기록 정렬: 최신이 위로 ✅
- **변경**: `pages/0_PYLON_PROBE.py`에서 `reversed(st.session_state.probe_history)` 사용
- **효과**: 최신 대화가 맨 위에 표시됨
- **주의사항**: `message_id`는 생성 시점에 부여되므로 렌더링 순서와 무관하게 key 충돌 없음

### 2. nav_payload에 subview 필드 추가 ✅
- **변경**: `src/copilot/navigation.py`의 `create_nav_links_from_plan()` 함수
- **nav_payload 스키마**:
  ```python
  {
    "target_page": "pages/1_에너지_인텔리전스.py",
    "subview": "bill_vs_actual",  # 페이지 내 탭/섹션 식별자
    "filters": {...},
    "context": {...}
  }
  ```

### 3. subview 매핑 강화 ✅
- **구현**: `_determine_subview()` 함수 추가
- **매핑 규칙**:
  - `comparison` + `bill_vs_actual_gap` → `"bill_vs_actual"`
  - `trend` + `cost_won` → `"trend_cost"`
  - `trend` + `usage_kwh` → `"trend_usage"`
  - `top_n` + `usage_kwh` → `"top_sites_usage"`
  - `anomaly` → `"anomaly"`
  - 기본값 → `"overview"`

### 4. 페이지 내부 탭 자동 선택 구현 ✅
- **변경**: `pages/1_에너지_인텔리전스.py`
- **구현 방식**:
  - `st.tabs` 대신 `st.radio` 사용 (기본 index 지원)
  - `probe_nav_subview`를 읽어서 탭 인덱스 계산
  - 조건부 렌더링으로 선택된 탭만 표시
- **subview → 탭 매핑**:
  - `"overview"` → 탭 0 (개요)
  - `"plan_vs_actual"` → 탭 1 (계획 대비 실적)
  - `"bill_vs_actual"` → 탭 2 (청구서 vs 실사용량)
  - `"trend_cost"`, `"trend_usage"`, `"top_sites_usage"` → 탭 0 (개요)

## 수정된 파일

1. **`pages/0_PYLON_PROBE.py`**
   - 대화 기록 렌더링 시 `reversed()` 적용

2. **`src/copilot/navigation.py`**
   - `create_nav_links_from_plan()`: nav_payload에 `subview` 추가
   - `_determine_subview()`: 질문 유형별 subview 매핑 함수 추가

3. **`pages/1_에너지_인텔리전스.py`**
   - `probe_nav_subview` 읽기 로직 추가
   - `st.tabs` → `st.radio` + 조건부 렌더링으로 변경
   - subview 기반 탭 자동 선택 구현

## 테스트 시나리오

### Q1: "중부지역 최근 2년간 전기료 변화 추이에 대해 설명해줘"
**기대 결과:**
- Plan: `query_type=trend`, `metric=cost_won`, `filters.region=["중부"]`
- subview: `"trend_cost"` → 탭 0 (개요) 자동 선택
- 답변 텍스트가 대화 기록 최상단에 1회만 표시
- "자세히 보기" 버튼 클릭 시:
  - 에너지 인텔리전스 페이지로 이동
  - 개요 탭이 자동 선택됨
  - 필터 자동 적용 (지역: 중부, 기간: 최근 2년)

### Q2: "이어서 전기료 상위국소 4개 알려줘"
**기대 결과:**
- Q1의 중부지역 컨텍스트 상속
- Plan: `query_type=top_n`, `metric=cost_won`, `filters.region=["중부"]` (상속), `top_n=4`
- 답변 텍스트가 대화 기록 최상단에 1회만 표시
- "자세히 보기" 버튼 클릭 시:
  - 에너지 인텔리전스 페이지로 이동
  - 개요 탭이 자동 선택됨
  - 필터 자동 적용 (지역: 중부)

### Q3: "수도권 청구서와 실사용량 차이 비교해줘"
**기대 결과:**
- Plan: `query_type=comparison`, `metric=bill_vs_actual_gap`, `filters.region=["수도권"]`
- subview: `"bill_vs_actual"` → 탭 2 (청구서 vs 실사용량) 자동 선택
- "자세히 보기" 버튼 클릭 시:
  - 에너지 인텔리전스 페이지로 이동
  - **청구서 vs 실사용량 탭이 자동 선택됨** ✅
  - 필터 자동 적용 (지역: 수도권)

## 주요 개선 사항

1. **대화 기록 정렬**
   - 최신 대화가 위에 표시되어 사용자 경험 개선
   - `message_id` 기반 key 정책으로 충돌 없음

2. **서브메뉴 자동 선택**
   - PROBE가 제공하는 링크 클릭 시 해당 탭/섹션이 자동으로 선택됨
   - 사용자가 수동으로 탭을 찾을 필요 없음

3. **subview 매핑**
   - 질문 유형과 지표에 따라 적절한 탭 자동 선택
   - 비교 질문은 비교 탭, 추이 질문은 개요 탭 등

4. **once-only 처리**
   - `probe_nav`는 읽은 후 삭제하여 재사용 방지
   - 주석으로 명확히 표시



