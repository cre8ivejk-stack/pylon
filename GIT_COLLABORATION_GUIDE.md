# Git 협업 가이드

## 🤝 두 명의 개발자 협업 시나리오

### 시나리오: 각자 새로운 메뉴(페이지) 개발

```
개발자 A: pages/5_📊_데이터마트_분석.py 생성
개발자 B: pages/6_🔍_보고서_관리.py 생성
```

---

## ✅ 충돌 없는 경우 (안전)

### 케이스 1: 완전히 다른 파일 작업

```
개발자 A가 작업:
  pages/5_📊_데이터마트_분석.py (신규)
  data/datamart_connector.py (신규)

개발자 B가 작업:
  pages/6_🔍_보고서_관리.py (신규)
  data/report_generator.py (신규)

결과: ✅ 충돌 없음!
```

**이유:**
- 각자 다른 파일을 생성/수정
- Git이 자동으로 병합 가능

**워크플로우:**
```bash
# 개발자 A
git add pages/5_📊_데이터마트_분석.py data/datamart_connector.py
git commit -m "feat: 데이터마트 분석 페이지 추가"
git push origin development

# 개발자 B (나중에 push)
git pull origin development  # A의 변경사항 받기
git add pages/6_🔍_보고서_관리.py data/report_generator.py
git commit -m "feat: 보고서 관리 페이지 추가"
git push origin development

# 결과: 둘 다 정상 병합 ✅
```

---

## ⚠️ 충돌 가능한 경우

### 케이스 2: 같은 파일의 같은 부분 수정

```
개발자 A와 B 모두:
  app.py 수정 (같은 줄)
  components/layout.py 수정 (같은 함수)

결과: ❌ 충돌 발생!
```

**예시:**

```python
# app.py (원본)
import streamlit as st

st.title("PYLON")

# 개발자 A의 수정
import streamlit as st
import pandas as pd  # A가 추가

st.title("PYLON v2.0")  # A가 수정

# 개발자 B의 수정
import streamlit as st
import numpy as np  # B가 추가

st.title("PYLON - Energy Platform")  # B가 수정
```

**충돌 발생:**
```bash
# 개발자 B가 push 시도
git push origin development
# Error: Updates were rejected because the remote contains work...

# Pull 시도
git pull origin development
# CONFLICT: Merge conflict in app.py
```

---

## 🛡️ 충돌 방지 전략

### 1. 작업 전 항상 Pull

```bash
# 작업 시작 전 (매일 아침, 작업 전)
git checkout development
git pull origin development
```

### 2. 브랜치 전략 활용

```bash
# 개발자 A
git checkout -b feature/datamart-analysis
# 작업...
git push origin feature/datamart-analysis

# 개발자 B
git checkout -b feature/report-management
# 작업...
git push origin feature/report-management

# 각자 개발 완료 후
# → development로 merge (순차적으로)
```

### 3. 작업 영역 분리

**권장 방식:**
```
개발자 A 담당:
  pages/5_*.py
  data/datamart_*.py
  components/datamart_*.py

개발자 B 담당:
  pages/6_*.py
  data/report_*.py
  components/report_*.py

공통 파일은 사전 조율 후 수정
```

### 4. 자주 커밋 & Push

```bash
# 작은 단위로 자주 커밋
git add pages/5_data_analysis.py
git commit -m "feat: 데이터 로드 함수 추가"
git push origin development

# 나중에
git add pages/5_data_analysis.py
git commit -m "feat: 차트 추가"
git push origin development
```

---

## 🔄 실전 협업 워크플로우

### 방법 1: Feature 브랜치 (추천)

```
main/master (운영)
    ↓
development (개발 통합)
    ↓
    ├─ feature/dev-a-datamart (개발자 A)
    └─ feature/dev-b-report (개발자 B)
```

**개발자 A:**
```bash
# 1. 최신 코드 받기
git checkout development
git pull origin development

# 2. 자신의 feature 브랜치 생성
git checkout -b feature/dev-a-datamart

# 3. 개발 작업
# pages/5_데이터마트.py 생성
# data/datamart_connector.py 생성

# 4. 커밋 & Push
git add .
git commit -m "feat: 데이터마트 분석 페이지 추가"
git push origin feature/dev-a-datamart

# 5. 완료 후 development로 merge
git checkout development
git merge feature/dev-a-datamart
git push origin development
```

**개발자 B:**
```bash
# 1. 최신 코드 받기 (A의 작업 포함)
git checkout development
git pull origin development

# 2. 자신의 feature 브랜치 생성
git checkout -b feature/dev-b-report

# 3. 개발 작업
# pages/6_보고서.py 생성

# 4. 커밋 & Push
git add .
git commit -m "feat: 보고서 관리 페이지 추가"
git push origin feature/dev-b-report

# 5. 완료 후 development로 merge
git checkout development
git pull origin development  # A의 최신 작업 받기
git merge feature/dev-b-report
git push origin development
```

---

### 방법 2: 직접 Development 작업 (간단)

```bash
# 개발자 A
git pull origin development  # 항상 먼저!
# 작업...
git add pages/5_데이터마트.py
git commit -m "feat: 데이터마트 페이지"
git push origin development

# 개발자 B (조금 후)
git pull origin development  # A의 작업 받기
# 작업...
git add pages/6_보고서.py
git commit -m "feat: 보고서 페이지"
git push origin development
```

---

## 🚨 충돌 해결 방법

### 충돌이 발생했을 때

```bash
# Push 실패 시
git push origin development
# Error: Updates were rejected

# 최신 코드 받기
git pull origin development
# CONFLICT in app.py

# 충돌 확인
git status
# Unmerged paths:
#   both modified:   app.py
```

**충돌 파일 확인:**
```python
# app.py
<<<<<<< HEAD (내 변경사항)
import pandas as pd
st.title("PYLON v2.0")
=======
import numpy as np
st.title("PYLON - Energy Platform")
>>>>>>> origin/development (원격 변경사항)
```

**해결 방법:**
```python
# 둘 다 반영하도록 수정
import pandas as pd
import numpy as np
st.title("PYLON v2.0 - Energy Platform")
```

**완료:**
```bash
git add app.py
git commit -m "merge: 충돌 해결"
git push origin development
```

---

## 📋 협업 체크리스트

### 작업 시작 전
- [ ] `git pull origin development` 실행
- [ ] 최신 코드인지 확인
- [ ] 작업 영역 확인 (다른 개발자와 겹치는지)

### 작업 중
- [ ] 자주 커밋 (작은 단위)
- [ ] 의미 있는 커밋 메시지
- [ ] 다른 개발자와 소통

### Push 전
- [ ] `git pull origin development` (한번 더!)
- [ ] 로컬에서 테스트
- [ ] 충돌 없는지 확인

### Push 후
- [ ] 다른 개발자에게 알림
- [ ] Playground에서 확인 (필요시)

---

## 💡 권장 규칙

### 1. 파일 명명 규칙
```
pages/
  5_📊_데이터마트_분석.py      # 개발자 A
  6_🔍_보고서_관리.py          # 개발자 B
  
data/
  datamart_connector.py        # 개발자 A 전용
  report_generator.py          # 개발자 B 전용
  
components/
  datamart_charts.py           # 개발자 A 전용
  report_widgets.py            # 개발자 B 전용
```

### 2. 커밋 메시지 컨벤션
```bash
feat: 새 기능 추가
fix: 버그 수정
docs: 문서 수정
refactor: 코드 리팩토링
style: 코드 포맷팅
test: 테스트 코드
```

### 3. 소통 규칙
- Slack/Teams로 작업 시작/완료 공유
- 공통 파일 수정 시 사전 협의
- 매일 아침 코드 동기화

---

## ✅ 질문에 대한 답변

### Q: 각자 다른 메뉴를 만들 때 충돌이 없을까?

**A: 네, 충돌 없습니다!** ✅

```
개발자 A: pages/5_메뉴A.py 생성
개발자 B: pages/6_메뉴B.py 생성

→ 완전히 다른 파일이므로 충돌 없음
→ Git이 자동으로 병합
```

**단, 주의사항:**
1. 작업 전에 항상 `git pull`
2. 같은 파일을 동시에 수정하지 않기
3. 공통 모듈 수정 시 조율

---

## 🚀 추천 워크플로우 (요약)

```bash
# 매일 아침
git pull origin development

# 작업 시작
git checkout -b feature/my-work  # (옵션)

# 개발...

# 커밋
git add pages/새메뉴.py
git commit -m "feat: 새 메뉴 추가"

# Push 전 최신화
git pull origin development

# Push
git push origin development
# 또는 git push origin feature/my-work

# 다른 개발자에게 알림 📢
```

---

## 📞 문제 발생 시

1. **Push가 거부됨**: `git pull` 먼저 실행
2. **충돌 발생**: 파일 열어서 수동 병합
3. **모르겠을 때**: 다른 개발자와 상의

**팁:** 작은 단위로 자주 커밋하고 Push하면 충돌 확률이 줄어듭니다!

