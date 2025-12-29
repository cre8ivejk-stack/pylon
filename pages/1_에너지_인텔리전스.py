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

# Global filters (sidebar)
available_yymm = sorted(bills_df['yymm'].unique().tolist())
filters = render_sidebar_filters(available_yymm)

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
    
    # Merge bills and actual with explicit suffixes
    merged_bill_actual = filtered_bills.merge(
        actual_df,
        on=['yymm', 'site_id'],
        how='left',
        suffixes=('', '_actual')
    )
    
    if len(merged_bill_actual) == 0:
        st.warning("Bill vs Actual 비교 데이터가 없습니다.")
    else:
        # Calculate error
        merged_bill_actual['error_pct'] = merged_bill_actual.apply(
            lambda row: calculate_bill_actual_error(row.get('kwh_actual', 0), row.get('kwh_bill', 0)),
            axis=1
        )
        
        # Classify mismatch
        merged_bill_actual['mismatch_class'] = merged_bill_actual.apply(
            classify_bill_actual_mismatch,
            axis=1
        )
        
        # Distribution chart
        st.markdown("### 오차 분포")
        
        fig_dist = px.histogram(
            merged_bill_actual[merged_bill_actual['error_pct'].notna()],
            x='error_pct',
            nbins=50,
            title='Distribution of Bill vs Actual Error (%)',
            labels={'error_pct': 'Error (%)'}
        )
        
        st.plotly_chart(fig_dist, use_container_width=True)
        
        # Classification summary
        st.markdown("### 분류별 현황")
        
        class_summary = merged_bill_actual['mismatch_class'].value_counts().reset_index()
        class_summary.columns = ['분류', '건수']
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.dataframe(class_summary, use_container_width=True, hide_index=True)
        
        with col2:
            fig_pie = px.pie(
                class_summary,
                names='분류',
                values='건수',
                title='Mismatch Classification'
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Problem sites requiring action - ORANGE for attention needed
        st.markdown(f'<h3 style="color: {PYLON_ORANGE};">⚠️ 조사 필요 국소</h3>', unsafe_allow_html=True)
        
        problem_sites = merged_bill_actual[
            merged_bill_actual['mismatch_class'].isin(['조사 필요', '긴급 조사'])
        ].copy()
        
        if len(problem_sites) > 0:
            # Select available columns (region comes from filtered_bills)
            display_cols = ['site_id', 'region', 'contract_type', 'kwh_bill', 'kwh_actual', 'error_pct', 'mismatch_class']
            available_cols = [col for col in display_cols if col in problem_sites.columns]
            
            problem_display = problem_sites[available_cols].sort_values('error_pct', key=abs, ascending=False).head(20)
            
            # Widget card for action creation
            render_widget_card(
                title="Bill vs Actual 불일치 국소",
                value=f"{len(problem_sites)} 건",
                metric_label="조사 필요 국소 수",
                validation_state=ValidationState.IN_FLIGHT,
                evidence_table=problem_display,
                action_manager=action_manager,
                action_category=ActionCategory.BILL_ACTUAL_MISMATCH,
                action_description_template=f"Bill vs Actual 오차 조사 필요 ({len(problem_sites)}개 국소)",
                site_ids=problem_sites['site_id'].tolist()
            )
        else:
            st.success("✅ 조사가 필요한 국소가 없습니다.")

# Footer with PYLON branding
st.markdown(create_footer(), unsafe_allow_html=True)

