# PROBE 페이지 리팩토링 완료 요약

## 해결된 문제

### 1. 중복 출력 제거 ✅
- **문제**: 대화 기록 안에 동일한 PROBE 답변이 2번 출력됨
- **해결**: 
  - `render_chat_message()`가 답변 텍스트를 1회만 출력
  - `render_probe_response()`는 답변 텍스트를 출력하지 않고, evidence와 links만 출력
  - 중복 방지 원칙을 함수 주석에 명확히 기록

### 2. st.expander key 에러 해결 ✅
- **문제**: `TypeError: LayoutsMixin.expander() got an unexpected keyword argument 'key'`
- **해결**: 
  - `st.expander()` 호출에서 `key` 파라미터 제거
  - expander는 위젯 key 충돌 대상이 아니므로 key 불필요
  - 예외 처리 추가 (expander 실패 시 fallback)

### 3. 링크 버튼 안정화 ✅
- **문제**: "🔗 자세히 보기" 링크가 제대로 나오지 않거나 에러 발생
- **해결**:
  - 링크 버튼 key를 `f"probe_nav_btn_{message_id}_{idx}"` 형식으로 통일
  - 링크가 없을 때도 안정적으로 표시 ("표시할 링크 없음" 메시지)
  - 예외 처리 추가 (버튼 생성 실패 시 에러 메시지 표시)
  - `st.switch_page()` 사용, query string 미사용

### 4. 멀티턴 대화 보장 ✅
- **문제**: 2번째 질문 입력 시 반응 없음 (렌더 에러로 앱 중단)
- **해결**:
  - 모든 렌더링 단계에 try/except 추가
  - `_process_query()` 함수 전체를 try/except로 감싸 앱 중단 방지
  - 대화 기록 렌더링에도 예외 처리 추가
  - 컨텍스트 상속 로직은 이미 구현되어 있음 (`plan_merge`)

### 5. 파일명 변경 및 메뉴 순서 조정 ✅
- **변경**: `pages/6_자연어_질의.py` → `pages/0_PYLON_PROBE.py`
- **효과**: Streamlit 멀티페이지에서 메뉴 최상단에 표시됨
- **업데이트**: `app.py` 및 다른 페이지들의 주석 업데이트

## 수정된 파일

1. **`pages/0_PYLON_PROBE.py`** (신규 생성)
   - 기존 `6_자연어_질의.py`를 리팩토링하여 생성
   - 예외 처리 강화
   - 컨텍스트 관리 개선

2. **`src/copilot/ui.py`**
   - `render_probe_response()`: 답변 텍스트 출력 제거, st.expander key 제거
   - `render_chat_message()`: 중복 방지 원칙 명확화
   - 링크 버튼 안정화 및 예외 처리

3. **`app.py`**
   - 파일명 참조 업데이트: `6_자연어_질의.py` → `0_PYLON_PROBE.py`

4. **기타 페이지들** (`1_에너지_인텔리전스.py`, `2_성과_리스크_관리.py`, `3_최적화_실행.py`, `4_검증_실증.py`)
   - 주석 업데이트: Copilot → PROBE, 파일명 업데이트

5. **`pages/6_자연어_질의.py`** (삭제)
   - 기존 파일 삭제

## 테스트 시나리오

### Q1: "중부지역 최근 2년간 전기료 변화 추이에 대해 설명해줘"
**기대 결과:**
- Plan: `query_type=trend`, `metric=cost_won`, `filters.region=["중부"]`, `time_range=last_n_months(n=24)`
- 답변 텍스트가 대화 기록에 1회만 표시됨
- Evidence expander가 에러 없이 동작
- "자세히 보기" 버튼이 최소 1개 표시됨

### Q2: "이어서 전기료 상위국소 4개 알려줘"
**기대 결과:**
- Q1의 중부지역 컨텍스트 상속
- Plan: `query_type=top_n`, `metric=cost_won` (Q1에서 상속), `filters.region=["중부"]` (Q1에서 상속), `top_n=4`
- 답변 텍스트 중복 없음
- 모든 버튼/expander가 정상 동작

### 재실행/스크롤 테스트
- 페이지 새로고침 후에도 에러 없음
- 히스토리 반복 렌더링 시에도 key 충돌 없음
- 모든 expander가 정상 동작

## 주요 개선 사항

1. **중복 방지 원칙**
   - 답변 텍스트는 `render_chat_message()`에서만 1회 출력
   - `render_probe_response()`는 evidence와 links만 출력
   - 함수 주석에 원칙 명시

2. **Key 정책**
   - 버튼: `f"probe_nav_btn_{message_id}_{idx}"`
   - message_id는 단조 증가 카운터 기반
   - expander는 key 불필요 (충돌 대상 아님)

3. **예외 처리**
   - 모든 렌더링 단계에 try/except 추가
   - 앱이 중단되지 않도록 방어적 코딩
   - 에러 메시지를 UI에 표시하되 앱은 계속 실행

4. **메뉴 순서**
   - 파일명을 `0_PYLON_PROBE.py`로 변경하여 최상단에 표시
   - 사용자가 쉽게 접근 가능



