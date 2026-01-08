"""최적화 및 실행 페이지"""

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
from src.analytics import (
    detect_zero_usage_sites,
    recommend_contract_power_adjustment,
    calculate_anomaly_score
)
from src.actions import ActionManager
from src.models import GovernanceBadge, ActionCategory, ValidationState
from src.config_loader import load_governance_config
from components.global_controls import render_sidebar_filters, render_governance_badges, apply_filters, render_filter_summary
from components.widget_card import render_widget_card, render_simple_metric_card
from components.action_inbox import render_compact_action_inbox
from styles import (
    PYLON_BLUE, PYLON_GREEN, PYLON_ORANGE,
    apply_page_style, create_footer
)

# Page config
st.set_page_config(page_title="최적화 & 실행 | PYLON", layout="wide", page_icon="🎯")

# Apply PYLON brand colors
st.markdown(apply_page_style(), unsafe_allow_html=True)

# Initialize
data_dir = Path("data")
dal = DataAccessLayer(data_dir)
action_manager = ActionManager(data_dir)
gov_config = load_governance_config()

# Header with brand color
st.markdown(f'<h1 style="color: {PYLON_BLUE};">🎯 PYLON - 최적화 & 실행</h1>', unsafe_allow_html=True)
st.markdown("계약전력 최적화, 요금제 변경, 이상 탐지")

# User and system status in sidebar
with st.sidebar:
    st.markdown("## 👤 사용자")
    if "current_user" not in st.session_state:
        st.session_state["current_user"] = "담당자"
    st.session_state["current_user"] = st.text_input(
        "담당자 이름", 
        st.session_state["current_user"],
        key="user_input_page3",
        help="조치 할당 및 작업함 필터링에 사용됩니다"
    )
    st.divider()
    
    st.markdown("## 🎛️ 시스템 상태")
    render_compact_action_inbox(action_manager, st.session_state["current_user"])
    st.divider()

# Load data
bills_df = dal.load_bills()
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
tab1, tab2, tab3 = st.tabs(["⚡ 계약전력 최적화", "🔍 이상 국소 탐지", "📍 사용량 0 국소"])

with tab1:
    st.markdown("## ⚡ 계약전력 감설/증설")
    
    st.info("💡 최근 6개월 사용 패턴을 분석하여 계약전력 최적화 기회를 식별합니다.")
    
    # Get recent 6 months data
    months_sorted = sorted(bills_df['yymm'].unique())
    recent_months = months_sorted[-6:] if len(months_sorted) >= 6 else months_sorted
    
    recent_bills = bills_df[
        (bills_df['yymm'].isin(recent_months)) &
        (bills_df['contract_type'] == '정액')  # Only for 정액 contracts
    ]
    
    if len(recent_bills) == 0:
        st.warning("정액 계약 데이터가 없습니다.")
    else:
        # Analyze each site
        optimization_results = []
        
        for site_id in filtered_bills['site_id'].unique():
            site_bills = recent_bills[recent_bills['site_id'] == site_id]
            
            if len(site_bills) >= 3:  # Need at least 3 months
                recommendation = recommend_contract_power_adjustment(site_bills)
                
                if recommendation['savings_est'] != 0:
                    site_info = site_master[site_master['site_id'] == site_id].iloc[0]
                    
                    optimization_results.append({
                        'site_id': site_id,
                        'region': site_info['region'],
                        'site_type': site_info['site_type'],
                        'current_contract_kw': recommendation['current_contract_kw'],
                        'recommended_kw': recommendation['new_contract_kw'],
                        'savings_est': recommendation['savings_est'],
                        'recommendation': recommendation['recommendation']
                    })
        
        if len(optimization_results) > 0:
            opt_df = pd.DataFrame(optimization_results)
            
            # Summary metrics
            total_savings = opt_df['savings_est'].sum()
            reduction_sites = len(opt_df[opt_df['savings_est'] > 0])
            increase_sites = len(opt_df[opt_df['savings_est'] < 0])
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                render_simple_metric_card(
                    "예상 절감액",
                    f"₩{total_savings:,.0f}/월",
                    help_text="감설 시 기본요금 절감"
                )
            
            with col2:
                render_simple_metric_card("감설 권고", f"{reduction_sites} 국소")
            
            with col3:
                render_simple_metric_card("증설 필요", f"{increase_sites} 국소")
            
            st.markdown("---")
            
            # Reduction opportunities: GREEN for savings/optimization
            st.markdown(f'<h3 style="color: {PYLON_GREEN};">🔽 감설 권고 국소</h3>', unsafe_allow_html=True)
            
            reduction_df = opt_df[opt_df['savings_est'] > 0].sort_values('savings_est', ascending=False)
            
            if len(reduction_df) > 0:
                render_widget_card(
                    title="계약전력 감설 권고",
                    value=f"{len(reduction_df)} 국소",
                    metric_label="감설 권고 국소 수",
                    validation_state=ValidationState.HYPOTHESIS,
                    evidence_table=reduction_df,
                    action_manager=action_manager,
                    action_category=ActionCategory.CONTRACT_OPTIMIZATION,
                    action_description_template=f"계약전력 감설 검토 ({len(reduction_df)}개 국소, 예상 절감액: ₩{reduction_df['savings_est'].sum():,.0f}/월)",
                    site_ids=reduction_df['site_id'].tolist()
                )
            else:
                st.info("감설 권고 국소가 없습니다.")
            
            st.markdown("---")
            
            # Increase needs
            st.markdown("### 🔼 증설 필요 국소")
            
            increase_df = opt_df[opt_df['savings_est'] < 0].sort_values('savings_est')
            
            if len(increase_df) > 0:
                render_widget_card(
                    title="계약전력 증설 필요",
                    value=f"{len(increase_df)} 국소",
                    metric_label="증설 필요 국소 수",
                    validation_state=ValidationState.IN_FLIGHT,
                    evidence_table=increase_df,
                    action_manager=action_manager,
                    action_category=ActionCategory.CONTRACT_OPTIMIZATION,
                    action_description_template=f"계약전력 증설 검토 (초과요금 위험, {len(increase_df)}개 국소)",
                    site_ids=increase_df['site_id'].tolist()
                )
            else:
                st.success("✅ 증설이 필요한 국소가 없습니다.")
        else:
            st.info("최적화 권고 사항이 없습니다.")

with tab2:
    st.markdown("## 🔍 이상 국소 탐지")
    
    st.info("💡 사용 패턴의 이상 변동을 탐지합니다 (Z-score 기반).")
    
    # Detect anomalies for each site
    anomaly_results = []
    
    # Get latest month from filtered data
    latest_month = filtered_bills['yymm'].max() if len(filtered_bills) > 0 else None
    
    for site_id in filtered_bills['site_id'].unique():
        site_bills = bills_df[bills_df['site_id'] == site_id].sort_values('yymm')
        
        if len(site_bills) >= 6:  # Need sufficient history
            site_with_anomaly = calculate_anomaly_score(site_bills, metric='kwh_bill')
            
            # Get recent anomalies
            recent_anomalies = site_with_anomaly[
                (site_with_anomaly['yymm'] == latest_month) &
                (site_with_anomaly['is_anomaly'] == True)
            ]
            
            if len(recent_anomalies) > 0:
                site_info = site_master[site_master['site_id'] == site_id].iloc[0]
                
                for _, anomaly_row in recent_anomalies.iterrows():
                    anomaly_results.append({
                        'site_id': site_id,
                        'region': site_info['region'],
                        'site_type': site_info['site_type'],
                        'yymm': anomaly_row['yymm'],
                        'kwh_bill': anomaly_row['kwh_bill'],
                        'rolling_mean': anomaly_row['rolling_mean'],
                        'z_score': anomaly_row['z_score']
                    })
    
    if len(anomaly_results) > 0:
        anomaly_df = pd.DataFrame(anomaly_results)
        
        st.markdown(f"### ⚠️ 이상 탐지: {len(anomaly_df)} 건")
        
        render_widget_card(
            title="이상 사용량 패턴 탐지",
            value=f"{len(anomaly_df)} 국소",
            metric_label="이상 탐지 국소 수",
            validation_state=ValidationState.IN_FLIGHT,
            evidence_table=anomaly_df,
            action_manager=action_manager,
            action_category=ActionCategory.ANOMALY_INVESTIGATION,
            action_description_template=f"이상 사용 패턴 조사 ({len(anomaly_df)}개 국소)",
            site_ids=anomaly_df['site_id'].tolist()
        )
        
        # Anomaly distribution
        st.markdown("### 이상 점수 분포")
        
        fig_anomaly = px.scatter(
            anomaly_df,
            x='rolling_mean',
            y='kwh_bill',
            color='z_score',
            hover_data=['site_id', 'region'],
            title='Anomaly Detection: Actual vs Expected Usage',
            labels={'rolling_mean': 'Expected (Rolling Mean)', 'kwh_bill': 'Actual kWh'},
            color_continuous_scale='RdYlBu_r'
        )
        
        st.plotly_chart(fig_anomaly, use_container_width=True)
    else:
        st.success("✅ 이상 패턴이 탐지되지 않았습니다.")

with tab3:
    st.markdown("## 📍 사용량 0 국소")
    
    st.info("💡 연속 3개월 이상 사용량이 0인 국소를 탐지합니다 (필터 적용됨).")
    
    # Detect zero usage sites (use filtered data)
    zero_sites = detect_zero_usage_sites(filtered_bills, months=3)
    
    if len(zero_sites) > 0:
        # Get details
        zero_details = []
        
        for _, row in zero_sites.iterrows():
            site_id = row['site_id']
            site_info = site_master[site_master['site_id'] == site_id]
            
            if len(site_info) > 0:
                site_info = site_info.iloc[0]
                
                # Get recent bills (use filtered data)
                site_bills = filtered_bills[
                    (filtered_bills['site_id'] == site_id) &
                    (filtered_bills['kwh_bill'] == 0)
                ].sort_values('yymm', ascending=False).head(6)
                
                zero_months_list = ','.join(site_bills['yymm'].astype(str).tolist())
                
                zero_details.append({
                    'site_id': site_id,
                    'site_name': site_info['site_name'],
                    'region': site_info['region'],
                    'site_type': site_info['site_type'],
                    'zero_months': row['zero_months'],
                    'recent_zero_periods': zero_months_list
                })
        
        zero_details_df = pd.DataFrame(zero_details)
        
        render_widget_card(
            title="사용량 0 국소",
            value=f"{len(zero_details_df)} 국소",
            metric_label="0 사용량 국소 수",
            validation_state=ValidationState.IN_FLIGHT,
            evidence_table=zero_details_df,
            action_manager=action_manager,
            action_category=ActionCategory.ZERO_USAGE,
            action_description_template=f"사용량 0 국소 조사 ({len(zero_details_df)}개 국소 - 폐쇄/이전 여부 확인)",
            site_ids=zero_details_df['site_id'].tolist()
        )
        
        # Regional distribution
        st.markdown("### 지역별 분포")
        
        region_dist = zero_details_df['region'].value_counts().reset_index()
        region_dist.columns = ['region', 'count']
        
        fig_region = px.bar(
            region_dist,
            x='region',
            y='count',
            title='지역별 사용량 0 국소 분포',
            labels={'region': '지역', 'count': '국소 수'}
        )
        
        st.plotly_chart(fig_region, use_container_width=True)
    else:
        st.success("✅ 사용량 0 국소가 없습니다.")

# Footer with PYLON branding
st.markdown(create_footer(), unsafe_allow_html=True)

