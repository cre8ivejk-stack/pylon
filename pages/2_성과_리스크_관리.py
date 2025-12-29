"""Performance & Risk Control page."""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import sys
import os

# Add parent directory to path (Streamlit Cloud compatibility)
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from src.data_access import DataAccessLayer
from src.analytics import calculate_risk_score, calculate_bill_actual_error
from src.actions import ActionManager
from src.verified_savings import VerifiedSavingsManager
from src.project_master import ProjectMasterManager
from src.models import GovernanceBadge, ActionCategory, ValidationState
from src.config_loader import load_governance_config
from components.global_controls import render_sidebar_filters, render_governance_badges, apply_filters, render_filter_summary
from components.widget_card import render_widget_card, render_simple_metric_card
from components.action_inbox import render_compact_action_inbox
from config.tasks import get_domains, get_tasks_by_domain
from styles import (
    PYLON_BLUE, PYLON_GREEN, PYLON_ORANGE, PYLON_RED,
    apply_page_style, create_footer
)

# Page config
st.set_page_config(page_title="성과 & 리스크 관리 | PYLON", layout="wide", page_icon="📊")

# Apply PYLON brand colors
st.markdown(apply_page_style(), unsafe_allow_html=True)

# Initialize
data_dir = Path("data")
dal = DataAccessLayer(data_dir)
action_manager = ActionManager(data_dir)
verified_savings_manager = VerifiedSavingsManager(data_dir)
project_master_manager = ProjectMasterManager(data_dir)
gov_config = load_governance_config()

# Header with brand color
st.markdown(f'<h1 style="color: {PYLON_BLUE};">📊 PYLON - 성과 & 리스크 관리</h1>', unsafe_allow_html=True)
st.markdown("과제 성과 및 리스크 모니터링")

# User and system status in sidebar
with st.sidebar:
    st.markdown("## 👤 사용자")
    if "current_user" not in st.session_state:
        st.session_state["current_user"] = "담당자"
    st.session_state["current_user"] = st.text_input(
        "담당자 이름", 
        st.session_state["current_user"],
        key="user_input_page2",
        help="조치 할당 및 작업함 필터링에 사용됩니다"
    )
    st.divider()
    
    st.markdown("## 🎛️ 시스템 상태")
    render_compact_action_inbox(action_manager, st.session_state["current_user"])
    st.divider()

# Load data
bills_df = dal.load_bills()
actual_df = dal.load_actual()
site_master = dal.load_site_master()

if len(bills_df) == 0:
    st.error("데이터를 로드할 수 없습니다.")
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
tab1, tab2 = st.tabs(["📈 과제 성과 관리", "⚠️ 전기요금 Risk Monitoring"])

with tab1:
    st.markdown("## 📈 과제별 성과 관리")
    
    # Load projects from master
    projects_df = project_master_manager.load_projects()
    
    # Three-tier savings display
    st.markdown("### 절감액 현황 (3단계)")
    
    # Calculate from projects
    expected_savings = projects_df[projects_df['status'] == '해야 할 일']['target_savings_krw'].sum()
    in_progress_savings = projects_df[projects_df['status'] == '진행 중']['actual_savings_krw'].sum()
    verified_total = projects_df['verified_savings_krw'].sum()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 💡 예상 절감")
        st.metric(
            label="계획/제안 단계",
            value=f"₩{expected_savings:,.0f}/월",
            help="계획 또는 제안된 절감 효과"
        )
    
    with col2:
        st.markdown("#### 🔄 진행 절감")
        st.metric(
            label="실행 중",
            value=f"₩{in_progress_savings:,.0f}/월",
            help="현재 실행 중인 과제의 예상 절감"
        )
    
    with col3:
        # Confirmed savings: GREEN for performance/success
        st.markdown(f'<h4 style="color: {PYLON_GREEN};">✅ 확정 절감</h4>', unsafe_allow_html=True)
        st.metric(
            label="검증 완료",
            value=f"₩{verified_total:,.0f}/월",
            help="검증 완료된 확정 절감액"
        )
    
    st.markdown("---")
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_target = projects_df['target_savings_krw'].sum()
        render_simple_metric_card("총 목표", f"₩{total_target:,.0f}/월")
    
    with col2:
        total_actual = projects_df['actual_savings_krw'].sum()
        render_simple_metric_card("총 실적", f"₩{total_actual:,.0f}/월")
    
    with col3:
        overall_achievement = (total_actual / total_target) * 100 if total_target > 0 else 0
        render_simple_metric_card("전체 달성률", f"{overall_achievement:.1f}%")
    
    st.markdown("---")
    
    # Project details by domain
    st.markdown("### 과제별 상세 (영역별)")
    
    st.info("💡 전략문서 #2 에너지 소모 절감 과제 체계와 연동됩니다.")
    
    # Domain tabs
    domains = get_domains()
    domain_tabs = st.tabs([f"📌 {domain}" for domain in domains])
    
    for domain_idx, domain in enumerate(domains):
        with domain_tabs[domain_idx]:
            domain_projects = projects_df[projects_df['domain'] == domain]
            
            if len(domain_projects) == 0:
                st.warning(f"{domain}에 등록된 과제가 없습니다.")
            else:
                # Get tasks from catalog
                domain_tasks = get_tasks_by_domain(domain)
                
                # Show task catalog
                st.markdown(f"**{domain} 전략 과제 목록:**")
                task_names = [f"`{task.task_name}`" for task in domain_tasks]
                st.markdown(" · ".join(task_names))
                
                st.markdown("---")
                
                # Display projects with action button
                for idx, project in domain_projects.iterrows():
                    with st.expander(f"{project['project_name']} ({project['status']})"):
                        col_info, col_action = st.columns([3, 1])
                        
                        with col_info:
                            col_a, col_b, col_c, col_d = st.columns(4)
                            
                            with col_a:
                                st.metric("목표 절감", f"₩{project['target_savings_krw']:,.0f}")
                            
                            with col_b:
                                st.metric("실적 절감", f"₩{project['actual_savings_krw']:,.0f}")
                            
                            with col_c:
                                st.metric("확정 절감", f"₩{project['verified_savings_krw']:,.0f}")
                            
                            with col_d:
                                achievement = (project['actual_savings_krw'] / project['target_savings_krw'] * 100) if project['target_savings_krw'] > 0 else 0
                                st.metric("달성률", f"{achievement:.1f}%")
                        
                        with col_action:
                            st.write("")
                            st.write("")
                            if st.button("📊 솔루션 실증 페이지로 이동", key=f"view_validation_{project['project_id']}", type="primary"):
                                # Set session state and navigate
                                st.session_state["selected_project_id"] = project['project_id']
                                st.session_state["selected_domain"] = project['domain']
                                st.switch_page("pages/4_검증_실증.py")
    
    st.markdown("---")
    
    # Add new project
    st.markdown("### 📊 공식 과제 등록")
    
    with st.form("add_project_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            new_domain = st.selectbox(
                "대분류",
                options=['억세스분야', '설비분야', 'Core/전송']
            )
        
        with col2:
            new_project_name = st.text_input(
                "과제명",
                placeholder="예: AI 기반 냉방 제어"
            )
        
        with col3:
            new_target_savings = st.number_input(
                "목표 절감액 (원/월)",
                min_value=0,
                value=0,
                step=1_000_000
            )
        
        submitted = st.form_submit_button("📊 공식 과제 등록", type="primary")
        
        if submitted:
            if not new_project_name:
                st.error("과제명을 입력해주세요.")
            else:
                new_id = project_master_manager.add_project(
                    project_name=new_project_name,
                    domain=new_domain,
                    target_savings_krw=new_target_savings
                )
                st.success(f"✅ 공식 과제 등록 완료: {new_id}")
                st.rerun()
    
    st.markdown("---")
    
    # Achievement chart by domain
    st.markdown("### 영역별 성과")
    
    domain_summary = projects_df.groupby('domain').agg({
        'target_savings_krw': 'sum',
        'actual_savings_krw': 'sum',
        'verified_savings_krw': 'sum'
    }).reset_index()
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=domain_summary['domain'],
        y=domain_summary['target_savings_krw'],
        name='목표 절감',
        marker_color='lightblue'
    ))
    
    fig.add_trace(go.Bar(
        x=domain_summary['domain'],
        y=domain_summary['actual_savings_krw'],
        name='실적 절감',
        marker_color='darkblue'
    ))
    
    fig.add_trace(go.Bar(
        x=domain_summary['domain'],
        y=domain_summary['verified_savings_krw'],
        name='확정 절감',
        marker_color='green'
    ))
    
    fig.update_layout(
        title='영역별 과제 성과',
        xaxis_title='영역',
        yaxis_title='절감액 (원/월)',
        barmode='group'
    )
    
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("## ⚠️ 전기요금 Risk Monitoring")
    
    # Merge bills with actual
    merged = filtered_bills.merge(
        actual_df,
        on=['yymm', 'site_id'],
        how='left'
    )
    
    if len(merged) == 0:
        st.warning("리스크 분석을 위한 데이터가 부족합니다.")
    else:
        # Calculate risk scores
        merged['impact'] = abs(merged['cost_actual_est'].fillna(merged['cost_bill']) - merged['cost_bill'])
        
        # Calculate likelihood based on error history
        site_error_history = []
        for site_id in merged['site_id'].unique():
            site_data = bills_df[bills_df['site_id'] == site_id].merge(
                actual_df[actual_df['site_id'] == site_id],
                on=['yymm', 'site_id'],
                how='left'
            )
            
            if len(site_data) > 0:
                # Count anomalies (error > 20%)
                site_data['error_pct'] = abs(
                    calculate_bill_actual_error(
                        site_data['kwh_actual'].fillna(site_data['kwh_bill']),
                        site_data['kwh_bill']
                    )
                )
                anomaly_count = (site_data['error_pct'] > 20).sum()
                likelihood = min(anomaly_count / len(site_data), 1.0)
            else:
                likelihood = 0.5
            
            site_error_history.append({
                'site_id': site_id,
                'likelihood': likelihood
            })
        
        likelihood_df = pd.DataFrame(site_error_history)
        merged = merged.merge(likelihood_df, on='site_id', how='left')
        merged['likelihood'] = merged['likelihood'].fillna(0.5)
        merged['confidence'] = merged['confidence'].fillna(0.7)
        
        # Calculate risk score
        risk_scores = merged.apply(
            lambda row: calculate_risk_score(row['impact'], row['likelihood'], row['confidence']),
            axis=1
        )
        merged['risk_score_raw'] = risk_scores.apply(lambda x: x['raw_score'])
        merged['risk_score_display'] = risk_scores.apply(lambda x: x['display_score'])
        
        # Risk summary (using display score for classification)
        st.markdown("### 리스크 요약")
        
        high_risk = len(merged[merged['risk_score_display'] > 70])
        medium_risk = len(merged[(merged['risk_score_display'] > 40) & (merged['risk_score_display'] <= 70)])
        low_risk = len(merged[merged['risk_score_display'] <= 40])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            render_simple_metric_card("총 리스크", f"{len(merged)}건")
        
        with col2:
            render_simple_metric_card("🔴 High", f"{high_risk}건")
        
        with col3:
            render_simple_metric_card("🟡 Medium", f"{medium_risk}건")
        
        with col4:
            render_simple_metric_card("🟢 Low", f"{low_risk}건")
        
        st.markdown("---")
        
        # Risk distribution
        st.markdown("### 리스크 분포")
        
        fig_risk_dist = px.histogram(
            merged,
            x='risk_score_display',
            nbins=30,
            title='리스크 점수 분포 (0~100)',
            labels={'risk_score_display': '리스크 점수'}
        )
        
        st.plotly_chart(fig_risk_dist, use_container_width=True)
        
        # High risk sites
        # High Risk: RED for critical attention
        st.markdown(f'<h3 style="color: {PYLON_RED};">🔴 High Risk 국소</h3>', unsafe_allow_html=True)
        
        high_risk_sites = merged[merged['risk_score_display'] > 70].copy()
        
        if len(high_risk_sites) > 0:
            high_risk_display = high_risk_sites[[
                'site_id', 'region', 'contract_type', 'cost_bill', 'impact', 'likelihood', 'confidence', 
                'risk_score_raw', 'risk_score_display'
            ]].sort_values('risk_score_raw', ascending=False).head(20)
            
            # Rename columns to Korean
            high_risk_display.columns = [
                '국소ID', '지역', '계약유형', '청구금액(원)', '영향도(원)', 
                '발생가능성', '신뢰도', '리스크점수(원기반)', '리스크점수(0~100)'
            ]
            
            # Widget card for action creation
            render_widget_card(
                title="High Risk 국소 모니터링",
                value=f"{len(high_risk_sites)} 건",
                metric_label="High Risk 국소 수",
                validation_state=ValidationState.IN_FLIGHT,
                evidence_table=high_risk_display,
                action_manager=action_manager,
                action_category=ActionCategory.ANOMALY_INVESTIGATION,
                action_description_template=f"High Risk 국소 조사 및 조치 ({len(high_risk_sites)}개 국소)",
                site_ids=high_risk_sites['site_id'].tolist()
            )
        else:
            st.success("✅ High Risk 국소가 없습니다.")
        
        st.markdown("---")
        
        # Risk heatmap by region and contract type
        st.markdown("### 리스크 히트맵 (지역 x 계약유형)")
        
        risk_pivot = merged.groupby(['region', 'contract_type'])['risk_score_display'].mean().reset_index()
        risk_pivot_table = risk_pivot.pivot(index='region', columns='contract_type', values='risk_score_display')
        
        fig_heatmap = px.imshow(
            risk_pivot_table,
            title='평균 리스크 점수 (지역 x 계약유형)',
            labels=dict(x="계약유형", y="지역", color="리스크 점수"),
            color_continuous_scale='RdYlGn_r'
        )
        
        st.plotly_chart(fig_heatmap, use_container_width=True)

# Footer with PYLON branding
st.markdown(create_footer(), unsafe_allow_html=True)

