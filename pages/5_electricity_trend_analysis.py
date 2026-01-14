"""월별 전기 사용량 및 전기료 추이 분석 페이지
2025년 1~12월, 2026년 1~3월 총 15개월 데이터 시각화"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import sys

# Add parent directory to path (Streamlit Cloud compatibility)
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from src.data_access import DataAccessLayer
from styles import (
    PYLON_BLUE, PYLON_GREEN, PYLON_ORANGE, PYLON_TEXT,
    apply_page_style, create_footer
)

# Page config
st.set_page_config(
    page_title="월별 전기 추이 분석 | PYLON",
    layout="wide",
    page_icon="📊"
)

# Apply PYLON brand colors
st.markdown(apply_page_style(), unsafe_allow_html=True)

# Initialize
data_dir = Path("data")
dal = DataAccessLayer(data_dir)

# Header
st.markdown(f'<h1 style="color: {PYLON_BLUE};">📊 월별 전기 사용량 및 전기료 추이 분석</h1>', unsafe_allow_html=True)
st.markdown("**2025년 1월 ~ 2026년 3월 (총 15개월) 데이터 분석**")

st.divider()

# Load data from data folder
try:
    bills_df = dal.load_bills()

    if len(bills_df) == 0:
        st.error("⚠️ 청구서 데이터를 로드할 수 없습니다.")
        st.info("data 폴더에 sample_bills.parquet 파일이 있는지 확인해주세요.")
        st.stop()

except Exception as e:
    st.error(f"데이터 로드 중 오류 발생: {str(e)}")
    st.info("data 폴더의 데이터 파일을 확인해주세요.")
    st.stop()

# Define target months (2025년 1~12월, 2026년 1~3월)
# yymm 형식: 202501 (2025년 1월), 202601 (2026년 1월) 등 정수형
target_months = []
# 2025년 1~12월
for month in range(1, 13):
    target_months.append(202500 + month)  # 202501, 202502, ..., 202512
# 2026년 1~3월
for month in range(1, 4):
    target_months.append(202600 + month)  # 202601, 202602, 202603

# Ensure yymm is integer type for comparison
bills_df['yymm'] = bills_df['yymm'].astype(int)

# Filter data for target months
filtered_df = bills_df[bills_df['yymm'].isin(target_months)].copy()

if len(filtered_df) == 0:
    st.warning("요청하신 기간의 데이터가 없습니다. 샘플 데이터를 생성하거나 실제 데이터를 업로드해주세요.")
    available_months = sorted(bills_df['yymm'].unique())
    st.info(f"현재 사용 가능한 월: {', '.join(map(str, available_months[:20]))}" +
            (f" ... (총 {len(available_months)}개월)" if len(available_months) > 20 else ""))
    st.stop()

# Aggregate by month
monthly_data = filtered_df.groupby('yymm').agg({
    'kwh_bill': 'sum',
    'cost_bill': 'sum',
    'site_id': 'nunique'  # Number of unique sites
}).reset_index()

monthly_data.columns = ['yymm', 'total_kwh', 'total_cost', 'site_count']

# Sort by yymm
monthly_data = monthly_data.sort_values('yymm').reset_index(drop=True)

# Create readable month labels
def format_month_label(yymm_int):
    """Convert yymm integer to readable format (e.g., 202501 -> '2025-01')"""
    yymm_str = str(yymm_int)
    if len(yymm_str) == 6:
        year = yymm_str[:4]
        month = yymm_str[4:6]
        return f"{year}-{month}"
    return str(yymm_int)

monthly_data['month_label'] = monthly_data['yymm'].apply(format_month_label)

# Summary metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_kwh = monthly_data['total_kwh'].sum()
    st.metric("총 전기 사용량", f"{total_kwh:,.0f} kWh")

with col2:
    total_cost = monthly_data['total_cost'].sum()
    st.metric("총 전기료", f"₩{total_cost:,.0f}")

with col3:
    avg_monthly_kwh = monthly_data['total_kwh'].mean()
    st.metric("월평균 사용량", f"{avg_monthly_kwh:,.0f} kWh")

with col4:
    avg_monthly_cost = monthly_data['total_cost'].mean()
    st.metric("월평균 전기료", f"₩{avg_monthly_cost:,.0f}")

st.divider()

# Create dual-axis chart for usage and cost
try:
    fig = make_subplots(
        specs=[[{"secondary_y": True}]],
        subplot_titles=("월별 전기 사용량 및 전기료 추이")
    )

    # Add usage line (left axis)
    fig.add_trace(
        go.Scatter(
            x=monthly_data['month_label'],
            y=monthly_data['total_kwh'],
            name='전기 사용량 (kWh)',
            mode='lines+markers',
            line=dict(color=PYLON_BLUE, width=3),
            marker=dict(size=8, color=PYLON_BLUE),
            hovertemplate='<b>%{x}</b><br>사용량: %{y:,.0f} kWh<extra></extra>'
        ),
        secondary_y=False,
    )

    # Add cost line (right axis)
    fig.add_trace(
        go.Scatter(
            x=monthly_data['month_label'],
            y=monthly_data['total_cost'],
            name='전기료 (원)',
            mode='lines+markers',
            line=dict(color=PYLON_ORANGE, width=3, dash='dash'),
            marker=dict(size=8, color=PYLON_ORANGE),
            hovertemplate='<b>%{x}</b><br>전기료: ₩%{y:,.0f}<extra></extra>'
        ),
        secondary_y=True,
    )

    # Update axes
    fig.update_xaxes(
        title_text="월",
        tickangle=-45,
        showgrid=True,
        gridcolor='rgba(128, 128, 128, 0.2)'
    )

    fig.update_yaxes(
        title_text="전기 사용량 (kWh)",
        secondary_y=False,
        showgrid=True,
        gridcolor='rgba(128, 128, 128, 0.1)'
    )

    fig.update_yaxes(
        title_text="전기료 (원)",
        secondary_y=True,
        showgrid=False
    )

    # Update layout
    fig.update_layout(
        title={
            'text': '월별 전기 사용량 및 전기료 추이 (2025-01 ~ 2026-03)',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18}
        },
        height=500,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )

    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"차트 생성 중 오류 발생: {str(e)}")
    st.info("데이터를 확인해주세요.")

st.divider()

# Separate charts section
st.markdown("## 📈 상세 분석")

tab1, tab2, tab3 = st.tabs(["전기 사용량", "전기료", "데이터 테이블"])

with tab1:
    st.markdown("### 전기 사용량 추이")

    # Usage bar chart
    fig_usage = go.Figure()

    fig_usage.add_trace(go.Bar(
        x=monthly_data['month_label'],
        y=monthly_data['total_kwh'],
        name='전기 사용량',
        marker=dict(
            color=monthly_data['total_kwh'],
            colorscale='Blues',
            showscale=True,
            colorbar=dict(title="kWh")
        ),
        text=[f"{val:,.0f}" for val in monthly_data['total_kwh']],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>사용량: %{y:,.0f} kWh<extra></extra>'
    ))

    fig_usage.update_layout(
        title='월별 전기 사용량 (kWh)',
        xaxis_title='월',
        yaxis_title='전기 사용량 (kWh)',
        height=400,
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white'
    )

    st.plotly_chart(fig_usage, use_container_width=True)

    # Usage statistics
    col1, col2, col3 = st.columns(3)

    with col1:
        max_kwh_month = monthly_data.loc[monthly_data['total_kwh'].idxmax(), 'month_label']
        max_kwh_value = monthly_data['total_kwh'].max()
        st.metric("최대 사용량 월", max_kwh_month, f"{max_kwh_value:,.0f} kWh")

    with col2:
        min_kwh_month = monthly_data.loc[monthly_data['total_kwh'].idxmin(), 'month_label']
        min_kwh_value = monthly_data['total_kwh'].min()
        st.metric("최소 사용량 월", min_kwh_month, f"{min_kwh_value:,.0f} kWh")

    with col3:
        # Calculate month-over-month change
        monthly_data['kwh_change'] = monthly_data['total_kwh'].pct_change() * 100
        avg_change = monthly_data['kwh_change'].mean()
        st.metric("월평균 변화율", f"{avg_change:+.2f}%")

with tab2:
    st.markdown("### 전기료 추이")

    # Cost bar chart
    fig_cost = go.Figure()

    fig_cost.add_trace(go.Bar(
        x=monthly_data['month_label'],
        y=monthly_data['total_cost'],
        name='전기료',
        marker=dict(
            color=monthly_data['total_cost'],
            colorscale='Oranges',
            showscale=True,
            colorbar=dict(title="원")
        ),
        text=[f"₩{val:,.0f}" for val in monthly_data['total_cost']],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>전기료: ₩%{y:,.0f}<extra></extra>'
    ))

    fig_cost.update_layout(
        title='월별 전기료 (원)',
        xaxis_title='월',
        yaxis_title='전기료 (원)',
        height=400,
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white'
    )

    st.plotly_chart(fig_cost, use_container_width=True)

    # Cost statistics
    col1, col2, col3 = st.columns(3)

    with col1:
        max_cost_month = monthly_data.loc[monthly_data['total_cost'].idxmax(), 'month_label']
        max_cost_value = monthly_data['total_cost'].max()
        st.metric("최대 전기료 월", max_cost_month, f"₩{max_cost_value:,.0f}")

    with col2:
        min_cost_month = monthly_data.loc[monthly_data['total_cost'].idxmin(), 'month_label']
        min_cost_value = monthly_data['total_cost'].min()
        st.metric("최소 전기료 월", min_cost_month, f"₩{min_cost_value:,.0f}")

    with col3:
        # Calculate month-over-month change
        monthly_data['cost_change'] = monthly_data['total_cost'].pct_change() * 100
        avg_change = monthly_data['cost_change'].mean()
        st.metric("월평균 변화율", f"{avg_change:+.2f}%")

    # Cost per kWh trend
    st.markdown("#### 단위 전기료 추이 (원/kWh)")

    # Avoid division by zero
    monthly_data['cost_per_kwh'] = monthly_data.apply(
        lambda row: row['total_cost'] / row['total_kwh'] if row['total_kwh'] > 0 else 0,
        axis=1
    )

    fig_unit_cost = go.Figure()

    fig_unit_cost.add_trace(go.Scatter(
        x=monthly_data['month_label'],
        y=monthly_data['cost_per_kwh'],
        name='단위 전기료',
        mode='lines+markers',
        line=dict(color=PYLON_GREEN, width=2),
        marker=dict(size=8, color=PYLON_GREEN),
        fill='tonexty',
        fillcolor=f'{PYLON_GREEN}20',
        hovertemplate='<b>%{x}</b><br>단위 전기료: ₩%{y:,.2f}/kWh<extra></extra>'
    ))

    fig_unit_cost.update_layout(
        title='월별 단위 전기료 (원/kWh)',
        xaxis_title='월',
        yaxis_title='단위 전기료 (원/kWh)',
        height=350,
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white'
    )

    st.plotly_chart(fig_unit_cost, use_container_width=True)

with tab3:
    st.markdown("### 월별 데이터 상세")

    # Prepare display table
    display_data = monthly_data[[
        'month_label', 'total_kwh', 'total_cost', 'site_count'
    ]].copy()

    # Add calculated columns (avoid division by zero)
    display_data['cost_per_kwh'] = display_data.apply(
        lambda row: row['total_cost'] / row['total_kwh'] if row['total_kwh'] > 0 else 0,
        axis=1
    )
    display_data['kwh_change_pct'] = display_data['total_kwh'].pct_change() * 100
    display_data['cost_change_pct'] = display_data['total_cost'].pct_change() * 100

    # Rename columns
    display_data.columns = [
        '월',
        '전기 사용량 (kWh)',
        '전기료 (원)',
        '국소 수',
        '단위 전기료 (원/kWh)',
        '사용량 변화율 (%)',
        '전기료 변화율 (%)'
    ]

    # Format numbers
    display_data['전기 사용량 (kWh)'] = display_data['전기 사용량 (kWh)'].apply(lambda x: f"{x:,.0f}")
    display_data['전기료 (원)'] = display_data['전기료 (원)'].apply(lambda x: f"₩{x:,.0f}")
    display_data['단위 전기료 (원/kWh)'] = display_data['단위 전기료 (원/kWh)'].apply(lambda x: f"₩{x:,.2f}")
    display_data['사용량 변화율 (%)'] = display_data['사용량 변화율 (%)'].apply(lambda x: f"{x:+.2f}%" if pd.notna(x) else "-")
    display_data['전기료 변화율 (%)'] = display_data['전기료 변화율 (%)'].apply(lambda x: f"{x:+.2f}%" if pd.notna(x) else "-")

    st.dataframe(
        display_data,
        use_container_width=True,
        hide_index=True
    )

    # Download button
    csv = monthly_data[[
        'month_label', 'total_kwh', 'total_cost', 'site_count'
    ]].to_csv(index=False)

    st.download_button(
        label="📥 데이터 다운로드 (CSV)",
        data=csv,
        file_name="monthly_electricity_trend_2025_2026.csv",
        mime="text/csv"
    )

st.divider()

# Footer
st.markdown(create_footer(), unsafe_allow_html=True)