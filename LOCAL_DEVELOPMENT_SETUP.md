# 로컬 개발환경 구축 가이드

## 📋 개요

이 문서는 로컬 PC(Windows)에서 PYLON 프로젝트를 개발하기 위한 환경 구축 사항을 정리합니다.

**작성일**: 2026-01-14  
**환경**: Windows 10, Python 3.13.7

---

## ✅ 완료된 작업 사항

### 1. Git 원격 저장소 설정

현재 프로젝트는 두 개의 원격 저장소에 연결되어 있습니다:

```bash
# GitLab 공개 저장소 (백업/참고용)
origin: https://gitlab.com/cre8ivejk-stack/pylon.git

# SKT 내부 Playground 저장소 (운영 배포용)
pylon-test4: https://gitlab.tde.sktelecom.com/PGPRIVATE/playground-pylon-test4.git
```

**사용 방법:**
- 로컬 개발 후 `origin main`에 push: `git push origin main`
- SKT Playground 배포 시: `git push pylon-test4 main` (향후 작업 예정)

### 2. Python 환경

- **Python 버전**: 3.13.7
- **실행 명령어**: `py` (Windows Python Launcher 사용)

### 3. 의존성 설치

```bash
# requirements.txt에 명시된 패키지 설치
py -m pip install -r requirements.txt
```

**주요 패키지:**
- Streamlit 1.30.0 (실제 설치된 버전: 1.52.1)
- Pandas 2.0.3
- NumPy 1.24.3
- Plotly 5.18.0
- 기타 (requirements.txt 참조)

### 4. Streamlit 설정 (로컬 개발용)

**파일 위치**: `.streamlit/config.toml`

**현재 설정:**
```toml
[server]
headless = true
# SKT Playground 배포 시 아래 주석을 해제하세요:
# baseUrlPath = "pylon-test4"

[browser]
gatherUsageStats = false
```

**설정 설명:**
- `baseUrlPath`가 **주석 처리**되어 있어 로컬에서 `http://localhost:8501`로 직접 접속 가능
- SKT Playground 배포 시에는 `baseUrlPath = "pylon-test4"` 주석을 해제해야 함
- 현재는 로컬 개발 중이므로 주석 처리 상태 유지

### 5. 앱 실행 방법

**명령어:**
```bash
py -m streamlit run app.py
```

**접속 주소:**
- 로컬: `http://localhost:8501`
- 브라우저가 자동으로 열리지 않으면 위 주소를 직접 입력

**백그라운드 실행:**
- PowerShell에서 백그라운드로 실행 가능
- 프로세스 확인: `netstat -ano | findstr :8501`

---

## 🔧 문제 해결 이력

### 문제 1: 404 에러 발생

**증상:**
- `http://localhost:8501` 접속 시 404 에러 발생

**원인:**
- `.streamlit/config.toml`에 `baseUrlPath = "pylon-test4"` 설정이 활성화되어 있었음
- 이 설정은 SKT Playground 배포용으로, 로컬에서는 불필요

**해결:**
- `baseUrlPath` 설정을 주석 처리
- 앱 재시작 후 정상 작동 확인

---

## 🤖 자연어 질의(LLM/NLQ) 실험 기능

### 개요
- 신규 메뉴 **“자연어 질의(실험)”**가 추가되었습니다.
- 기본은 **규칙 기반**으로 동작하며, 선택적으로 **LLM(OpenAI 또는 OpenAI 호환 엔드포인트)** 로 “계획(JSON)”을 생성할 수 있습니다.
- 실행은 항상 앱 내부 데이터(`bills/actual/site_master`)로만 수행됩니다(LLM은 계획만 생성).

### 실행/확인
- 홈 화면 하단 **“🤖 실험 기능”** 섹션 또는 좌측 페이지 목록에서:
  - `pages/6_자연어_질의.py`
- 예시:
  - “동부지역 최근 두달동안 가장 전력사용량이 높은 중계국사 top20을 추출해줘”

### LLM 사용 설정(선택)
PowerShell에서 환경변수를 설정한 뒤 앱을 실행하세요.

```powershell
# OpenAI API Key (필수)
$env:OPENAI_API_KEY = "YOUR_KEY"

# (선택) 모델 지정
$env:PYLON_LLM_MODEL = "gpt-4o-mini"

# (선택) OpenAI 호환 엔드포인트 사용 시
# $env:OPENAI_BASE_URL = "https://your-openai-compatible-endpoint/v1"
```

앱의 “자연어 질의(실험)” 페이지에서 **“LLM로 계획 생성”** 토글을 켜면,
LLM이 생성한 **계획(JSON)** 을 확인할 수 있습니다.

### 구현 파일
- `src/nlq.py`: 질의 파싱/실행(제한된 내부 쿼리)
- `src/llm_nlq.py`: LLM을 이용해 제한된 JSON 계획 생성(검증 포함)
- `pages/6_자연어_질의.py`: UI(프롬프트 입력 → 결과 테이블 → 확인 경로 안내)

### 문제 2: Python 실행 명령어

**Windows 환경 특이사항:**
- `python` 명령어가 인식되지 않을 수 있음
- `py` (Python Launcher) 사용 권장
- 또는 `python.exe` 직접 경로 사용

---

## 📁 프로젝트 구조

```
C:\251213_pylon\
├── app.py                    # 메인 진입점
├── requirements.txt          # Python 의존성
├── .streamlit/
│   └── config.toml          # Streamlit 설정 (로컬용)
├── src/                     # 핵심 비즈니스 로직
├── pages/                   # Streamlit 페이지들
├── components/              # 재사용 컴포넌트
├── data/                    # 데이터 파일 (Parquet)
├── config/                  # 설정 파일 (YAML)
└── styles/                  # 스타일 정의
```

---

## 🚀 개발 워크플로우

### 1. 코드 수정
- 로컬에서 `app.py` 및 관련 파일 수정
- Streamlit이 자동으로 변경사항 감지 및 리로드

### 2. 테스트
- 브라우저에서 `http://localhost:8501` 접속하여 확인
- 각 페이지별 기능 테스트

### 3. 커밋 및 Push
```bash
# 변경사항 확인
git status

# 스테이징
git add .

# 커밋
git commit -m "feat: 기능 설명"

# GitLab에 push
git push origin main
```

### 4. SKT Playground 배포 (향후)
```bash
# 1. .streamlit/config.toml 수정
# baseUrlPath = "pylon-test4" 주석 해제

# 2. 커밋
git add .streamlit/config.toml
git commit -m "config: SKT Playground 배포 설정"

# 3. SKT 저장소에 push
git push pylon-test4 main
```

---

## ⚠️ 주의사항

### 로컬 개발 시
- ✅ `baseUrlPath` 설정은 주석 처리 상태 유지
- ✅ `http://localhost:8501`로 직접 접속
- ✅ 로컬에서 충분히 테스트 후 커밋

### SKT Playground 배포 시
- ⚠️ `baseUrlPath = "pylon-test4"` 주석 해제 필수
- ⚠️ 배포 전 로컬에서 테스트 완료 확인
- ⚠️ 배포 후 `http://playground-url/pylon-test4` 경로로 접속

---

## 📝 체크리스트

### 초기 설정 완료 여부
- [x] Git 원격 저장소 연결 확인
- [x] Python 설치 확인 (3.13.7)
- [x] 의존성 설치 완료
- [x] Streamlit 설정 파일 수정 (로컬용)
- [x] 앱 실행 테스트 완료

### 개발 시작 전 확인
- [ ] 최신 코드 pull: `git pull origin main`
- [ ] 가상환경 활성화 (선택사항)
- [ ] 의존성 최신화: `py -m pip install -r requirements.txt --upgrade`
- [ ] 앱 실행 확인: `py -m streamlit run app.py`

---

## 🔗 관련 문서

- `README.md`: 프로젝트 개요 및 기본 사용법
- `DEVELOPMENT_GUIDE.md`: 개발 가이드 (Jupyter 워크플로우 포함)
- `QUICK_START.md`: 빠른 시작 가이드
- `DEPLOYMENT_GUIDE.md`: 배포 가이드

---

## 📞 문의

개발환경 구축 관련 문제 발생 시:
1. 이 문서의 문제 해결 이력 확인
2. 관련 문서 참조
3. 팀에 문의

---

**마지막 업데이트**: 2026-01-14

