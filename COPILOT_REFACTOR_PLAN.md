# Copilot 재구성 계획

## 수정/생성할 파일 목록

### 1. 새로 생성할 파일
- `src/copilot/executor.py` - Plan 실행 로직 (집계/비교/추이 등)
- `components/copilot_panel.py` - 공통 Copilot 패널 컴포넌트 (사이드바용)
- `tests/test_copilot_integration.py` - 통합 테스트 (10개 샘플 질문)

### 2. 수정할 파일
- `src/copilot/schemas.py` - Result 스키마 추가 (Answer, Evidence, Links, Confidence)
- `src/copilot/ui.py` - 채팅형 UI로 재구성, 답변 포맷 렌더링
- `src/copilot/planner.py` - 기존 유지 (이미 구현됨)
- `src/copilot/deeplink.py` - 기존 유지 (이미 구현됨)
- `app.py` - Copilot 패널 통합
- `pages/6_자연어_질의.py` - deprecated 처리 (메뉴에서 숨김)
- `pages/1_에너지_인텔리전스.py` - Copilot 패널 추가
- `pages/2_성과_리스크_관리.py` - Copilot 패널 추가
- `pages/3_최적화_실행.py` - Copilot 패널 추가
- `pages/4_검증_실증.py` - Copilot 패널 추가

### 3. 삭제/비활성화할 파일
- `pages/6_자연어_질의.py` - deprecated 처리 (기능은 유지하되 메뉴에서 숨김)

## 구현 순서

1. **executor.py 생성** - Plan 실행 로직
2. **schemas.py 확장** - Result 스키마 추가
3. **ui.py 재구성** - 채팅형 UI
4. **copilot_panel.py 생성** - 공통 패널
5. **app.py 수정** - Copilot 통합
6. **각 페이지 수정** - Copilot 패널 추가
7. **테스트 코드 작성**
8. **pages/6_자연어_질의.py deprecated 처리**



