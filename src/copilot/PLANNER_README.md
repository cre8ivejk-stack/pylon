# Copilot Planner - 자연어 질의를 Plan으로 변환

이 모듈은 자연어 질의를 구조화된 Plan(JSON)으로 변환하는 LLM 기반 플래너를 제공합니다.

## 파일 구조

- `schemas.py`: Plan 스키마 정의 (Plan, TimeRange, Filters, QueryType, Metric)
- `planner.py`: LLM 플래너 및 규칙 기반 fallback 구현
- `ui.py`: Clarification UI 컴포넌트

## Plan 스키마

```python
{
  "query_type": "top_n" | "trend" | "comparison" | "anomaly" | "recommendation",
  "metric": "usage_kwh" | "cost_won" | "unit_cost" | "bill_vs_actual_gap",
  "time_range": {
    "type": "last_n_months" | "yymm_range" | "single_yymm",
    "n": <양의 정수>,  // last_n_months인 경우
    "start_yymm": <YYYYMM>,  // yymm_range인 경우
    "end_yymm": <YYYYMM>,  // yymm_range인 경우
    "yymm": <YYYYMM>  // single_yymm인 경우
  },
  "filters": {
    "region": ["수도권", "중부", "동부", "서부"],
    "site_type": ["기지국", "통합국", "사옥", "중계국", "IDC", "기타"],
    "contract_type_major": ["정액", "종량"],
    "contract_target": "전체" | "한전계약(ME)" | "건물계약(MC)",
    "rapa": "전체" | "RAPA" | "비RAPA",
    "network_gen": ["3G", "LTE", "5G"]
  },
  "group_by": ["yymm", "region", "site_type", ...],
  "top_n": <양의 정수>,  // top_n 쿼리인 경우 필수
  "clarification_needed": true | false,
  "clarification_question": "<질문>"  // clarification_needed=true인 경우 필수
}
```

## 사용 방법

### 기본 사용

```python
from src.copilot.planner import plan_with_fallback

query = "동부지역 최근 2개월 전력사용량 상위 20개"
plan, metadata = plan_with_fallback(query)

# Plan 검증
is_valid, error = plan.validate()
if is_valid:
    # Plan 실행
    result = execute_plan(plan)
```

### Clarification 처리

```python
from src.copilot.ui import render_clarification

if plan.clarification_needed:
    answer = render_clarification(plan)
    if answer:
        # 재질의 생성
        refined_query = f"{original_query} ({answer})"
        plan, _ = plan_with_fallback(refined_query)
```

## LLM 출력 규칙

1. **반드시 JSON 객체만** 출력 (설명/코드블록/마크다운 금지)
2. `response_format={"type": "json_object"}` 사용하여 JSON 강제
3. JSON 검증 실패 시 규칙 기반 fallback 자동 사용

## Fallback 메커니즘

LLM이 실패하거나 JSON 검증에 실패하면:
1. 규칙 기반 파서로 Plan 생성
2. metadata에 `method: "rule_based"` 및 `llm_error` 포함

## 테스트 결과

10개 샘플 질의 모두 스키마 검증 통과:

1. ✅ "동부지역 최근 2개월 전력사용량 상위 20개"
2. ✅ "수도권 2024년 1월부터 12월까지 전기료 추이"
3. ✅ "중부지역 기지국 최근 3개월 전기료가 가장 높은 국소 top10"
4. ✅ "서부지역 정액제 한전계약 5G 국소 최근 6개월 전력사용량 상위 30개"
5. ✅ "수도권의 청구서전력량과 실사용전력량 비교의 2024년에 관해 분석"
6. ✅ "동부지역 IDC 최근 1개월 단가 추이"
7. ✅ "전체 지역 최근 12개월 전력사용량이 가장 높은 중계국 top50"
8. ✅ "수도권 RAPA 국소 최근 3개월 전기료 변화"
9. ✅ "중부지역 건물계약 종량제 국소 최근 2개월 전력사용량 상위 15개"
10. ✅ "2024년 1월 수도권 기지국 전기료 분석"

## 완료 기준

✅ 샘플 10문장에 대해 plan이 스키마 검증을 통과합니다.



