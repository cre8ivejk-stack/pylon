# SKT Playground 배포 가이드 (내일 작업용)

## 📋 현재 상태 (2026-01-12 종료 시점)

### ✅ 완료
- SKT GitLab 저장소 생성: `playground-pylon-test2`
- Git remote 설정 완료: `skt2`
- 토큰: `tde2-99eC2AF0D6-H2CoB8bpDWm86MQp1OjF5Zwk.01.0z02atdpn`
- 코드 푸시 성공
- 원본 안정 버전 복원 완료

### ⏳ 남은 작업
- Playground에서 앱 정상 실행

---

## 🎯 내일 작업 계획

### 1단계: 작동하는 예시 정확히 복사

**중요**: 다른 작동하는 Playground 앱의 설정을 **정확히** 복사

```yaml
# 참고: energy-mgmt-2025의 Diyfile.yaml
name: energy-mgmt-2025
entrypoint: streamlit run app.py --server.port $PORT
description: |
  energy-mgmt-2025
service_type: python-streamlit
properties:
  - revision: master
    ingress:
      path: /energy-mgmt-2025
    image:
      from: 'public.ecr.aws/docker/library/python:3.9-slim'
```

**적용 시 변경할 것**:
- `name: playground-pylon-test2`
- `path: /pylon-test2` (또는 Playground UI에서 자동 할당된 경로 확인)
- `python:3.11-slim` (필요 시)

---

### 2단계: 최소 테스트 앱으로 시작

**실패 원인**: 처음부터 전체 PYLON 앱 → 504 타임아웃

**해결**: 단계별 접근

#### Step 1: Hello World
```python
# app.py
import streamlit as st
st.title("✅ 작동합니다!")
st.write("Streamlit 버전:", st.__version__)
```

#### Step 2: 설정 추가
```toml
# .streamlit/config.toml
[server]
headless = true

[browser]
gatherUsageStats = false
```

#### Step 3: 데이터 없는 UI
```python
# PYLON UI만 (데이터 로딩 제거)
```

#### Step 4: 실제 데이터
```python
# 전체 PYLON 앱
```

---

### 3단계: 주요 이슈 해결 방법

#### 이슈 A: 504 Gateway Timeout
**원인**: 앱 시작 시 모든 데이터 로딩 → 너무 오래 걸림

**해결**:
1. Lazy loading (버튼 클릭 시 로드)
2. 캐싱 강화
3. 데이터 파일 크기 확인

#### 이슈 B: JavaScript 모듈 로딩 에러
**원인**: baseUrlPath 설정 불일치

**해결**:
1. baseUrlPath 제거 (Playground가 자동 처리)
2. 또는 정확한 경로 매칭
3. Streamlit 버전 조정 (1.28-1.29 권장)

#### 이슈 C: Not Found (404)
**원인**: 경로 불일치

**해결**:
1. Playground UI에서 실제 할당된 URL 확인
2. `ingress.path`를 실제 경로와 일치
3. 여러 패턴 시도:
   - `/pylon-test2`
   - `/playground-pylon-test2`
   - Playground가 제공하는 URL

---

## 📝 체크리스트 (내일 작업 시)

### 준비 단계
- [ ] Playground에서 다른 작동하는 앱의 Diyfile.yaml 확인
- [ ] 실제 할당된 URL 패턴 파악
- [ ] 로그 접근 방법 확인

### 배포 단계
- [ ] 최소 테스트 앱 생성 (Hello World)
- [ ] Diyfile.yaml 생성 (작동하는 예시 복사)
- [ ] Git 푸시: `git push skt2 main:master --force`
- [ ] Playground 재배포
- [ ] 로그 확인: "You can now view your Streamlit app"
- [ ] URL 접속 테스트

### 문제 발생 시
- [ ] Playground 로그 확인 (에러 메시지 복사)
- [ ] 브라우저 콘솔 (F12) 확인
- [ ] Network 탭에서 실패한 요청 확인
- [ ] 단계별로 디버깅

---

## 💡 핵심 원칙 (내일)

1. **천천히, 단계별로**
   - 한 번에 하나씩 변경
   - 각 단계마다 테스트

2. **작동하는 예시 따라하기**
   - 창의적으로 하지 말고 정확히 복사
   - 차이점 최소화

3. **로그 우선**
   - 항상 Playground 로그 먼저 확인
   - 에러 메시지가 정답을 알려줌

4. **간단하게 유지**
   - 복잡한 설정은 나중에
   - 먼저 화면이 뜨게 만들기

---

## 🔧 유용한 명령어

### Git 작업
```bash
cd C:\251213_pylon

# 현재 상태 확인
git status

# 변경사항 커밋
git add .
git commit -m "메시지"

# master에만 푸시 (main은 안정 버전 유지)
git push skt2 main:master --force

# 롤백이 필요하면
git reset --hard origin/main
git push skt2 main:master --force
```

### 빠른 테스트
```bash
# 로컬에서 Streamlit 실행 (Windows PowerShell)
cd C:\251213_pylon
streamlit run app.py
# http://localhost:8501 에서 확인
```

---

## 📞 도움 요청 시 필요한 정보

1. **Playground 로그** (처음 30줄과 마지막 30줄)
2. **브라우저 콘솔 에러** (F12 → Console 탭)
3. **접속 시도한 URL**
4. **Playground UI에 표시된 실제 URL**
5. **현재 Diyfile.yaml 내용**

---

## 🎯 성공 기준

- [ ] URL 접속 시 화면 표시됨
- [ ] JavaScript 에러 없음
- [ ] 버튼 클릭 작동
- [ ] 데이터 로딩 성공
- [ ] 페이지 이동 가능

---

**화이팅! 내일은 성공할 것입니다!** 🚀

