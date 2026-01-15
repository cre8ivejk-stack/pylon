"""
LLM-backed NLQ planner with enhanced context understanding.

We ask an LLM to produce a *strict JSON* plan with a limited schema,
then we validate + execute it via src.nlq.execute_plan().

This keeps the LLM in a "planner" role (safe) and the app in an "executor" role (deterministic).

Enhanced: LLM now understands the full app context and can generate richer responses.
"""

from __future__ import annotations

from dataclasses import asdict
import json
import os
from typing import Any, Dict, Optional, Tuple

from src.nlq import NLQPlan, SUPPORTED_REGIONS, SUPPORTED_SITE_TYPES


def _get_openai_client():
    """
    Lazy import so the app still runs without openai installed.
    Supports both environment variables and Streamlit secrets.
    """
    try:
        from openai import OpenAI  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "openai 패키지가 설치되어 있지 않습니다. `pip install openai` 후 다시 시도하세요."
        ) from e

    # Try Streamlit secrets first, then environment variables
    api_key = None
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "OPENAI_API_KEY" in st.secrets:
            api_key = st.secrets["OPENAI_API_KEY"]
    except Exception:
        pass  # Not in Streamlit context or secrets not available
    
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY가 설정되어 있지 않습니다.\n"
            "설정 방법:\n"
            "1. .streamlit/secrets.toml 파일에 OPENAI_API_KEY = \"your-key\" 추가\n"
            "2. 또는 환경변수로 설정: $env:OPENAI_API_KEY = \"your-key\" (PowerShell)"
        )

    base_url = None
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "OPENAI_BASE_URL" in st.secrets:
            base_url = st.secrets["OPENAI_BASE_URL"]
    except Exception:
        pass
    
    if not base_url:
        base_url = os.getenv("OPENAI_BASE_URL")  # optional for OpenAI-compatible endpoints
    
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


def _system_prompt() -> str:
    """
    Enhanced system prompt with full app context and detailed page functions.
    """
    return f"""
너는 **PYLON 에너지 운영 플랫폼**의 자연어 질의 처리기다.

## PYLON 플랫폼 개요
PYLON은 SKT Network센터의 에너지 운영을 지원하는 통합 플랫폼으로, 다음 4개 주요 페이지로 구성되어 있다:

### 1. 에너지 인텔리전스 (pages/1_에너지_인텔리전스.py)
**Tab 1: 개요**
- 총 전력량, 총 전기요금, 평균 단가 (전년 동기 대비)
- 계획 대비 실적 개요 (차이, 달성률, 사용량 효과)
- 주요 변동 Top 5
- 월별 3개년 비교 (전력량/요금/단가/YoY)

**Tab 2: 계획 대비 실적**
- 월별 추이 차트 (Plan vs Actual)
- 차이 분석 테이블 (월별 variance)

**Tab 3: 청구서 vs 실사용량** ⭐ 중요
- 월별 분석 (선택한 월 기준)
- 개요: 청구서 전력량 vs 실사용 전력량, 청구서 요금 vs 실사용 기반 추정 요금
- 기준별 비교 분석:
  * 지역별 비교 (청구서 vs 실사용량)
  * 설비유형별 비교
  * 계약대상별 비교 (ME: 한전계약, MC: 건물계약)
  * 계약유형별 비교 (정액 vs 종량)
  * 세대별 비교 (3G/LTE/5G)
  * RAPA여부별 비교
- 국소별 청구 상태 분석:
  * 과대청구/정상/과소청구 분류
  * 오차율 계산 및 분포

**사용 함수**: calculate_bill_actual_error(), classify_bill_actual_mismatch()

### 2. 성과 & 리스크 관리 (pages/2_성과_리스크_관리.py)
**Tab 1: 과제별 성과 관리**
- 3단계 절감액: 예상 절감 / 진행 중 / 확정 절감
- 프로젝트별 달성률

**Tab 2: 전기요금 Risk Monitoring**
- Risk Score 계산 (High/Medium/Low)
- 리스크 분포 히스토그램
- High Risk 국소 리스트

**사용 함수**: calculate_risk_score()

### 3. 최적화 & 실행 (pages/3_최적화_실행.py)
**Tab 1: 계약전력 최적화**
- 최근 6개월 패턴 분석
- 감설 권고 (예상 절감액)
- 증설 필요 (초과요금 위험)

**Tab 2: 이상 국소 탐지**
- Z-score 기반 이상 탐지

**Tab 3: 사용량 0 국소**
- 연속 0 사용 국소 탐지

**사용 함수**: recommend_contract_power_adjustment(), calculate_anomaly_score(), detect_zero_usage_sites()

### 4. 검증 & 실증 (pages/4_검증_실증.py)
- 솔루션 실증 실험 관리
- 과제별 효과 검증

## 데이터 구조
- **bills**: 청구서 데이터 (yymm, site_id, kwh_bill, cost_bill, contract_type, contract_power_kw, region)
- **actual**: 실사용량 데이터 (yymm, site_id, kwh_actual, cost_actual_est, data_source, confidence)
- **plan**: 계획 데이터 (yymm, kwh_plan, cost_plan)
- **traffic**: 트래픽 데이터 (yymm, site_id, gb_traffic)
- **site_master**: 국소 마스터 (site_id, site_name, region, site_type, voltage, contract_type)

## 지원 필터 옵션 (앱 좌측 사이드바 필터)
- **지역 (regions)**: {SUPPORTED_REGIONS}
- **설비유형 (site_types)**: {SUPPORTED_SITE_TYPES}
- **계약대상 (contract_target)**: "전체" | "한전계약(ME)" | "건물계약(MC)"
- **계약유형 (contract_type_major)**: ["정액"] | ["종량"] | ["정액", "종량"]
- **네트워크 세대 (network_gen)**: ["3G"] | ["LTE"] | ["5G"] | ["3G", "LTE", "5G"]
- **RAPA 여부 (rapa)**: "전체" | "RAPA" | "비RAPA"

## 질의 처리 규칙
1. **반드시 JSON 객체만** 출력한다. (설명/코드블록/문장 금지)
2. **필수 필드**: metric은 반드시 포함되어야 함. 질의에서 추론할 수 없어도 기본값 "kwh_actual"을 사용하라.
3. 스키마는 아래 키만 사용:
   - query_type: "top_n" | "comparison" | "analysis" | "trend"
   - metric: "kwh_actual" | "kwh_bill" | "cost_bill" | "cost_actual_est"
   - months: 양의 정수 (최근 N개월) 또는 null
   - year: 양의 정수 (예: 2024, 2025) 또는 null
   - start_month: 1-12 사이의 정수 (시작 월) 또는 null
   - end_month: 1-12 사이의 정수 (종료 월) 또는 null
   - top_n: 양의 정수 (상위 N개) 또는 null
   - regions: null 또는 문자열 배열 (허용 값만 사용)
   - site_types: null 또는 문자열 배열 (허용 값만 사용)
   - comparison_type: "bill_actual" | "plan_actual" | null
   - contract_target: null 또는 "한전계약(ME)" | "건물계약(MC)" (명시되지 않으면 null)
   - contract_type_major: null 또는 문자열 배열 (["정액"] | ["종량"] | ["정액", "종량"])
   - network_gen: null 또는 문자열 배열 (["3G"] | ["LTE"] | ["5G"] | ["3G", "LTE", "5G"])
   - rapa: null 또는 "RAPA" | "비RAPA" (명시되지 않으면 null)

3. **질의 유형 판단** (매우 중요):
   - "추이", "변화", "트렌드", "추세", "경향", "월별", "기간별", "시계열" → query_type="trend"
     * 예: "동부권역 25년1월부터 12월까지 3G국소 전력사용량 추이"
     * 예: "수도권 최근 6개월 전기료 변화"
     * 예: "중부지역 기지국 전력량 월별 추세"
   - "비교", "vs", "대비", "차이" → query_type="comparison", comparison_type 적절히 설정
   - "분석", "정리", "요약" → query_type="analysis"
   - "top", "상위", "가장 높은" → query_type="top_n"

4. **비교 질의 처리**:
   - "청구서 vs 실사용량", "청구서전력량과 실사용전력량 비교" → comparison_type="bill_actual"
   - "계획 vs 실적", "계획 대비 실적" → comparison_type="plan_actual"

5. **지표 선택 가이드** (매우 중요 - metric은 필수 필드):
   - "전기료", "요금", "비용", "금액", "원" → metric="cost_bill"
   - "사용량", "전력량", "kwh", "전력 사용", "전력사용량" → metric="kwh_actual" (실사용량 우선)
   - "청구서", "청구" → metric="kwh_bill" 또는 "cost_bill" (문맥에 따라)
   - **중요**: metric은 반드시 다음 중 하나여야 함: "kwh_actual", "kwh_bill", "cost_bill", "cost_actual_est"
   - **기본값**: 질의에서 명확하지 않으면 "kwh_actual" 사용

6. **연도 및 기간 추출**:
   - "24년", "2024년", "25년", "2025년" → year=2024 또는 year=2025
   - "1월부터 12월까지", "1월~12월", "1-12월" → start_month=1, end_month=12
   - "최근 N개월" → months=N (trend가 아닌 경우)
   - **중요**: "추이" 질의의 경우, months 대신 year와 start_month/end_month를 사용
   - start_month와 end_month는 1-12 사이의 정수 또는 null

7. **지역/설비유형 매핑**:
   - 사용자가 명시하지 않으면 null
   - "중계국사" → site_types=["중계국"]

8. **추가 필터 추출**:
   - "한전계약", "ME" → contract_target="한전계약(ME)"
   - "건물계약", "MC" → contract_target="건물계약(MC)"
   - "정액", "정액제" → contract_type_major=["정액"]
   - "종량", "종량제" → contract_type_major=["종량"]
   - "3G", "LTE", "5G" → network_gen에 해당 값 추가
   - "RAPA", "라파" → rapa="RAPA"
   - "비RAPA", "non-RAPA" → rapa="비RAPA"
   - 사용자가 명시하지 않으면 해당 필드는 null

## 예시 출력 (모든 예시에서 metric은 반드시 포함됨)
질의: "동부지역 최근 두달동안 가장 전력사용량이 높은 중계국사 top20을 추출해줘"
출력: {{"query_type":"top_n","metric":"kwh_actual","months":2,"top_n":20,"regions":["동부"],"site_types":["중계국"],"year":null,"comparison_type":null,"contract_target":null,"contract_type_major":null,"network_gen":null,"rapa":null}}

질의: "수도권의 청구서전력량과 실사용전력량 비교의 24년에 관해 분석하고 정리해줘"
출력: {{"query_type":"comparison","comparison_type":"bill_actual","year":2024,"regions":["수도권"],"site_types":null,"metric":"kwh_bill","months":null,"top_n":null,"contract_target":null,"contract_type_major":null,"network_gen":null,"rapa":null}}

질의: "수도권 최근 3개월 전기료가 가장 높은 site top10"
출력: {{"query_type":"top_n","metric":"cost_bill","months":3,"top_n":10,"regions":["수도권"],"site_types":null,"year":null,"comparison_type":null,"contract_target":null,"contract_type_major":null,"network_gen":null,"rapa":null}}

질의: "수도권 정액제 한전계약 5G 국소 최근 2개월 전력사용량 top20"
출력: {{"query_type":"top_n","metric":"kwh_actual","months":2,"top_n":20,"regions":["수도권"],"site_types":null,"year":null,"comparison_type":null,"contract_target":"한전계약(ME)","contract_type_major":["정액"],"network_gen":["5G"],"rapa":null}}

질의: "동부권역 25년1월부터 12월까지 3G국소 전력사용량 추이"
출력: {{"query_type":"trend","metric":"kwh_actual","year":2025,"start_month":1,"end_month":12,"regions":["동부"],"site_types":null,"months":null,"top_n":null,"comparison_type":null,"contract_target":null,"contract_type_major":null,"network_gen":["3G"],"rapa":null}}

질의: "수도권 최근 6개월 전기료 변화 추이"
출력: {{"query_type":"trend","metric":"cost_bill","months":6,"regions":["수도권"],"site_types":null,"year":null,"top_n":null,"comparison_type":null,"contract_target":null,"contract_type_major":null,"network_gen":null,"rapa":null}}

질의: "중부지역 기지국 분석"
출력: {{"query_type":"analysis","metric":"kwh_actual","regions":["중부"],"site_types":["기지국"],"months":null,"top_n":null,"year":null,"comparison_type":null,"contract_target":null,"contract_type_major":null,"network_gen":null,"rapa":null}}
""".strip()


def plan_with_llm(user_prompt: str) -> Tuple[NLQPlan, Dict[str, Any]]:
    """
    Generate query plan using LLM with enhanced context.
    
    Returns:
      plan: NLQPlan
      meta: debug information (raw JSON, model, etc.)
    """
    client = _get_openai_client()
    
    # Try Streamlit secrets first, then environment variables
    model = "gpt-4o-mini"  # default
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "PYLON_LLM_MODEL" in st.secrets:
            model = st.secrets["PYLON_LLM_MODEL"]
    except Exception:
        pass
    
    if model == "gpt-4o-mini":  # still default, try env
        model = os.getenv("PYLON_LLM_MODEL", "gpt-4o-mini")

    resp = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": _system_prompt()},
            {"role": "user", "content": (user_prompt or "").strip()},
        ],
    )

    content = (resp.choices[0].message.content or "").strip()
    
    # Try to extract JSON if wrapped in code blocks or markdown
    if "```" in content:
        # Extract JSON from code block
        lines = content.split("\n")
        json_lines = []
        in_json = False
        for line in lines:
            if "```json" in line or "```" in line:
                in_json = not in_json
                continue
            if in_json:
                json_lines.append(line)
        content = "\n".join(json_lines)
    
    try:
        obj = json.loads(content)
    except Exception as e:
        raise RuntimeError(f"LLM 출력이 JSON 파싱에 실패했습니다. 원문: {content[:500]}") from e

    # Pass user_prompt to validation for fallback metric inference
    plan = _validate_and_build_plan(obj, user_prompt=user_prompt)
    return plan, {
        "provider": "openai",
        "model": model,
        "raw": obj,
        "plan": asdict(plan),
    }


def generate_answer_with_llm(
    user_prompt: str,
    result_df,
    plan: NLQPlan,
    debug: Dict[str, Any]
) -> str:
    """
    Generate a natural language answer based on the query results.
    
    Args:
        user_prompt: Original user query
        result_df: Result DataFrame from execute_plan
        plan: Executed NLQPlan
        debug: Debug information from execute_plan
    
    Returns:
        Natural language answer in Korean
    """
    client = _get_openai_client()
    
    model = "gpt-4o-mini"
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "PYLON_LLM_MODEL" in st.secrets:
            model = st.secrets["PYLON_LLM_MODEL"]
    except Exception:
        pass
    
    if model == "gpt-4o-mini":
        model = os.getenv("PYLON_LLM_MODEL", "gpt-4o-mini")
    
    # Prepare result summary based on query type
    result_summary = ""
    if plan.query_type == "trend":
        # Trend analysis: focus on monthly patterns
        if result_df is not None and len(result_df) > 0:
            monthly_data = result_df.to_dict('records')
            summary = debug.get("summary", {})
            
            result_summary = f"""
월별 추이 분석 결과:
- 분석 기간: {summary.get('num_months', len(monthly_data))}개월
- 총합: {summary.get('total_value', 0):,.0f}
- 월평균: {summary.get('avg_monthly', 0):,.0f}
- 최고 월: {summary.get('max_month', 'N/A')} ({summary.get('max_value', 0):,.0f})
- 최저 월: {summary.get('min_month', 'N/A')} ({summary.get('min_value', 0):,.0f})
- 전체 변화율: {summary.get('overall_change_pct', 0):.2f}%
- 월평균 변화율: {summary.get('avg_mom_change_pct', 0):.2f}%

월별 상세 데이터:
{json.dumps(monthly_data, ensure_ascii=False, indent=2)}
"""
        else:
            result_summary = "조건에 해당하는 데이터가 없습니다."
        
        # Build prompt for trend analysis
        answer_prompt = f"""
사용자 질의: {user_prompt}

실행된 쿼리 계획:
- 질의 유형: 추이 분석 (trend)
- 지표: {plan.metric}
- 연도: {plan.year if plan.year else '미지정'}
- 기간: {plan.start_month}월~{plan.end_month}월 (전체 기간)
- 지역: {plan.regions if plan.regions else '전체'}
- 설비유형: {plan.site_types if plan.site_types else '전체'}
- 네트워크 세대: {plan.network_gen if plan.network_gen else '전체'}

{result_summary}

위 결과를 바탕으로 사용자에게 자연스러운 한국어로 답변을 작성해주세요.

답변 형식:
1. 질의에 대한 간단한 확인
2. 월별 추이 패턴 분석 (증감 추세, 최고/최저 시점, 변화율 등)
3. 주요 인사이트 (예: 특정 시기에 급증/급감, 계절성 패턴 등)
4. 앱에서 더 자세히 확인할 수 있는 페이지 안내

답변은 4-6문단 정도로 작성하고, 월별 추이를 상세히 분석하여 설명해주세요. 단순히 숫자만 나열하지 말고, 패턴과 추세를 중심으로 설명해주세요.
"""
    elif plan.query_type == "comparison":
        # Comparison analysis
        summary = debug.get("summary", {})
        result_summary = f"""
비교 분석 결과:
{json.dumps(summary, ensure_ascii=False, indent=2)}
"""
        answer_prompt = f"""
사용자 질의: {user_prompt}

실행된 쿼리 계획:
- 질의 유형: 비교 분석 (comparison)
- 비교 유형: {plan.comparison_type}
- 지표: {plan.metric}
- 연도: {plan.year if plan.year else '미지정'}
- 지역: {plan.regions if plan.regions else '전체'}

{result_summary}

위 결과를 바탕으로 사용자에게 자연스러운 한국어로 답변을 작성해주세요.
"""
    else:
        # Top N or other queries
        if result_df is not None and len(result_df) > 0:
            # Top 5 rows as sample
            top_rows = result_df.head(5).to_dict('records')
            total_count = len(result_df)
            total_value = result_df['value'].sum() if 'value' in result_df.columns else None
            
            result_summary = f"""
결과 요약:
- 총 {total_count}개 국소가 조건에 해당합니다.
{f"- 총합: {total_value:,.0f}" if total_value is not None else ""}
- 상위 5개 국소:
{json.dumps(top_rows, ensure_ascii=False, indent=2)}
"""
        else:
            result_summary = "조건에 해당하는 데이터가 없습니다."
        
        # Build prompt for answer generation
        answer_prompt = f"""
사용자 질의: {user_prompt}

실행된 쿼리 계획:
- 지표: {plan.metric}
- 기간: 최근 {plan.months}개월
- 상위: {plan.top_n}개
- 지역: {plan.regions if plan.regions else '전체'}
- 설비유형: {plan.site_types if plan.site_types else '전체'}

{result_summary}

위 결과를 바탕으로 사용자에게 자연스러운 한국어로 답변을 작성해주세요.

답변 형식:
1. 질의에 대한 간단한 확인
2. 주요 결과 요약 (상위 국소, 총합 등)
3. 인사이트나 주의사항 (있는 경우)
4. 앱에서 더 자세히 확인할 수 있는 페이지 안내

답변은 3-5문단 정도로 작성하고, 전문적이지만 이해하기 쉽게 작성해주세요.
"""
    
    resp = client.chat.completions.create(
        model=model,
        temperature=0.3,  # Slightly higher for more natural language
        messages=[
            {
                "role": "system",
                "content": "너는 PYLON 에너지 운영 플랫폼의 분석 결과를 사용자에게 설명하는 전문가다. 한국어로 자연스럽고 전문적인 답변을 작성한다."
            },
            {"role": "user", "content": answer_prompt},
        ],
    )
    
    return (resp.choices[0].message.content or "").strip()


def _validate_and_build_plan(obj: Dict[str, Any], user_prompt: Optional[str] = None) -> NLQPlan:
    if not isinstance(obj, dict):
        raise RuntimeError("LLM 출력이 JSON 객체가 아닙니다.")

    metric = obj.get("metric")
    months = obj.get("months")
    top_n = obj.get("top_n")
    regions = obj.get("regions")
    site_types = obj.get("site_types")
    query_type = obj.get("query_type", "top_n")
    comparison_type = obj.get("comparison_type")
    year = obj.get("year")
    start_month = obj.get("start_month")
    end_month = obj.get("end_month")
    contract_target = obj.get("contract_target")
    contract_type_major = obj.get("contract_type_major")
    network_gen = obj.get("network_gen")
    rapa = obj.get("rapa")
    
    # Extract month range from year if not explicitly provided
    if query_type == "trend" and year:
        if not start_month:
            start_month = 1
        if not end_month:
            end_month = 12

    # Fallback: If metric is None, try to infer from user prompt
    if metric is None:
        if user_prompt:
            # Use rule-based extraction as fallback
            text = user_prompt.lower()
            if any(k in text for k in ["요금", "전기료", "비용", "금액", "원"]):
                metric = "cost_bill"
            elif any(k in text for k in ["전력사용량", "전력량", "사용량", "kwh", "전력 사용"]):
                metric = "kwh_actual"
            elif query_type == "comparison" and comparison_type == "bill_actual":
                metric = "kwh_bill"  # Default for bill_actual comparison
            else:
                metric = "kwh_actual"  # Default for most queries
        else:
            # No prompt available, use defaults
            if query_type == "comparison" and comparison_type == "bill_actual":
                metric = "kwh_bill"
            else:
                metric = "kwh_actual"
    
    allowed_metrics = {"kwh_actual", "kwh_bill", "cost_bill", "cost_actual_est"}
    if metric not in allowed_metrics:
        raise RuntimeError(f"metric 값이 유효하지 않습니다: {metric}")

    allowed_query_types = {"top_n", "comparison", "analysis", "trend"}
    if query_type not in allowed_query_types:
        raise RuntimeError(f"query_type 값이 유효하지 않습니다: {query_type}")

    if months is not None:
        if not isinstance(months, int) or months <= 0:
            raise RuntimeError(f"months 값이 유효하지 않습니다: {months}")
    
    if top_n is not None:
        if not isinstance(top_n, int) or top_n <= 0:
            raise RuntimeError(f"top_n 값이 유효하지 않습니다: {top_n}")

    if year is not None:
        if not isinstance(year, int) or year < 2000 or year > 2100:
            raise RuntimeError(f"year 값이 유효하지 않습니다: {year}")

    if regions is not None:
        if not isinstance(regions, list) or not all(isinstance(x, str) for x in regions):
            raise RuntimeError("regions는 null 또는 문자열 배열이어야 합니다.")
        bad = [x for x in regions if x not in SUPPORTED_REGIONS]
        if bad:
            raise RuntimeError(f"regions에 허용되지 않는 값이 포함됨: {bad}")

    if site_types is not None:
        if not isinstance(site_types, list) or not all(isinstance(x, str) for x in site_types):
            raise RuntimeError("site_types는 null 또는 문자열 배열이어야 합니다.")
        # Normalize common synonym
        site_types = ["중계국" if x == "중계국사" else x for x in site_types]
        bad = [x for x in site_types if x not in SUPPORTED_SITE_TYPES]
        if bad:
            raise RuntimeError(f"site_types에 허용되지 않는 값이 포함됨: {bad}")

    if comparison_type is not None:
        allowed_comparison_types = {"bill_actual", "plan_actual"}
        if comparison_type not in allowed_comparison_types:
            raise RuntimeError(f"comparison_type 값이 유효하지 않습니다: {comparison_type}")

    # Validate additional filters
    if contract_target is not None:
        allowed_contract_targets = {"전체", "한전계약(ME)", "건물계약(MC)"}
        if contract_target not in allowed_contract_targets:
            raise RuntimeError(f"contract_target 값이 유효하지 않습니다: {contract_target}")

    if contract_type_major is not None:
        if not isinstance(contract_type_major, list) or not all(isinstance(x, str) for x in contract_type_major):
            raise RuntimeError("contract_type_major는 null 또는 문자열 배열이어야 합니다.")
        allowed_contract_types = {"정액", "종량"}
        bad = [x for x in contract_type_major if x not in allowed_contract_types]
        if bad:
            raise RuntimeError(f"contract_type_major에 허용되지 않는 값이 포함됨: {bad}")

    if network_gen is not None:
        if not isinstance(network_gen, list) or not all(isinstance(x, str) for x in network_gen):
            raise RuntimeError("network_gen는 null 또는 문자열 배열이어야 합니다.")
        allowed_network_gens = {"3G", "LTE", "5G"}
        bad = [x for x in network_gen if x not in allowed_network_gens]
        if bad:
            raise RuntimeError(f"network_gen에 허용되지 않는 값이 포함됨: {bad}")

    if rapa is not None:
        allowed_rapa = {"전체", "RAPA", "비RAPA"}
        if rapa not in allowed_rapa:
            raise RuntimeError(f"rapa 값이 유효하지 않습니다: {rapa}")

    return NLQPlan(
        metric=metric,
        months=months,
        top_n=top_n,
        regions=regions,
        site_types=site_types,
        query_type=query_type,
        comparison_type=comparison_type,
        year=year,
        start_month=start_month,
        end_month=end_month,
        contract_target=contract_target,
        contract_type_major=contract_type_major,
        network_gen=network_gen,
        rapa=rapa,
    )
