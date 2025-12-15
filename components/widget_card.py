"""Reusable widget card component with action creation."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Optional, Callable, List
from src.actions import ActionManager
from src.models import ActionCategory, ValidationState


def render_widget_card(
    title: str,
    value: any,
    metric_label: str,
    validation_state: ValidationState,
    evidence_chart: Optional[go.Figure] = None,
    evidence_table: Optional[pd.DataFrame] = None,
    action_manager: Optional[ActionManager] = None,
    action_category: Optional[ActionCategory] = None,
    action_description_template: Optional[str] = None,
    owner: str = "담당자",
    site_ids: Optional[List[str]] = None
) -> None:
    """
    Render a widget card with evidence, target list, and action creation.
    
    Args:
        title: Widget title
        value: Main metric value
        metric_label: Label for the metric
        validation_state: Current validation state
        evidence_chart: Plotly chart for evidence (optional)
        evidence_table: DataFrame for evidence (optional)
        action_manager: ActionManager for creating actions (optional)
        action_category: Category for created actions (optional)
        action_description_template: Template for action description (optional)
        owner: Default action owner
        site_ids: List of site IDs for bulk action creation (optional)
    """
    # Validation state badge
    state_colors = {
        ValidationState.HYPOTHESIS: "🔵",
        ValidationState.IN_FLIGHT: "🟡",
        ValidationState.VERIFIED: "🟢"
    }
    state_label = validation_state.to_korean() if hasattr(validation_state, 'to_korean') else validation_state.value
    state_badge = f"{state_colors.get(validation_state, '⚪')} {state_label}"
    
    # Main metric display
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"### {title}")
        st.metric(label=metric_label, value=value)
    
    with col2:
        st.markdown("**검증 상태**")
        st.markdown(state_badge)
    
    # Evidence section
    with st.expander("📊 근거 보기"):
        if evidence_chart:
            st.plotly_chart(evidence_chart, use_container_width=True)
        
        if evidence_table is not None and len(evidence_table) > 0:
            st.dataframe(evidence_table, use_container_width=True, hide_index=True)
        
        if not evidence_chart and (evidence_table is None or len(evidence_table) == 0):
            st.info("표시할 근거 데이터가 없습니다.")
    
    # Target list section
    if evidence_table is not None and len(evidence_table) > 0:
        with st.expander("🎯 대상 리스트"):
            st.dataframe(evidence_table, use_container_width=True, hide_index=True)
            
            # Download button
            csv = evidence_table.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="CSV 다운로드",
                data=csv,
                file_name=f"{title}_targets.csv",
                mime="text/csv"
            )
    
    # Action creation section
    if action_manager and action_category:
        with st.expander("⚡ 조치 생성"):
            st.markdown(f"**카테고리:** {action_category.value}")
            
            action_desc = st.text_area(
                "조치 내용",
                value=action_description_template or f"{title} 관련 조치",
                key=f"action_desc_{title}"
            )
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                action_owner = st.text_input("담당자", value=owner, key=f"action_owner_{title}")
            
            with col_b:
                due_days = st.number_input("마감일 (일)", min_value=1, max_value=90, value=7, key=f"due_days_{title}")
            
            if st.button("✅ 조치 생성", key=f"create_action_{title}"):
                # Create action
                evidence_links = [title]
                
                action = action_manager.create_action(
                    owner=action_owner,
                    category=action_category,
                    description=action_desc,
                    site_id=site_ids[0] if site_ids and len(site_ids) == 1 else None,
                    evidence_links=evidence_links,
                    due_days=due_days
                )
                
                st.success(f"✅ 조치 생성 완료: {action.id}")
                st.info(f"담당자: {action_owner} | 마감일: {action.due_date.strftime('%Y-%m-%d')}")
    
    st.divider()


def render_simple_metric_card(
    title: str,
    value: any,
    delta: Optional[any] = None,
    help_text: Optional[str] = None
) -> None:
    """
    Render a simple metric card without action creation.
    
    Args:
        title: Metric title
        value: Metric value
        delta: Delta value (optional)
        help_text: Help text (optional)
    """
    st.metric(
        label=title,
        value=value,
        delta=delta,
        help=help_text
    )

