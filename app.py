"""PYLON - SKT Network센터 에너지 운영 플랫폼

Streamlit 애플리케이션의 메인 진입점입니다.
"""

import streamlit as st
from pathlib import Path

from src.data_access import DataAccessLayer
from src.actions import ActionManager
from src.models import GovernanceBadge
from src.config_loader import load_governance_config
from components.global_controls import render_governance_badges
from components.action_inbox import render_action_inbox
from components.strategy_overview import render_strategy_overview
from components.key_initiatives import render_key_initiatives

# Page configuration
st.set_page_config(
    page_title="PYLON - 에너지 운영 플랫폼",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize
data_dir = Path("data")

# Cache data loading for better performance
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_app_data():
    """Load all data with caching"""
    dal = DataAccessLayer(data_dir)
    bills_df = dal.load_bills()
    return dal, bills_df

@st.cache_data(ttl=300)
def load_governance_data():
    """Load governance config with caching"""
    return load_governance_config()

# Load data (cached)
dal, bills_df = load_app_data()
action_manager = ActionManager(data_dir)
gov_config = load_governance_data()
latest_yymm = bills_df['yymm'].max() if len(bills_df) > 0 else None
governance_badge = GovernanceBadge.create_from_config_and_data(gov_config, latest_yymm)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .subtitle {
        font-size: 1.2rem;
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .feature-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">⚡ PYLON</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">SKT Network센터 에너지 관리 운영 플랫폼</div>', unsafe_allow_html=True)

st.divider()

# Governance badges
render_governance_badges(governance_badge)

# 전략 섹션 추가
render_strategy_overview()
render_key_initiatives()

# Welcome section
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("## 🎯 플랫폼 개요")
    
    st.markdown("""
    **PYLON**은 단순한 대시보드가 아닌, 에너지 운영의 전체 라이프사이클을 지원하는 통합 플랫폼입니다.
    
    ### 핵심 가치
    
    - **🔍 Intelligence**: 계획 대비 실적, 청구서 vs 실사용량 분석
    - **⚠️ Risk Control**: 전기요금 리스크 모니터링 및 선제적 대응
    - **🎯 Optimization**: 계약전력 최적화, 이상 탐지, 요금제 변경 추천
    - **✅ Validation**: 과제 효과 검증, IDEA 실증 실험 관리
    - **⚡ Action Management**: 조치 생성부터 완료까지 전체 추적
    
    ### 사용 방법
    
    왼쪽 사이드바에서 4개 주요 메뉴를 통해 각 기능에 접근할 수 있습니다:
    
    1. **Energy Intelligence** - 에너지 사용 현황 및 계획 대비 실적
    2. **Performance & Risk** - 과제 성과 관리 및 리스크 모니터링
    3. **Optimization & Action** - 최적화 기회 발굴 및 조치 생성
    4. **Validation & IDEA** - 효과 검증 및 실증 실험
    """)

with col2:
    st.markdown("## 📊 시스템 상태")
    
    # Quick stats
    site_master = dal.load_site_master()
    
    if len(bills_df) > 0:
        latest_month = bills_df['yymm'].max()
        total_sites = len(site_master)
        total_cost = bills_df[bills_df['yymm'] == latest_month]['cost_bill'].sum()
        
        st.metric("최신 데이터", latest_month)
        st.metric("관리 국소", f"{total_sites:,} 개소")
        st.metric("당월 전기요금", f"₩{total_cost:,.0f}")
    else:
        st.warning("데이터를 로드할 수 없습니다.")
    
    st.markdown("---")
    
    # Action stats
    current_user = st.session_state.get("current_user", "담당자")
    action_stats = action_manager.get_action_stats(current_user)
    
    st.markdown("### ⚡ 작업 현황")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("해야 할 일", action_stats['todo'])
        st.metric("진행 중", action_stats['doing'])
    with col_b:
        st.metric("완료", action_stats['done'])
        if action_stats['overdue'] > 0:
            st.metric("⚠️ 지연", action_stats['overdue'])
        else:
            st.metric("✅ 지연", 0)

st.divider()

# 내 작업함
st.markdown("## 📬 내 작업함")
st.markdown("""
**내 작업함**은 사용자(실무자)가 '조치 필요'로 표시한 항목의 개인 큐입니다.

다음 항목들이 포함됩니다:
- 📊 계약전력 감설/증설 후보
- 💰 요금제 변경 추천 후보
- ⚠️ Billing Consistency Risk (실사용량 vs 청구서) 이슈
- 🔬 솔루션 실증 "추가 검증 필요" 과제

각 항목은 **대기/진행/완료/보류** 상태로 관리됩니다.
""")
render_action_inbox(action_manager, st.session_state.get("current_user", "담당자"))

st.divider()

# 빠른 시작
st.markdown("## 🚀 빠른 시작")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("### 📊 에너지 현황")
    st.markdown("전사 에너지 사용 및 비용 흐름을 한눈에 파악합니다.")
    st.page_link("pages/1_에너지_인텔리전스.py", label="→ 에너지 인텔리전스", icon="⚡")

with col2:
    st.markdown("### ⚠️ 리스크 관리")
    st.markdown("요금 이상 및 정합 리스크를 조기에 탐지합니다.")
    st.page_link("pages/2_성과_리스크_관리.py", label="→ 성과 & 리스크", icon="📊")

with col3:
    st.markdown("### 🎯 최적화")
    st.markdown("절감 후보를 추천하고 조치로 연결합니다.")
    st.page_link("pages/3_최적화_실행.py", label="→ 최적화 & 실행", icon="🎯")

with col4:
    st.markdown("### ✅ 검증")
    st.markdown("실증 결과를 확정 성과로 반영합니다.")
    st.page_link("pages/4_검증_실증.py", label="→ 검증 & 실증", icon="🔬")

st.divider()

# Data management
with st.expander("📁 데이터 소스 관리"):
    st.markdown("### 데이터 업로드")
    
    st.info("""
    현재 샘플 데이터를 사용하고 있습니다. 실제 데이터를 업로드하려면 아래에서 파일을 선택하세요.
    
    **지원 형식**: CSV, Parquet
    """)
    
    data_type = st.selectbox(
        "데이터 유형",
        options=['bills', 'actual', 'plan', 'traffic', 'site_master'],
        format_func=lambda x: {
            'bills': '청구서 데이터',
            'actual': '실사용량 데이터',
            'plan': '계획 데이터',
            'traffic': '트래픽 데이터',
            'site_master': '국소 마스터'
        }[x]
    )
    
    uploaded_file = st.file_uploader(
        "파일 선택",
        type=['csv', 'parquet'],
        help="CSV 또는 Parquet 파일을 업로드하세요"
    )
    
    if uploaded_file is not None:
        if st.button("업로드", type="primary"):
            if dal.upload_data(uploaded_file, data_type):
                st.success("✅ 데이터 업로드 완료! 페이지를 새로고침하세요.")
                st.rerun()

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem 0;">
    <p><strong>PYLON v0.0.3 (Dev) | SKT Network ESG추진팀</strong></p>
</div>
""", unsafe_allow_html=True)

