"""
NLQ (Natural Language Query) helper for PYLON.

Goal:
- Accept a Korean natural language prompt about bills/usage.
- Convert to a constrained, safe internal query.
- Return both the computed result (DataFrame) and "where to verify in the app".

This is intentionally NOT a general-purpose SQL generator.
We keep the supported query surface small and deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Dict, List, Optional, Tuple

import pandas as pd


SUPPORTED_REGIONS = ["수도권", "중부", "동부", "서부"]
SUPPORTED_SITE_TYPES = ["기지국", "통합국", "사옥", "중계국", "IDC", "기타"]


@dataclass(frozen=True)
class RouteHint:
    page_path: str
    label: str
    reason: str


@dataclass(frozen=True)
class NLQPlan:
    """
    A small, structured representation of a supported user request.
    Supports all filters available in the app sidebar.
    """

    metric: str  # "kwh_actual" | "kwh_bill" | "cost_bill" | "cost_actual_est"
    months: Optional[int] = None  # trailing N months (based on max yymm in source df)
    top_n: Optional[int] = None
    regions: Optional[List[str]] = None
    site_types: Optional[List[str]] = None
    query_type: str = "top_n"  # "top_n" | "comparison" | "analysis" | "trend"
    comparison_type: Optional[str] = None  # "bill_actual" | "plan_actual"
    year: Optional[int] = None  # e.g., 2024
    start_month: Optional[int] = None  # 1-12, for trend analysis
    end_month: Optional[int] = None  # 1-12, for trend analysis
    # Additional filters from sidebar
    contract_target: Optional[str] = None  # "전체" | "한전계약(ME)" | "건물계약(MC)"
    contract_type_major: Optional[List[str]] = None  # ["정액"] | ["종량"] | ["정액", "종량"]
    network_gen: Optional[List[str]] = None  # ["3G"] | ["LTE"] | ["5G"] | ["3G", "LTE", "5G"]
    rapa: Optional[str] = None  # "전체" | "RAPA" | "비RAPA"


def _latest_n_yymm(source_df: pd.DataFrame, months: int) -> List[int]:
    if source_df.empty or "yymm" not in source_df.columns:
        return []
    yymm_sorted = sorted(pd.Series(source_df["yymm"]).dropna().astype(int).unique().tolist())
    if not yymm_sorted:
        return []
    return yymm_sorted[-months:]


def _extract_regions(text: str) -> Optional[List[str]]:
    hits = [r for r in SUPPORTED_REGIONS if r in text]
    return hits or None


def _extract_site_types(text: str) -> Optional[List[str]]:
    # common synonyms
    if "중계국사" in text:
        return ["중계국"]
    hits = [t for t in SUPPORTED_SITE_TYPES if t in text]
    return hits or None


def _extract_top_n(text: str, default: int = 20) -> int:
    m = re.search(r"top\s*(\d+)", text, flags=re.IGNORECASE)
    if m:
        return max(1, int(m.group(1)))
    m = re.search(r"상위\s*(\d+)", text)
    if m:
        return max(1, int(m.group(1)))
    return default


def _extract_recent_months(text: str, default: int = 2) -> int:
    # Examples: 최근 두달/최근 2달/최근 2개월/최근 두개월/최근 3개월
    if "최근" not in text:
        return default
    if re.search(r"최근\s*(두|2)\s*(달|개월)", text):
        return 2
    m = re.search(r"최근\s*(\d+)\s*(달|개월)", text)
    if m:
        return max(1, int(m.group(1)))
    return default


def _extract_metric(text: str) -> str:
    # Prefer "사용량/전력량" => kwh_actual if available, else kwh_bill (resolved later)
    # If user explicitly asks cost/요금 => cost_bill
    if any(k in text for k in ["요금", "전기료", "비용", "금액", "원"]):
        return "cost_bill"
    if any(k in text for k in ["전력사용량", "전력량", "사용량", "kwh", "전력 사용"]):
        return "kwh_actual"
    # default to usage (actual) for most analytics questions
    return "kwh_actual"


def build_plan(user_prompt: str) -> NLQPlan:
    """
    Parse a prompt into a constrained NLQPlan.
    This is rule-based and intentionally conservative.
    """
    text = (user_prompt or "").strip()
    metric = _extract_metric(text)
    months = _extract_recent_months(text, default=2)
    top_n = _extract_top_n(text, default=20)
    regions = _extract_regions(text)
    site_types = _extract_site_types(text)
    
    # Detect query type
    query_type = "top_n"  # default
    comparison_type = None
    year = None
    
    if any(k in text for k in ["비교", "vs", "대비", "차이"]):
        query_type = "comparison"
        if any(k in text for k in ["청구서", "청구"]) and any(k in text for k in ["실사용", "실제"]):
            comparison_type = "bill_actual"
        elif any(k in text for k in ["계획", "plan"]) and any(k in text for k in ["실적", "actual"]):
            comparison_type = "plan_actual"
    
    # Extract year
    import re
    year_match = re.search(r"(20\d{2})년|(\d{2})년", text)
    if year_match:
        if year_match.group(1):
            year = int(year_match.group(1))
        elif year_match.group(2):
            year = 2000 + int(year_match.group(2))
    
    # Extract month range for trend analysis
    start_month = None
    end_month = None
    if query_type == "trend":
        # "1월부터 12월까지", "1월~12월", "1-12월"
        month_range_match = re.search(r"(\d{1,2})월\s*(부터|~|-)\s*(\d{1,2})월", text)
        if month_range_match:
            start_month = int(month_range_match.group(1))
            end_month = int(month_range_match.group(3))
    
    # Extract additional filters
    contract_target = None
    contract_type_major = None
    network_gen = None
    rapa = None
    
    # Contract target
    if any(k in text for k in ["한전계약", "ME", "한전"]):
        contract_target = "한전계약(ME)"
    elif any(k in text for k in ["건물계약", "MC", "건물"]):
        contract_target = "건물계약(MC)"
    
    # Contract type
    if "정액" in text or "정액제" in text:
        contract_type_major = ["정액"]
    elif "종량" in text or "종량제" in text:
        contract_type_major = ["종량"]
    
    # Network generation
    network_gen_list = []
    if "3G" in text:
        network_gen_list.append("3G")
    if "LTE" in text:
        network_gen_list.append("LTE")
    if "5G" in text:
        network_gen_list.append("5G")
    if network_gen_list:
        network_gen = network_gen_list
    
    # RAPA
    if any(k in text for k in ["RAPA", "라파", "RAPA국소"]):
        rapa = "RAPA"
    elif any(k in text for k in ["비RAPA", "non-RAPA", "비라파"]):
        rapa = "비RAPA"
    
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


def execute_plan(
    plan: NLQPlan,
    *,
    bills_df: pd.DataFrame,
    actual_df: pd.DataFrame,
    site_master_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, Dict[str, object]]:
    """
    Execute a supported plan using in-memory DataFrames.

    Returns:
      - result dataframe (top N sites)
      - debug dict (what was applied)
    """

    # Resolve metric source
    if plan.metric in ("kwh_actual", "cost_actual_est") and (actual_df is None or actual_df.empty):
        # fallback
        metric = "kwh_bill" if plan.metric == "kwh_actual" else "cost_bill"
        source = bills_df
    elif plan.metric in ("kwh_actual", "cost_actual_est"):
        metric = plan.metric
        source = actual_df
    else:
        metric = plan.metric
        source = bills_df

    # Determine time window
    if plan.months is None:
        # If months is None, use all available data
        yymm_list = sorted(pd.Series(source["yymm"]).dropna().astype(int).unique().tolist())
    else:
        yymm_list = _latest_n_yymm(source, plan.months)
    if yymm_list:
        source_f = source[source["yymm"].astype(int).isin(yymm_list)].copy()
    else:
        source_f = source.copy()

    # Join site master for region / site_type / name
    sm = site_master_df[["site_id", "site_name", "region", "site_type"]].copy() if not site_master_df.empty else pd.DataFrame()
    if not sm.empty:
        merged = source_f.merge(sm, on="site_id", how="left", suffixes=("_src", "_sm"))
    else:
        merged = source_f.copy()
        merged["site_name"] = None
        if "region" not in merged.columns:
            merged["region"] = None
        merged["site_type"] = None

    # Normalize columns after merge (bills has region, site_master has region/site_type)
    # Prefer site_master values when present; otherwise fall back to source values.
    if "region_sm" in merged.columns or "region_src" in merged.columns:
        region_sm = merged["region_sm"] if "region_sm" in merged.columns else None
        region_src = merged["region_src"] if "region_src" in merged.columns else None
        if region_sm is not None and region_src is not None:
            merged["region"] = region_sm.fillna(region_src)
        elif region_sm is not None:
            merged["region"] = region_sm
        else:
            merged["region"] = region_src
    # In case some datasets already have plain 'region'
    if "region" not in merged.columns:
        merged["region"] = None

    if "site_type_sm" in merged.columns or "site_type_src" in merged.columns:
        st_sm = merged["site_type_sm"] if "site_type_sm" in merged.columns else None
        st_src = merged["site_type_src"] if "site_type_src" in merged.columns else None
        if st_sm is not None and st_src is not None:
            merged["site_type"] = st_sm.fillna(st_src)
        elif st_sm is not None:
            merged["site_type"] = st_sm
        else:
            merged["site_type"] = st_src
    if "site_type" not in merged.columns:
        merged["site_type"] = None

    if "site_name_sm" in merged.columns or "site_name_src" in merged.columns:
        name_sm = merged["site_name_sm"] if "site_name_sm" in merged.columns else None
        name_src = merged["site_name_src"] if "site_name_src" in merged.columns else None
        if name_sm is not None and name_src is not None:
            merged["site_name"] = name_sm.fillna(name_src)
        elif name_sm is not None:
            merged["site_name"] = name_sm
        else:
            merged["site_name"] = name_src
    if "site_name" not in merged.columns:
        merged["site_name"] = None

    # Apply filters
    if plan.regions:
        if "region" in merged.columns:
            merged = merged[merged["region"].isin(plan.regions)]
    if plan.site_types:
        if "site_type" in merged.columns:
            merged = merged[merged["site_type"].isin(plan.site_types)]

    # Aggregate
    if metric not in merged.columns:
        return pd.DataFrame(), {
            "error": f"선택한 지표({metric}) 컬럼이 데이터에 없습니다.",
            "metric": metric,
            "yymm_list": yymm_list,
        }

    agg = (
        merged.groupby(["site_id", "site_name", "region", "site_type"], dropna=False)[metric]
        .sum()
        .reset_index()
        .rename(columns={metric: "value"})
        .sort_values("value", ascending=False)
    )
    
    # Apply top_n limit if specified
    if plan.top_n is not None:
        agg = agg.head(plan.top_n)

    # Add helpful formatting columns
    agg.insert(0, "rank", range(1, len(agg) + 1))

    return agg, {
        "metric": metric,
        "source": "actual" if source is actual_df else "bills",
        "yymm_list": yymm_list,
        "regions": plan.regions,
        "site_types": plan.site_types,
        "top_n": plan.top_n,
        "months": plan.months,
    }


def route_hints_for_plan(plan: NLQPlan) -> List[RouteHint]:
    """
    Provide "where to verify" navigation hints inside the app.
    """
    hints: List[RouteHint] = []

    # Energy usage / bills analysis lives in Energy Intelligence
    if plan.metric in ("kwh_actual", "kwh_bill", "cost_bill", "cost_actual_est"):
        hints.append(
            RouteHint(
                page_path="pages/1_에너지_인텔리전스.py",
                label="에너지 인텔리전스",
                reason="전력 사용량/청구서/실사용량 데이터 기반 분석 및 필터(기간/지역/설비유형) 확인",
            )
        )

    # If user talks about risk/정합성, suggest risk page too
    # (rule-based: check typical keywords)
    # This function only sees the plan, so keep it generic.
    return hints


def korean_answer_summary(plan: NLQPlan, debug: Dict[str, object]) -> str:
    metric = debug.get("metric", plan.metric)
    months = int(debug.get("months", plan.months))
    top_n = int(debug.get("top_n", plan.top_n))

    metric_name = {
        "kwh_actual": "실사용량(kWh)",
        "kwh_bill": "청구 전력량(kWh)",
        "cost_bill": "청구 금액(원)",
        "cost_actual_est": "실사용 추정금액(원)",
    }.get(metric, str(metric))

    parts = [f"요청하신 조건으로 최근 {months}개월 기준 **{metric_name} TOP {top_n}**를 계산했습니다."]

    if debug.get("yymm_list"):
        yymm_list = debug["yymm_list"]
        parts.append(f"- 기간: {min(yymm_list)} ~ {max(yymm_list)}")
    if debug.get("regions"):
        parts.append(f"- 지역: {', '.join(debug['regions'])}")
    if debug.get("site_types"):
        parts.append(f"- 설비유형: {', '.join(debug['site_types'])}")

    return "\n".join(parts)

