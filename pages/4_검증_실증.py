"""검증 및 실증(IDEA) 페이지"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path (Streamlit Cloud compatibility)
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from src.data_access import DataAccessLayer
from src.experiments import ExperimentManager
from src.actions import ActionManager
from src.verified_savings import VerifiedSavingsManager
from src.project_master import ProjectMasterManager
from src.models import GovernanceBadge, ActionCategory, ValidationState
from src.config_loader import load_governance_config
from components.global_controls import render_governance_badges
from components.widget_card import render_simple_metric_card
from components.action_inbox import render_compact_action_inbox
# PROBE is now available as a dedicated page (pages/0_PYLON_PROBE.py)
from styles import (
    PYLON_BLUE, PYLON_GREEN,
    apply_page_style, create_footer
)

# Page config
st.set_page_config(page_title="검증 & 실증 | PYLON", layout="wide", page_icon="🔬")

# Apply PYLON brand colors
st.markdown(apply_page_style(), unsafe_allow_html=True)

# Initialize
data_dir = Path("data")
dal = DataAccessLayer(data_dir)
action_manager = ActionManager(data_dir)
experiment_manager = ExperimentManager(data_dir)
verified_savings_manager = VerifiedSavingsManager(data_dir)
project_master_manager = ProjectMasterManager(data_dir)
gov_config = load_governance_config()

# Header with brand color
st.markdown(f'<h1 style="color: {PYLON_BLUE};">🔬 PYLON - 솔루션 실증 & 검증</h1>', unsafe_allow_html=True)
st.markdown("과제별 효과검증 및 에너지 절감 솔루션의 실증 실험 관리")

# User and system status in sidebar
with st.sidebar:
    st.markdown("## 👤 사용자")
    if "current_user" not in st.session_state:
        st.session_state["current_user"] = "담당자"
    st.session_state["current_user"] = st.text_input(
        "담당자 이름", 
        st.session_state["current_user"],
        key="user_input_page4",
        help="조치 할당 및 작업함 필터링에 사용됩니다"
    )
    st.divider()
    
    st.markdown("## 🎛️ 시스템 상태")
    render_compact_action_inbox(action_manager, st.session_state["current_user"])
    st.divider()

# Load data
bills_df = dal.load_bills()
traffic_df = dal.load_traffic()
site_master = dal.load_site_master()

if len(bills_df) == 0:
    st.error("데이터를 로드할 수 없습니다.")
    st.stop()

# Governance badges with auto-computed freshness
latest_yymm = bills_df['yymm'].max() if len(bills_df) > 0 else None
governance_badge = GovernanceBadge.create_from_config_and_data(gov_config, latest_yymm)
render_governance_badges(governance_badge)

st.markdown("---")

# 솔루션 실증 (IDEA)
st.markdown("## 🧪 솔루션 실증 - 과제별 효과검증")

st.info("""
💡 **성과관리**에서 선택한 과제의 효과를 검증하고, 확정 절감액으로 반영합니다.

- 억세스분야: LTE Mod., 3G Fade-Out, SA, Power Saving 등
- 설비분야: 노후냉방기 대체, 외기냉방, 필름형태양광, 온도상향 등
- Core/전송: F/H Zero Power化, Server Power Saving 등
""")

# Load projects
projects_df = project_master_manager.load_projects()

# Check if navigated from 성과 관리 with selected project
if "selected_project_id" in st.session_state and st.session_state["selected_project_id"]:
    default_project_id = st.session_state["selected_project_id"]
    default_domain = st.session_state.get("selected_domain", None)
    # Clear after use
    st.session_state["selected_project_id"] = None
    if "selected_domain" in st.session_state:
        st.session_state["selected_domain"] = None
else:
    default_project_id = None
    default_domain = None

# Filters
st.markdown("### 필터")

col_filter1, col_filter2 = st.columns(2)

with col_filter1:
    # Domain filter
    domain_options = ['전체', '억세스분야', '설비분야', 'Core/전송']
    
    # Find default domain index
    if default_domain and default_domain in domain_options:
        default_domain_index = domain_options.index(default_domain)
    else:
        default_domain_index = 0
    
    selected_domain = st.selectbox(
        "영역 선택",
        options=domain_options,
        index=default_domain_index,
        key="domain_filter_validation"
    )

with col_filter2:
    # Filter projects by domain
    if selected_domain == '전체':
        filtered_projects = projects_df
    else:
        filtered_projects = projects_df[projects_df['domain'] == selected_domain]
    
    # Project selection filter
    project_options = ['전체'] + filtered_projects['project_id'].tolist()
    project_labels = ['전체'] + [f"{row['domain']} - {row['project_name']}" for _, row in filtered_projects.iterrows()]
    project_label_map = dict(zip(project_options, project_labels))
    
    # Find default index
    if default_project_id and default_project_id in project_options:
        default_index = project_options.index(default_project_id)
    else:
        default_index = 0
    
    selected_project = st.selectbox(
        "과제 선택",
        options=project_options,
        format_func=lambda x: project_label_map[x],
        index=default_index,
        key="project_filter_validation"
    )

st.markdown("---")

# If specific project selected, show validation section
if selected_project != '전체':
    project_data = projects_df[projects_df['project_id'] == selected_project].iloc[0]
    
    st.markdown(f"## 📊 {project_data['project_name']} - 효과검증")
    
    # Summary KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("목표 절감", f"₩{project_data['target_savings_krw']:,.0f}/월")
    
    with col2:
        st.metric("실적 절감", f"₩{project_data['actual_savings_krw']:,.0f}/월")
    
    with col3:
        st.metric("확정 절감", f"₩{project_data['verified_savings_krw']:,.0f}/월")
    
    with col4:
        achievement = (project_data['actual_savings_krw'] / project_data['target_savings_krw'] * 100) if project_data['target_savings_krw'] > 0 else 0
        st.metric("달성률", f"{achievement:.1f}%")
    
    st.markdown("---")
    
    # Before/After comparison (sample data for demonstration)
    st.markdown("### 전 / 후 비교")
    
    col_config1, col_config2 = st.columns(2)
    
    with col_config1:
        comparison_months = st.number_input(
            "비교 개월 수",
            min_value=1,
            max_value=6,
            value=3,
            key="validation_comparison_months"
        )
    
    with col_config2:
        baseline_month = st.selectbox(
            "기준월 (적용 전)",
            options=sorted(bills_df['yymm'].unique(), reverse=True),
            index=6 if len(bills_df['yymm'].unique()) > 6 else 0,
            key="validation_baseline_month"
        )
    
    # Sample before/after data
    months_sorted = sorted(bills_df['yymm'].unique())
    if baseline_month in months_sorted:
        baseline_idx = months_sorted.index(baseline_month)
        
        before_months = months_sorted[max(0, baseline_idx - comparison_months):baseline_idx]
        after_months = months_sorted[baseline_idx:min(len(months_sorted), baseline_idx + comparison_months)]
        
        if len(before_months) > 0 and len(after_months) > 0:
            # Calculate sample savings (random subset for demo)
            np.random.seed(hash(selected_project) % 2**32)
            sample_sites = np.random.choice(bills_df['site_id'].unique(), size=min(30, len(bills_df['site_id'].unique())), replace=False)
            
            before_bills = bills_df[bills_df['yymm'].isin(before_months) & bills_df['site_id'].isin(sample_sites)]
            after_bills = bills_df[bills_df['yymm'].isin(after_months) & bills_df['site_id'].isin(sample_sites)]
            
            before_avg_kwh = before_bills['kwh_bill'].sum() / len(before_months) if len(before_months) > 0 else 0
            after_avg_kwh = after_bills['kwh_bill'].sum() / len(after_months) if len(after_months) > 0 else 0
            
            before_avg_cost = before_bills['cost_bill'].sum() / len(before_months) if len(before_months) > 0 else 0
            after_avg_cost = after_bills['cost_bill'].sum() / len(after_months) if len(after_months) > 0 else 0
            
            kwh_reduction = before_avg_kwh - after_avg_kwh
            cost_reduction = before_avg_cost - after_avg_cost
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.metric(
                    "전력량 절감",
                    f"{kwh_reduction:,.0f} kWh/월",
                    delta=f"{(kwh_reduction / before_avg_kwh * 100) if before_avg_kwh > 0 else 0:.1f}%"
                )
            
            with col_b:
                st.metric(
                    "비용 절감",
                    f"₩{cost_reduction:,.0f}/월",
                    delta=f"{(cost_reduction / before_avg_cost * 100) if before_avg_cost > 0 else 0:.1f}%"
                )
            
            # Chart
            before_monthly = before_bills.groupby('yymm')['kwh_bill'].sum().reset_index()
            before_monthly['period'] = '전'
            
            after_monthly = after_bills.groupby('yymm')['kwh_bill'].sum().reset_index()
            after_monthly['period'] = '후'
            
            combined_monthly = pd.concat([before_monthly, after_monthly])
            
            fig_comparison = px.line(
                combined_monthly,
                x='yymm',
                y='kwh_bill',
                color='period',
                title=f'{project_data["project_name"]} 전력 사용량 전후 비교',
                labels={'yymm': '월', 'kwh_bill': '총 kWh', 'period': '기간'},
                markers=True
            )
            
            # Add baseline line (without add_vline to avoid type errors)
            # Use add_shape instead for safety
            fig_comparison.add_shape(
                type="line",
                x0=baseline_idx,
                y0=0,
                x1=baseline_idx,
                y1=1,
                yref="paper",
                line=dict(color="red", width=2, dash="dash")
            )
            
            st.plotly_chart(fig_comparison, use_container_width=True)
    
    st.markdown("---")
    
    # Notes
    st.markdown("### 검증 근거 및 메모")
    
    validation_notes = st.text_area(
        "검증 근거",
        placeholder="효과 검증 과정 및 근거를 입력하세요...",
        height=150,
        key=f"validation_notes_{selected_project}"
    )
    
    st.markdown("---")
    
    # Verification action
    col_action1, col_action2 = st.columns(2)
    
    with col_action1:
        verified_amount = st.number_input(
            "확정 절감액 (원/월)",
            min_value=0,
            value=int(project_data['actual_savings_krw']),
            step=1_000_000,
            key=f"verified_amount_{selected_project}"
        )
    
    with col_action2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.button("✅ 검증 완료로 반영", type="primary", key=f"verify_btn_{selected_project}"):
            # Update project with verified savings
            project_master_manager.update_project(
                project_id=selected_project,
                verified_savings_krw=verified_amount,
                status='완료' if verified_amount > 0 else project_data['status']
            )
            
            # Create verified savings record
            saving_id = verified_savings_manager.create_verified_saving(
                yymm=baseline_month,
                site_id=None,
                category=project_data['project_name'],
                verified_savings_krw=verified_amount,
                notes=validation_notes if validation_notes else f"{project_data['project_name']} 효과 검증 완료"
            )
            
            # Create action
            current_user = st.session_state.get("current_user", "담당자")
            action = action_manager.create_action(
                owner=current_user,
                category=ActionCategory.VERIFICATION,
                description=f"{project_data['project_name']} 효과 검증 완료: ₩{verified_amount:,.0f}/월",
                evidence_links=[f"과제: {project_data['project_name']}"],
                due_days=1
            )
            
            st.success(f"✅ 검증 완료! 확정 절감: ₩{verified_amount:,.0f}/월")
            st.info(f"검증 ID: {saving_id} | 조치 ID: {action.id}")
            st.balloons()
            st.rerun()

else:
    # Show all projects summary
    st.markdown("### 전체 과제 현황")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        render_simple_metric_card("전체 과제", f"{len(projects_df)} 건")
    
    with col2:
        in_progress = len(projects_df[projects_df['status'] == '진행 중'])
        render_simple_metric_card("진행 중", f"{in_progress} 건")
    
    with col3:
        completed = len(projects_df[projects_df['status'] == '완료'])
        render_simple_metric_card("완료", f"{completed} 건")
    
    with col4:
        total_verified = projects_df['verified_savings_krw'].sum()
        render_simple_metric_card("확정 절감", f"₩{total_verified:,.0f}/월")

st.markdown("---")

# Load experiments
experiments_df = experiment_manager.load_experiments()

# Experiment list
st.markdown("### 🧪 파일럿 실험 목록")

if len(experiments_df) > 0:
    # Display experiments
    for idx, exp in experiments_df.iterrows():
        status_emoji = {
            '설계': '📋',
            '진행중': '🔄',
            '완료': '✅',
            '중단': '⏸️'
        }
        
        with st.expander(f"{status_emoji.get(exp['status'], '📌')} {exp['id']}: {exp['hypothesis']} ({exp['status']})"):
            col_a, col_b = st.columns([2, 1])
            
            with col_a:
                st.markdown(f"**가설:** {exp['hypothesis']}")
                st.markdown(f"**KPI:** {exp['kpi']}")
                st.markdown(f"**범위:** {exp['scope']}")
                st.markdown(f"**기간:** {exp['start_date'][:10]} ~ {exp['end_date'][:10]}")
                
                if exp['results']:
                    st.markdown(f"**결과:** {exp['results']}")
            
            with col_b:
                new_status = st.selectbox(
                    "상태 변경",
                    options=['설계', '진행중', '완료', '중단'],
                    index=['설계', '진행중', '완료', '중단'].index(exp['status']),
                    key=f"exp_status_{exp['id']}"
                )
                
                new_results = st.text_area(
                    "결과 입력",
                    value=exp['results'] if exp['results'] else "",
                    key=f"exp_results_{exp['id']}"
                )
                
                if st.button("업데이트", key=f"update_exp_{exp['id']}"):
                    if experiment_manager.update_experiment(
                        exp['id'],
                        status=new_status,
                        results=new_results if new_results else None
                    ):
                        st.success("업데이트 완료!")
                        st.rerun()
else:
    st.info("등록된 실증 실험이 없습니다.")

st.markdown("---")

# Create new experiment
st.markdown("### 🧪 파일럿 실험 등록 (IDEA)")

with st.form("new_experiment_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        new_hypothesis = st.text_input(
            "가설",
            placeholder="예: AI 기반 냉방 제어로 전력 사용량 10% 절감"
        )
        
        new_kpi = st.text_input(
            "KPI",
            placeholder="예: kWh 절감률 (%)"
        )
    
    with col2:
        new_scope = st.text_input(
            "실험 범위",
            placeholder="예: 수도권 기지국 10개소"
        )
        
        col_date1, col_date2 = st.columns(2)
        
        with col_date1:
            new_start_date = st.date_input(
                "시작일",
                value=datetime.now().date()
            )
        
        with col_date2:
            new_end_date = st.date_input(
                "종료일",
                value=(datetime.now() + timedelta(days=90)).date()
            )
    
    submitted = st.form_submit_button("🧪 파일럿 실험 등록", type="primary")
    
    if submitted:
        if not new_hypothesis or not new_kpi or not new_scope:
            st.error("모든 필수 항목을 입력해주세요.")
        else:
            experiment = experiment_manager.create_experiment(
                hypothesis=new_hypothesis,
                kpi=new_kpi,
                scope=new_scope,
                start_date=datetime.combine(new_start_date, datetime.min.time()),
                end_date=datetime.combine(new_end_date, datetime.min.time()),
                status="설계"
            )
            
            st.success(f"✅ 파일럿 실험 등록 완료: {experiment.id}")
            st.rerun()

# Footer with PYLON branding
st.markdown(create_footer(), unsafe_allow_html=True)

