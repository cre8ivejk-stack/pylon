"""
Deeplink generation and parsing for PYLON platform.

This module provides standardized query parameter handling for deep linking
and filter state synchronization across pages.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import streamlit as st


@dataclass
class FilterParams:
    """
    Standardized filter parameters for PYLON deeplinks.
    
    All parameters are optional and can be None or empty lists.
    """
    yymm: Optional[List[int]] = None  # List of yymm values (e.g., [202401, 202402])
    region: Optional[List[str]] = None  # List of regions (e.g., ["수도권", "동부"])
    site_type: Optional[List[str]] = None  # List of site types (e.g., ["기지국", "중계국"])
    contract_type_major: Optional[List[str]] = None  # List of contract types (e.g., ["정액", "종량"])
    contract_target: Optional[str] = None  # Single value: "전체", "한전계약(ME)", "건물계약(MC)"
    rapa: Optional[str] = None  # Single value: "전체", "RAPA", "비RAPA"
    network_gen: Optional[List[str]] = None  # List of network generations (e.g., ["3G", "LTE", "5G"])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for query params."""
        result = {}
        
        if self.yymm:
            result["yymm"] = [str(ym) for ym in self.yymm]
        if self.region:
            result["region"] = self.region
        if self.site_type:
            result["site_type"] = self.site_type
        if self.contract_type_major:
            result["contract_type_major"] = self.contract_type_major
        if self.contract_target and self.contract_target != "전체":
            result["contract_target"] = self.contract_target
        if self.rapa and self.rapa != "전체":
            result["rapa"] = self.rapa
        if self.network_gen:
            result["network_gen"] = self.network_gen
        
        return result
    
    @classmethod
    def from_dict(cls, params: Dict[str, Any]) -> FilterParams:
        """Create FilterParams from dictionary (e.g., from query_params)."""
        def parse_list(value: Any) -> Optional[List[str]]:
            if value is None:
                return None
            if isinstance(value, str):
                return [value]
            if isinstance(value, list):
                return [str(v) for v in value]
            return None
        
        def parse_int_list(value: Any) -> Optional[List[int]]:
            if value is None:
                return None
            if isinstance(value, str):
                try:
                    return [int(value)]
                except ValueError:
                    return None
            if isinstance(value, list):
                result = []
                for v in value:
                    try:
                        result.append(int(v))
                    except (ValueError, TypeError):
                        pass
                return result if result else None
            return None
        
        return cls(
            yymm=parse_int_list(params.get("yymm")),
            region=parse_list(params.get("region")),
            site_type=parse_list(params.get("site_type")),
            contract_type_major=parse_list(params.get("contract_type_major")),
            contract_target=params.get("contract_target") if params.get("contract_target") else None,
            rapa=params.get("rapa") if params.get("rapa") else None,
            network_gen=parse_list(params.get("network_gen")),
        )
    
    def to_filter_dict(self) -> Dict[str, Any]:
        """
        Convert to filter dictionary format used by global_controls.
        
        Returns:
            Dictionary compatible with render_sidebar_filters output
        """
        result: Dict[str, Any] = {
            'period_unit': '월 단위',  # Default
            'selected_periods': [],
            'regions': self.region if self.region else ["수도권", "중부", "동부", "서부"],
            'site_types': self.site_type if self.site_type else ["기지국", "통합국", "사옥", "중계국", "IDC", "기타"],
            'contract_target': self.contract_target if self.contract_target else '전체',
            'contract_type_major': self.contract_type_major if self.contract_type_major else ["정액", "종량"],
            'contract_type_minor': ['전체'],
            'network_gen': self.network_gen if self.network_gen else ["3G", "LTE", "5G"],
            'rapa': self.rapa if self.rapa else '전체',
        }
        
        # Convert yymm to yymm_list
        if self.yymm:
            result['yymm_list'] = self.yymm
        else:
            result['yymm_list'] = []
        
        return result


def parse_filters_from_query_params() -> FilterParams:
    """
    Parse filter parameters from Streamlit query_params.
    
    Returns:
        FilterParams object with parsed values
    """
    if not hasattr(st, "query_params"):
        return FilterParams()
    
    params = st.query_params.to_dict()
    return FilterParams.from_dict(params)


def update_query_params_from_filters(filters: Dict[str, Any]) -> None:
    """
    Update Streamlit query_params from filter dictionary.
    
    Args:
        filters: Filter dictionary from render_sidebar_filters or compatible format
    """
    if not hasattr(st, "query_params"):
        return
    
    # Convert filter dict to FilterParams
    filter_params = FilterParams(
        yymm=filters.get("yymm_list"),
        region=filters.get("regions"),
        site_type=filters.get("site_types"),
        contract_type_major=filters.get("contract_type_major"),
        contract_target=filters.get("contract_target"),
        rapa=filters.get("rapa"),
        network_gen=filters.get("network_gen"),
    )
    
    # Update query params
    params_dict = filter_params.to_dict()
    
    # Clear existing params first
    current_params = st.query_params.to_dict()
    for key in list(current_params.keys()):
        if key in ["yymm", "region", "site_type", "contract_type_major", 
                   "contract_target", "rapa", "network_gen"]:
            del st.query_params[key]
    
    # Set new params
    for key, value in params_dict.items():
        if isinstance(value, list):
            st.query_params[key] = value
        else:
            st.query_params[key] = value


def create_deeplink(
    page: str,
    filters: Optional[FilterParams] = None,
    **additional_params: Any
) -> str:
    """
    Create a deeplink URL for a specific page with filters.
    
    Args:
        page: Page path (e.g., "pages/1_에너지_인텔리전스.py" or "1_에너지_인텔리전스")
        filters: FilterParams object (optional)
        **additional_params: Additional query parameters
    
    Returns:
        Full URL with query parameters
    
    Example:
        >>> filters = FilterParams(region=["수도권"], site_type=["기지국"])
        >>> url = create_deeplink("1_에너지_인텔리전스", filters=filters)
        >>> # Returns: "http://localhost:8501/1_에너지_인텔리전스?region=수도권&site_type=기지국"
    """
    # Normalize page name
    if page.startswith("pages/"):
        page = page.replace("pages/", "").replace(".py", "")
    elif page.endswith(".py"):
        page = page.replace(".py", "")
    
    # Build query params
    params_dict = {}
    
    if filters:
        params_dict.update(filters.to_dict())
    
    # Add additional params
    params_dict.update(additional_params)
    
    # Build query string
    query_parts = []
    for key, value in params_dict.items():
        if isinstance(value, list):
            for v in value:
                query_parts.append(f"{key}={v}")
        elif value is not None:
            query_parts.append(f"{key}={value}")
    
    query_string = "&".join(query_parts)
    
    # Return relative URL (Streamlit will handle base URL)
    if query_string:
        return f"/{page}?{query_string}"
    else:
        return f"/{page}"


def sync_filters_with_query_params(
    default_filters: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Sync filters with query params: read from query params if available,
    otherwise use default filters.
    
    Args:
        default_filters: Default filter dictionary
    
    Returns:
        Synced filter dictionary
    """
    # Try to read from query params
    filter_params = parse_filters_from_query_params()
    
    # Convert to filter dict format
    query_filter_dict = filter_params.to_filter_dict()
    
    # Merge: query params override defaults
    result = default_filters.copy()
    
    # Only override if query params have values
    if filter_params.yymm:
        result['yymm_list'] = filter_params.yymm
    if filter_params.region:
        result['regions'] = filter_params.region
    if filter_params.site_type:
        result['site_types'] = filter_params.site_type
    if filter_params.contract_type_major:
        result['contract_type_major'] = filter_params.contract_type_major
    if filter_params.contract_target:
        result['contract_target'] = filter_params.contract_target
    if filter_params.rapa:
        result['rapa'] = filter_params.rapa
    if filter_params.network_gen:
        result['network_gen'] = filter_params.network_gen
    
    return result


def create_deeplink_from_plan(plan: 'Plan') -> List['Deeplink']:
    """
    Create deeplinks from Plan.
    
    Args:
        plan: Plan object
    
    Returns:
        List of Deeplink objects (1~3개)
    """
    from src.copilot.schemas import Deeplink
    
    links = []
    
    # Convert plan filters to FilterParams
    filter_params = FilterParams(
        yymm=_get_yymm_list_from_plan(plan),
        region=plan.filters.region,
        site_type=plan.filters.site_type,
        contract_type_major=plan.filters.contract_type_major,
        contract_target=plan.filters.contract_target,
        rapa=plan.filters.rapa,
        network_gen=plan.filters.network_gen,
    )
    
    # Determine appropriate pages based on query_type and metric
    if plan.query_type == "trend" or plan.metric in ["usage_kwh", "cost_won"]:
        # Energy Intelligence page
        url = create_deeplink("1_에너지_인텔리전스", filters=filter_params)
        links.append(Deeplink(
            title="에너지 인텔리전스",
            url=url,
            description="전력 사용량/요금 분석 및 추이 확인"
        ))
    
    if plan.query_type == "comparison" or plan.metric == "bill_vs_actual_gap":
        # Bill vs Actual page (Tab 3)
        url = create_deeplink("1_에너지_인텔리전스", filters=filter_params, month=_get_single_yymm_from_plan(plan))
        links.append(Deeplink(
            title="청구서 vs 실사용량",
            url=url,
            description="청구서와 실사용량 비교 분석"
        ))
    
    if plan.query_type == "anomaly":
        # Optimization page
        url = create_deeplink("3_최적화_실행.py", filters=filter_params)
        links.append(Deeplink(
            title="최적화 & 실행",
            url=url,
            description="이상 국소 탐지 및 최적화"
        ))
    
    # Default: Energy Intelligence if no specific match
    if not links:
        url = create_deeplink("1_에너지_인텔리전스", filters=filter_params)
        links.append(Deeplink(
            title="에너지 인텔리전스",
            url=url,
            description="에너지 사용 현황 분석"
        ))
    
    # Limit to 3 links
    return links[:3]


def _get_yymm_list_from_plan(plan: 'Plan') -> Optional[List[int]]:
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
    return None


def _get_single_yymm_from_plan(plan: 'Plan') -> Optional[int]:
    """Get single yymm for month parameter."""
    if plan.time_range.type == "single_yymm":
        return plan.time_range.yymm
    elif plan.time_range.type == "yymm_range":
        return plan.time_range.end_yymm  # Use end month
    return None

