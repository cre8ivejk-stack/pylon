# PYLON 코드 리뷰 가이드 (v1.1 업데이트)

## 📦 압축 파일 내용

**review.zip** (업데이트됨 - 2025-12-13)

```
review.zip
├── src/                       # 핵심 비즈니스 로직 (10개 파일) ⚠️ 3개 신규 추가
├── components/                # 재사용 컴포넌트 (4개 파일)
├── pages/                     # 4개 메인 페이지 (5개 파일, 한글명)
├── tests/                     # 단위 테스트 (2개 파일)
├── config/                    # 설정 파일 (1개 파일) ⚠️ 신규
├── app.py                     # 메인 진입점
├── requirements.txt           # 의존성 (PyYAML 추가) ⚠️ 업데이트
└── 문서 파일 4개              # README, DEPLOYMENT_GUIDE, 등
```

---

## 🆕 주요 업데이트 사항 (v1.1)

### 1. 신규 파일 (3개)
- ✅ `config/governance.yaml` - 거버넌스 설정
- ✅ `src/config_loader.py` - YAML 설정 로더
- ✅ `src/verified_savings.py` - 검증 절감액 관리

### 2. 핵심 개선사항 (7가지)
1. ✅ **Floating point 수정** - `calculate_plan_variance()` 반올림 적용
2. ✅ **실제 사용자 기능** - 사이드바에서 사용자 입력, session_state 활용
3. ✅ **Governance 자동화** - 데이터 최신성 자동 계산, YAML 설정 기반
4. ✅ **Risk Score 개선** - raw_score(KRW) + display_score(0~100) 이중 표시
5. ✅ **검증 완료 플로우** - verified_savings 저장 → 성과 관리 반영
6. ✅ **완전 한글화** - 모든 UI 라벨, 컬럼명 한글화
7. ✅ **의존성 추가** - PyYAML>=6.0

### 3. 테스트 상태
```
✅ 24/24 tests PASSED
✅ Floating point artifact 해결
✅ Risk Score 테스트 업데이트
```

---

## 🎯 코드 리뷰 우선순위 (업데이트)

### ⭐⭐⭐ 최우선 (50분 소요)

#### 1. **src/analytics.py** (300줄) - 20분
**가장 중요한 파일 - 2가지 주요 변경**

**변경 1: Floating Point 수정**
```python
# Line ~30
def calculate_plan_variance(actual_value, plan_value):
    return {
        'variance': float(round(variance, 10)),  # ⚠️ 신규
        'variance_pct': float(round(variance_pct, 10)),
        'achievement_rate': float(round(achievement_rate, 10))
    }

✅ 체크: round(, 10) 적용으로 floating point artifact 해결
✅ 체크: 모든 반환값에 일관되게 적용
```

**변경 2: Risk Score 공식 개선**
```python
# Line ~60
def calculate_risk_score(impact, likelihood, confidence):
    raw_score = impact * likelihood * confidence  # KRW scale
    display_score = (impact/10M) * likelihood * confidence * 100  # 0-100
    
    return {
        'raw_score': float(round(raw_score, 2)),
        'display_score': float(round(display_score, 2))
    }

✅ 체크: raw_score가 실제 KRW 금액 유지
✅ 체크: display_score가 비교/순위용 0~100 스케일
✅ 체크: 반환 타입이 Dict로 변경됨 (기존 float에서)
```

**리뷰 포인트**:
- [ ] Floating point 처리가 모든 계산 함수에 일관되게 적용되었는가?
- [ ] Risk Score의 두 가지 스케일이 명확히 구분되는가?
- [ ] 기존 호출부에서 Dict 반환값을 올바르게 처리하는가?

---

#### 2. **src/config_loader.py** (40줄) - 5분
**신규 파일 - YAML 설정 로더**

```python
def load_governance_config(config_path: Path = None):
    defaults = {
        'official_version': 'v1.0',
        'plan_locked': False,
        'exception_applied': 0
    }
    
    # config/governance.yaml 읽기
    # 파일 없으면 defaults 반환

✅ 체크: 파일 없을 때 fallback 처리
✅ 체크: YAML 파싱 에러 처리
✅ 체크: UTF-8 인코딩 명시
```

**리뷰 포인트**:
- [ ] 파일이 없거나 손상되었을 때 안전한가?
- [ ] 기본값이 합리적인가?
- [ ] YAML 라이브러리 의존성 추가됨 (requirements.txt)

---

#### 3. **src/verified_savings.py** (120줄) - 10분
**신규 파일 - 검증 절감액 관리**

```python
class VerifiedSavingsManager:
    def create_verified_saving(yymm, site_id, category, 
                               verified_savings_krw, notes):
        # ID 생성 (SAV0001, SAV0002, ...)
        # Parquet 저장
        
    def get_total_verified_savings():
        # 전체 검증 절감액 합계 반환

✅ 체크: ID 생성 로직 (ActionManager와 동일 패턴)
✅ 체크: 동시성 문제 가능성
✅ 체크: Parquet I/O 에러 처리
```

**리뷰 포인트**:
- [ ] ID 생성에 race condition 가능성은?
- [ ] site_id가 None일 때 처리 (집계 절감)
- [ ] 중복 저장 방지 로직이 필요한가?

---

#### 4. **src/models.py** (170줄) - 10분
**주요 변경: GovernanceBadge 자동화**

```python
@dataclass
class GovernanceBadge:
    # ... 기존 필드 ...
    
    @staticmethod
    def create_from_config_and_data(config: dict, 
                                    latest_yymm: str = None):
        # config에서 설정 읽기
        # latest_yymm을 "YYYY-MM" 포맷으로 변환
        # GovernanceBadge 인스턴스 생성

✅ 체크: YYMM → YYYY-MM 변환 로직
✅ 체크: latest_yymm이 None일 때 처리
```

**리뷰 포인트**:
- [ ] 날짜 변환 로직이 정확한가? (23 → 2023, 24 → 2024)
- [ ] Static method vs Class method 선택이 적절한가?

---

#### 5. **config/governance.yaml** (6줄) - 3분
**신규 파일 - 거버넌스 설정**

```yaml
official_version: "v2.3"
plan_locked: true
exception_applied: 0

✅ 체크: 간단하고 명확한 구조
✅ 체크: 한글 주석 가능
```

**리뷰 포인트**:
- [ ] 설정 값의 타입이 명확한가?
- [ ] 추가 설정이 필요한가?
- [ ] 문서화가 필요한가?

---

### ⭐⭐ 중요 (40분 소요)

#### 6. **app.py** (210줄) - 10분
**주요 변경: 사용자 입력 + Governance 자동화**

```python
# 신규: 사이드바 사용자 섹션
with st.sidebar:
    st.markdown("## 👤 사용자")
    if "current_user" not in st.session_state:
        st.session_state["current_user"] = "담당자"
    st.session_state["current_user"] = st.text_input(
        "내 이름", st.session_state["current_user"]
    )

# 신규: Governance 자동 생성
gov_config = load_governance_config()
bills_df = dal.load_bills()
latest_yymm = bills_df['yymm'].max()
governance_badge = GovernanceBadge.create_from_config_and_data(
    gov_config, latest_yymm
)

✅ 체크: session_state 사용 패턴
✅ 체크: 모든 페이지 간 공유 가능
```

**리뷰 포인트**:
- [ ] session_state가 페이지 간 올바르게 공유되는가?
- [ ] 사용자 입력 validation이 필요한가?
- [ ] bills_df 로드 실패 시 fallback 처리

---

#### 7. **pages/1_에너지_인텔리전스.py** (350줄) - 10분
**주요 변경: 사용자 입력 + Governance**

```python
# 각 페이지마다 동일한 사용자 입력 섹션
with st.sidebar:
    st.markdown("## 👤 사용자")
    if "current_user" not in st.session_state:
        st.session_state["current_user"] = "담당자"
    st.session_state["current_user"] = st.text_input(
        "내 이름", 
        st.session_state["current_user"],
        key="user_input_page1"  # ⚠️ 각 페이지마다 unique key
    )

✅ 체크: 각 페이지의 key가 unique한가?
✅ 체크: session_state 동기화
```

**리뷰 포인트**:
- [ ] 사용자 입력이 모든 페이지에서 일관되게 보이는가?
- [ ] key 충돌이 없는가?

---

#### 8. **pages/2_성과_리스크_관리.py** (320줄) - 10분
**주요 변경: Risk Score + 3단계 절감**

**변경 1: Risk Score 처리**
```python
# Line ~225
risk_scores = merged.apply(
    lambda row: calculate_risk_score(...), axis=1
)
merged['risk_score_raw'] = risk_scores.apply(lambda x: x['raw_score'])
merged['risk_score_display'] = risk_scores.apply(lambda x: x['display_score'])

# Line ~235: 한글 컬럼명
high_risk_display.columns = [
    '국소ID', '지역', '계약유형', '청구금액(원)', '영향도(원)', 
    '발생가능성', '신뢰도', '리스크점수(원기반)', '리스크점수(0~100)'
]

✅ 체크: Dict 반환값 처리
✅ 체크: 한글 컬럼명 적용
```

**변경 2: 3단계 절감 표시**
```python
# Line ~90
verified_total = verified_savings_manager.get_total_verified_savings()

col1: 예상 절감 (계획/제안)
col2: 진행 절감 (실행 중)
col3: 확정 절감 (검증 완료) ⚠️ verified_total 표시

✅ 체크: verified_savings 통합
✅ 체크: 3단계 구분 명확
```

**리뷰 포인트**:
- [ ] Risk Score의 두 값이 올바르게 추출되는가?
- [ ] 한글 컬럼명이 데이터와 매칭되는가?
- [ ] 확정 절감이 실시간으로 업데이트되는가?

---

#### 9. **pages/4_검증_실증.py** (420줄) - 10분
**주요 변경: 검증 완료 플로우**

```python
# Line ~240
if st.button("✅ 검증 완료로 반영", type="primary"):
    # 1. verified_savings 저장
    saving_id = verified_savings_manager.create_verified_saving(
        yymm=phase_out_month,
        site_id=None,  # 집계
        category="3G Phase-Out",
        verified_savings_krw=cost_reduction,
        notes=f"..."
    )
    
    # 2. Action 생성
    current_user = st.session_state.get("current_user", "담당자")
    action = action_manager.create_action(
        owner=current_user,  # ⚠️ 실제 사용자
        category=ActionCategory.VERIFICATION,
        description=f"...",
        ...
    )
    
    st.success(f"✅ 검증 완료 반영: {saving_id}")
    st.balloons()

✅ 체크: 검증 완료 → 저장 → Action 생성
✅ 체크: 실제 사용자 활용
```

**리뷰 포인트**:
- [ ] verified_savings와 action이 모두 생성되는가?
- [ ] 버튼 중복 클릭 방지가 필요한가?
- [ ] 성공 메시지가 사용자 친화적인가?

---

### ⭐ 참고 (20분 소요)

#### 10. **components/global_controls.py** (145줄) - 5분
**한글화 업데이트**

```python
# Line ~65
with col1:
    st.metric(label="공식 기준", value=f"{badge.official_version}")
with col2:
    lock_status = "적용" if badge.plan_locked else "미적용"
    st.metric(label="계획 잠금", value=lock_status)
with col3:
    st.metric(label="데이터 최신성", value=badge.data_freshness)
with col4:
    exception_status = "있음" if badge.exceptions_applied > 0 else "없음"
    st.metric(label="예외 적용", value=f"{exception_status} ({badge.exceptions_applied}건)")

✅ 체크: 모든 라벨 한글
✅ 체크: 상태 표시 명확
```

---

#### 11. **components/action_inbox.py** (105줄) - 5분
**한글화**

```python
st.markdown("### 📬 내 작업함")
st.markdown(f"**📬 작업:** {stats['todo']} 대기 | {stats['doing']} 진행 | ...")
```

---

#### 12. **tests/test_analytics.py** (350줄) - 10분
**Risk Score 테스트 업데이트**

```python
def test_high_risk(self):
    result = calculate_risk_score(...)
    assert result['raw_score'] == 10_000_000 * 0.8 * 0.9
    assert 50 < result['display_score'] <= 100

✅ 체크: Dict 반환값 테스트
✅ 체크: 두 가지 스케일 검증
```

---

## 📊 파일 통계 (업데이트)

| 파일 | 라인 수 | 변경 | 우선순위 | 소요 시간 |
|------|---------|------|----------|-----------|
| src/analytics.py | 300 | 수정 | ⭐⭐⭐ | 20분 |
| src/config_loader.py | 40 | 신규 | ⭐⭐⭐ | 5분 |
| src/verified_savings.py | 120 | 신규 | ⭐⭐⭐ | 10분 |
| src/models.py | 170 | 수정 | ⭐⭐⭐ | 10분 |
| config/governance.yaml | 6 | 신규 | ⭐⭐⭐ | 3분 |
| app.py | 210 | 수정 | ⭐⭐ | 10분 |
| pages/1_에너지_인텔리전스.py | 350 | 수정 | ⭐⭐ | 10분 |
| pages/2_성과_리스크_관리.py | 320 | 수정 | ⭐⭐ | 10분 |
| pages/4_검증_실증.py | 420 | 수정 | ⭐⭐ | 10분 |
| components/global_controls.py | 145 | 수정 | ⭐ | 5분 |
| components/action_inbox.py | 105 | 수정 | ⭐ | 5분 |
| tests/test_analytics.py | 350 | 수정 | ⭐ | 10분 |

**총 소요 시간**: 110분 (집중 리뷰 기준)

---

## 🔍 주요 리뷰 체크리스트 (업데이트)

### 1. 코드 품질
- [ ] **Floating point 처리**: round(, 10) 일관되게 적용
- [ ] **타입 변경 영향**: calculate_risk_score가 Dict 반환 (기존 float)
- [ ] **신규 파일 구조**: config_loader, verified_savings 설계 적절성
- [ ] **한글화 일관성**: 모든 UI 라벨이 한글인가?

### 2. 에러 처리
- [ ] **YAML 파싱 실패**: config_loader에서 fallback 처리
- [ ] **데이터 없음**: latest_yymm이 None일 때
- [ ] **파일 I/O**: verified_savings Parquet 저장 실패
- [ ] **session_state 미초기화**: current_user가 없을 때

### 3. 성능
- [ ] **불필요한 로드**: 각 페이지마다 config 로드 (캐싱 고려?)
- [ ] **risk_scores apply**: lambda 함수 성능 (대량 데이터)
- [ ] **verified_savings 조회**: 매번 Parquet 읽기 (캐싱?)

### 4. 보안
- [ ] **사용자 입력 검증**: current_user에 특수문자/길이 제한?
- [ ] **YAML injection**: governance.yaml 수동 편집 시 위험성
- [ ] **파일 경로**: config/governance.yaml 경로 안전성

### 5. 비즈니스 로직
- [ ] **Risk Score 공식**: raw vs display 구분이 명확한가?
- [ ] **검증 완료 플로우**: verified_savings + action 생성 순서
- [ ] **3단계 절감**: 예상/진행/확정 구분 기준 명확

### 6. 테스트
- [ ] **24개 테스트 통과**: pytest 결과 확인
- [ ] **Floating point**: artifact 완전 해결
- [ ] **Risk Score**: Dict 반환값 테스트 추가

---

## 🚨 주요 이슈 후보 (업데이트)

### Critical (즉시 확인)
1. **타입 변경 영향**: calculate_risk_score 반환 타입 변경
   - 모든 호출부에서 Dict 처리하는지 확인
   - 기존 코드가 float 가정했다면 오류 가능성

2. **사용자 입력 key 충돌**: 
   - 각 페이지마다 `key="user_input_pageN"` 사용
   - 누락된 페이지 없는지 확인

3. **검증 완료 중복 클릭**:
   - "검증 완료로 반영" 버튼 중복 클릭 시 중복 저장
   - 세션 플래그 또는 ID 중복 체크 필요

### High Priority
4. **성능**: config 로드가 페이지마다 반복
   - st.cache_data 적용 고려
   
5. **verified_savings 통합**:
   - 성과 관리에서 실시간 반영되는지 확인
   - 캐시 무효화 필요 여부

### Medium Priority
6. **한글 인코딩**: governance.yaml UTF-8 보장
7. **session_state 초기화**: 페이지 첫 진입 시 처리
8. **날짜 변환**: YYMM → YYYY-MM 로직 (2030년대 고려)

---

## 💬 리뷰 코멘트 템플릿

### 긍정적 피드백
```
👍 잘한 점:
- Floating point artifact 완벽 해결
- Risk Score 이중 스케일로 실용성 향상
- 검증 완료 플로우로 운영 라이프사이클 완성
- 완전 한글화로 UX 대폭 개선
```

### 개선 제안
```
💡 개선 제안:
- [src/analytics.py:65] Risk Score Dict 반환 - 호출부 영향 확인 필요
- [pages/4_검증_실증.py:245] 검증 완료 버튼 중복 클릭 방지
- [app.py:25] config 로드 캐싱 고려
- [src/verified_savings.py:45] ID 생성 동시성 문제
```

### 질문
```
❓ 질문:
- Risk Score의 raw vs display 사용 기준이 명확한가?
- 확정 절감이 월별인가 연간인가?
- YAML 설정 변경 시 앱 재시작 필요한가?
```

---

## 📝 리뷰 후 액션 아이템

```markdown
## v1.1 리뷰 결과 요약

### Critical (즉시 수정 필요)
- [ ] calculate_risk_score Dict 반환 - 모든 호출부 확인
- [ ] 검증 완료 버튼 중복 클릭 방지

### Important (다음 스프린트)
- [ ] config 로드 캐싱 적용
- [ ] verified_savings ID 생성 Lock
- [ ] 사용자 입력 validation

### Nice to Have (백로그)
- [ ] YAML 설정 UI 제공
- [ ] 확정 절감 상세 내역 페이지
- [ ] Risk Score 설명 툴팁 추가
```

---

## 🔗 참고 문서

압축 파일에 포함된 문서들:

1. **README.md**: 프로젝트 개요, 설치 방법
2. **DEPLOYMENT_GUIDE.md**: 배포 가이드, 데이터 연동
3. **PROJECT_SUMMARY.md**: 완성 항목 체크리스트
4. **ARCHITECTURE.md**: 시스템 아키텍처 다이어그램

---

## ⏱️ 권장 리뷰 순서 (업데이트)

### Day 1 (1시간 10분)
1. **변경사항 요약** 읽기 (5분)
2. **src/analytics.py** 리뷰 (20분) ⚠️ 중점
3. **src/config_loader.py** 리뷰 (5분) ⚠️ 신규
4. **src/verified_savings.py** 리뷰 (10분) ⚠️ 신규
5. **src/models.py** 리뷰 (10분)
6. **config/governance.yaml** 확인 (3분) ⚠️ 신규
7. **app.py** 리뷰 (10분)
8. 메모 정리 (7분)

### Day 2 (1시간)
1. **pages/2_성과_리스크_관리.py** (15분) ⚠️ 중점
2. **pages/4_검증_실증.py** (15분) ⚠️ 중점
3. **pages/1_에너지_인텔리전스.py** (10분)
4. **components/** 파일들 (10분)
5. **tests/test_analytics.py** (10분)
6. 최종 리뷰 코멘트 작성 (10분)

---

## 📧 연락처

리뷰 중 질문사항이 있으면:
- 프로젝트 폴더의 상세 문서 참고
- 테스트 코드로 의도 파악
- 실제 실행하여 동작 확인 (streamlit run app.py)

---

## ✅ 체크리스트

리뷰 시작 전:
- [ ] pytest 24개 테스트 통과 확인
- [ ] requirements.txt PyYAML 추가 확인
- [ ] config/governance.yaml 존재 확인

리뷰 완료 후:
- [ ] Critical 이슈 식별
- [ ] 개선 제안 작성
- [ ] 다음 액션 아이템 정리

---

*코드 리뷰 가이드 v1.1 | PYLON Project | Updated 2025-12-13*
