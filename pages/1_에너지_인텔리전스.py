"""에너지 인텔리전스 페이지 - 개요, 계획 대비 실적, 청구서 vs 실사용량"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import altair as alt
from pathlib import Path
import sys
import os

# Add parent directory to path (Streamlit Cloud compatibility)
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from src.data_access import DataAccessLayer
from src.analytics import (
    calculate_plan_variance,
    calculate_bill_actual_error,
    classify_bill_actual_mismatch,
    decompose_cost_variance,
    calculate_yoy_comparison,
    prepare_monthly_3year_comparison
)
from src.actions import ActionManager
from src.models import GovernanceBadge, ActionCategory, ValidationState
from src.config_loader import load_governance_config
from components.global_controls import render_sidebar_filters, render_governance_badges, apply_filters, render_filter_summary
from components.widget_card import render_widget_card, render_simple_metric_card
from components.action_inbox import render_compact_action_inbox
# PROBE is now available as a dedicated page (pages/0_PYLON_PROBE.py)
from styles import (
    PYLON_BLUE, PYLON_ORANGE, apply_page_style, create_footer
)

# Page config
st.set_page_config(page_title="에너지 인텔리전스 | PYLON", layout="wide", page_icon="⚡")

# Apply PYLON brand colors
st.markdown(apply_page_style(), unsafe_allow_html=True)

# Initialize
data_dir = Path("data")
dal = DataAccessLayer(data_dir)
action_manager = ActionManager(data_dir)

# Load governance config
gov_config = load_governance_config()

# Header with brand color
st.markdown(f'<h1 style="color: {PYLON_BLUE};">⚡ PYLON - Energy Intelligence</h1>', unsafe_allow_html=True)
st.markdown("에너지 사용 현황 분석 및 계획 대비 실적 모니터링")

# User and system status in sidebar
with st.sidebar:
    st.markdown("## 👤 사용자")
    if "current_user" not in st.session_state:
        st.session_state["current_user"] = "담당자"
    st.session_state["current_user"] = st.text_input(
        "담당자 이름", 
        st.session_state["current_user"],
        key="user_input_page1",
        help="조치 할당 및 작업함 필터링에 사용됩니다"
    )
    st.divider()
    
    st.markdown("## 🎛️ 시스템 상태")
    render_compact_action_inbox(action_manager, st.session_state["current_user"])
    st.divider()

# Load data
bills_df = dal.load_bills()
actual_df = dal.load_actual()
plan_df = dal.load_plan()
site_master = dal.load_site_master()

if len(bills_df) == 0:
    st.error("청구서 데이터를 로드할 수 없습니다.")
    st.stop()

# Governance badges with auto-computed freshness
latest_yymm = bills_df['yymm'].max() if len(bills_df) > 0 else None
governance_badge = GovernanceBadge.create_from_config_and_data(gov_config, latest_yymm)
render_governance_badges(governance_badge)

# Apply probe_nav filters if present (before rendering filters)
from src.copilot.navigation import apply_probe_nav_to_filters
if "probe_nav" in st.session_state:
    probe_nav = st.session_state["probe_nav"]
    nav_filters = probe_nav.get("filters", {})
    if nav_filters:
        # Initialize filter state if needed
        if "filters" not in st.session_state:
            st.session_state.filters = {}
        # Apply copilot filters to session_state
        if "yymm_list" in nav_filters:
            st.session_state.filters["yymm_list"] = nav_filters["yymm_list"]
        if "regions" in nav_filters:
            st.session_state.filters["regions"] = nav_filters["regions"]
        if "site_types" in nav_filters:
            st.session_state.filters["site_types"] = nav_filters["site_types"]
        if "contract_type_major" in nav_filters:
            st.session_state.filters["contract_type_major"] = nav_filters["contract_type_major"]
        if "contract_target" in nav_filters:
            st.session_state.filters["contract_target"] = nav_filters["contract_target"]
        if "rapa" in nav_filters:
            st.session_state.filters["rapa"] = nav_filters["rapa"]
        if "network_gen" in nav_filters:
            st.session_state.filters["network_gen"] = nav_filters["network_gen"]
    # Clear probe_nav after use (once-only)
    del st.session_state["probe_nav"]

# Global filters (sidebar) - with query params sync
available_yymm = sorted(bills_df['yymm'].unique().tolist())
filters = render_sidebar_filters(available_yymm, sync_with_query_params=True)

# Filter summary
render_filter_summary(filters)

# Apply filters
filtered_bills = apply_filters(bills_df, filters)

st.markdown("---")

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 개요", "📈 계획 대비 실적", "🔍 청구서 vs 실사용량"])

with tab1:
    st.markdown("## 📊 에너지 개요")
    
    if len(filtered_bills) == 0:
        st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
    else:
        # Calculate previous year same period data for comparison
        yymm_list = filters.get('yymm_list', [])
        prev_year_yymm = []
        
        if yymm_list:
            for ym in yymm_list:
                ym_str = str(ym)
                if len(ym_str) == 6:  # YYYYMM format
                    year = int(ym_str[:4])
                    month = ym_str[4:6]
                    prev_year_ym = int(f"{year-1}{month}")
                    prev_year_yymm.append(prev_year_ym)
        
        # Get previous year data with same filters (except period)
        if prev_year_yymm:
            filters_prev = filters.copy()
            filters_prev['yymm_list'] = prev_year_yymm
            filtered_bills_prev = apply_filters(bills_df, filters_prev)
            
            prev_total_kwh = filtered_bills_prev['kwh_bill'].sum()
            prev_total_cost = filtered_bills_prev['cost_bill'].sum()
            prev_avg_unit_cost = (prev_total_cost / prev_total_kwh) if prev_total_kwh > 0 else 0
        else:
            prev_total_kwh = 0
            prev_total_cost = 0
            prev_avg_unit_cost = 0
        
        # Current period totals
        total_kwh = filtered_bills['kwh_bill'].sum()
        total_cost = filtered_bills['cost_bill'].sum()
        avg_unit_cost = (total_cost / total_kwh) if total_kwh > 0 else 0
        
        # Calculate changes
        kwh_change = ((total_kwh - prev_total_kwh) / prev_total_kwh * 100) if prev_total_kwh > 0 else None
        cost_change = ((total_cost - prev_total_cost) / prev_total_cost * 100) if prev_total_cost > 0 else None
        unit_cost_change = ((avg_unit_cost - prev_avg_unit_cost) / prev_avg_unit_cost * 100) if prev_avg_unit_cost > 0 else None
        
        # KPI tiles
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            delta_str = None
            if kwh_change is not None:
                delta_str = f"{kwh_change:+.1f}% (전년 동기 대비)"
            render_simple_metric_card("총 전력량", f"{total_kwh:,.0f} kWh", delta=delta_str)
            if prev_total_kwh > 0:
                st.caption(f"전년: {prev_total_kwh:,.0f} kWh")
        
        with col2:
            delta_str = None
            if cost_change is not None:
                delta_str = f"{cost_change:+.1f}% (전년 동기 대비)"
            render_simple_metric_card("총 전기요금", f"₩{total_cost:,.0f}", delta=delta_str)
            if prev_total_cost > 0:
                st.caption(f"전년: ₩{prev_total_cost:,.0f}")
        
        with col3:
            delta_str = None
            if unit_cost_change is not None:
                delta_str = f"{unit_cost_change:+.1f}% (전년 동기 대비)"
            render_simple_metric_card("평균 단가", f"₩{avg_unit_cost:.1f}/kWh", delta=delta_str)
            if prev_avg_unit_cost > 0:
                st.caption(f"전년: ₩{prev_avg_unit_cost:.1f}/kWh")
        
        with col4:
            # YoY comparison - use the last month in selection
            selected_period = filters['yymm_list'][-1] if filters.get('yymm_list') else None
            yoy_change = calculate_yoy_comparison(bills_df, selected_period, 'cost_bill') if selected_period else None
            yoy_display = f"{yoy_change:+.1f}%" if yoy_change is not None else "N/A"
            render_simple_metric_card("YoY 변화 (최종월)", yoy_display, help_text="선택 기간의 마지막 월 기준")
        
        # Button for 3-year comparison chart
        st.markdown("### 📊 상세 분석")
        
        # Initialize session state for chart toggle
        if "show_3year_chart" not in st.session_state:
            st.session_state["show_3year_chart"] = False
        
        # Toggle button
        button_label = "📉 월별 3개년 비교 숨기기" if st.session_state["show_3year_chart"] else "📊 월별 3개년 비교 보기 (전력량/요금/단가/YoY)"
        if st.button(button_label, key="toggle_3year_chart"):
            st.session_state["show_3year_chart"] = not st.session_state["show_3year_chart"]
        
        # Show charts if toggled on
        if st.session_state["show_3year_chart"]:
            # Apply filters excluding period filter (to show full 3 years)
            # Create a copy of filters without the period filter
            filters_no_period = filters.copy()
            filters_no_period['yymm_list'] = []  # Remove period restriction
            
            # Apply all other filters
            filtered_bills_no_period = apply_filters(bills_df, filters_no_period)
            
            # Prepare 3-year comparison data for multiple metrics
            kwh_data = prepare_monthly_3year_comparison(filtered_bills_no_period, 'kwh_bill')
            cost_data = prepare_monthly_3year_comparison(filtered_bills_no_period, 'cost_bill')
            
            if len(kwh_data) > 0 and len(cost_data) > 0:
                # Calculate average unit cost (cost/kwh)
                avg_cost_data = kwh_data.copy()
                avg_cost_data = avg_cost_data.merge(cost_data, on=['year', 'month'], suffixes=('_kwh', '_cost'))
                avg_cost_data['avg_unit_cost'] = avg_cost_data.apply(
                    lambda row: row['kwh_cost'] / row['kwh_kwh'] if row['kwh_kwh'] > 0 else 0,
                    axis=1
                )
                avg_cost_data = avg_cost_data[['year', 'month', 'avg_unit_cost']].copy()
                avg_cost_data.rename(columns={'avg_unit_cost': 'kwh'}, inplace=True)
                
                # Calculate YoY change for each month
                yoy_data = []
                for year in kwh_data['year'].unique():
                    for month in range(1, 13):
                        current = cost_data[(cost_data['year'] == year) & (cost_data['month'] == month)]
                        prev = cost_data[(cost_data['year'] == year - 1) & (cost_data['month'] == month)]
                        
                        if len(current) > 0 and len(prev) > 0:
                            current_val = current['kwh'].values[0]
                            prev_val = prev['kwh'].values[0]
                            
                            if prev_val > 0:
                                yoy_pct = ((current_val - prev_val) / prev_val) * 100
                                yoy_data.append({'year': year, 'month': month, 'kwh': yoy_pct})
                
                yoy_df = pd.DataFrame(yoy_data) if yoy_data else pd.DataFrame(columns=['year', 'month', 'kwh'])
                
                # Create tabs for different metrics
                chart_tab1, chart_tab2, chart_tab3, chart_tab4 = st.tabs([
                    "⚡ 전력량", "💰 전기요금", "📊 평균단가", "📈 YoY 변화"
                ])
                
                with chart_tab1:
                    chart_kwh = alt.Chart(kwh_data).mark_bar().encode(
                        x=alt.X('month:O', title='월', axis=alt.Axis(labelAngle=0)),
                        y=alt.Y('kwh:Q', title='kWh', axis=alt.Axis(format=',.0f')),
                        color=alt.Color('year:N', title='연도', legend=alt.Legend(orient='top')),
                        xOffset='year:N',
                        tooltip=[
                            alt.Tooltip('year:N', title='연도'),
                            alt.Tooltip('month:O', title='월'),
                            alt.Tooltip('kwh:Q', title='kWh', format=',.0f')
                        ]
                    ).properties(
                        title='월별 전력량 (kWh) - 3개년 비교',
                        height=400
                    )
                    st.altair_chart(chart_kwh, use_container_width=True)
                    
                    with st.expander("📊 데이터 테이블"):
                        pivot = kwh_data.pivot(index='month', columns='year', values='kwh')
                        pivot.columns.name = None
                        pivot.index.name = '월'
                        st.dataframe(pivot.style.format("{:,.0f}"), use_container_width=True)
                
                with chart_tab2:
                    chart_cost = alt.Chart(cost_data).mark_bar().encode(
                        x=alt.X('month:O', title='월', axis=alt.Axis(labelAngle=0)),
                        y=alt.Y('kwh:Q', title='전기요금 (원)', axis=alt.Axis(format=',.0f')),
                        color=alt.Color('year:N', title='연도', legend=alt.Legend(orient='top')),
                        xOffset='year:N',
                        tooltip=[
                            alt.Tooltip('year:N', title='연도'),
                            alt.Tooltip('month:O', title='월'),
                            alt.Tooltip('kwh:Q', title='전기요금', format=',.0f')
                        ]
                    ).properties(
                        title='월별 전기요금 (원) - 3개년 비교',
                        height=400
                    )
                    st.altair_chart(chart_cost, use_container_width=True)
                    
                    with st.expander("📊 데이터 테이블"):
                        pivot = cost_data.pivot(index='month', columns='year', values='kwh')
                        pivot.columns.name = None
                        pivot.index.name = '월'
                        st.dataframe(pivot.style.format("₩{:,.0f}"), use_container_width=True)
                
                with chart_tab3:
                    chart_avg = alt.Chart(avg_cost_data).mark_bar().encode(
                        x=alt.X('month:O', title='월', axis=alt.Axis(labelAngle=0)),
                        y=alt.Y('kwh:Q', title='평균 단가 (원/kWh)', axis=alt.Axis(format='.1f')),
                        color=alt.Color('year:N', title='연도', legend=alt.Legend(orient='top')),
                        xOffset='year:N',
                        tooltip=[
                            alt.Tooltip('year:N', title='연도'),
                            alt.Tooltip('month:O', title='월'),
                            alt.Tooltip('kwh:Q', title='평균 단가', format='.1f')
                        ]
                    ).properties(
                        title='월별 평균 단가 (원/kWh) - 3개년 비교',
                        height=400
                    )
                    st.altair_chart(chart_avg, use_container_width=True)
                    
                    with st.expander("📊 데이터 테이블"):
                        pivot = avg_cost_data.pivot(index='month', columns='year', values='kwh')
                        pivot.columns.name = None
                        pivot.index.name = '월'
                        st.dataframe(pivot.style.format("₩{:.1f}"), use_container_width=True)
                
                with chart_tab4:
                    if len(yoy_df) > 0:
                        chart_yoy = alt.Chart(yoy_df).mark_bar().encode(
                            x=alt.X('month:O', title='월', axis=alt.Axis(labelAngle=0)),
                            y=alt.Y('kwh:Q', title='YoY 변화율 (%)', axis=alt.Axis(format='.1f')),
                            color=alt.Color('year:N', title='연도', legend=alt.Legend(orient='top')),
                            xOffset='year:N',
                            tooltip=[
                                alt.Tooltip('year:N', title='연도'),
                                alt.Tooltip('month:O', title='월'),
                                alt.Tooltip('kwh:Q', title='YoY 변화율 (%)', format='.1f')
                            ]
                        ).properties(
                            title='월별 YoY 변화율 (%) - 전년 동월 대비',
                            height=400
                        )
                        st.altair_chart(chart_yoy, use_container_width=True)
                        
                        with st.expander("📊 데이터 테이블"):
                            pivot = yoy_df.pivot(index='month', columns='year', values='kwh')
                            pivot.columns.name = None
                            pivot.index.name = '월'
                            st.dataframe(pivot.style.format("{:+.1f}%"), use_container_width=True)
                    else:
                        st.info("YoY 비교를 위한 전년도 데이터가 부족합니다.")
            else:
                st.info("표시할 3개년 비교 데이터가 없습니다.")
        
        st.markdown("---")
        
        # Plan variance
        st.markdown("### 계획 대비 실적 개요")
        
        # Filter plan by selected periods
        plan_month = plan_df[plan_df['yymm'].isin(filters['yymm_list'])] if filters.get('yymm_list') else plan_df
        
        if len(plan_month) > 0:
            plan_cost = plan_month['cost_plan'].sum()
            plan_kwh = plan_month['kwh_plan'].sum()
            
            variance_result = calculate_plan_variance(total_cost, plan_cost)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                render_simple_metric_card(
                    "계획 대비 차이",
                    f"₩{variance_result['variance']:,.0f}",
                    delta=f"{variance_result['variance_pct']:.1f}%"
                )
            
            with col2:
                render_simple_metric_card(
                    "달성률",
                    f"{variance_result['achievement_rate']:.1f}%"
                )
            
            with col3:
                # Decomposition
                decomp = decompose_cost_variance(total_cost, plan_cost, total_kwh, plan_kwh)
                render_simple_metric_card(
                    "사용량 효과",
                    f"₩{decomp['usage_effect']:,.0f}",
                    help_text="사용량 변동에 의한 비용 영향"
                )
        else:
            st.info("계획 데이터가 없습니다.")
        
        st.markdown("---")
        
        # Top changes
        st.markdown("### 📌 주요 변동 Top 5")
        
        # Calculate month-over-month change per site - use last selected period
        months_sorted = sorted(bills_df['yymm'].unique())
        selected_yymm = filters['yymm_list'][-1] if filters.get('yymm_list') else None
        
        if len(months_sorted) >= 2 and selected_yymm and selected_yymm in months_sorted:
            current_idx = months_sorted.index(selected_yymm)
            if current_idx > 0:
                prev_month = months_sorted[current_idx - 1]
                
                current_month_bills = filtered_bills[filtered_bills['yymm'] == selected_yymm]
                prev_month_bills = bills_df[
                    (bills_df['yymm'] == prev_month) &
                    (bills_df['site_id'].isin(current_month_bills['site_id']))
                ]
                
                merged = current_month_bills.merge(
                    prev_month_bills[['site_id', 'cost_bill']],
                    on='site_id',
                    how='inner',
                    suffixes=('_curr', '_prev')
                )
                
                merged['cost_change'] = merged['cost_bill_curr'] - merged['cost_bill_prev']
                merged['cost_change_pct'] = (merged['cost_change'] / merged['cost_bill_prev']) * 100
                
                # Top 5 increases
                top_increases = merged.nlargest(5, 'cost_change')[
                    ['site_id', 'region', 'cost_bill_curr', 'cost_bill_prev', 'cost_change', 'cost_change_pct']
                ]
                
                st.markdown("#### 비용 증가 Top 5")
                st.dataframe(top_increases, use_container_width=True, hide_index=True)
        else:
            st.info("월별 비교 데이터가 부족합니다.")

with tab2:
    st.markdown("## 📈 계획 대비 실적")
    
    # Trend chart
    st.markdown("### 월별 추이")
    
    # Aggregate by month
    monthly_actual = filtered_bills.groupby('yymm').agg({
        'kwh_bill': 'sum',
        'cost_bill': 'sum'
    }).reset_index()
    
    # Merge with plan
    monthly_plan = plan_df.groupby('yymm').agg({
        'kwh_plan': 'sum',
        'cost_plan': 'sum'
    }).reset_index()
    
    monthly_combined = monthly_actual.merge(monthly_plan, on='yymm', how='left')
    
    # Cost trend
    fig_cost = go.Figure()
    
    fig_cost.add_trace(go.Scatter(
        x=monthly_combined['yymm'],
        y=monthly_combined['cost_plan'],
        name='Plan',
        mode='lines+markers',
        line=dict(dash='dash', color='blue')
    ))
    
    fig_cost.add_trace(go.Scatter(
        x=monthly_combined['yymm'],
        y=monthly_combined['cost_bill'],
        name='Actual',
        mode='lines+markers',
        line=dict(color='red')
    ))
    
    fig_cost.update_layout(
        title='Monthly Cost: Plan vs Actual',
        xaxis_title='Month',
        yaxis_title='Cost (KRW)',
        hovermode='x unified'
    )
    
    st.plotly_chart(fig_cost, use_container_width=True)
    
    # Variance table
    st.markdown("### 차이 분석")
    
    monthly_combined['variance'] = monthly_combined['cost_bill'] - monthly_combined['cost_plan']
    monthly_combined['variance_pct'] = (monthly_combined['variance'] / monthly_combined['cost_plan']) * 100
    
    variance_table = monthly_combined[['yymm', 'cost_plan', 'cost_bill', 'variance', 'variance_pct']].copy()
    variance_table.columns = ['월', '계획', '실적', '차이', '차이율(%)']
    
    st.dataframe(variance_table, use_container_width=True, hide_index=True)

with tab3:
    st.markdown("## 🔍 청구서 vs 실사용량")
    
    # 청구서vs실사용량 화면 전용 월 선택
    st.markdown("### 📅 분석 기간 선택")
    st.info("💡 이 화면은 월별 분석을 제공합니다. 아래에서 분석할 월을 선택하세요. (사이드바의 기간 필터와는 독립적입니다)")
    
    # 사용 가능한 모든 월 가져오기
    all_available_months = sorted(bills_df['yymm'].unique().tolist(), reverse=True)
    
    # Read selected month from query params if available
    query_params = st.query_params.to_dict() if hasattr(st, "query_params") else {}
    query_month = query_params.get("month")
    
    # Determine default month
    if query_month:
        try:
            default_month = int(query_month)
            if default_month not in all_available_months:
                default_month = all_available_months[0] if all_available_months else None
        except (ValueError, TypeError):
            default_month = all_available_months[0] if all_available_months else None
    else:
        default_month = all_available_months[0] if all_available_months else None
    
    # Find index for default month
    default_index = 0
    if default_month and default_month in all_available_months:
        default_index = all_available_months.index(default_month)
    
    # 월 선택 UI
    col_month1, col_month2 = st.columns([3, 1])
    
    with col_month1:
        # 월 선택 selectbox
        selected_month = st.selectbox(
            "분석 대상 월",
            options=all_available_months,
            index=default_index,
            format_func=lambda x: f"{str(x)[:4]}년 {str(x)[4:6]}월",
            key="bill_actual_month_selector"
        )
        
        # Update query params when month changes
        if hasattr(st, "query_params") and selected_month != query_month:
            st.query_params["month"] = str(selected_month)
    
    with col_month2:
        st.metric("선택된 월", f"{str(selected_month)[:4]}.{str(selected_month)[4:6]}")
    
    st.markdown("---")
    
    # 기간 필터 제외한 필터 적용 (해당 월의 데이터만)
    # 먼저 선택된 월의 데이터만 필터링
    bills_for_month = bills_df[bills_df['yymm'] == selected_month].copy()
    
    # 기간 외 다른 필터 적용 (지역, 계약유형 등)
    filters_no_period = filters.copy()
    filters_no_period['yymm_list'] = []  # 기간 필터 제거
    filtered_bills_month = apply_filters(bills_for_month, filters_no_period)
    
    # Merge bills and actual with explicit suffixes
    merged_bill_actual = filtered_bills_month.merge(
        actual_df,
        on=['yymm', 'site_id'],
        how='left',
        suffixes=('', '_actual')
    )
    
    if len(merged_bill_actual) == 0:
        st.warning(f"선택한 월({str(selected_month)[:4]}년 {str(selected_month)[4:6]}월)에 해당하는 데이터가 없습니다.")
    else:
        # === 개요 섹션 ===
        st.markdown(f"### 📊 개요 ({str(selected_month)[:4]}년 {str(selected_month)[4:6]}월)")
        
        # 청구서 기반 집계
        total_kwh_bill = merged_bill_actual['kwh_bill'].sum()
        total_cost_bill = merged_bill_actual['cost_bill'].sum()
        
        # 실사용 기반 집계
        total_kwh_actual = merged_bill_actual['kwh_actual'].sum()
        
        # 실사용 전력량 기반 추정 요금 계산
        # 방법: 청구서의 평균 단가를 실사용 전력량에 적용
        avg_unit_cost = total_cost_bill / total_kwh_bill if total_kwh_bill > 0 else 0
        estimated_cost_from_actual = total_kwh_actual * avg_unit_cost
        
        # 차이 계산
        kwh_diff = total_kwh_actual - total_kwh_bill
        kwh_diff_pct = (kwh_diff / total_kwh_bill * 100) if total_kwh_bill > 0 else 0
        cost_diff = estimated_cost_from_actual - total_cost_bill
        cost_diff_pct = (cost_diff / total_cost_bill * 100) if total_cost_bill > 0 else 0
        
        # 4개 컬럼으로 주요 지표 표시
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            delta_str = f"{kwh_diff:+,.0f} kWh ({kwh_diff_pct:+.1f}%)"
            render_simple_metric_card(
                "청구서 전력량", 
                f"{total_kwh_bill:,.0f} kWh",
                help_text="청구서 기준 전력 사용량"
            )
            st.caption(f"📊 실사용: {total_kwh_actual:,.0f} kWh")
            st.caption(f"📈 차이: {delta_str}")
        
        with col2:
            delta_str = f"{kwh_diff:+,.0f} kWh ({kwh_diff_pct:+.1f}%)"
            render_simple_metric_card(
                "실사용 전력량",
                f"{total_kwh_actual:,.0f} kWh",
                delta=delta_str if kwh_diff != 0 else None,
                help_text="계측 데이터 기준 실제 사용량"
            )
        
        with col3:
            delta_str = f"{cost_diff:+,.0f} 원 ({cost_diff_pct:+.1f}%)"
            render_simple_metric_card(
                "청구서 요금",
                f"₩{total_cost_bill:,.0f}",
                help_text="실제 청구된 전기요금"
            )
            st.caption(f"📊 추정: ₩{estimated_cost_from_actual:,.0f}")
            st.caption(f"📈 차이: {delta_str}")
        
        with col4:
            delta_str = f"{cost_diff:+,.0f} 원 ({cost_diff_pct:+.1f}%)"
            render_simple_metric_card(
                "실사용 기반 추정 요금",
                f"₩{estimated_cost_from_actual:,.0f}",
                delta=delta_str if cost_diff != 0 else None,
                help_text=f"실사용량 × 평균단가(₩{avg_unit_cost:.1f}/kWh)"
            )
        
        st.markdown("---")
        
        # === 기준별 비교 그래프 ===
        st.markdown(f"### 📊 기준별 비교 분석 ({str(selected_month)[:4]}년 {str(selected_month)[4:6]}월)")
        st.markdown("다양한 기준으로 청구서와 실사용량을 비교합니다.")
        
        # Merge with site_master to get site_type
        merged_with_site = merged_bill_actual.merge(
            site_master[['site_id', 'site_type', 'voltage']],
            on='site_id',
            how='left'
        )
        
        # Create tabs for different comparison criteria
        comp_tab1, comp_tab2, comp_tab3, comp_tab4, comp_tab5, comp_tab6 = st.tabs([
            "🗺️ 지역별", "🏢 설비유형별", "📋 계약대상별", "💰 계약유형별", "📡 세대별", "⚡ RAPA여부별"
        ])
        
        with comp_tab1:
            st.markdown("#### 지역별 청구서 vs 실사용량 비교")
            
            # Aggregate by region
            region_agg = merged_with_site.groupby('region').agg({
                'kwh_bill': 'sum',
                'kwh_actual': 'sum',
                'cost_bill': 'sum'
            }).reset_index()
            
            # Calculate estimated cost from actual
            region_agg['cost_actual_est'] = region_agg['kwh_actual'] * avg_unit_cost
            
            # Create comparison chart
            fig_region = go.Figure()
            
            fig_region.add_trace(go.Bar(
                name='청구서 전력량',
                x=region_agg['region'],
                y=region_agg['kwh_bill'],
                marker_color=PYLON_BLUE,
                text=region_agg['kwh_bill'].apply(lambda x: f"{x:,.0f}"),
                textposition='outside'
            ))
            
            fig_region.add_trace(go.Bar(
                name='실사용 전력량',
                x=region_agg['region'],
                y=region_agg['kwh_actual'],
                marker_color=PYLON_ORANGE,
                text=region_agg['kwh_actual'].apply(lambda x: f"{x:,.0f}"),
                textposition='outside'
            ))
            
            fig_region.update_layout(
                title='지역별 전력량 비교 (kWh)',
                xaxis_title='지역',
                yaxis_title='전력량 (kWh)',
                barmode='group',
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_region, use_container_width=True)
            
            # Cost comparison
            fig_region_cost = go.Figure()
            
            fig_region_cost.add_trace(go.Bar(
                name='청구서 요금',
                x=region_agg['region'],
                y=region_agg['cost_bill'],
                marker_color=PYLON_BLUE,
                text=region_agg['cost_bill'].apply(lambda x: f"₩{x:,.0f}"),
                textposition='outside'
            ))
            
            fig_region_cost.add_trace(go.Bar(
                name='실사용 기반 추정 요금',
                x=region_agg['region'],
                y=region_agg['cost_actual_est'],
                marker_color=PYLON_ORANGE,
                text=region_agg['cost_actual_est'].apply(lambda x: f"₩{x:,.0f}"),
                textposition='outside'
            ))
            
            fig_region_cost.update_layout(
                title='지역별 요금 비교 (원)',
                xaxis_title='지역',
                yaxis_title='요금 (원)',
                barmode='group',
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_region_cost, use_container_width=True)
            
            with st.expander("📊 상세 데이터"):
                region_agg['kwh_diff'] = region_agg['kwh_actual'] - region_agg['kwh_bill']
                region_agg['kwh_diff_pct'] = (region_agg['kwh_diff'] / region_agg['kwh_bill'] * 100).round(2)
                region_agg['cost_diff'] = region_agg['cost_actual_est'] - region_agg['cost_bill']
                region_agg['cost_diff_pct'] = (region_agg['cost_diff'] / region_agg['cost_bill'] * 100).round(2)
                st.dataframe(region_agg, use_container_width=True, hide_index=True)
        
        with comp_tab2:
            st.markdown("#### 설비유형별 청구서 vs 실사용량 비교")
            
            # Aggregate by site_type
            site_type_agg = merged_with_site.groupby('site_type').agg({
                'kwh_bill': 'sum',
                'kwh_actual': 'sum',
                'cost_bill': 'sum'
            }).reset_index()
            
            site_type_agg['cost_actual_est'] = site_type_agg['kwh_actual'] * avg_unit_cost
            
            fig_site_type = go.Figure()
            
            fig_site_type.add_trace(go.Bar(
                name='청구서 전력량',
                x=site_type_agg['site_type'],
                y=site_type_agg['kwh_bill'],
                marker_color=PYLON_BLUE,
                text=site_type_agg['kwh_bill'].apply(lambda x: f"{x:,.0f}"),
                textposition='outside'
            ))
            
            fig_site_type.add_trace(go.Bar(
                name='실사용 전력량',
                x=site_type_agg['site_type'],
                y=site_type_agg['kwh_actual'],
                marker_color=PYLON_ORANGE,
                text=site_type_agg['kwh_actual'].apply(lambda x: f"{x:,.0f}"),
                textposition='outside'
            ))
            
            fig_site_type.update_layout(
                title='설비유형별 전력량 비교 (kWh)',
                xaxis_title='설비유형',
                yaxis_title='전력량 (kWh)',
                barmode='group',
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_site_type, use_container_width=True)
            
            # Cost comparison
            fig_site_type_cost = go.Figure()
            
            fig_site_type_cost.add_trace(go.Bar(
                name='청구서 요금',
                x=site_type_agg['site_type'],
                y=site_type_agg['cost_bill'],
                marker_color=PYLON_BLUE,
                text=site_type_agg['cost_bill'].apply(lambda x: f"₩{x:,.0f}"),
                textposition='outside'
            ))
            
            fig_site_type_cost.add_trace(go.Bar(
                name='실사용 기반 추정 요금',
                x=site_type_agg['site_type'],
                y=site_type_agg['cost_actual_est'],
                marker_color=PYLON_ORANGE,
                text=site_type_agg['cost_actual_est'].apply(lambda x: f"₩{x:,.0f}"),
                textposition='outside'
            ))
            
            fig_site_type_cost.update_layout(
                title='설비유형별 요금 비교 (원)',
                xaxis_title='설비유형',
                yaxis_title='요금 (원)',
                barmode='group',
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_site_type_cost, use_container_width=True)
            
            with st.expander("📊 상세 데이터"):
                site_type_agg['kwh_diff'] = site_type_agg['kwh_actual'] - site_type_agg['kwh_bill']
                site_type_agg['kwh_diff_pct'] = (site_type_agg['kwh_diff'] / site_type_agg['kwh_bill'] * 100).round(2)
                site_type_agg['cost_diff'] = site_type_agg['cost_actual_est'] - site_type_agg['cost_bill']
                site_type_agg['cost_diff_pct'] = (site_type_agg['cost_diff'] / site_type_agg['cost_bill'] * 100).round(2)
                st.dataframe(site_type_agg, use_container_width=True, hide_index=True)
        
        with comp_tab3:
            st.markdown("#### 계약대상별 청구서 vs 실사용량 비교")
            
            # Aggregate by contract_target
            contract_target_agg = merged_with_site.groupby('contract_target').agg({
                'kwh_bill': 'sum',
                'kwh_actual': 'sum',
                'cost_bill': 'sum'
            }).reset_index()
            
            contract_target_agg['cost_actual_est'] = contract_target_agg['kwh_actual'] * avg_unit_cost
            
            fig_contract_target = go.Figure()
            
            fig_contract_target.add_trace(go.Bar(
                name='청구서 전력량',
                x=contract_target_agg['contract_target'],
                y=contract_target_agg['kwh_bill'],
                marker_color=PYLON_BLUE,
                text=contract_target_agg['kwh_bill'].apply(lambda x: f"{x:,.0f}"),
                textposition='outside'
            ))
            
            fig_contract_target.add_trace(go.Bar(
                name='실사용 전력량',
                x=contract_target_agg['contract_target'],
                y=contract_target_agg['kwh_actual'],
                marker_color=PYLON_ORANGE,
                text=contract_target_agg['kwh_actual'].apply(lambda x: f"{x:,.0f}"),
                textposition='outside'
            ))
            
            fig_contract_target.update_layout(
                title='계약대상별 전력량 비교 (kWh)',
                xaxis_title='계약대상 (ME: 한전계약, MC: 건물계약)',
                yaxis_title='전력량 (kWh)',
                barmode='group',
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_contract_target, use_container_width=True)
            
            # Cost comparison
            fig_contract_target_cost = go.Figure()
            
            fig_contract_target_cost.add_trace(go.Bar(
                name='청구서 요금',
                x=contract_target_agg['contract_target'],
                y=contract_target_agg['cost_bill'],
                marker_color=PYLON_BLUE,
                text=contract_target_agg['cost_bill'].apply(lambda x: f"₩{x:,.0f}"),
                textposition='outside'
            ))
            
            fig_contract_target_cost.add_trace(go.Bar(
                name='실사용 기반 추정 요금',
                x=contract_target_agg['contract_target'],
                y=contract_target_agg['cost_actual_est'],
                marker_color=PYLON_ORANGE,
                text=contract_target_agg['cost_actual_est'].apply(lambda x: f"₩{x:,.0f}"),
                textposition='outside'
            ))
            
            fig_contract_target_cost.update_layout(
                title='계약대상별 요금 비교 (원)',
                xaxis_title='계약대상 (ME: 한전계약, MC: 건물계약)',
                yaxis_title='요금 (원)',
                barmode='group',
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_contract_target_cost, use_container_width=True)
            
            with st.expander("📊 상세 데이터"):
                contract_target_agg['kwh_diff'] = contract_target_agg['kwh_actual'] - contract_target_agg['kwh_bill']
                contract_target_agg['kwh_diff_pct'] = (contract_target_agg['kwh_diff'] / contract_target_agg['kwh_bill'] * 100).round(2)
                contract_target_agg['cost_diff'] = contract_target_agg['cost_actual_est'] - contract_target_agg['cost_bill']
                contract_target_agg['cost_diff_pct'] = (contract_target_agg['cost_diff'] / contract_target_agg['cost_bill'] * 100).round(2)
                st.dataframe(contract_target_agg, use_container_width=True, hide_index=True)
        
        with comp_tab4:
            st.markdown("#### 계약유형별 청구서 vs 실사용량 비교")
            
            # Aggregate by contract_type
            contract_type_agg = merged_with_site.groupby('contract_type').agg({
                'kwh_bill': 'sum',
                'kwh_actual': 'sum',
                'cost_bill': 'sum'
            }).reset_index()
            
            contract_type_agg['cost_actual_est'] = contract_type_agg['kwh_actual'] * avg_unit_cost
            
            fig_contract_type = go.Figure()
            
            fig_contract_type.add_trace(go.Bar(
                name='청구서 전력량',
                x=contract_type_agg['contract_type'],
                y=contract_type_agg['kwh_bill'],
                marker_color=PYLON_BLUE,
                text=contract_type_agg['kwh_bill'].apply(lambda x: f"{x:,.0f}"),
                textposition='outside'
            ))
            
            fig_contract_type.add_trace(go.Bar(
                name='실사용 전력량',
                x=contract_type_agg['contract_type'],
                y=contract_type_agg['kwh_actual'],
                marker_color=PYLON_ORANGE,
                text=contract_type_agg['kwh_actual'].apply(lambda x: f"{x:,.0f}"),
                textposition='outside'
            ))
            
            fig_contract_type.update_layout(
                title='계약유형별 전력량 비교 (kWh)',
                xaxis_title='계약유형',
                yaxis_title='전력량 (kWh)',
                barmode='group',
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_contract_type, use_container_width=True)
            
            # Cost comparison
            fig_contract_type_cost = go.Figure()
            
            fig_contract_type_cost.add_trace(go.Bar(
                name='청구서 요금',
                x=contract_type_agg['contract_type'],
                y=contract_type_agg['cost_bill'],
                marker_color=PYLON_BLUE,
                text=contract_type_agg['cost_bill'].apply(lambda x: f"₩{x:,.0f}"),
                textposition='outside'
            ))
            
            fig_contract_type_cost.add_trace(go.Bar(
                name='실사용 기반 추정 요금',
                x=contract_type_agg['contract_type'],
                y=contract_type_agg['cost_actual_est'],
                marker_color=PYLON_ORANGE,
                text=contract_type_agg['cost_actual_est'].apply(lambda x: f"₩{x:,.0f}"),
                textposition='outside'
            ))
            
            fig_contract_type_cost.update_layout(
                title='계약유형별 요금 비교 (원)',
                xaxis_title='계약유형',
                yaxis_title='요금 (원)',
                barmode='group',
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_contract_type_cost, use_container_width=True)
            
            with st.expander("📊 상세 데이터"):
                contract_type_agg['kwh_diff'] = contract_type_agg['kwh_actual'] - contract_type_agg['kwh_bill']
                contract_type_agg['kwh_diff_pct'] = (contract_type_agg['kwh_diff'] / contract_type_agg['kwh_bill'] * 100).round(2)
                contract_type_agg['cost_diff'] = contract_type_agg['cost_actual_est'] - contract_type_agg['cost_bill']
                contract_type_agg['cost_diff_pct'] = (contract_type_agg['cost_diff'] / contract_type_agg['cost_bill'] * 100).round(2)
                st.dataframe(contract_type_agg, use_container_width=True, hide_index=True)
        
        with comp_tab5:
            st.markdown("#### 세대별 청구서 vs 실사용량 비교")
            
            # Aggregate by network_gen
            network_gen_agg = merged_with_site.groupby('network_gen').agg({
                'kwh_bill': 'sum',
                'kwh_actual': 'sum',
                'cost_bill': 'sum'
            }).reset_index()
            
            network_gen_agg['cost_actual_est'] = network_gen_agg['kwh_actual'] * avg_unit_cost
            
            fig_network_gen = go.Figure()
            
            fig_network_gen.add_trace(go.Bar(
                name='청구서 전력량',
                x=network_gen_agg['network_gen'],
                y=network_gen_agg['kwh_bill'],
                marker_color=PYLON_BLUE,
                text=network_gen_agg['kwh_bill'].apply(lambda x: f"{x:,.0f}"),
                textposition='outside'
            ))
            
            fig_network_gen.add_trace(go.Bar(
                name='실사용 전력량',
                x=network_gen_agg['network_gen'],
                y=network_gen_agg['kwh_actual'],
                marker_color=PYLON_ORANGE,
                text=network_gen_agg['kwh_actual'].apply(lambda x: f"{x:,.0f}"),
                textposition='outside'
            ))
            
            fig_network_gen.update_layout(
                title='세대별 전력량 비교 (kWh)',
                xaxis_title='세대 (3G/LTE/5G)',
                yaxis_title='전력량 (kWh)',
                barmode='group',
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_network_gen, use_container_width=True)
            
            # Cost comparison
            fig_network_gen_cost = go.Figure()
            
            fig_network_gen_cost.add_trace(go.Bar(
                name='청구서 요금',
                x=network_gen_agg['network_gen'],
                y=network_gen_agg['cost_bill'],
                marker_color=PYLON_BLUE,
                text=network_gen_agg['cost_bill'].apply(lambda x: f"₩{x:,.0f}"),
                textposition='outside'
            ))
            
            fig_network_gen_cost.add_trace(go.Bar(
                name='실사용 기반 추정 요금',
                x=network_gen_agg['network_gen'],
                y=network_gen_agg['cost_actual_est'],
                marker_color=PYLON_ORANGE,
                text=network_gen_agg['cost_actual_est'].apply(lambda x: f"₩{x:,.0f}"),
                textposition='outside'
            ))
            
            fig_network_gen_cost.update_layout(
                title='세대별 요금 비교 (원)',
                xaxis_title='세대 (3G/LTE/5G)',
                yaxis_title='요금 (원)',
                barmode='group',
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_network_gen_cost, use_container_width=True)
            
            with st.expander("📊 상세 데이터"):
                network_gen_agg['kwh_diff'] = network_gen_agg['kwh_actual'] - network_gen_agg['kwh_bill']
                network_gen_agg['kwh_diff_pct'] = (network_gen_agg['kwh_diff'] / network_gen_agg['kwh_bill'] * 100).round(2)
                network_gen_agg['cost_diff'] = network_gen_agg['cost_actual_est'] - network_gen_agg['cost_bill']
                network_gen_agg['cost_diff_pct'] = (network_gen_agg['cost_diff'] / network_gen_agg['cost_bill'] * 100).round(2)
                st.dataframe(network_gen_agg, use_container_width=True, hide_index=True)
        
        with comp_tab6:
            st.markdown("#### RAPA여부별 청구서 vs 실사용량 비교")
            
            # Aggregate by rapa_type
            rapa_agg = merged_with_site.groupby('rapa_type').agg({
                'kwh_bill': 'sum',
                'kwh_actual': 'sum',
                'cost_bill': 'sum'
            }).reset_index()
            
            rapa_agg['cost_actual_est'] = rapa_agg['kwh_actual'] * avg_unit_cost
            
            fig_rapa = go.Figure()
            
            fig_rapa.add_trace(go.Bar(
                name='청구서 전력량',
                x=rapa_agg['rapa_type'],
                y=rapa_agg['kwh_bill'],
                marker_color=PYLON_BLUE,
                text=rapa_agg['kwh_bill'].apply(lambda x: f"{x:,.0f}"),
                textposition='outside'
            ))
            
            fig_rapa.add_trace(go.Bar(
                name='실사용 전력량',
                x=rapa_agg['rapa_type'],
                y=rapa_agg['kwh_actual'],
                marker_color=PYLON_ORANGE,
                text=rapa_agg['kwh_actual'].apply(lambda x: f"{x:,.0f}"),
                textposition='outside'
            ))
            
            fig_rapa.update_layout(
                title='RAPA여부별 전력량 비교 (kWh)',
                xaxis_title='RAPA여부',
                yaxis_title='전력량 (kWh)',
                barmode='group',
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_rapa, use_container_width=True)
            
            # Cost comparison
            fig_rapa_cost = go.Figure()
            
            fig_rapa_cost.add_trace(go.Bar(
                name='청구서 요금',
                x=rapa_agg['rapa_type'],
                y=rapa_agg['cost_bill'],
                marker_color=PYLON_BLUE,
                text=rapa_agg['cost_bill'].apply(lambda x: f"₩{x:,.0f}"),
                textposition='outside'
            ))
            
            fig_rapa_cost.add_trace(go.Bar(
                name='실사용 기반 추정 요금',
                x=rapa_agg['rapa_type'],
                y=rapa_agg['cost_actual_est'],
                marker_color=PYLON_ORANGE,
                text=rapa_agg['cost_actual_est'].apply(lambda x: f"₩{x:,.0f}"),
                textposition='outside'
            ))
            
            fig_rapa_cost.update_layout(
                title='RAPA여부별 요금 비교 (원)',
                xaxis_title='RAPA여부',
                yaxis_title='요금 (원)',
                barmode='group',
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_rapa_cost, use_container_width=True)
            
            with st.expander("📊 상세 데이터"):
                rapa_agg['kwh_diff'] = rapa_agg['kwh_actual'] - rapa_agg['kwh_bill']
                rapa_agg['kwh_diff_pct'] = (rapa_agg['kwh_diff'] / rapa_agg['kwh_bill'] * 100).round(2)
                rapa_agg['cost_diff'] = rapa_agg['cost_actual_est'] - rapa_agg['cost_bill']
                rapa_agg['cost_diff_pct'] = (rapa_agg['cost_diff'] / rapa_agg['cost_bill'] * 100).round(2)
                st.dataframe(rapa_agg, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # === 국소별 청구 상태 분석 ===
        st.markdown(f"### 📌 국소별 청구 상태 분석 ({str(selected_month)[:4]}년 {str(selected_month)[4:6]}월)")
        
        # 국소별 오차율 계산 (실사용량이 있는 국소만)
        site_analysis = merged_bill_actual[
            (merged_bill_actual['kwh_actual'] > 0) & 
            (merged_bill_actual['kwh_bill'] > 0)
        ].copy()
        
        # 오차율 계산: (청구서 - 실사용량) / 실사용량 * 100
        site_analysis['billing_error_pct'] = (
            (site_analysis['kwh_bill'] - site_analysis['kwh_actual']) / 
            site_analysis['kwh_actual'] * 100
        )
        
        # 분류 기준 (±5% 이내는 정상)
        def classify_billing_status(error_pct):
            if pd.isna(error_pct):
                return '데이터 없음'
            elif error_pct > 5:
                return '과대청구'
            elif error_pct < -5:
                return '과소청구'
            else:
                return '정상'
        
        site_analysis['billing_status'] = site_analysis['billing_error_pct'].apply(classify_billing_status)
        
        # 집계
        status_counts = site_analysis['billing_status'].value_counts()
        total_sites = len(site_analysis)
        
        # 3개 컬럼으로 통계 표시
        col1, col2, col3 = st.columns(3)
        
        with col1:
            over_count = status_counts.get('과대청구', 0)
            over_pct = (over_count / total_sites * 100) if total_sites > 0 else 0
            render_simple_metric_card(
                "과대청구 국소",
                f"{over_count:,} 개소",
                delta=f"{over_pct:.1f}%",
                help_text="청구서가 실사용량보다 5% 이상 많은 국소"
            )
        
        with col2:
            normal_count = status_counts.get('정상', 0)
            normal_pct = (normal_count / total_sites * 100) if total_sites > 0 else 0
            render_simple_metric_card(
                "정상 국소",
                f"{normal_count:,} 개소",
                delta=f"{normal_pct:.1f}%",
                help_text="청구서와 실사용량 차이가 ±5% 이내인 국소"
            )
        
        with col3:
            under_count = status_counts.get('과소청구', 0)
            under_pct = (under_count / total_sites * 100) if total_sites > 0 else 0
            render_simple_metric_card(
                "과소청구 국소",
                f"{under_count:,} 개소",
                delta=f"{under_pct:.1f}%",
                help_text="청구서가 실사용량보다 5% 이상 적은 국소"
            )
        
        # 파이 차트로 비율 시각화
        st.markdown("#### 청구 상태 분포")
        
        # 색상 매핑
        color_map = {
            '과대청구': '#E74C3C',  # 빨강
            '정상': '#27AE60',      # 녹색
            '과소청구': '#F39C12',  # 주황
            '데이터 없음': '#95A5A6'  # 회색
        }
        
        # 전체 청구 상태 분포 차트
        if len(status_counts) > 0:
            fig_pie = go.Figure(data=[go.Pie(
                labels=status_counts.index,
                values=status_counts.values,
                marker=dict(colors=[color_map.get(status, '#95A5A6') for status in status_counts.index]),
                textinfo='label+percent+value',
                texttemplate='%{label}<br>%{value}개소<br>(%{percent})',
                hole=0.3  # 도넛 차트
            )])
            
            fig_pie.update_layout(
                title='국소 개수 기준 청구 상태 분포',
                height=400,
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.1
                )
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # 과대청구 국소 상세 분석
        st.markdown("#### 과대청구 국소 상세 분석")
        
        # 과대청구 국소만 필터링
        overcharged_sites = site_analysis[site_analysis['billing_status'] == '과대청구'].copy()
        
        if len(overcharged_sites) > 0:
            # site_master 정보 병합
            overcharged_with_info = overcharged_sites.merge(
                site_master[['site_id', 'site_type', 'voltage']],
                on='site_id',
                how='left'
            )
            
            # 2x3 그리드로 6개 기준별 도넛 차트 생성
            col_d1, col_d2, col_d3 = st.columns(3)
            
            with col_d1:
                # 지역별
                region_counts = overcharged_with_info['region'].value_counts()
                fig_region = go.Figure(data=[go.Pie(
                    labels=region_counts.index,
                    values=region_counts.values,
                    textinfo='label+value',
                    texttemplate='%{label}<br>%{value}개소',
                    hole=0.4
                )])
                fig_region.update_layout(
                    title='지역별 과대청구 국소',
                    height=300,
                    showlegend=False,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig_region, use_container_width=True)
            
            with col_d2:
                # 설비유형별
                site_type_counts = overcharged_with_info['site_type'].value_counts()
                fig_site_type = go.Figure(data=[go.Pie(
                    labels=site_type_counts.index,
                    values=site_type_counts.values,
                    textinfo='label+value',
                    texttemplate='%{label}<br>%{value}개소',
                    hole=0.4
                )])
                fig_site_type.update_layout(
                    title='설비유형별 과대청구 국소',
                    height=300,
                    showlegend=False,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig_site_type, use_container_width=True)
            
            with col_d3:
                # 계약대상별
                contract_target_counts = overcharged_with_info['contract_target'].value_counts()
                fig_contract_target = go.Figure(data=[go.Pie(
                    labels=contract_target_counts.index,
                    values=contract_target_counts.values,
                    textinfo='label+value',
                    texttemplate='%{label}<br>%{value}개소',
                    hole=0.4
                )])
                fig_contract_target.update_layout(
                    title='계약대상별 과대청구 국소',
                    height=300,
                    showlegend=False,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig_contract_target, use_container_width=True)
            
            col_d4, col_d5, col_d6 = st.columns(3)
            
            with col_d4:
                # 계약유형별
                contract_type_counts = overcharged_with_info['contract_type'].value_counts()
                fig_contract_type = go.Figure(data=[go.Pie(
                    labels=contract_type_counts.index,
                    values=contract_type_counts.values,
                    textinfo='label+value',
                    texttemplate='%{label}<br>%{value}개소',
                    hole=0.4
                )])
                fig_contract_type.update_layout(
                    title='계약유형별 과대청구 국소',
                    height=300,
                    showlegend=False,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig_contract_type, use_container_width=True)
            
            with col_d5:
                # 세대별
                network_gen_counts = overcharged_with_info['network_gen'].value_counts()
                fig_network_gen = go.Figure(data=[go.Pie(
                    labels=network_gen_counts.index,
                    values=network_gen_counts.values,
                    textinfo='label+value',
                    texttemplate='%{label}<br>%{value}개소',
                    hole=0.4
                )])
                fig_network_gen.update_layout(
                    title='세대별 과대청구 국소',
                    height=300,
                    showlegend=False,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig_network_gen, use_container_width=True)
            
            with col_d6:
                # RAPA여부별
                rapa_counts = overcharged_with_info['rapa_type'].value_counts()
                fig_rapa = go.Figure(data=[go.Pie(
                    labels=rapa_counts.index,
                    values=rapa_counts.values,
                    textinfo='label+value',
                    texttemplate='%{label}<br>%{value}개소',
                    hole=0.4
                )])
                fig_rapa.update_layout(
                    title='RAPA여부별 과대청구 국소',
                    height=300,
                    showlegend=False,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig_rapa, use_container_width=True)
        else:
            st.info("과대청구 국소가 없습니다.")
        
        # 상세 통계 테이블
        with st.expander("📊 상세 통계"):
            stats_table = pd.DataFrame({
                '청구 상태': status_counts.index,
                '국소 개수': status_counts.values,
                '비율 (%)': (status_counts.values / total_sites * 100).round(2),
                '기준': ['청구서가 실사용량보다 5% 초과', 
                        '청구서와 실사용량 차이 ±5% 이내',
                        '청구서가 실사용량보다 5% 미만',
                        '실사용량 데이터 없음'][:len(status_counts)]
            })
            st.dataframe(stats_table, use_container_width=True, hide_index=True)
            
            # 추가 통계
            st.markdown("**📈 오차율 통계**")
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            
            with col_s1:
                st.metric("평균 오차율", f"{site_analysis['billing_error_pct'].mean():.2f}%")
            with col_s2:
                st.metric("중앙값 오차율", f"{site_analysis['billing_error_pct'].median():.2f}%")
            with col_s3:
                st.metric("최대 오차율", f"{site_analysis['billing_error_pct'].max():.2f}%")
            with col_s4:
                st.metric("최소 오차율", f"{site_analysis['billing_error_pct'].min():.2f}%")
        
        st.markdown("---")
        
        st.markdown("---")
        
        # === 과대청구 국소 리스트 ===
        st.markdown(f'<h3 style="color: {PYLON_ORANGE};">⚠️ 과대청구 국소 리스트 ({str(selected_month)[:4]}년 {str(selected_month)[4:6]}월)</h3>', unsafe_allow_html=True)
        
        # 검토/점검 상태 초기화 (session_state)
        if 'site_review_status' not in st.session_state:
            st.session_state['site_review_status'] = {}
        
        # 과대청구 국소만 필터링 (site_analysis에서 이미 계산됨)
        overcharged_list = site_analysis[site_analysis['billing_status'] == '과대청구'].copy()
        
        if len(overcharged_list) > 0:
            # site_master 정보 추가
            overcharged_list = overcharged_list.merge(
                site_master[['site_id', 'site_type', 'site_name', 'voltage']],
                on='site_id',
                how='left'
            )
            
            # 실사용 전력량 기반 추정 청구 요금 계산
            overcharged_list['estimated_cost'] = overcharged_list['kwh_actual'] * avg_unit_cost
            
            # 과대청구 금액 계산 (추정청구요금 - 실제청구요금)
            # 음수 = 실제 청구가 더 많음 (과대청구)
            overcharged_list['overcharge_amount'] = overcharged_list['estimated_cost'] - overcharged_list['cost_bill']
            
            # 과대청구 금액의 절댓값이 큰 순으로 정렬 (실제로는 음수이므로 ascending=True)
            overcharged_list = overcharged_list.sort_values('overcharge_amount', ascending=True)
            
            # 검토/점검 상태 추가
            def get_review_status(site_id):
                status = st.session_state['site_review_status'].get(site_id, {})
                reviewed = "✅" if status.get('reviewed', False) else "❌"
                inspected = "✅" if status.get('inspected', False) else "❌"
                return reviewed, inspected
            
            overcharged_list['review_status'] = overcharged_list['site_id'].apply(
                lambda x: get_review_status(x)[0]
            )
            overcharged_list['inspection_status'] = overcharged_list['site_id'].apply(
                lambda x: get_review_status(x)[1]
            )
            
            # 표시할 컬럼 선택
            display_cols = [
                'site_id', 'site_name', 'region', 'site_type', 'contract_type', 
                'kwh_bill', 'kwh_actual', 'cost_bill', 'estimated_cost', 
                'overcharge_amount', 'billing_error_pct', 'review_status', 'inspection_status'
            ]
            available_cols = [col for col in display_cols if col in overcharged_list.columns]
            
            overcharged_display = overcharged_list[available_cols].copy()
            
            # 컬럼명 한글화
            column_rename = {
                'site_id': '국소ID',
                'site_name': '국소명',
                'region': '지역',
                'site_type': '설비유형',
                'contract_type': '계약유형',
                'kwh_bill': '청구서 전력량(kWh)',
                'kwh_actual': '실사용 전력량(kWh)',
                'cost_bill': '청구 요금(원)',
                'estimated_cost': '추정 요금(원)',
                'overcharge_amount': '과대청구 금액(원)',
                'billing_error_pct': '과대청구율(%)',
                'review_status': '검토',
                'inspection_status': '점검'
            }
            overcharged_display.rename(columns=column_rename, inplace=True)
            
            # 요약 정보
            total_overcharge = abs(overcharged_list['overcharge_amount'].sum())
            avg_overcharge = abs(overcharged_list['overcharge_amount'].mean())
            max_overcharge = abs(overcharged_list['overcharge_amount'].min())  # min이 가장 큰 음수
            
            # 검토/점검 통계
            reviewed_count = sum(1 for site_id in overcharged_list['site_id'] 
                                if st.session_state['site_review_status'].get(site_id, {}).get('reviewed', False))
            inspected_count = sum(1 for site_id in overcharged_list['site_id'] 
                                 if st.session_state['site_review_status'].get(site_id, {}).get('inspected', False))
            
            st.markdown(f"""
            **📊 과대청구 국소 현황**
            - 총 **{len(overcharged_list)}개 국소**에서 과대청구 발생 (청구서가 실사용량보다 5% 이상 많음)
            - 총 과대청구 금액: **₩{total_overcharge:,.0f}** (실사용 기준 추정 대비)
            - 평균 과대청구 금액: **₩{avg_overcharge:,.0f}** / 최대: **₩{max_overcharge:,.0f}**
            - 평균 과대청구율: **{overcharged_list['billing_error_pct'].mean():.2f}%** / 최대: **{overcharged_list['billing_error_pct'].max():.2f}%**
            
            **✅ 작업 진행 현황**
            - 검토 완료: **{reviewed_count}개** / {len(overcharged_list)}개 ({reviewed_count/len(overcharged_list)*100:.1f}%)
            - 점검 완료: **{inspected_count}개** / {len(overcharged_list)}개 ({inspected_count/len(overcharged_list)*100:.1f}%)
            
            ⚠️ **정렬 기준**: 과대청구 금액이 큰 순서로 표시 (금액 영향도 기준)
            """)
            
            st.markdown("---")
            
            # 상위 20개만 표시 옵션
            show_all = st.checkbox("전체 국소 표시", value=False, key="show_all_overcharged")
            
            if show_all:
                display_df = overcharged_display
                st.markdown(f"**전체 {len(display_df)}개 과대청구 국소** (과대청구 금액 큰 순)")
            else:
                display_df = overcharged_display.head(20)
                st.markdown(f"**상위 20개 과대청구 국소** (과대청구 금액 큰 순)")
            
            # 데이터 테이블 표시
            st.dataframe(
                display_df.style.format({
                    '청구서 전력량(kWh)': '{:,.0f}',
                    '실사용 전력량(kWh)': '{:,.0f}',
                    '청구 요금(원)': '₩{:,.0f}',
                    '추정 요금(원)': '₩{:,.0f}',
                    '과대청구 금액(원)': '₩{:,.0f}',
                    '과대청구율(%)': '{:+.2f}'
                }),
                use_container_width=True,
                hide_index=True,
                height=600
            )
            
            # CSV 다운로드 버튼
            st.markdown("---")
            csv = overcharged_display.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 과대청구 국소 리스트 다운로드 (CSV)",
                data=csv,
                file_name=f"과대청구_국소_{str(selected_month)}.csv",
                mime="text/csv",
                key="download_overcharged_csv"
            )
            
            # === 국소 상세보기 ===
            st.markdown("---")
            st.markdown("### 🔍 국소 상세보기")
            
            col_select1, col_select2 = st.columns([2, 1])
            
            with col_select1:
                # 국소 선택 (국소ID + 국소명 형식)
                site_options = overcharged_list.apply(
                    lambda row: f"{row['site_id']} - {row['site_name']} ({row['region']})", 
                    axis=1
                ).tolist()
                site_ids = overcharged_list['site_id'].tolist()
                
                selected_site_display = st.selectbox(
                    "상세 정보를 볼 국소를 선택하세요",
                    options=site_options,
                    key="site_detail_selector"
                )
                
                # 선택된 국소 ID 추출
                selected_site_id = site_ids[site_options.index(selected_site_display)]
            
            with col_select2:
                st.metric("선택된 국소", selected_site_id)
            
            # 선택된 국소의 상세 정보
            if selected_site_id:
                site_detail = overcharged_list[overcharged_list['site_id'] == selected_site_id].iloc[0]
                
                st.markdown("---")
                
                # 지도와 기본 정보를 나란히 표시
                col_map, col_info = st.columns([1, 1])
                
                with col_map:
                    st.markdown("**🗺️ 위치 정보**")
                    
                    # 국소의 좌표 정보 가져오기
                    site_master_detail = site_master[site_master['site_id'] == selected_site_id].iloc[0]
                    
                    if 'latitude' in site_master_detail and 'longitude' in site_master_detail:
                        # 지도 데이터 준비
                        map_data = pd.DataFrame({
                            'lat': [site_master_detail['latitude']],
                            'lon': [site_master_detail['longitude']]
                        })
                        
                        # 지도 표시
                        st.map(map_data, zoom=13, use_container_width=True)
                        
                        # 주소 정보
                        if 'address' in site_master_detail:
                            st.info(f"📍 **주소**: {site_master_detail['address']}")
                            st.caption(f"위도: {site_master_detail['latitude']:.6f}, 경도: {site_master_detail['longitude']:.6f}")
                    else:
                        st.info("위치 정보가 없습니다.")
                
                with col_info:
                    st.markdown("**📍 기본 정보**")
                    st.write(f"**국소ID**: {site_detail['site_id']}")
                    st.write(f"**국소명**: {site_detail['site_name']}")
                    st.write(f"**지역**: {site_detail['region']}")
                    st.write(f"**설비유형**: {site_detail['site_type']}")
                    st.write(f"**전압**: {site_master_detail.get('voltage', 'N/A')}")
                    
                    st.markdown("**📋 계약 정보**")
                    st.write(f"**계약유형**: {site_detail['contract_type']}")
                    st.write(f"**계약대상**: {site_detail['contract_target']}")
                    st.write(f"**세대**: {site_detail['network_gen']}")
                    st.write(f"**RAPA**: {site_detail['rapa_type']}")
                
                st.markdown("---")
                
                # 전력 및 요금 정보
                col_d3, col_d4 = st.columns(2)
                
                with col_d3:
                    st.markdown("**⚡ 전력 정보**")
                    st.metric("청구서 전력량", f"{site_detail['kwh_bill']:,.0f} kWh")
                    st.metric("실사용 전력량", f"{site_detail['kwh_actual']:,.0f} kWh")
                
                with col_d4:
                    st.markdown("**💰 요금 정보**")
                    st.metric("청구 요금", f"₩{site_detail['cost_bill']:,.0f}")
                    st.metric("추정 요금", f"₩{site_detail['estimated_cost']:,.0f}")
                
                # 검토/점검 상태 관리
                st.markdown("---")
                st.markdown("#### ✏️ 검토 및 점검 관리")
                
                # 현재 국소의 상태 가져오기
                current_status = st.session_state['site_review_status'].get(
                    selected_site_id, 
                    {'reviewed': False, 'inspected': False, 'reviewer': '', 'inspector': '', 
                     'review_date': '', 'inspection_date': '', 'notes': ''}
                )
                
                col_check1, col_check2 = st.columns(2)
                
                with col_check1:
                    st.markdown("**📋 검토 상태**")
                    reviewed = st.checkbox(
                        "검토 완료",
                        value=current_status['reviewed'],
                        key=f"reviewed_{selected_site_id}"
                    )
                    
                    if reviewed:
                        reviewer = st.text_input(
                            "검토자",
                            value=current_status.get('reviewer', ''),
                            key=f"reviewer_{selected_site_id}"
                        )
                        # 날짜 안전 처리
                        try:
                            default_date = pd.to_datetime(current_status.get('review_date')) if current_status.get('review_date') else pd.Timestamp.now()
                        except:
                            default_date = pd.Timestamp.now()
                        
                        review_date = st.date_input(
                            "검토 일자",
                            value=default_date,
                            key=f"review_date_{selected_site_id}"
                        )
                    else:
                        reviewer = ''
                        review_date = ''
                
                with col_check2:
                    st.markdown("**🔧 점검 상태**")
                    inspected = st.checkbox(
                        "점검 완료",
                        value=current_status['inspected'],
                        key=f"inspected_{selected_site_id}"
                    )
                    
                    if inspected:
                        inspector = st.text_input(
                            "점검자",
                            value=current_status.get('inspector', ''),
                            key=f"inspector_{selected_site_id}"
                        )
                        # 날짜 안전 처리
                        try:
                            default_date = pd.to_datetime(current_status.get('inspection_date')) if current_status.get('inspection_date') else pd.Timestamp.now()
                        except:
                            default_date = pd.Timestamp.now()
                        
                        inspection_date = st.date_input(
                            "점검 일자",
                            value=default_date,
                            key=f"inspection_date_{selected_site_id}"
                        )
                    else:
                        inspector = ''
                        inspection_date = ''
                
                # 메모
                notes = st.text_area(
                    "특이사항 메모",
                    value=current_status.get('notes', ''),
                    height=100,
                    key=f"notes_{selected_site_id}",
                    help="과대청구 원인, 조치 내용 등을 기록하세요"
                )
                
                # 저장 버튼
                col_btn1, col_btn2 = st.columns([1, 3])
                with col_btn1:
                    if st.button("💾 저장", key=f"save_status_{selected_site_id}", type="primary"):
                        st.session_state['site_review_status'][selected_site_id] = {
                            'reviewed': reviewed,
                            'inspected': inspected,
                            'reviewer': reviewer if reviewed else '',
                            'inspector': inspector if inspected else '',
                            'review_date': str(review_date) if reviewed else '',
                            'inspection_date': str(inspection_date) if inspected else '',
                            'notes': notes
                        }
                        st.success("✅ 저장되었습니다!")
                        st.rerun()
                
                # 저장된 정보 표시
                if current_status['reviewed'] or current_status['inspected']:
                    st.markdown("---")
                    st.markdown("**📝 저장된 정보**")
                    
                    info_cols = st.columns(2)
                    with info_cols[0]:
                        if current_status['reviewed']:
                            st.info(f"✅ **검토 완료**\n- 검토자: {current_status.get('reviewer', 'N/A')}\n- 일자: {current_status.get('review_date', 'N/A')}")
                    
                    with info_cols[1]:
                        if current_status['inspected']:
                            st.info(f"✅ **점검 완료**\n- 점검자: {current_status.get('inspector', 'N/A')}\n- 일자: {current_status.get('inspection_date', 'N/A')}")
                    
                    if current_status.get('notes'):
                        st.warning(f"📝 **메모**: {current_status['notes']}")
                
                # 과대청구 상세 분석
                st.markdown("---")
                st.markdown("#### 📊 과대청구 상세 분석")
                
                col_a1, col_a2, col_a3 = st.columns(3)
                
                with col_a1:
                    st.metric(
                        "과대청구 금액",
                        f"₩{abs(site_detail['overcharge_amount']):,.0f}",
                        help="실제 청구 요금 - 실사용 기반 추정 요금"
                    )
                
                with col_a2:
                    st.metric(
                        "과대청구율",
                        f"{site_detail['billing_error_pct']:.2f}%",
                        help="(청구서 - 실사용) / 실사용 × 100"
                    )
                
                with col_a3:
                    # 평균 대비 차이
                    avg_error = overcharged_list['billing_error_pct'].mean()
                    diff_from_avg = site_detail['billing_error_pct'] - avg_error
                    st.metric(
                        "평균 대비",
                        f"{diff_from_avg:+.2f}%p",
                        help=f"전체 평균 과대청구율: {avg_error:.2f}%"
                    )
                
                # 월별 추이 (해당 국소의 최근 6개월 데이터)
                st.markdown("---")
                st.markdown("#### 📈 최근 6개월 추이")
                
                # 해당 국소의 최근 6개월 데이터 가져오기
                site_history = bills_df[bills_df['site_id'] == selected_site_id].sort_values('yymm', ascending=False).head(6)
                site_history = site_history.sort_values('yymm')  # 오름차순으로 다시 정렬
                
                if len(site_history) > 0:
                    # actual 데이터도 가져오기
                    site_history_actual = actual_df[actual_df['site_id'] == selected_site_id]
                    site_history = site_history.merge(
                        site_history_actual[['yymm', 'site_id', 'kwh_actual']],
                        on=['yymm', 'site_id'],
                        how='left'
                    )
                    
                    # 추정 요금 계산
                    site_history['estimated_cost'] = site_history['kwh_actual'] * avg_unit_cost
                    site_history['overcharge_amount'] = site_history['cost_bill'] - site_history['estimated_cost']
                    
                    # x축 레이블 생성 (안전하게 처리)
                    def format_yymm(yymm):
                        yymm_str = str(int(yymm))  # 정수로 변환 후 문자열로
                        if len(yymm_str) == 6:
                            return f"{yymm_str[:4]}.{yymm_str[4:6]}"
                        return yymm_str
                    
                    site_history['month_label'] = site_history['yymm'].apply(format_yymm)
                    
                    # 차트 생성
                    fig_trend = go.Figure()
                    
                    # 청구서 전력량
                    fig_trend.add_trace(go.Scatter(
                        x=site_history['month_label'],
                        y=site_history['kwh_bill'],
                        name='청구서 전력량',
                        mode='lines+markers',
                        line=dict(color=PYLON_BLUE, width=2),
                        marker=dict(size=8)
                    ))
                    
                    # 실사용 전력량
                    fig_trend.add_trace(go.Scatter(
                        x=site_history['month_label'],
                        y=site_history['kwh_actual'],
                        name='실사용 전력량',
                        mode='lines+markers',
                        line=dict(color=PYLON_ORANGE, width=2),
                        marker=dict(size=8)
                    ))
                    
                    fig_trend.update_layout(
                        title=f'{selected_site_id} 전력량 추이',
                        xaxis_title='월',
                        yaxis_title='전력량 (kWh)',
                        height=400,
                        hovermode='x unified',
                        xaxis=dict(type='category')  # 카테고리 타입으로 명시
                    )
                    
                    st.plotly_chart(fig_trend, use_container_width=True)
                    
                    # 요금 추이
                    fig_cost = go.Figure()
                    
                    fig_cost.add_trace(go.Bar(
                        x=site_history['month_label'],
                        y=site_history['cost_bill'],
                        name='청구 요금',
                        marker_color=PYLON_BLUE
                    ))
                    
                    fig_cost.add_trace(go.Bar(
                        x=site_history['month_label'],
                        y=site_history['estimated_cost'],
                        name='추정 요금',
                        marker_color=PYLON_ORANGE
                    ))
                    
                    fig_cost.update_layout(
                        title=f'{selected_site_id} 요금 추이',
                        xaxis_title='월',
                        yaxis_title='요금 (원)',
                        barmode='group',
                        height=400,
                        hovermode='x unified',
                        xaxis=dict(type='category')  # 카테고리 타입으로 명시
                    )
                    
                    st.plotly_chart(fig_cost, use_container_width=True)
                    
                    # 데이터 테이블
                    with st.expander("📊 상세 데이터 보기"):
                        history_display = site_history[['yymm', 'kwh_bill', 'kwh_actual', 'cost_bill', 'estimated_cost', 'overcharge_amount']].copy()
                        history_display['yymm'] = history_display['yymm'].apply(format_yymm)
                        history_display.columns = ['월', '청구서(kWh)', '실사용(kWh)', '청구요금(원)', '추정요금(원)', '과대청구금액(원)']
                        st.dataframe(history_display, use_container_width=True, hide_index=True)
                else:
                    st.info("최근 6개월 데이터가 없습니다.")
            
            st.markdown("---")
        else:
            st.success("✅ 과대청구 국소가 없습니다.")

# Footer with PYLON branding
st.markdown(create_footer(), unsafe_allow_html=True)

