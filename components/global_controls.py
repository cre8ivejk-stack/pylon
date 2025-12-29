"""Global controls and governance badges."""

import streamlit as st
from typing import Dict, List, Optional, Any
from src.models import GovernanceBadge
import pandas as pd


def _initialize_filter_state():
    """Initialize filter state in session_state if not exists."""
    if 'filters' not in st.session_state:
        st.session_state.filters = {
            'period_unit': '월 단위',
            'selected_periods': [],
            'regions': ["수도권", "중부", "동부", "서부"],
            'site_types': ["기지국", "통합국", "사옥", "중계국", "IDC", "기타"],
            'contract_target': '전체',
            'contract_type_major': ["정액", "종량"],
            'contract_type_minor': ['전체'],
            'network_gen': ["3G", "LTE", "5G"],
            'rapa': '전체'
        }


def _convert_period_to_yymm(period_unit: str, year: Optional[int], quarters: List[int], months: List[int]) -> List[int]:
    """
    Convert period selection to yymm list.
    
    Args:
        period_unit: '연 단위', '분기 단위', '월 단위'
        year: Selected year(s) - could be single int or list
        quarters: Selected quarters (1,2,3,4)
        months: Selected months (1~12)
    
    Returns:
        List of yymm integers (e.g., 202401)
    """
    yymm_list = []
    
    if period_unit == '연 단위':
        # year is a list of years
        if isinstance(year, list):
            for y in year:
                for m in range(1, 13):
                    yymm_list.append(int(f"{y}{m:02d}"))
        else:
            for m in range(1, 13):
                yymm_list.append(int(f"{year}{m:02d}"))
    
    elif period_unit == '분기 단위':
        # year is single year, quarters is list
        for q in quarters:
            q_months = {
                1: [1, 2, 3],
                2: [4, 5, 6],
                3: [7, 8, 9],
                4: [10, 11, 12]
            }
            for m in q_months[q]:
                yymm_list.append(int(f"{year}{m:02d}"))
    
    else:  # '월 단위'
        # year is single year, months is list
        for m in months:
            yymm_list.append(int(f"{year}{m:02d}"))
    
    return yymm_list


def render_sidebar_filters(
    available_yymm: List[str]
) -> Dict[str, Any]:
    """
    Render filter controls in sidebar.
    
    Args:
        available_yymm: Available months from data
    
    Returns:
        Dictionary with filter selections including yymm_list
    """
    _initialize_filter_state()
    
    with st.sidebar:
        st.markdown("## 🎯 조회 범위")
        
        # === 기간 필터 ===
        st.markdown("### 📅 기간")
        
        period_unit = st.radio(
            "기간 단위",
            options=['연 단위', '분기 단위', '월 단위'],
            index=2,  # Default: 월 단위
            key='filter_period_unit'
        )
        
        # Extract available years from yymm (handle both int and str formats)
        available_years = []
        for ym in available_yymm:
            ym_str = str(ym)
            if len(ym_str) >= 4:  # New format: 202401
                year = int(ym_str[:4])
            else:  # Old format: 2401
                year = 2000 + int(ym_str[:2])
            available_years.append(year)
        available_years = sorted(list(set(available_years)))
        default_year = available_years[-1] if available_years else 2026
        
        yymm_list = []
        
        if period_unit == '연 단위':
            selected_years = st.multiselect(
                "연도 선택",
                options=available_years,
                default=[default_year],
                key='filter_years'
            )
            if selected_years:
                yymm_list = _convert_period_to_yymm(period_unit, selected_years, [], [])
        
        elif period_unit == '분기 단위':
            col_y, col_q = st.columns([1, 1])
            with col_y:
                selected_year = st.selectbox(
                    "연도",
                    options=available_years,
                    index=len(available_years)-1 if available_years else 0,
                    key='filter_year_q'
                )
            with col_q:
                selected_quarters = st.multiselect(
                    "분기",
                    options=[1, 2, 3, 4],
                    default=[1, 2, 3, 4],
                    format_func=lambda x: f"{x}분기",
                    key='filter_quarters'
                )
            if selected_quarters:
                yymm_list = _convert_period_to_yymm(period_unit, selected_year, selected_quarters, [])
        
        else:  # '월 단위'
            col_y, col_m = st.columns([1, 1])
            with col_y:
                selected_year = st.selectbox(
                    "연도",
                    options=available_years,
                    index=len(available_years)-1 if available_years else 0,
                    key='filter_year_m'
                )
            
            # Month selection with "전체" option
            all_months_option = st.checkbox("전체 월 선택", value=True, key='filter_all_months')
            
            if all_months_option:
                selected_months = list(range(1, 13))
            else:
                selected_months = st.multiselect(
                    "월 선택",
                    options=list(range(1, 13)),
                    default=list(range(1, 13)),
                    format_func=lambda x: f"{x}월",
                    key='filter_months'
                )
            
            if selected_months:
                yymm_list = _convert_period_to_yymm(period_unit, selected_year, [], selected_months)
        
        # Filter yymm_list to only available data (convert available_yymm to int)
        available_yymm_int = [int(ym) for ym in available_yymm]
        yymm_list = [ym for ym in yymm_list if ym in available_yymm_int]
        
        st.divider()
        
        # === 지역 필터 ===
        st.markdown("### 🌍 지역")
        regions_options = ["수도권", "중부", "동부", "서부"]
        # Use saved value from session_state if available
        default_regions = st.session_state.filters.get('regions', regions_options) if 'filter_regions' not in st.session_state else st.session_state.get('filter_regions', regions_options)
        selected_regions = st.multiselect(
            "지역 선택",
            options=regions_options,
            default=default_regions,
            key='filter_regions'
        )
        
        st.divider()
        
        # === 설비유형 필터 ===
        st.markdown("### 🏢 설비유형")
        site_types_options = ["기지국", "통합국", "사옥", "중계국", "IDC", "기타"]
        default_site_types = st.session_state.filters.get('site_types', site_types_options) if 'filter_site_types' not in st.session_state else st.session_state.get('filter_site_types', site_types_options)
        selected_site_types = st.multiselect(
            "설비유형 선택",
            options=site_types_options,
            default=default_site_types,
            key='filter_site_types'
        )
        
        st.divider()
        
        # === 계약대상 필터 ===
        st.markdown("### 🔌 계약대상")
        contract_target = st.radio(
            "계약대상 선택",
            options=['전체', '한전계약(ME)', '건물계약(MC)'],
            index=0,
            key='filter_contract_target'
        )
        
        st.divider()
        
        # === 계약유형 필터 ===
        st.markdown("### 📋 계약유형")
        
        # 대분류
        contract_major_options = ["정액", "종량"]
        default_contract_major = st.session_state.filters.get('contract_type_major', contract_major_options) if 'filter_contract_major' not in st.session_state else st.session_state.get('filter_contract_major', contract_major_options)
        selected_contract_major = st.multiselect(
            "계약유형 (대분류)",
            options=contract_major_options,
            default=default_contract_major,
            key='filter_contract_major'
        )
        
        # 소분류 (향후 확장)
        contract_minor_info = st.info("💡 소분류는 향후 실제 요금제 정보로 확장 예정 (현재: 전체)")
        
        st.divider()
        
        # === 네트워크 세대 필터 ===
        st.markdown("### 📡 네트워크 세대")
        network_gen_options = ["3G", "LTE", "5G"]
        default_network_gen = st.session_state.filters.get('network_gen', network_gen_options) if 'filter_network_gen' not in st.session_state else st.session_state.get('filter_network_gen', network_gen_options)
        selected_network_gen = st.multiselect(
            "세대 선택",
            options=network_gen_options,
            default=default_network_gen,
            key='filter_network_gen'
        )
        
        st.divider()
        
        # === RAPA 여부 필터 ===
        st.markdown("### ⚡ RAPA 여부")
        rapa_filter = st.radio(
            "RAPA 선택",
            options=['전체', 'RAPA', '비RAPA'],
            index=0,
            key='filter_rapa'
        )
        
        st.divider()
    
    # Update session state
    filters = {
        'period_unit': period_unit,
        'yymm_list': yymm_list,
        'regions': selected_regions if selected_regions else regions_options,
        'site_types': selected_site_types if selected_site_types else site_types_options,
        'contract_target': contract_target,
        'contract_type_major': selected_contract_major if selected_contract_major else contract_major_options,
        'contract_type_minor': ['전체'],  # 향후 확장
        'network_gen': selected_network_gen if selected_network_gen else network_gen_options,
        'rapa': rapa_filter
    }
    
    st.session_state.filters = filters
    
    return filters


def render_filter_summary(filters: Dict[str, Any]) -> None:
    """
    Render one-line filter summary at the top of page.
    
    Args:
        filters: Filter dictionary
    """
    summary_parts = []
    
    # Period
    if filters.get('yymm_list'):
        yymm = filters['yymm_list']
        if len(yymm) <= 3:
            period_str = f"기간: {', '.join([str(ym) for ym in yymm])}"
        else:
            period_str = f"기간: {yymm[0]}~{yymm[-1]} ({len(yymm)}개월)"
        summary_parts.append(period_str)
    
    # Region
    regions = filters.get('regions', [])
    if len(regions) == 4:
        summary_parts.append("지역: 전체")
    elif regions:
        summary_parts.append(f"지역: {', '.join(regions)}")
    
    # Site type
    site_types = filters.get('site_types', [])
    if len(site_types) == 6:
        summary_parts.append("설비: 전체")
    elif site_types:
        summary_parts.append(f"설비: {', '.join(site_types)}")
    
    # Contract target
    contract_target = filters.get('contract_target', '전체')
    if contract_target != '전체':
        summary_parts.append(f"계약대상: {contract_target}")
    else:
        summary_parts.append("계약대상: 전체")
    
    # Contract type major
    contract_major = filters.get('contract_type_major', [])
    if len(contract_major) == 2:
        summary_parts.append("계약유형: 전체")
    elif contract_major:
        summary_parts.append(f"계약유형: {', '.join(contract_major)}")
    
    # Network gen
    network_gen = filters.get('network_gen', [])
    if len(network_gen) == 3:
        summary_parts.append("네트워크: 전체")
    elif network_gen:
        summary_parts.append(f"네트워크: {', '.join(network_gen)}")
    
    # RAPA
    rapa = filters.get('rapa', '전체')
    if rapa != '전체':
        summary_parts.append(f"RAPA: {rapa}")
    
    # Display
    st.info("**📊 선택된 조회 조건:** " + " | ".join(summary_parts))


def render_governance_badges(badge: GovernanceBadge) -> None:
    """
    Render governance badges showing system state.
    
    Args:
        badge: GovernanceBadge object with governance info
    """
    st.markdown("### 📋 운영 체계 상태")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="운영 기준 버전",
            value=f"v{badge.official_version} (Dev)",
            help="대시보드 산식·정의·필터 기준의 버전"
        )
    
    with col2:
        # 계획 기준 반영 상태 (확정/진행중/미반영)
        if badge.plan_locked:
            plan_status = "✅ 완료"
            plan_color = "green"
        else:
            plan_status = "🔄 진행중"
            plan_color = "orange"
        
        st.metric(
            label="계획 기준 반영",
            value=plan_status,
            help="계획(목표) 값이 대시보드 KPI에 반영된 상태"
        )
    
    with col3:
        # Format data freshness as "YYYY년 MM월 기준"
        if badge.data_freshness and badge.data_freshness != "N/A":
            parts = badge.data_freshness.split('-')
            if len(parts) == 2:
                freshness_display = f"{parts[0]}년 {parts[1]}월"
            else:
                freshness_display = badge.data_freshness
        else:
            freshness_display = "N/A"
        
        st.metric(
            label="데이터 최신성",
            value=freshness_display,
            help="최신 데이터 기준월"
        )
    
    with col4:
        exception_status = "없음" if badge.exceptions_applied == 0 else "있음"
        st.metric(
            label="예외적용",
            value=f"{exception_status} ({badge.exceptions_applied}건)",
            help="적용된 예외 규칙 수"
        )
    
    with col5:
        st.metric(
            label="운영 점검 주기",
            value="월 1회",
            help="전기료 WG 운영 - 월 1회 실적 점검"
        )
    
    st.divider()


def apply_filters(
    df: pd.DataFrame,
    filters: Dict[str, Any]
) -> pd.DataFrame:
    """
    Apply global filters to dataframe.
    Automatically detects available columns and applies filters safely.
    
    Args:
        df: DataFrame to filter
        filters: Filter dictionary from render_sidebar_filters
    
    Returns:
        Filtered dataframe
    """
    if len(df) == 0:
        return df
    
    filtered = df.copy()
    
    # === Period filter (yymm) ===
    yymm_list = filters.get('yymm_list', [])
    if yymm_list and 'yymm' in filtered.columns:
        # Convert both to int for comparison
        filtered['yymm_int'] = filtered['yymm'].astype(int)
        yymm_list_int = [int(ym) for ym in yymm_list]
        filtered = filtered[filtered['yymm_int'].isin(yymm_list_int)]
        filtered = filtered.drop(columns=['yymm_int'])
    
    # === Region filter ===
    regions = filters.get('regions', [])
    if regions and 'region' in filtered.columns:
        filtered = filtered[filtered['region'].isin(regions)]
    
    # === Site type filter ===
    site_types = filters.get('site_types', [])
    if site_types and 'site_type' in filtered.columns:
        filtered = filtered[filtered['site_type'].isin(site_types)]
    
    # === Contract target filter (계약대상: ME/MC) ===
    contract_target = filters.get('contract_target', '전체')
    if contract_target != '전체':
        # Map UI selection to data values
        target_map = {
            '한전계약(ME)': 'ME',
            '건물계약(MC)': 'MC'
        }
        target_value = target_map.get(contract_target, contract_target)
        
        # Try multiple column name candidates
        target_col = None
        for col_name in ['contract_target', 'contract_target_cd', '계약대상']:
            if col_name in filtered.columns:
                target_col = col_name
                break
        
        if target_col:
            filtered = filtered[filtered[target_col] == target_value]
    
    # === Contract type major filter ===
    contract_major = filters.get('contract_type_major', [])
    if contract_major and 'contract_type' in filtered.columns:
        filtered = filtered[filtered['contract_type'].isin(contract_major)]
    
    # === Contract type minor filter (향후 확장) ===
    # contract_minor는 현재 "전체"만 있으므로 스킵
    
    # === Network generation filter ===
    network_gen = filters.get('network_gen', [])
    if network_gen:
        # Try multiple column name candidates
        network_col = None
        for col_name in ['network_gen', 'network_generation', '세대']:
            if col_name in filtered.columns:
                network_col = col_name
                break
        
        if network_col:
            filtered = filtered[filtered[network_col].isin(network_gen)]
    
    # === RAPA filter ===
    rapa = filters.get('rapa', '전체')
    if rapa != '전체':
        # Try multiple column name candidates
        rapa_col = None
        for col_name in ['is_rapa', 'rapa_yn', 'rapa']:
            if col_name in filtered.columns:
                rapa_col = col_name
                break
        
        if rapa_col:
            # Handle boolean or Y/N format
            if filtered[rapa_col].dtype == bool:
                if rapa == 'RAPA':
                    filtered = filtered[filtered[rapa_col] == True]
                else:  # '비RAPA'
                    filtered = filtered[filtered[rapa_col] == False]
            else:
                # Assume Y/N format
                if rapa == 'RAPA':
                    filtered = filtered[filtered[rapa_col].isin(['Y', 'y', 'RAPA'])]
                else:  # '비RAPA'
                    filtered = filtered[filtered[rapa_col].isin(['N', 'n', '비RAPA', 'non-RAPA'])]
    
    return filtered


# Legacy function for backward compatibility (deprecated)
def render_global_controls(
    available_months: List[str],
    available_regions: List[str],
    available_site_types: List[str],
    available_contract_types: List[str]
) -> Dict[str, any]:
    """
    DEPRECATED: Use render_sidebar_filters instead.
    
    This function is kept for backward compatibility but will show a warning.
    """
    st.warning("⚠️ render_global_controls는 더 이상 사용되지 않습니다. render_sidebar_filters를 사용하세요.")
    
    # Return a minimal filter dict
    return {
        'period': available_months[-1] if available_months else None,
        'regions': available_regions,
        'site_types': available_site_types,
        'contract_types': available_contract_types,
        'yymm_list': [available_months[-1]] if available_months else []
    }
