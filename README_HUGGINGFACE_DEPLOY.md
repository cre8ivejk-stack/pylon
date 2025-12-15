# PYLON - Hugging Face Spaces 배포 (GitLab 사용)

## 🚀 Hugging Face Spaces로 배포하기

Hugging Face Spaces는 GitLab 저장소를 완전히 지원합니다!

---

## 📋 1단계: GitLab 저장소 생성 및 업로드

### GitLab 저장소 생성
1. https://gitlab.com 접속 → 로그인
2. **"New project"** 클릭
3. **"Create blank project"**
4. 설정:
   - Project name: `pylon`
   - Visibility: **Public** (무료 배포용)
   - **"Create project"** 클릭

### 코드 업로드
```bash
cd C:\251213_pylon

# Git 초기화
git init

# 모든 파일 추가
git add .

# 커밋
git commit -m "Initial commit: PYLON v0.0.3"

# GitLab 저장소 연결 (YOUR_USERNAME을 본인 GitLab 아이디로 변경!)
git remote add origin https://gitlab.com/YOUR_USERNAME/pylon.git

# 브랜치 이름 변경
git branch -M main

# 푸시
git push -u origin main
```

---

## 📦 2단계: Hugging Face Spaces 설정 파일 추가

### app.py가 이미 있으므로, 추가로 필요한 파일만 생성

#### `.streamlit/config.toml` (이미 생성됨)
```toml
[theme]
primaryColor="#667eea"
backgroundColor="#FFFFFF"
secondaryBackgroundColor="#F0F2F6"
textColor="#262730"
font="sans serif"

[server]
headless = true
enableCORS = false
enableXsrfProtection = true
```

#### `requirements.txt` (이미 있음)
- 현재 파일 그대로 사용

---

## 🎯 3단계: Hugging Face Spaces 생성

### 1. Hugging Face 계정 생성
1. https://huggingface.co 접속
2. **"Sign Up"** 클릭
3. 이메일로 가입 또는 GitHub/Google 계정 연동

### 2. Space 생성
1. 로그인 후 우측 상단 프로필 → **"New Space"**
2. Space 설정:
   - **Space name**: `pylon` (URL이 됨)
   - **License**: Apache 2.0
   - **Space SDK**: **Streamlit** 선택 ⚠️ 중요!
   - **Visibility**: Public (무료)
3. **"Create Space"** 클릭

### 3. GitLab 저장소 연결

Space 생성 후 **"Files and versions"** 탭에서:

#### 방법 A: Web UI로 업로드
1. **"Add file"** → **"Upload files"**
2. 프로젝트의 모든 파일을 드래그 앤 드롭
3. **"Commit"** 클릭

#### 방법 B: Git으로 푸시 (권장)
```bash
cd C:\251213_pylon

# Hugging Face Space를 Git remote로 추가
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/pylon

# 푸시
git push hf main
```

**참고**: Hugging Face Git 접근에는 토큰이 필요합니다.
- Settings → Access Tokens → "New token" 생성
- `git push` 시 비밀번호로 토큰 입력

---

## ✅ 4단계: 배포 완료!

- 배포는 자동으로 시작됩니다 (3-5분 소요)
- 완료 후 URL:
  ```
  https://huggingface.co/spaces/YOUR_USERNAME/pylon
  ```
- 이 URL을 누구에게나 공유 가능!

---

## 🔄 업데이트 방법

코드 수정 후:

### GitLab에 푸시 (소스 관리)
```bash
git add .
git commit -m "Update: 설명"
git push origin main
```

### Hugging Face에 동기화
```bash
git push hf main
```

또는 GitLab CI/CD로 자동 동기화 설정 가능!

---

## 🎨 추가 설정

### README.md 추가 (Space 소개)
Space에 `README.md` 추가하면 설명이 표시됩니다:

```markdown
---
title: PYLON Energy Operations
emoji: ⚡
colorFrom: blue
colorTo: purple
sdk: streamlit
sdk_version: 1.30.0
app_file: app.py
pinned: false
---

# PYLON - Energy Operations Platform

SKT Network센터 에너지 관리 운영 플랫폼

## 기능
- 에너지 인텔리전스
- 성과 & 리스크 관리
- 최적화 & 실행
- 검증 & 실증
```

---

## 💡 팁

### 1. 비공개 Space (유료)
- 유료 플랜으로 Private Space 생성 가능
- 접근 제어 가능

### 2. GPU 사용 (유료)
- ML 모델 실행 시 GPU Space 업그레이드
- 기본 CPU로도 PYLON은 충분함

### 3. 도메인 커스텀
- 유료 플랜에서 커스텀 도메인 가능

### 4. GitLab CI/CD 자동 배포
`.gitlab-ci.yml` 추가:
```yaml
deploy:
  stage: deploy
  script:
    - git remote add hf https://$HF_USERNAME:$HF_TOKEN@huggingface.co/spaces/$HF_USERNAME/pylon
    - git push hf main
  only:
    - main
```

---

## 📊 무료 플랜 제한

- **CPU**: 2 vCPU
- **RAM**: 16GB
- **Storage**: 50GB
- **Bandwidth**: 무제한

PYLON 앱은 무료 플랫폼으로 충분합니다!

---

## 🆚 Hugging Face vs Streamlit Cloud

| 항목 | Hugging Face | Streamlit Cloud |
|------|--------------|-----------------|
| GitLab 지원 | ✅ | ❌ |
| GitHub 지원 | ✅ | ✅ |
| 무료 리소스 | 16GB RAM | 1GB RAM |
| 커뮤니티 | ML/AI 중심 | Data Apps 중심 |
| 난이도 | ⭐⭐ | ⭐ |

---

## 🔗 유용한 링크

- Hugging Face Docs: https://huggingface.co/docs/hub/spaces
- Streamlit on Spaces: https://huggingface.co/docs/hub/spaces-sdks-streamlit
- GitLab Integration: https://huggingface.co/docs/hub/repositories-getting-started

---

**배포 성공하시면 URL 공유해주세요! 🎉**

