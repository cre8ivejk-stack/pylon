# PROBE 리팩토링 계획

## 수정 대상 파일 목록

### 1. 핵심 모듈
- `src/copilot/planner.py` - plan_merge 로직 추가, 컨텍스트 기반 Plan 생성
- `src/copilot/ui.py` - PROBE 명칭 변경, key 정책 통일, 중복 출력 제거
- `src/copilot/schemas.py` - ConversationMemory 스키마 추가 (필요시)

### 2. 페이지
- `pages/6_자연어_질의.py` - PROBE 명칭 변경, 대화 기록 구조 개선, 중복 제거, 컨텍스트 관리

### 3. 네비게이션
- `src/copilot/navigation.py` - probe_nav 명칭 변경 (copilot_nav → probe_nav)
- `pages/1_에너지_인텔리전스.py` - probe_nav 읽기 (copilot_nav → probe_nav)

### 4. 기타
- `components/copilot_panel.py` - PROBE 명칭 변경 (참고용, 현재는 사용 안 함)
- `app.py` - PROBE 명칭 변경

## 주요 변경사항

1. **명칭 변경**: Copilot → PROBE (사용자 노출 텍스트)
2. **중복 출력 제거**: 대화 기록에만 답변 표시, 별도 섹션 제거
3. **컨텍스트 연결**: conversation memory + plan_merge
4. **Key 정책**: message_id 기반 유니크 key 생성
5. **네비게이션**: copilot_nav → probe_nav



