# PROBE 서브메뉴 자동 이동 기능 원복 완료

## 원복된 작업

### 1. subview 관련 로직 제거 ✅
- **`src/copilot/navigation.py`**:
  - `_determine_subview()` 함수 완전 제거
  - `create_nav_links_from_plan()`에서 subview 관련 코드 제거
  - nav_payload에서 `"subview"` 필드 제거
  - nav_payload 구조 단순화: `{"filters": {...}, "context": {...}}`만 유지

### 2. 탭 자동 선택 로직 제거 및 UI 복구 ✅
- **`pages/1_에너지_인텔리전스.py`**:
  - `probe_nav_subview` 읽기 로직 제거
  - `subview_to_tab` 매핑 제거
  - `st.radio` 기반 탭 선택 제거
  - **원래대로 복구**: `st.tabs` 사용
  - 조건부 렌더링 (`if selected_tab_idx == 0:`) 제거
  - `with tab1:`, `with tab2:`, `with tab3:` 구조로 복구

### 3. 필터 전달 최소 구조 유지 ✅
- `st.session_state["probe_nav"]["filters"]` 구조 유지
- 페이지 이동 시 필터만 전달, 탭/서브메뉴 선택은 제거

## 유지된 기능

### A) 대화 기록 최신-상단 정렬 ✅
- `pages/0_PYLON_PROBE.py`에서 `reversed(st.session_state.probe_history)` 사용
- 최신 대화가 맨 위에 표시됨
- `message_id` 기반 key 정책으로 충돌 없음

### B) 링크 버튼 안정화 (페이지 단위) ✅
- "자세히 보기" 버튼은 페이지 이동만 수행
- `st.session_state["probe_nav"]`에 filters 저장
- `st.switch_page("pages/<파일명>.py")` 실행
- 버튼 key: `f"probe_nav_btn_{message_id}_{idx}"`

## 수정된 파일

1. **`src/copilot/navigation.py`**
   - subview 관련 로직 완전 제거
   - nav_payload 구조 단순화

2. **`pages/1_에너지_인텔리전스.py`**
   - 탭 자동 선택 로직 제거
   - `st.tabs`로 원복

## 테스트 시나리오

### Q1: "중부지역 최근 2년간 전기료 변화 추이에 대해 설명해줘"
**기대 결과:**
- 답변 텍스트가 대화 기록 최상단에 1회만 표시
- "자세히 보기" 버튼 표시
- 버튼 클릭 시:
  - 에너지 인텔리전스 페이지로 이동 ✅
  - **개요 탭이 기본으로 표시됨** (자동 선택 없음) ✅
  - 필터 자동 적용 (지역: 중부, 기간: 최근 2년) ✅

### Q2: "이어서 전기료 상위국소 4개 알려줘"
**기대 결과:**
- Q1의 중부지역 컨텍스트 상속
- 답변 텍스트가 대화 기록 최상단에 1회만 표시
- "자세히 보기" 버튼 클릭 시 페이지 이동 및 필터 적용

### 재실행/스크롤 테스트
- 페이지 새로고침 후에도 에러 없음
- 히스토리 반복 렌더링 시에도 key 충돌 없음
- UI가 깨지지 않고 정상 표시됨

## 완료 기준 확인

- ✅ 서브메뉴/탭 자동 이동 기능 완전 제거
- ✅ UI가 원래대로 복구됨 (st.tabs 사용)
- ✅ 대화기록 최신이 상단에 위치
- ✅ 링크는 페이지 이동만 수행하며 정상 동작
- ✅ 화면 깨짐/에러 없음



