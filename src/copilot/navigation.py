"""
Navigation helpers for Copilot using session_state.

This module provides session_state-based navigation instead of URL query params.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from src.copilot.schemas import Plan, NavLink, TimeRange


def create_nav_links_from_plan(plan: Plan) -> List[NavLink]:
    """
    Create navigation links from Plan using session_state.
    
    Args:
        plan: Plan object
    
    Returns:
        List of NavLink objects (1~3개)
    """
    links = []
    
    # Build nav_payload (without subview - page-level navigation only)
    nav_payload = {
        "filters": _plan_filters_to_dict(plan),
        "context": {
            "query_type": plan.query_type,
            "metric": plan.metric,
            "time_range": plan.time_range.to_dict(),
        }
    }
    
    # Determine appropriate pages based on query_type and metric
    if plan.query_type == "trend" or plan.metric in ["usage_kwh", "cost_won"]:
        # Energy Intelligence page
        links.append(NavLink(
            title="에너지 인텔리전스에서 자세히 보기",
            target_page="pages/1_에너지_인텔리전스.py",
            nav_payload=nav_payload,
            description="전력 사용량/요금 분석 및 추이 확인"
        ))
    
    if plan.query_type == "comparison" or plan.metric == "bill_vs_actual_gap":
        # Bill vs Actual page (Tab 3)
        nav_payload_bill = nav_payload.copy()
        links.append(NavLink(
            title="청구서 vs 실사용량에서 자세히 보기",
            target_page="pages/1_에너지_인텔리전스.py",
            nav_payload=nav_payload_bill,
            description="청구서와 실사용량 비교 분석"
        ))
    
    if plan.query_type == "anomaly":
        # Optimization page
        links.append(NavLink(
            title="최적화 & 실행에서 자세히 보기",
            target_page="pages/3_최적화_실행.py",
            nav_payload=nav_payload,
            description="이상 국소 탐지 및 최적화"
        ))
    
    # Default: Energy Intelligence if no specific match
    if not links:
        links.append(NavLink(
            title="에너지 인텔리전스에서 자세히 보기",
            target_page="pages/1_에너지_인텔리전스.py",
            nav_payload=nav_payload,
            description="에너지 사용 현황 분석"
        ))
    
    # Limit to 3 links
    return links[:3]


def _plan_filters_to_dict(plan: Plan) -> Dict[str, Any]:
    """Convert plan filters to dictionary format for session_state."""
    filters = {}
    
    # yymm list
    yymm_list = _get_yymm_list_from_plan(plan)
    if yymm_list:
        filters["yymm_list"] = yymm_list
    
    # region
    if plan.filters.region:
        filters["regions"] = plan.filters.region
    
    # site_type
    if plan.filters.site_type:
        filters["site_types"] = plan.filters.site_type
    
    # contract_type_major
    if plan.filters.contract_type_major:
        filters["contract_type_major"] = plan.filters.contract_type_major
    
    # contract_target
    if plan.filters.contract_target:
        filters["contract_target"] = plan.filters.contract_target
    
    # rapa
    if plan.filters.rapa:
        filters["rapa"] = plan.filters.rapa
    
    # network_gen
    if plan.filters.network_gen:
        filters["network_gen"] = plan.filters.network_gen
    
    return filters


def _get_yymm_list_from_plan(plan: Plan) -> Optional[List[int]]:
    """Extract yymm list from plan time_range."""
    if plan.time_range.type == "single_yymm":
        return [plan.time_range.yymm] if plan.time_range.yymm else None
    elif plan.time_range.type == "yymm_range":
        if plan.time_range.start_yymm and plan.time_range.end_yymm:
            # Generate list
            result = []
            current = plan.time_range.start_yymm
            while current <= plan.time_range.end_yymm:
                result.append(current)
                # Increment month
                year = current // 100
                month = current % 100
                if month == 12:
                    current = (year + 1) * 100 + 1
                else:
                    current = year * 100 + (month + 1)
            return result
    elif plan.time_range.type == "last_n_months":
        # This will be handled by the target page based on available data
        return None
    return None


def apply_probe_nav_to_filters(default_filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply probe_nav filters to default filters.
    
    This should be called at the start of target pages.
    
    Args:
        default_filters: Default filter dictionary
    
    Returns:
        Updated filter dictionary with probe_nav applied
    """
    import streamlit as st
    
    probe_nav = st.session_state.get("probe_nav")
    if not probe_nav:
        return default_filters
    
    nav_filters = probe_nav.get("filters", {})
    if not nav_filters:
        return default_filters
    
    # Merge: probe_nav filters override defaults
    result = default_filters.copy()
    
    # Apply each filter from probe_nav
    if "yymm_list" in nav_filters:
        result["yymm_list"] = nav_filters["yymm_list"]
    
    if "regions" in nav_filters:
        result["regions"] = nav_filters["regions"]
    
    if "site_types" in nav_filters:
        result["site_types"] = nav_filters["site_types"]
    
    if "contract_type_major" in nav_filters:
        result["contract_type_major"] = nav_filters["contract_type_major"]
    
    if "contract_target" in nav_filters:
        result["contract_target"] = nav_filters["contract_target"]
    
    if "rapa" in nav_filters:
        result["rapa"] = nav_filters["rapa"]
    
    if "network_gen" in nav_filters:
        result["network_gen"] = nav_filters["network_gen"]
    
    # Clear probe_nav after use (once-only)
    # Uncomment if you want to clear after first use:
    # del st.session_state["probe_nav"]
    
    return result


# Backward compatibility
apply_copilot_nav_to_filters = apply_probe_nav_to_filters

