# 🚀 빠른 시작 가이드

## 📍 현재 워크플로우

```
사내망 Jupyter에서 개발
    ↓ git push
Playground에서 검증
```

---

## 🎯 사내망 Jupyter에서 시작하기

### Step 1: 최신 코드 받기

```bash
cd pylon-test4/
git checkout master
git pull pylon-test4 master
```

### Step 2: 개발 브랜치 생성/전환

```bash
git checkout -b development
# 또는 이미 있다면
git checkout development
```

### Step 3: notebooks 폴더 생성

```bash
mkdir notebooks
```

### Step 4: 새 노트북으로 개발 시작

`notebooks/datamart_dev.ipynb` 생성:

```python
# Cell 1: 환경 확인
import pandas as pd
import sqlalchemy
import plotly.graph_objects as go

print("✅ 시작 준비 완료!")

# Cell 2: 데이터마트 연결
conn_string = "postgresql://user:pass@host:port/db"
engine = sqlalchemy.create_engine(conn_string)

# Cell 3: 데이터 로드 테스트
df = pd.read_sql("SELECT * FROM your_table LIMIT 100", engine)
df.head()

# Cell 4: 차트 테스트
fig = go.Figure()
fig.add_trace(go.Scatter(x=df['date'], y=df['value']))
fig.show()  # 노트북에서 바로 확인!
```

### Step 5: 검증 완료 후 .py 파일로 정리

```python
# data/datamart_connector.py 생성
# 노트북에서 검증된 코드 복사
```

### Step 6: Git 커밋 & Push

```bash
git add data/*.py pages/*.py
git commit -m "feat: 데이터마트 연동 추가"
git push pylon-test4 development

# 확신이 들면 master로
git checkout master
git merge development
git push pylon-test4 master  # Playground 배포!
```

---

## 📚 상세 가이드

더 자세한 내용은 다음 문서 참조:

- **`notebooks/WORKFLOW_SECURE.md`**: 전체 워크플로우 상세 가이드
- **`notebooks/template_code.py`**: 복사해서 사용할 템플릿 코드
- **`DEVELOPMENT_GUIDE.md`**: 개발 환경 전체 가이드

---

## ✅ 체크리스트

### 시작 전
- [ ] 사내망 Jupyter 접속
- [ ] pylon-test4 디렉토리로 이동
- [ ] `git pull pylon-test4 master` 실행
- [ ] development 브랜치 전환

### 개발 중
- [ ] notebooks에서 충분히 테스트
- [ ] 차트가 제대로 나오는지 확인
- [ ] 에러 케이스 처리
- [ ] .py 파일로 정리

### 배포 전
- [ ] Jupyter에서 모든 기능 검증 완료
- [ ] development 브랜치에 커밋
- [ ] 코드 리뷰
- [ ] master에 merge

### 배포 후
- [ ] Playground 빌드 대기
- [ ] 사내망에서 앱 접속
- [ ] 새 기능 확인

---

## 🔄 전체 플로우

```
[사내망 Jupyter]
notebooks/dev.ipynb
  ↓ 개발 & 검증 (90%)
data/*.py, pages/*.py
  ↓ git push development
  ↓ 코드 리뷰
  ↓ git push master
[Playground]
  ↓ 자동 빌드
  ↓ 사내망에서 확인 (10%)
✅ 완료 또는 수정
```

