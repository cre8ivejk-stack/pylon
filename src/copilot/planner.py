"""
LLM-based planner for converting natural language queries to structured plans.

This module implements the planner that uses LLM to generate Plan objects from user queries.
"""

from __future__ import annotations

import json
import os
import re
from typing import Dict, Any, Optional, Tuple
from dataclasses import asdict

from src.copilot.schemas import (
    Plan,
    QueryType,
    Metric,
    TimeRange,
    Filters,
    SUPPORTED_REGIONS,
    SUPPORTED_SITE_TYPES,
    SUPPORTED_CONTRACT_TYPES,
    SUPPORTED_CONTRACT_TARGETS,
    SUPPORTED_RAPA,
    SUPPORTED_NETWORK_GEN,
    SUPPORTED_GROUP_BY,
)


def _get_openai_client():
    """Lazy import OpenAI client."""
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("openai package is required. Install with: pip install openai")
    
    # Try Streamlit secrets first, then environment variables
    api_key = None
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "OPENAI_API_KEY" in st.secrets:
            api_key = st.secrets["OPENAI_API_KEY"]
    except Exception:
        pass
    
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in secrets or environment variables")
    
    return OpenAI(api_key=api_key)


def _system_prompt() -> str:
    """Generate system prompt for LLM planner."""
    return f"""
너는 PYLON 에너지 운영 플랫폼의 자연어 질의를 구조화된 Plan(JSON)으로 변환하는 플래너다.

## Plan 스키마

반드시 다음 JSON 스키마를 정확히 따라야 한다:

{{
  "query_type": "top_n" | "trend" | "comparison" | "anomaly" | "recommendation",
  "metric": "usage_kwh" | "cost_won" | "unit_cost" | "bill_vs_actual_gap",
  "time_range": {{
    "type": "last_n_months" | "yymm_range" | "single_yymm",
    "n": <양의 정수> (last_n_months인 경우),
    "start_yymm": <YYYYMM 정수> (yymm_range인 경우),
    "end_yymm": <YYYYMM 정수> (yymm_range인 경우),
    "yymm": <YYYYMM 정수> (single_yymm인 경우)
  }},
  "filters": {{
    "region": ["수도권", "중부", "동부", "서부"] (선택, 배열),
    "site_type": ["기지국", "통합국", "사옥", "중계국", "IDC", "기타"] (선택, 배열),
    "contract_type_major": ["정액", "종량"] (선택, 배열),
    "contract_target": "전체" | "한전계약(ME)" | "건물계약(MC)" (선택),
    "rapa": "전체" | "RAPA" | "비RAPA" (선택),
    "network_gen": ["3G", "LTE", "5G"] (선택, 배열)
  }},
  "group_by": ["yymm", "region", "site_type", ...] (선택, 배열),
  "top_n": <양의 정수> (top_n 쿼리인 경우 필수),
  "clarification_needed": true | false,
  "clarification_question": "<질문>" (clarification_needed=true인 경우 필수)
}}

## 질의 유형 판단

- "top", "상위", "가장 높은", "가장 많은" → query_type="top_n"
- "추이", "변화", "트렌드", "월별", "기간별" → query_type="trend"
- "비교", "vs", "대비", "차이" → query_type="comparison"
- "이상", "비정상", "anomaly" → query_type="anomaly"
- "권고", "추천", "recommendation" → query_type="recommendation"

## 지표 판단

- "사용량", "전력량", "kwh" → metric="usage_kwh"
- "요금", "전기료", "비용", "원" → metric="cost_won"
- "단가", "평균 단가" → metric="unit_cost"
- "청구서 차이", "청구서 vs 실사용", "오차" → metric="bill_vs_actual_gap"

## 시간 범위 판단

- "최근 N개월", "지난 N개월" → {{"type": "last_n_months", "n": N}}
- "YYYYMM부터 YYYYMM까지", "YYYYMM~YYYYMM" → {{"type": "yymm_range", "start_yymm": YYYYMM, "end_yymm": YYYYMM}}
- "YYYYMM", "YYYY년 MM월" → {{"type": "single_yymm", "yymm": YYYYMM}}

## 필터 추출

- 지역: "수도권", "중부", "동부", "서부" → filters.region
- 설비유형: "기지국", "통합국", "사옥", "중계국", "IDC", "기타" → filters.site_type
- 계약유형: "정액", "종량" → filters.contract_type_major
- 계약대상: "한전계약", "ME" → "한전계약(ME)", "건물계약", "MC" → "건물계약(MC)"
- RAPA: "RAPA" → "RAPA", "비RAPA" → "비RAPA"
- 네트워크: "3G", "LTE", "5G" → filters.network_gen

## Clarification

질의가 모호하거나 여러 해석이 가능한 경우:
- clarification_needed=true
- clarification_question에 명확한 선택지를 제시 (한 개만)

예: "지역을 선택해주세요: 수도권, 중부, 동부, 서부"

## 출력 규칙

1. 반드시 JSON 객체만 출력한다 (설명/코드블록/마크다운 금지)
2. 모든 필드는 스키마에 정의된 값만 사용
3. null 대신 필드를 생략하거나 빈 배열 사용
4. 필수 필드: query_type, metric, time_range, filters, clarification_needed

## 예시

질의: "동부지역 최근 2개월 전력사용량 상위 20개"
출력: {{"query_type":"top_n","metric":"usage_kwh","time_range":{{"type":"last_n_months","n":2}},"filters":{{"region":["동부"]}},"top_n":20,"clarification_needed":false}}

질의: "수도권 2024년 1월부터 12월까지 전기료 추이"
출력: {{"query_type":"trend","metric":"cost_won","time_range":{{"type":"yymm_range","start_yymm":202401,"end_yymm":202412}},"filters":{{"region":["수도권"]}},"group_by":["yymm"],"clarification_needed":false}}

질의: "전력사용량이 높은 국소"
출력: {{"query_type":"top_n","metric":"usage_kwh","time_range":{{"type":"last_n_months","n":2}},"filters":{{}},"top_n":20,"clarification_needed":true,"clarification_question":"기간을 선택해주세요: 최근 1개월, 최근 3개월, 최근 6개월, 최근 12개월"}}
""".strip()


def plan_with_llm(user_query: str) -> Tuple[Plan, Dict[str, Any]]:
    """
    Generate plan from natural language query using LLM.
    
    Args:
        user_query: Natural language query string
    
    Returns:
        (plan, metadata) tuple
    """
    client = _get_openai_client()
    
    # Get model from secrets or env
    model = "gpt-4o-mini"
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "PYLON_LLM_MODEL" in st.secrets:
            model = st.secrets["PYLON_LLM_MODEL"]
    except Exception:
        pass
    
    if model == "gpt-4o-mini":
        model = os.getenv("PYLON_LLM_MODEL", "gpt-4o-mini")
    
    # Call LLM
    resp = client.chat.completions.create(
        model=model,
        temperature=0,
        response_format={"type": "json_object"},  # Force JSON output
        messages=[
            {"role": "system", "content": _system_prompt()},
            {"role": "user", "content": user_query.strip()},
        ],
    )
    
    content = resp.choices[0].message.content or "{}"
    
    # Parse JSON
    try:
        obj = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM output is not valid JSON: {e}")
    
    # Validate and build plan
    plan = _validate_and_build_plan(obj)
    
    metadata = {
        "provider": "openai",
        "model": model,
        "raw_json": obj,
    }
    
    return plan, metadata


def _validate_and_build_plan(obj: Dict[str, Any]) -> Plan:
    """Validate and build Plan from dictionary."""
    # Validate required fields
    if "query_type" not in obj:
        raise ValueError("Missing required field: query_type")
    if "metric" not in obj:
        raise ValueError("Missing required field: metric")
    if "time_range" not in obj:
        raise ValueError("Missing required field: time_range")
    if "filters" not in obj:
        obj["filters"] = {}
    
    # Validate query_type
    valid_query_types = {qt.value for qt in QueryType}
    if obj["query_type"] not in valid_query_types:
        raise ValueError(f"Invalid query_type: {obj['query_type']}. Must be one of {valid_query_types}")
    
    # Validate metric
    valid_metrics = {m.value for m in Metric}
    if obj["metric"] not in valid_metrics:
        raise ValueError(f"Invalid metric: {obj['metric']}. Must be one of {valid_metrics}")
    
    # Build TimeRange
    time_range_data = obj["time_range"]
    time_range = TimeRange.from_dict(time_range_data)
    
    # Build Filters
    filters_data = obj.get("filters", {})
    filters = Filters.from_dict(filters_data)
    
    # Validate filter values
    if filters.region:
        invalid = [r for r in filters.region if r not in SUPPORTED_REGIONS]
        if invalid:
            raise ValueError(f"Invalid region values: {invalid}")
    
    if filters.site_type:
        invalid = [s for s in filters.site_type if s not in SUPPORTED_SITE_TYPES]
        if invalid:
            raise ValueError(f"Invalid site_type values: {invalid}")
    
    if filters.contract_type_major:
        invalid = [c for c in filters.contract_type_major if c not in SUPPORTED_CONTRACT_TYPES]
        if invalid:
            raise ValueError(f"Invalid contract_type_major values: {invalid}")
    
    if filters.contract_target and filters.contract_target not in SUPPORTED_CONTRACT_TARGETS:
        raise ValueError(f"Invalid contract_target: {filters.contract_target}")
    
    if filters.rapa and filters.rapa not in SUPPORTED_RAPA:
        raise ValueError(f"Invalid rapa: {filters.rapa}")
    
    if filters.network_gen:
        invalid = [n for n in filters.network_gen if n not in SUPPORTED_NETWORK_GEN]
        if invalid:
            raise ValueError(f"Invalid network_gen values: {invalid}")
    
    # Validate group_by
    group_by = obj.get("group_by")
    if group_by:
        invalid = [g for g in group_by if g not in SUPPORTED_GROUP_BY]
        if invalid:
            raise ValueError(f"Invalid group_by values: {invalid}")
    
    # Validate top_n
    top_n = obj.get("top_n")
    if top_n is not None:
        if not isinstance(top_n, int) or top_n <= 0:
            raise ValueError(f"top_n must be positive integer, got: {top_n}")
    
    # Validate clarification
    clarification_needed = obj.get("clarification_needed", False)
    clarification_question = obj.get("clarification_question")
    
    if clarification_needed and not clarification_question:
        raise ValueError("clarification_question required when clarification_needed=true")
    
    # Build Plan
    plan = Plan(
        query_type=obj["query_type"],
        metric=obj["metric"],
        time_range=time_range,
        filters=filters,
        group_by=group_by,
        top_n=top_n,
        clarification_needed=clarification_needed,
        clarification_question=clarification_question,
    )
    
    # Final validation
    is_valid, error_msg = plan.validate()
    if not is_valid:
        raise ValueError(f"Plan validation failed: {error_msg}")
    
    return plan


def plan_with_fallback(
    user_query: str,
    conversation_context: Optional[List[Dict[str, Any]]] = None,
    previous_plan: Optional[Plan] = None
) -> Tuple[Plan, Dict[str, Any]]:
    """
    Generate plan with LLM, fallback to rule-based if LLM fails.
    
    Supports context-aware planning with conversation history and plan merging.
    
    Args:
        user_query: Natural language query string
        conversation_context: List of previous conversation turns (optional)
        previous_plan: Previous confirmed plan to merge with (optional)
    
    Returns:
        (plan, metadata) tuple
    """
    metadata = {"method": "unknown"}
    
    # Check if this is a follow-up query (이어서, 그럼, 최근 N개월 등)
    is_followup = _is_followup_query(user_query)
    
    # If follow-up and previous_plan exists, merge plans
    if is_followup and previous_plan:
        try:
            plan = plan_merge(previous_plan, user_query)
            metadata["method"] = "plan_merge"
            metadata["merged"] = True
            return plan, metadata
        except Exception as e:
            metadata["merge_error"] = str(e)
            # Continue to normal planning
    
    # Try LLM first (with context if available)
    try:
        plan, llm_meta = plan_with_llm(user_query, conversation_context)
        metadata.update(llm_meta)
        metadata["method"] = "llm"
        return plan, metadata
    except Exception as e:
        # Fallback to rule-based
        metadata["llm_error"] = str(e)
        metadata["method"] = "rule_based"
        
        plan = _rule_based_plan(user_query, previous_plan)
        return plan, metadata


def plan_merge(previous_plan: Plan, new_query: str) -> Plan:
    """
    Merge previous plan with new query.
    
    Previous plan's filters/time_range/metric are inherited as defaults,
    and new query's explicit changes overwrite them.
    
    Args:
        previous_plan: Previous confirmed plan
        new_query: New user query
    
    Returns:
        Merged Plan
    
    Policy:
    - Previous plan provides defaults
    - New query's explicit values overwrite defaults
    - If new query doesn't specify something, inherit from previous
    """
    # First, try to generate a plan from new query (without previous context)
    # This gives us what the new query explicitly specifies
    try:
        new_plan, _ = plan_with_llm(new_query)
    except Exception:
        # Fallback to rule-based (without previous_plan to see what new query specifies)
        new_plan = _rule_based_plan(new_query, None)
    
    # Merge filters: new query's explicit values overwrite, otherwise inherit
    merged_filters = Filters(
        # If new query specifies region, use it; otherwise inherit
        region=new_plan.filters.region if new_plan.filters.region else previous_plan.filters.region,
        site_type=new_plan.filters.site_type if new_plan.filters.site_type else previous_plan.filters.site_type,
        contract_type_major=new_plan.filters.contract_type_major if new_plan.filters.contract_type_major else previous_plan.filters.contract_type_major,
        contract_target=new_plan.filters.contract_target if new_plan.filters.contract_target else previous_plan.filters.contract_target,
        rapa=new_plan.filters.rapa if new_plan.filters.rapa else previous_plan.filters.rapa,
        network_gen=new_plan.filters.network_gen if new_plan.filters.network_gen else previous_plan.filters.network_gen,
    )
    
    # Time range: if new query specifies time (has valid n or yymm), use it; otherwise inherit
    merged_time_range = new_plan.time_range
    if new_plan.time_range.type == "last_n_months":
        if new_plan.time_range.n is None:
            # New query didn't specify n, inherit from previous
            merged_time_range = previous_plan.time_range
    elif new_plan.time_range.type == "yymm_range":
        if not new_plan.time_range.start_yymm or not new_plan.time_range.end_yymm:
            # New query didn't specify range, inherit from previous
            merged_time_range = previous_plan.time_range
    elif new_plan.time_range.type == "single_yymm":
        if not new_plan.time_range.yymm:
            # New query didn't specify yymm, inherit from previous
            merged_time_range = previous_plan.time_range
    
    # Metric: if new query specifies a metric (not default), use it; otherwise inherit
    merged_metric = new_plan.metric
    # Check if new metric is just default (usage_kwh) - if so, inherit previous
    if merged_metric == Metric.USAGE_KWH.value:
        # Check if new query explicitly mentioned usage (to distinguish from default)
        query_lower = new_query.lower()
        if not any(k in query_lower for k in ["사용량", "전력량", "kwh", "사용"]):
            # New query didn't explicitly mention usage, inherit previous
            merged_metric = previous_plan.metric
    
    # Query type: if new query specifies a query type (not default top_n), use it; otherwise inherit
    merged_query_type = new_plan.query_type
    if merged_query_type == QueryType.TOP_N.value:
        # Check if new query explicitly mentioned top_n keywords
        query_lower = new_query.lower()
        if not any(k in query_lower for k in ["top", "상위", "가장 높은", "가장 많은"]):
            # New query didn't explicitly mention top_n, inherit previous
            merged_query_type = previous_plan.query_type
    
    # Top_n: if new query specifies top_n, use it; otherwise inherit
    merged_top_n = new_plan.top_n if new_plan.top_n is not None else previous_plan.top_n
    
    # Group_by: prefer new, fallback to previous
    merged_group_by = new_plan.group_by if new_plan.group_by else previous_plan.group_by
    
    return Plan(
        query_type=merged_query_type,
        metric=merged_metric,
        time_range=merged_time_range,
        filters=merged_filters,
        group_by=merged_group_by,
        top_n=merged_top_n,
        clarification_needed=new_plan.clarification_needed,
        clarification_question=new_plan.clarification_question,
    )


def _is_followup_query(query: str) -> bool:
    """Check if query is a follow-up (이어서, 그럼, 최근 N개월 등)."""
    followup_keywords = [
        "이어서", "그럼", "그렇다면", "그 중", "그것", "그것의",
        "최근", "지난", "최근에", "최근에는"
    ]
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in followup_keywords)


def _rule_based_plan(user_query: str, previous_plan: Optional[Plan] = None) -> Plan:
    """
    Rule-based plan generation (fallback).
    
    This is a simple rule-based parser as fallback when LLM fails.
    
    Args:
        user_query: Natural language query string
        previous_plan: Optional previous plan to inherit from
    """
    query_lower = user_query.lower()
    
    # Determine query_type
    if any(k in query_lower for k in ["top", "상위", "가장 높은", "가장 많은"]):
        query_type = QueryType.TOP_N.value
    elif any(k in query_lower for k in ["추이", "변화", "트렌드", "월별"]):
        query_type = QueryType.TREND.value
    elif any(k in query_lower for k in ["비교", "vs", "대비"]):
        query_type = QueryType.COMPARISON.value
    elif any(k in query_lower for k in ["이상", "비정상"]):
        query_type = QueryType.ANOMALY.value
    elif any(k in query_lower for k in ["권고", "추천"]):
        query_type = QueryType.RECOMMENDATION.value
    else:
        query_type = QueryType.TOP_N.value  # Default
    
    # Determine metric
    if any(k in query_lower for k in ["요금", "전기료", "비용", "원"]):
        metric = Metric.COST_WON.value
    elif any(k in query_lower for k in ["단가", "평균 단가"]):
        metric = Metric.UNIT_COST.value
    elif any(k in query_lower for k in ["청구서 차이", "오차"]):
        metric = Metric.BILL_VS_ACTUAL_GAP.value
    else:
        metric = Metric.USAGE_KWH.value  # Default
    
    # Extract time range
    time_range = _extract_time_range(user_query)
    
    # Extract filters
    filters = _extract_filters(user_query)
    
    # Extract top_n
    top_n = _extract_top_n(user_query)
    if query_type == QueryType.TOP_N.value and top_n is None:
        top_n = 20  # Default
    
    # If previous_plan exists and this is a follow-up, inherit defaults
    if previous_plan and _is_followup_query(user_query):
        # Inherit from previous plan if not specified in new query
        if not filters.region:
            filters.region = previous_plan.filters.region
        if not filters.site_type:
            filters.site_type = previous_plan.filters.site_type
        if not filters.contract_type_major:
            filters.contract_type_major = previous_plan.filters.contract_type_major
        if not filters.contract_target:
            filters.contract_target = previous_plan.filters.contract_target
        if not filters.rapa:
            filters.rapa = previous_plan.filters.rapa
        if not filters.network_gen:
            filters.network_gen = previous_plan.filters.network_gen
        
        # Inherit time_range if not specified
        if time_range.type == "last_n_months" and time_range.n is None:
            time_range = previous_plan.time_range
        
        # Inherit metric if default
        if metric == Metric.USAGE_KWH.value:
            metric = previous_plan.metric
        
        # Inherit query_type if default
        if query_type == QueryType.TOP_N.value:
            query_type = previous_plan.query_type
        
        # Inherit top_n if not specified
        if top_n is None:
            top_n = previous_plan.top_n
    
    return Plan(
        query_type=query_type,
        metric=metric,
        time_range=time_range,
        filters=filters,
        top_n=top_n,
        clarification_needed=False,
    )


def _extract_time_range(query: str) -> TimeRange:
    """Extract time range from query."""
    import re
    
    # Try yymm_range: "2024년 1월부터 12월까지", "202401~202412"
    range_match = re.search(r"(\d{4})년\s*(\d{1,2})월\s*부터\s*(\d{4})년\s*(\d{1,2})월", query)
    if range_match:
        start_year = int(range_match.group(1))
        start_month = int(range_match.group(2))
        end_year = int(range_match.group(3))
        end_month = int(range_match.group(4))
        return TimeRange(
            type="yymm_range",
            start_yymm=int(f"{start_year}{start_month:02d}"),
            end_yymm=int(f"{end_year}{end_month:02d}"),
        )
    
    # Try single_yymm: "2024년 1월", "202401"
    single_match = re.search(r"(\d{4})년\s*(\d{1,2})월", query)
    if single_match:
        year = int(single_match.group(1))
        month = int(single_match.group(2))
        return TimeRange(type="single_yymm", yymm=int(f"{year}{month:02d}"))
    
    # Try last_n_months: "최근 2개월", "지난 3개월"
    months_match = re.search(r"(최근|지난)\s*(\d+)\s*개?월", query)
    if months_match:
        n = int(months_match.group(2))
        return TimeRange(type="last_n_months", n=n)
    
    # Default: last 2 months
    return TimeRange(type="last_n_months", n=2)


def _extract_filters(query: str) -> Filters:
    """Extract filters from query."""
    filters = Filters()
    
    # Extract regions
    regions = [r for r in SUPPORTED_REGIONS if r in query]
    if regions:
        filters.region = regions
    
    # Extract site_types
    site_types = [s for s in SUPPORTED_SITE_TYPES if s in query]
    if site_types:
        filters.site_type = site_types
    
    # Extract contract_type_major
    if "정액" in query:
        filters.contract_type_major = ["정액"]
    elif "종량" in query:
        filters.contract_type_major = ["종량"]
    
    # Extract contract_target
    if "한전계약" in query or "ME" in query:
        filters.contract_target = "한전계약(ME)"
    elif "건물계약" in query or "MC" in query:
        filters.contract_target = "건물계약(MC)"
    
    # Extract rapa
    if "RAPA" in query or "라파" in query:
        filters.rapa = "RAPA"
    elif "비RAPA" in query:
        filters.rapa = "비RAPA"
    
    # Extract network_gen
    network_gens = [n for n in SUPPORTED_NETWORK_GEN if n in query]
    if network_gens:
        filters.network_gen = network_gens
    
    return filters


def _extract_top_n(query: str) -> Optional[int]:
    """Extract top_n from query."""
    import re
    
    # "top 20", "상위 20개"
    match = re.search(r"(top|상위)\s*(\d+)", query, re.IGNORECASE)
    if match:
        return int(match.group(2))
    
    return None

