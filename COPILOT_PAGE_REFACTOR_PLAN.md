# Copilot 페이지 전환 및 딥링크 수정 계획

## 수정할 파일 목록

### 1. 새로 생성/대체할 파일
- `pages/6_자연어_질의.py` → Copilot 전용 페이지로 재작성

### 2. 수정할 파일
- `src/copilot/deeplink.py` - session_state 기반 네비게이션으로 전면 수정
- `src/copilot/ui.py` - st.page_link 제거, st.switch_page + session_state 사용
- `src/copilot/schemas.py` - NavLink 스키마 추가 (title, target_page, nav_payload)
- `pages/1_에너지_인텔리전스.py` - copilot_nav 읽어서 필터 자동 적용
- `src/copilot/executor.py` - 필터 처리 정확도 개선 (rapa, contract_type_major 등)
- `components/copilot_panel.py` - 사이드바용은 비활성화 또는 제거
- `app.py` - 사이드바 Copilot 제거
- `pages/2_성과_리스크_관리.py` - 사이드바 Copilot 제거
- `pages/3_최적화_실행.py` - 사이드바 Copilot 제거
- `pages/4_검증_실증.py` - 사이드바 Copilot 제거

## 구현 순서

1. **schemas.py 수정** - NavLink 스키마 추가
2. **deeplink.py 전면 수정** - session_state 기반 네비게이션
3. **ui.py 수정** - st.switch_page 사용
4. **executor.py 수정** - 필터 처리 정확도 개선
5. **pages/6_자연어_질의.py 재작성** - Copilot 전용 페이지
6. **pages/1_에너지_인텔리전스.py 수정** - copilot_nav 필터 자동 적용
7. **사이드바 Copilot 제거** - app.py 및 각 페이지



