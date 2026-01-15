# Git Rebase 실행 가이드 (현재 상황 대응)

## 현재 상태
- ✅ Rebase 진행 중 (충돌 해결 완료)
- ⚠️ 추가 변경사항 있음 (staged되지 않은 파일들)
- ⚠️ 새 파일: PYLON_NOTEBOOKLM_SOURCE.md

---

## 1. 실행할 Git 명령어 순서 (Rebase 방식)

### Step 1: 현재 변경사항 모두 스테이징
```powershell
git add .
```

### Step 2: Rebase 계속 진행 (에디터 건너뛰기)
```powershell
$env:GIT_EDITOR='true'
git rebase --continue
```

**또는 단계별로:**
```powershell
# 1. 원격 정보 가져오기 (이미 완료됨)
git fetch origin

# 2. Rebase 계속 진행
$env:GIT_EDITOR='true'
git rebase --continue
```

### Step 3: Rebase 완료 확인
```powershell
git log --oneline --graph -10
```

### Step 4: 최종 Push
```powershell
git push origin main
```

---

## 2. 충돌 발생 시 해결 체크리스트

### 2.1 충돌 감지
```powershell
git status
# "CONFLICT (content): Merge conflict in <파일명>" 메시지 확인
```

### 2.2 충돌 파일 확인
```powershell
# 충돌 파일 목록 확인
git status

# 충돌 파일만 필터링
git diff --name-only --diff-filter=U
```

### 2.3 충돌 마커 확인

충돌 파일을 열어서 다음 마커를 찾습니다:

```
<<<<<<< HEAD (또는 커밋 해시)
내 변경사항 (B의 코드)
=======
A의 변경사항 (원격 main의 코드)
>>>>>>> origin/main (또는 커밋 해시)
```

**마커 의미:**
- `<<<<<<<`: 충돌 시작 (내 변경)
- `=======`: 구분선
- `>>>>>>>`: 충돌 끝 (A의 변경)

### 2.4 충돌 해결 절차

#### ✅ 체크리스트

- [ ] **Step 1**: 충돌 파일 열기
  ```powershell
  code <충돌파일명>  # VS Code
  # 또는
  notepad <충돌파일명>  # 메모장
  ```

- [ ] **Step 2**: 충돌 영역 분석
  - A의 변경사항: `=======` 아래 부분 확인
  - 내 변경사항: `<<<<<<<` 아래 부분 확인
  - 충돌 원인 파악

- [ ] **Step 3**: 해결 원칙 적용
  - ✅ A의 로직/동작 기본 유지
  - ✅ 내 변경이 필요한 부분만 최소 침습으로 합치기
  - ✅ 양쪽 변경 모두 필요한 경우 병합

- [ ] **Step 4**: 충돌 해결 예시

  **케이스 1: A의 변경만 유지**
  ```python
  # 충돌 상태
  <<<<<<< HEAD
  def old_function():
      return "old"
  =======
  def new_function():
      return "new"
  >>>>>>> origin/main
  
  # 해결: A의 변경 유지
  def new_function():
      return "new"
  ```

  **케이스 2: 내 변경만 유지 (내 변경이 더 중요할 때)**
  ```python
  # 충돌 상태
  <<<<<<< HEAD
  def my_important_function():
      return "my logic"
  =======
  def other_function():
      return "other"
  >>>>>>> origin/main
  
  # 해결: 내 변경 유지 (단, A의 변경도 검토 필요)
  def my_important_function():
      return "my logic"
  ```

  **케이스 3: 양쪽 모두 병합**
  ```python
  # 충돌 상태
  <<<<<<< HEAD
  def function_a():
      return "a"
  =======
  def function_b():
      return "b"
  >>>>>>> origin/main
  
  # 해결: 양쪽 모두 유지
  def function_a():
      return "a"
  
  def function_b():
      return "b"
  ```

  **케이스 4: 함수 내부 로직 충돌**
  ```python
  # 충돌 상태
  <<<<<<< HEAD
  def calculate(x, y):
      result = x + y  # 내 로직
      return result
  =======
  def calculate(x, y):
      result = x * y  # A의 로직
      return result
  >>>>>>> origin/main
  
  # 해결: A의 로직 기본 유지, 내 변경이 필요하면 최소 침습
  def calculate(x, y):
      result = x * y  # A의 로직 유지
      # 내 추가 로직이 필요하면 주석이나 별도 함수로
      return result
  ```

- [ ] **Step 5**: 충돌 마커 제거
  - 모든 `<<<<<<<`, `=======`, `>>>>>>>` 마커 제거
  - 최종 코드만 남기기

- [ ] **Step 6**: 충돌 해결 완료 표시
  ```powershell
  # 해결한 파일을 staging area에 추가
  git add <해결한파일명>
  
  # 또는 모든 충돌 해결 파일 추가
  git add .
  ```

- [ ] **Step 7**: Rebase 계속 진행
  ```powershell
  $env:GIT_EDITOR='true'
  git rebase --continue
  ```

- [ ] **Step 8**: Rebase 중단 (필요시)
  ```powershell
  git rebase --abort
  ```

### 2.5 충돌 해결 검증

#### 코드 검증
```powershell
# Python 문법 오류 확인
python -m py_compile <파일명>

# 또는 전체 프로젝트
python -m compileall .
```

#### 테스트 실행
```powershell
# 관련 테스트 실행
pytest tests/
# 또는
python -m pytest tests/test_<관련파일>.py
```

#### 빌드 확인 (해당되는 경우)
```powershell
# 프로젝트 빌드
python setup.py build
```

---

## 3. 충돌 해결 원칙 상세

### 3.1 A의 로직 기본 유지
- **이유**: A가 먼저 push했으므로 이미 검증된 코드일 가능성 높음
- **방법**: A의 변경사항을 기본으로 채택

### 3.2 최소 침습 병합
- **원칙**: 가능한 한 A의 코드 구조를 유지
- **방법**: 
  - 내 변경이 필수적이면 최소한의 수정만
  - 주석이나 별도 함수로 분리
  - A의 함수 시그니처 유지

### 3.3 검토 필요 사항
- A의 변경이 내 변경과 충돌하는 이유
- 양쪽 변경 모두 필요한지
- 하나를 선택해도 되는지

---

## 4. 최종 Push 전 확인 항목

### 4.1 Git 상태 확인
```powershell
# 현재 상태 확인
git status

# 커밋 히스토리 확인
git log --oneline --graph -10

# 원격과의 차이 확인
git diff origin/main..HEAD
```

### 4.2 코드 검증

#### 문법 검사
```powershell
# Python
python -m py_compile **/*.py

# 또는 전체 프로젝트
python -m compileall .
```

#### 린터 실행 (해당되는 경우)
```powershell
# pylint, flake8 등
pylint src/
flake8 src/
```

### 4.3 테스트 실행
```powershell
# 전체 테스트
pytest tests/

# 특정 테스트
pytest tests/test_<관련파일>.py -v

# 커버리지 포함
pytest tests/ --cov=src
```

### 4.4 빌드 확인
```powershell
# 프로젝트 빌드
python setup.py build

# 또는 패키지 설치 테스트
pip install -e .
```

### 4.5 실행 확인
```powershell
# 앱 실행 테스트
streamlit run app.py

# 또는
python app.py
```

### 4.6 최종 체크리스트
- [ ] 모든 충돌 해결 완료
- [ ] 문법 오류 없음
- [ ] 린터 경고 해결 (해당되는 경우)
- [ ] 테스트 통과
- [ ] 빌드 성공 (해당되는 경우)
- [ ] 앱 정상 실행
- [ ] 히스토리 확인 (선형 구조)
- [ ] 원격과의 차이 확인

---

## 5. Rebase 대안: Merge 방식

Rebase가 부담되면 Merge 방식 사용 가능

### 5.1 Merge 방식 절차

#### Step 1: Rebase 중단
```powershell
git rebase --abort
```

#### Step 2: 현재 상태 확인
```powershell
git status
git log --oneline -5
```

#### Step 3: 원격 정보 가져오기
```powershell
git fetch origin
```

#### Step 4: Merge 실행
```powershell
# Rebase 대신 Merge
git pull origin main
# 또는
git merge origin/main
```

#### Step 5: Merge 충돌 해결
- Rebase와 동일한 충돌 해결 절차 (섹션 2 참조)
- 단, 충돌 마커가 약간 다를 수 있음:
```
<<<<<<< HEAD
내 변경사항
=======
A의 변경사항
>>>>>>> origin/main
```

#### Step 6: Merge 커밋 생성
```powershell
# 충돌 해결 후
git add .
git commit -m "Merge origin/main into local branch"
```

#### Step 7: Push
```powershell
git push origin main
```

### 5.2 Rebase vs Merge 비교

| 항목 | Rebase | Merge |
|------|--------|-------|
| 히스토리 | 선형 (깔끔) | 병합 커밋 생성 |
| 복잡도 | 중간 (충돌 시 여러 번 해결) | 낮음 (충돌 한 번만) |
| 안전성 | 높음 (단계별 확인 가능) | 높음 |
| 추천 | 히스토리 정리 원할 때 | 간단하게 병합 원할 때 |

### 5.3 Merge 방식 장단점

**장점:**
- 충돌을 한 번만 해결
- 원래 커밋 히스토리 보존
- 더 직관적

**단점:**
- 병합 커밋이 생성되어 히스토리가 복잡해짐
- 여러 사람이 작업 시 히스토리가 지저분해질 수 있음

---

## 6. 문제 발생 시 대응

### 6.1 Rebase 중단
```powershell
# Rebase 취소
git rebase --abort
```

### 6.2 Merge 취소
```powershell
# Merge 취소
git merge --abort
```

### 6.3 원격과 로컬 상태 확인
```powershell
# 원격 브랜치 정보 확인
git remote -v
git branch -r

# 로컬과 원격 차이
git log HEAD..origin/main
git log origin/main..HEAD
```

### 6.4 백업 브랜치 생성 (안전장치)
```powershell
# 현재 상태 백업
git branch backup-before-merge

# 백업 브랜치로 돌아가기 (필요시)
git checkout backup-before-merge
```

---

## 7. 현재 상황 대응 (즉시 실행)

현재 Rebase 진행 중이고 충돌은 해결된 상태입니다. 다음 명령어를 순서대로 실행하세요:

```powershell
# 1. 추가 변경사항 스테이징
git add .

# 2. Rebase 계속 진행 (에디터 건너뛰기)
$env:GIT_EDITOR='true'
git rebase --continue

# 3. 완료 확인
git log --oneline --graph -10

# 4. Push
git push origin main
```

---

## 8. 주의사항

⚠️ **절대 하지 말아야 할 것:**
- `git push --force` 또는 `git push -f`
- `git push --force-with-lease` (특별한 경우 제외)
- Rebase/Merge 중인 상태에서 다른 작업

✅ **안전한 작업:**
- 항상 `git fetch` 먼저 실행
- 충돌 해결 후 테스트 실행
- Push 전 최종 확인
- 백업 브랜치 생성 (복잡한 경우)

