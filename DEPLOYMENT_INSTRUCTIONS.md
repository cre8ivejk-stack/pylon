# PYLON 배포 가이드

## Streamlit Cloud 배포 (추천)

### 1단계: GitHub 저장소 준비

1. GitHub 계정 생성 (없는 경우)
2. 새 저장소 생성 (public 또는 private)
3. 프로젝트 업로드:

```bash
cd C:\251213_pylon

# Git 초기화 (아직 안 했다면)
git init

# .gitignore 파일 생성 (중요!)
echo "__pycache__/" > .gitignore
echo "*.pyc" >> .gitignore
echo ".env" >> .gitignore
echo "*.log" >> .gitignore

# 파일 추가
git add .
git commit -m "Initial commit - PYLON v0.0.3"

# GitHub 저장소와 연결 (YOUR_USERNAME과 YOUR_REPO를 실제 값으로 변경)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

### 2단계: requirements.txt 확인

프로젝트 루트에 `requirements.txt` 파일이 있는지 확인하고, 없다면 생성:

```txt
streamlit>=1.52.0
pandas>=2.2.0
numpy>=2.0.0
plotly>=6.0.0
pyarrow>=22.0.0
pyyaml>=6.0.0
```

### 3단계: Streamlit Cloud 배포

1. https://share.streamlit.io 접속
2. GitHub 계정으로 로그인
3. "New app" 클릭
4. 저장소 선택:
   - Repository: `YOUR_USERNAME/YOUR_REPO`
   - Branch: `main`
   - Main file path: `app.py`
5. "Deploy!" 클릭

배포 완료 후 URL이 생성됩니다 (예: `https://your-app-name.streamlit.app`)

---

## 로컬 네트워크 공유

### Windows 방화벽 설정

1. Windows 방화벽 고급 설정 열기
2. 인바운드 규칙 → 새 규칙
3. 포트 → TCP → 특정 로컬 포트: 8501
4. 연결 허용 → 이름: "Streamlit PYLON"

### 실행 명령

```bash
cd C:\251213_pylon
.\Scripts\streamlit.exe run app.py --server.address 0.0.0.0 --server.port 8501
```

실행 후 Network URL을 동료들에게 공유하세요.

---

## Docker 배포 (고급)

### Dockerfile 생성

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
```

### 빌드 및 실행

```bash
docker build -t pylon-app .
docker run -p 8501:8501 pylon-app
```

---

## 사내 서버 배포

### Linux 서버에서 실행 (백그라운드)

```bash
# tmux 또는 screen 사용
tmux new -s pylon

cd /path/to/pylon
streamlit run app.py --server.address 0.0.0.0 --server.port 8501

# Ctrl+B, D로 세션 분리
```

### systemd 서비스로 등록 (자동 시작)

`/etc/systemd/system/pylon.service` 생성:

```ini
[Unit]
Description=PYLON Streamlit App
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/pylon
ExecStart=/usr/local/bin/streamlit run app.py --server.address 0.0.0.0 --server.port 8501
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

실행:
```bash
sudo systemctl enable pylon
sudo systemctl start pylon
```

---

## 접근 제어 및 보안

### Streamlit 인증 추가

`.streamlit/config.toml` 파일 생성:

```toml
[server]
enableCORS = false
enableXsrfProtection = true

[server.address]
headless = true
```

### 환경 변수로 민감 정보 관리

`.streamlit/secrets.toml` 파일 생성 (Git에는 추가하지 않음):

```toml
[auth]
admin_password = "your-secure-password"

[database]
connection_string = "your-connection-string"
```

코드에서 사용:
```python
import streamlit as st

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    password = st.text_input("비밀번호", type="password")
    if password == st.secrets["auth"]["admin_password"]:
        st.session_state.authenticated = True
        st.rerun()
    else:
        st.stop()
```

---

## 권장 배포 방식 (상황별)

| 상황 | 추천 방법 | 비용 | 난이도 |
|------|----------|------|--------|
| 팀 내부 테스트 | 로컬 네트워크 공유 | 무료 | ⭐ |
| 외부 공유 (소규모) | Streamlit Cloud | 무료 | ⭐⭐ |
| 사내 공식 운영 | 사내 서버 배포 | 서버 비용 | ⭐⭐⭐ |
| 대규모/엔터프라이즈 | Docker + K8s | 인프라 비용 | ⭐⭐⭐⭐⭐ |

---

## 문제 해결

### 포트가 이미 사용 중인 경우
```bash
# 다른 포트 사용
.\Scripts\streamlit.exe run app.py --server.port 8502
```

### 데이터 파일이 너무 큰 경우
- Git LFS 사용
- Streamlit Cloud의 경우 500MB 제한 확인
- 데이터를 외부 스토리지(S3, Azure Blob 등)에 저장

### 성능 최적화
- `@st.cache_data` 데코레이터 활용
- 큰 데이터프레임은 lazy loading
- 불필요한 재계산 방지

---

## 지원

배포 중 문제가 발생하면:
- Streamlit 공식 문서: https://docs.streamlit.io/deploy
- Streamlit 커뮤니티: https://discuss.streamlit.io

