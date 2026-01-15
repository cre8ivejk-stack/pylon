"""
UI components for Copilot NLQ system.

This module provides Streamlit UI components for handling clarifications
and displaying plan execution results.
"""

from __future__ import annotations

import streamlit as st
from typing import Optional, Dict, Any, List
from src.copilot.schemas import Plan, CopilotResponse, Evidence, Deeplink


def render_clarification(plan: Plan, key: Optional[str] = None) -> Optional[str]:
    """
    Render clarification UI and return user's answer.
    
    Args:
        plan: Plan with clarification_needed=true
        key: Optional unique key for Streamlit widgets (to avoid key conflicts)
    
    Returns:
        User's answer string, or None if not answered yet
    
    Key Policy:
    - If key provided, use it as prefix for all widget keys
    - Format: f"{key}_clarification_{widget_name}"
    """
    if not plan.clarification_needed or not plan.clarification_question:
        return None
    
    key_prefix = key or "probe_clarification"
    
    st.info("💡 **추가 정보가 필요합니다**")
    st.markdown(f"**질문:** {plan.clarification_question}")
    
    # Parse choices from question (simple heuristic)
    # Expected format: "선택해주세요: 옵션1, 옵션2, 옵션3"
    question = plan.clarification_question
    if ":" in question:
        choices_text = question.split(":")[-1].strip()
        choices = [c.strip() for c in choices_text.split(",")]
        
        if len(choices) > 1:
            selected = st.radio(
                "선택",
                options=choices,
                key=f"{key_prefix}_choice"
            )
            
            if st.button("확인", key=f"{key_prefix}_submit"):
                return selected
    
    # Fallback: text input
    answer = st.text_input(
        "답변",
        key=f"{key_prefix}_answer"
    )
    
    if st.button("확인", key=f"{key_prefix}_submit_text"):
        return answer
    
    return None


def render_plan_summary(plan: Plan, metadata: Dict[str, Any]) -> None:
    """
    Render plan summary for debugging/preview.
    
    Args:
        plan: Generated plan
        metadata: Plan generation metadata
    """
    with st.expander("📋 생성된 Plan (디버그)", expanded=False):
        st.json(plan.to_dict())
        
        if metadata:
            st.caption(f"생성 방법: {metadata.get('method', 'unknown')}")
            if "llm_error" in metadata:
                st.warning(f"LLM 오류 (규칙 기반으로 대체됨): {metadata['llm_error']}")


def render_plan_execution_result(
    plan: Plan,
    result_df: Any,  # pandas DataFrame
    summary: Optional[Dict[str, Any]] = None
) -> None:
    """
    Render plan execution results.
    
    Args:
        plan: Executed plan
        result_df: Result DataFrame
        summary: Optional summary statistics
    """
    st.markdown("## ✅ 실행 결과")
    
    if summary:
        st.markdown("### 📊 요약")
        st.json(summary)
    
    if result_df is not None and len(result_df) > 0:
        st.markdown("### 📋 상세 데이터")
        st.dataframe(result_df, use_container_width=True)
    else:
        st.info("조건에 해당하는 데이터가 없습니다.")


def render_probe_response(
    response: CopilotResponse,
    message_id: str,
    show_full_details: bool = True
) -> None:
    """
    Render PROBE response evidence and links (answer text is NOT rendered here).
    
    IMPORTANT: Answer text is rendered by render_chat_message() to avoid duplication.
    This function only renders evidence and links.
    
    Args:
        response: CopilotResponse object
        message_id: Unique message ID for key generation
        show_full_details: If True, show evidence and links. If False, nothing.
    
    Key Policy:
    - All widget keys use message_id prefix to ensure uniqueness
    - Format: f"{message_id}_{widget_type}_{index}"
    - Never use hash() or other non-deterministic values
    - st.expander does NOT support key parameter in some Streamlit versions, so we don't use it
    """
    if not show_full_details:
        return
    
    # Confidence indicator
    confidence_color = "green" if response.confidence >= 0.8 else "orange" if response.confidence >= 0.5 else "red"
    st.caption(f"신뢰도: {response.confidence:.0%}")
    
    if response.is_ambiguous:
        st.warning("⚠️ 질의가 다소 모호할 수 있습니다. 더 구체적인 질문을 해주시면 더 정확한 답변을 드릴 수 있습니다.")
    
    # Evidence section - NO key parameter for expander
    try:
        with st.expander("📊 근거 정보", expanded=False):
            evidence = response.evidence
            st.markdown(f"**적용 필터:**")
            for key, value in evidence.applied_filters.items():
                if value:
                    st.write(f"- {key}: {value}")
            
            st.markdown(f"**지표:** {evidence.metric}")
            st.markdown(f"**기간:** {evidence.time_range}")
            st.markdown(f"**데이터 소스:** {evidence.data_source}")
            st.markdown(f"**레코드 수:** {evidence.num_records:,}건")
    except Exception as e:
        # Fallback if expander fails
        st.markdown("**📊 근거 정보**")
        evidence = response.evidence
        st.markdown(f"**적용 필터:** {evidence.applied_filters}")
        st.markdown(f"**지표:** {evidence.metric}")
        st.markdown(f"**기간:** {evidence.time_range}")
    
    # Links section - using NavLink with session_state
    # Always show links section, even if empty
    st.markdown("### 🔗 자세히 보기")
    
    if hasattr(response, 'nav_links') and response.nav_links and len(response.nav_links) > 0:
        for idx, nav_link in enumerate(response.nav_links):
            # Use message_id + index for unique key
            button_key = f"probe_nav_btn_{message_id}_{idx}"
            try:
                if st.button(
                    f"→ {nav_link.title}",
                    key=button_key,
                    help=nav_link.description if hasattr(nav_link, 'description') else None,
                    use_container_width=True
                ):
                    # Set session_state and navigate
                    st.session_state["probe_nav"] = nav_link.nav_payload
                    st.switch_page(nav_link.target_page)
            except Exception as e:
                st.error(f"링크 버튼 오류: {str(e)}")
    else:
        # No links available
        st.info("이 질의에 대한 상세 페이지 링크를 생성할 수 없습니다.")


def render_copilot_response(response: CopilotResponse) -> None:
    """
    Legacy function name - redirects to render_probe_response.
    
    For backward compatibility.
    """
    import uuid
    message_id = str(uuid.uuid4())[:8]
    render_probe_response(response, message_id, show_full_details=True)


def render_chat_message(
    role: str,
    content: str,
    is_user: bool = True,
    message_id: Optional[str] = None,
    response: Optional[CopilotResponse] = None
) -> None:
    """
    Render a chat message with optional PROBE response details.
    
    IMPORTANT: This function renders the message content ONCE.
    If response is provided, it calls render_probe_response() which does NOT render
    the answer text again (to avoid duplication).
    
    Args:
        role: "user" or "assistant"
        content: Message content (answer text for assistant)
        is_user: True if user message, False if assistant
        message_id: Unique message ID (for assistant messages with links)
        response: Optional CopilotResponse for assistant messages (includes evidence/links)
    
    Key Policy:
    - User messages: No keys needed (just markdown)
    - Assistant messages: Use message_id for all interactive widgets
    - Answer text is rendered here ONCE, render_probe_response() does NOT render it again
    """
    if is_user:
        st.markdown(f"""
        <div style="background-color: #e3f2fd; padding: 10px; border-radius: 10px; margin: 5px 0;">
            <strong>👤 사용자:</strong> {content}
        </div>
        """, unsafe_allow_html=True)
    else:
        # Assistant message: render answer text ONCE
        st.markdown(f"""
        <div style="background-color: #f5f5f5; padding: 10px; border-radius: 10px; margin: 5px 0;">
            <strong>🤖 PROBE:</strong> {content}
        </div>
        """, unsafe_allow_html=True)
        
        # If response provided, render evidence and links (NOT answer text again)
        if response and message_id:
            try:
                render_probe_response(response, message_id, show_full_details=True)
            except Exception as e:
                st.error(f"응답 렌더링 오류: {str(e)}")


def render_query_input(
    default_value: str = "",
    key: str = "probe_query"
) -> str:
    """
    Render query input UI.
    
    Args:
        default_value: Default query text
        key: Streamlit key (default: "probe_query")
    
    Returns:
        User query string
    """
    query = st.text_input(
        "💬 PROBE에게 질문하세요",
        value=default_value,
        key=key,
        placeholder="예: 동부지역 최근 2개월 전력사용량 상위 20개",
        help="자연어로 질문하시면 PROBE가 분석 결과와 함께 답변해드립니다."
    )
    
    return query.strip()
