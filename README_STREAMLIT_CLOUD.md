# PYLON - Streamlit Cloud 배포 가이드

## 🚀 빠른 배포 (5단계)

### 1️⃣ GitHub 저장소 생성

1. https://github.com 접속 후 로그인
2. 우측 상단 **"+"** → **"New repository"** 클릭
3. 저장소 설정:
   - **Repository name**: `pylon` (원하는 이름)
   - **Public** 선택 (무료 배포는 Public만 가능)
   - **"Create repository"** 클릭

### 2️⃣ 로컬 Git 설정 및 업로드

PowerShell 또는 CMD에서 실행:

```bash
cd C:\251213_pylon

# Git 초기화 (이미 했다면 스킵)
git init

# 모든 파일 추가
git add .

# 커밋
git commit -m "Initial commit: PYLON v0.0.3"

# GitHub 저장소 연결 (YOUR_USERNAME을 본인 GitHub 아이디로 변경!)
git remote add origin https://github.com/YOUR_USERNAME/pylon.git

# 브랜치 이름을 main으로 변경
git branch -M main

# 푸시 (GitHub 로그인 창이 뜰 수 있음)
git push -u origin main
```

**❗ 중요**: `YOUR_USERNAME`을 본인의 실제 GitHub 사용자 이름으로 바꾸세요!

예시:
```bash
git remote add origin https://github.com/johndoe/pylon.git
```

### 3️⃣ Streamlit Cloud 계정 생성

1. https://share.streamlit.io 접속
2. **"Sign up"** 클릭
3. **"Continue with GitHub"** 선택
4. GitHub 계정으로 로그인 및 권한 승인

### 4️⃣ 앱 배포

1. Streamlit Cloud 대시보드에서 **"New app"** 클릭
2. 배포 설정:
   - **Repository**: `YOUR_USERNAME/pylon` 선택
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App URL** (선택): 원하는 URL 입력 (예: `pylon-skt-energy`)
3. **"Deploy!"** 클릭

### 5️⃣ 배포 완료 🎉

- 배포는 약 **3-5분** 소요됩니다
- 완료 후 URL이 생성됩니다:
  ```
  https://your-app-name.streamlit.app
  ```
- 이 URL을 누구에게나 공유할 수 있습니다!

---

## 🔧 문제 해결

### ❌ "git is not recognized" 에러

Git이 설치되지 않은 경우:
1. https://git-scm.com/download/win 에서 Git 다운로드
2. 설치 후 PowerShell/CMD 재시작

### ❌ GitHub 로그인 실패

- GitHub Desktop 사용:
  1. https://desktop.github.com 다운로드
  2. GitHub Desktop에서 저장소 생성 및 푸시

### ❌ 배포 후 에러 발생

1. Streamlit Cloud 대시보드에서 **"Manage app"** 클릭
2. **"Logs"** 탭에서 에러 메시지 확인
3. 주로 `requirements.txt`의 패키지 버전 문제

---

## 📊 배포 후 관리

### 앱 업데이트

코드 수정 후:
```bash
cd C:\251213_pylon
git add .
git commit -m "Update: 설명"
git push
```

→ Streamlit Cloud가 자동으로 재배포합니다!

### 앱 중지/재시작

Streamlit Cloud 대시보드에서:
- **"Reboot app"**: 앱 재시작
- **"Delete app"**: 앱 삭제

### 사용량 확인

- **무료 플랜**: 앱 1개, 월 1GB 데이터 전송
- 더 필요하면 유료 플랜으로 업그레이드

---

## 💡 팁

### 1. 비공개 데이터 사용 시

`.streamlit/secrets.toml` 파일 생성 (Git에는 포함 안 됨):
```toml
[database]
connection_string = "your-secret-connection"
```

Streamlit Cloud에서:
1. App settings → Secrets
2. 위 내용 복사해서 붙여넣기

### 2. 커스텀 도메인

유료 플랜에서 가능:
- `https://pylon.yourcompany.com`

### 3. 성능 최적화

- `@st.cache_data` 적극 활용 (이미 적용됨)
- 큰 파일은 GitHub LFS 사용
- 데이터는 외부 DB 연동 권장

---

## 📞 도움이 필요하면

- Streamlit 공식 문서: https://docs.streamlit.io/deploy
- Streamlit 포럼: https://discuss.streamlit.io
- GitHub Issues: 저장소에서 Issue 생성

---

**배포 성공하시면 URL 공유해주세요! 🎉**

