# GitLab → GitHub 미러링으로 Streamlit Cloud 배포

GitLab에서 소스 관리하면서 Streamlit Cloud로 배포하는 방법입니다.

---

## 📋 개념

```
[GitLab 저장소]  →  자동 미러링  →  [GitHub 저장소]  →  [Streamlit Cloud]
   (소스 관리)                         (배포용)             (호스팅)
```

- **GitLab**: 실제 개발 및 소스 관리
- **GitHub**: 배포 전용 미러 저장소
- **Streamlit Cloud**: GitHub 저장소를 바라보고 배포

---

## 🚀 설정 방법

### 1단계: GitLab 저장소 생성

```bash
cd C:\251213_pylon

git init
git add .
git commit -m "Initial commit: PYLON v0.0.3"

# GitLab 저장소 연결
git remote add origin https://gitlab.com/YOUR_USERNAME/pylon.git
git push -u origin main
```

### 2단계: GitHub 저장소 생성 (미러용)

1. https://github.com → "New repository"
2. Repository name: `pylon-mirror` (또는 `pylon`)
3. **Public** 선택
4. ⚠️ **"Initialize this repository"는 체크하지 않음**
5. "Create repository" 클릭

### 3단계: GitLab에서 자동 미러링 설정

#### GitLab 프로젝트에서:
1. Settings → Repository → Mirroring repositories
2. 설정:
   - **Git repository URL**: `https://github.com/YOUR_USERNAME/pylon-mirror.git`
   - **Mirror direction**: Push
   - **Authentication method**: Password
   - **Password**: GitHub Personal Access Token (아래에서 생성)

#### GitHub Personal Access Token 생성:
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. "Generate new token (classic)"
3. 설정:
   - **Note**: "GitLab Mirror"
   - **Expiration**: No expiration (또는 원하는 기간)
   - **Select scopes**: `repo` 전체 체크 ✅
4. "Generate token" → 토큰 복사 (한 번만 보임!)
5. 이 토큰을 GitLab의 Password 필드에 붙여넣기

#### GitLab 미러링 완료:
- **"Mirror repository"** 클릭
- 초록색 체크 표시가 나오면 성공!

### 4단계: Streamlit Cloud 배포

1. https://share.streamlit.io → GitHub 로그인
2. "New app" 클릭
3. 설정:
   - Repository: `YOUR_USERNAME/pylon-mirror`
   - Branch: `main`
   - Main file path: `app.py`
4. "Deploy!" 클릭

---

## 🔄 작업 흐름

### 일상적인 개발:
```bash
# GitLab에만 푸시
cd C:\251213_pylon
git add .
git commit -m "Update: 기능 추가"
git push origin main
```

→ GitLab이 자동으로 GitHub로 미러링  
→ Streamlit Cloud가 자동으로 재배포 🎉

---

## ✅ 장점

- ✅ GitLab에서 소스 관리 (내부 정책/보안)
- ✅ GitHub는 배포 전용
- ✅ 자동 동기화 (수동 작업 없음)
- ✅ Streamlit Cloud 무료 플랜 사용

---

## ⚠️ 주의사항

### 1. GitHub Token 보안
- Token은 외부에 노출되지 않도록 관리
- 만료 기간 설정 권장

### 2. 비공개 저장소
- GitLab은 Private 가능
- GitHub 미러는 Public이어야 Streamlit 무료 사용
- 민감 정보는 `.gitignore` 또는 Streamlit Secrets 사용

### 3. 미러링 확인
- GitLab → Settings → Repository → Mirroring repositories
- 마지막 동기화 시간 확인

---

## 🔧 문제 해결

### 미러링이 안 됨
- GitHub Token 권한 확인 (`repo` 스코프)
- Token 만료 여부 확인
- GitLab → Repository mirroring에서 "Update now" 클릭

### Streamlit 배포 실패
- GitHub 저장소가 Public인지 확인
- `requirements.txt` 파일 존재 확인
- Streamlit Cloud Logs 확인

---

## 🆚 방법 비교

| | GitLab Only | GitLab + GitHub Mirror |
|---|-------------|------------------------|
| 소스 관리 | GitLab | GitLab |
| 배포 | 수동/복잡 | Streamlit Cloud (자동) |
| 설정 복잡도 | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 비용 | 서버 필요 | 무료 |

---

**이 방법은 회사 정책상 GitLab을 써야 하지만, Streamlit Cloud의 편리함을 원할 때 최적입니다!**

