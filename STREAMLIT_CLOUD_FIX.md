# Streamlit Cloud 배포 오류 해결 가이드

## 1. 가능성 Top 5 (우리 레포 기준 근거)

### 🥇 1위: Jupyter 관련 패키지 포함 (확률: 90%)
**근거**: 
- `requirements.txt`에 `jupyter==1.0.0`, `jupyterlab==4.0.9`, `notebook==7.0.6`, `ipykernel==6.27.1`, `ipywidgets==8.1.1` 포함
- 실제 코드에서 Jupyter 패키지 import 없음 (grep 검색 결과 확인)
- Streamlit Cloud는 웹 앱 배포용이므로 Jupyter 불필요
- Jupyter 패키지들은 무거워서 빌드 시간 초과 또는 메모리 부족 가능

### 🥈 2위: 버전 고정이 지나치게 엄격함 (확률: 80%)
**근거**:
- 모든 패키지가 `==`로 고정 (예: `numpy==1.24.3`, `pandas==2.0.3`)
- `numpy==1.24.3`은 오래된 버전으로 최신 Python과 호환성 문제 가능
- Streamlit Cloud의 기본 Python 버전과 호환되지 않을 수 있음
- 의존성 해결 실패 가능성 높음

### 🥉 3위: Python 버전 명시 없음 (확률: 70%)
**근거**:
- `runtime.txt` 파일 없음
- `requirements.txt` 주석에 "Python 3.9+ required"만 있음
- Streamlit Cloud는 기본적으로 Python 3.11 사용
- 일부 오래된 패키지 버전이 Python 3.11과 호환되지 않을 수 있음

### 4위: pyarrow 버전 호환성 (확률: 60%)
**근거**:
- `pyarrow==14.0.1` 고정
- pandas 2.0.3과 pyarrow 14.0.1 조합이 최신 Python 환경에서 문제 가능
- Streamlit Cloud 빌드 환경에서 컴파일 실패 가능

### 5위: 불필요한 패키지로 인한 빌드 시간 초과 (확률: 50%)
**근거**:
- Jupyter 패키지들이 매우 무거움
- 빌드 시간이 Streamlit Cloud 제한 시간을 초과할 수 있음

---

## 2. 내 레포에서 확인된 문제

### 파일: `requirements.txt`
**위치**: 루트 디렉토리 ✅ (정상)

**문제점**:

1. **라인 23-28: Jupyter 관련 패키지 (불필요)**
   ```
   # Development & Analysis (Jupyter)
   jupyter==1.0.0
   jupyterlab==4.0.9
   notebook==7.0.6
   ipykernel==6.27.1
   ipywidgets==8.1.1
   ```
   **근거**: 실제 코드에서 Jupyter import 없음, Streamlit 앱에는 불필요

2. **라인 12: numpy 버전이 오래됨**
   ```
   numpy==1.24.3
   ```
   **근거**: Python 3.11+ 환경에서 호환성 문제 가능

3. **라인 11: pandas 버전 고정**
   ```
   pandas==2.0.3
   ```
   **근거**: numpy 1.24.3과 조합 시 의존성 해결 실패 가능

4. **라인 13: pyarrow 버전 고정**
   ```
   pyarrow==14.0.1
   ```
   **근거**: 최신 Python 환경에서 빌드 실패 가능

5. **Python 버전 명시 없음**
   - `runtime.txt` 파일 없음
   - Streamlit Cloud가 기본 Python 버전 사용 (보통 3.11)

### 파일: `.streamlit/config.toml`
**위치**: `.streamlit/config.toml` ✅ (정상)

**문제점**: 없음 (정상)

### 파일: `app.py`
**위치**: 루트 디렉토리 ✅ (정상)

**문제점**: 없음 (Streamlit Cloud가 자동으로 인식)

---

## 3. 수정안

### 수정 파일 1: `requirements.txt`

```diff
# PYLON - SKT Network센터 Energy Operations Platform
-# Python 3.9+ required
+# Python 3.9+ required (Streamlit Cloud uses Python 3.11 by default)

# Core framework
streamlit==1.30.0

# LLM (optional)
openai==1.61.1

# Data processing
-pandas==2.0.3
-numpy==1.24.3
-pyarrow==14.0.1
+pandas>=2.0.3,<3.0.0
+numpy>=1.24.3,<2.0.0
+pyarrow>=14.0.1,<16.0.0

# Visualization
plotly==5.18.0
altair==5.2.0

# Utilities
python-dateutil==2.8.2
PyYAML==6.0.1

-# Development & Analysis (Jupyter)
-jupyter==1.0.0
-jupyterlab==4.0.9
-notebook==7.0.6
-ipykernel==6.27.1
-ipywidgets==8.1.1
+# Development & Analysis (Jupyter) - REMOVED for Streamlit Cloud deployment
+# Jupyter packages are not needed for Streamlit web app deployment
```

### 수정 파일 2: `runtime.txt` (신규 생성)

```
python-3.11
```

**이유**: Streamlit Cloud의 기본 Python 버전과 일치시켜 호환성 보장

---

## 4. 수정 근거 설명

### 왜 이 수정이 Streamlit Cloud 설치 실패를 막는가?

1. **Jupyter 패키지 제거**
   - **문제**: Jupyter 패키지들은 매우 무거워서 빌드 시간이 길어지고 메모리 사용량이 증가
   - **해결**: Streamlit 앱에는 불필요하므로 제거하여 빌드 시간 단축 및 메모리 절약
   - **효과**: 빌드 시간 50% 이상 단축 예상

2. **버전 범위 완화 (== → >=,<)**
   - **문제**: 엄격한 버전 고정(`==`)은 의존성 해결 실패 가능성 증가
   - **해결**: 최소 버전 이상, 다음 메이저 버전 미만으로 범위 지정
   - **효과**: pip가 호환 가능한 버전을 자동으로 선택하여 설치 성공률 향상

3. **numpy/pandas/pyarrow 버전 범위 조정**
   - **문제**: 오래된 버전 고정으로 최신 Python 환경과 호환성 문제
   - **해결**: 최소 버전은 유지하되 상한선을 두어 최신 호환 버전 허용
   - **효과**: Python 3.11 환경에서도 정상 설치 가능

4. **runtime.txt 추가**
   - **문제**: Python 버전 불일치로 인한 패키지 호환성 문제
   - **해결**: 명시적으로 Python 3.11 지정 (Streamlit Cloud 기본값)
   - **효과**: 일관된 Python 환경에서 빌드되어 호환성 보장

---

## 5. 로컬 재현 테스트 명령어

### 테스트 1: 새 가상환경에서 requirements 설치

```powershell
# PowerShell에서 실행
cd C:\251213_pylon

# 새 가상환경 생성
python -m venv test_env

# 가상환경 활성화
.\test_env\Scripts\activate

# pip 업그레이드
python -m pip install --upgrade pip

# requirements.txt 설치 (수정 전)
pip install -r requirements.txt

# 에러 발생 시 에러 메시지 확인
```

### 테스트 2: 수정된 requirements.txt로 재테스트

```powershell
# 수정된 requirements.txt로 재설치
pip uninstall -y -r requirements.txt
pip install -r requirements.txt

# 성공 여부 확인
python -c "import streamlit; import pandas; import numpy; import pyarrow; print('All packages installed successfully')"
```

### 테스트 3: Streamlit 앱 실행 테스트

```powershell
# 앱이 정상 실행되는지 확인
streamlit run app.py --server.headless true

# 브라우저에서 http://localhost:8501 접속하여 확인
```

---

## 6. 배포 재시도 체크리스트

### Step 1: 파일 수정 및 커밋

```powershell
# 1. requirements.txt 수정 (위의 diff 적용)
# 2. runtime.txt 생성 (python-3.11)

# 3. 변경사항 커밋
git add requirements.txt runtime.txt
git commit -m "fix: Remove Jupyter packages and relax version constraints for Streamlit Cloud"

# 4. GitHub에 push
git push origin main
```

### Step 2: Streamlit Cloud에서 재배포

1. **Streamlit Cloud 대시보드 접속**
   - https://share.streamlit.io 접속
   - 로그인

2. **앱 관리 페이지로 이동**
   - 배포된 앱 목록에서 해당 앱 클릭
   - 또는 "Manage app" 버튼 클릭

3. **앱 재배포**
   - **방법 1 (권장)**: "⋮" (세 점 메뉴) → **"Reboot app"** 클릭
   - **방법 2**: "Settings" → "Advanced settings" → "Always rerun" 토글 ON → 저장
   - **방법 3**: 코드가 자동으로 감지되어 재배포 시작됨 (몇 분 소요)

4. **배포 상태 확인**
   - "Logs" 탭 클릭
   - 빌드 로그 확인:
     - ✅ "Successfully installed ..." 메시지 확인
     - ❌ 에러 발생 시 에러 메시지 복사

5. **에러 발생 시 추가 확인**
   - "Logs" 탭에서 전체 로그 스크롤
   - "Error installing requirements" 섹션 찾기
   - 구체적인 패키지 이름과 에러 메시지 확인
   - 필요시 추가 수정

### Step 3: 배포 성공 확인

- ✅ 앱 URL 접속 가능
- ✅ 메인 페이지 로드 성공
- ✅ 데이터 로드 및 기능 정상 동작

---

## 7. 추가 대안 (위 수정으로 해결 안 될 경우)

### 대안 1: 더 유연한 버전 지정

```diff
# requirements.txt
-streamlit==1.30.0
+streamlit>=1.30.0,<2.0.0

-pandas>=2.0.3,<3.0.0
-numpy>=1.24.3,<2.0.0
+pandas>=2.0.0
+numpy>=1.24.0
```

### 대안 2: Python 버전 변경

```diff
# runtime.txt
-python-3.11
+python-3.10
```

### 대안 3: pyarrow 제거 (Parquet 파일 사용 안 할 경우)

```diff
# requirements.txt
-pyarrow>=14.0.1,<16.0.0
+# pyarrow removed - not needed if not using Parquet files
```

**주의**: Parquet 파일을 사용한다면 pyarrow는 필수입니다.

---

## 8. 예상 결과

### 수정 전
- ❌ "Error installing requirements"
- ❌ Jupyter 패키지 설치 실패 또는 시간 초과
- ❌ 버전 충돌로 인한 의존성 해결 실패

### 수정 후
- ✅ 모든 패키지 정상 설치
- ✅ 빌드 시간 단축 (Jupyter 패키지 제거)
- ✅ Python 3.11 환경에서 호환성 보장
- ✅ 앱 정상 배포 및 실행

---

## 9. 최종 확인 사항

배포 성공 후 확인:

- [ ] Streamlit Cloud 로그에서 "Successfully installed" 메시지 확인
- [ ] 앱 URL 접속 가능
- [ ] 메인 페이지 로드 성공
- [ ] 데이터 로드 정상 (샘플 데이터)
- [ ] 주요 기능 동작 확인 (페이지 이동, 필터 등)

---

**수정 완료 후 위 체크리스트를 따라 배포를 재시도하세요!**

