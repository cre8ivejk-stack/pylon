"""🤖 PYLON PROBE - 자연어 질의 페이지

이 페이지는 PROBE의 메인 UX를 제공합니다.
사이드바가 아닌 전용 페이지로 제공됩니다.
"""

from pathlib import Path
import sys
import streamlit as st
import uuid
from typing import Optional, List, Dict, Any

# Add parent directory to path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from src.data_access import DataAccessLayer
from src.copilot.planner import plan_with_fallback
from src.copilot.executor import execute_plan
from src.copilot.schemas import CopilotResponse, Evidence, Metric
from src.copilot.ui import (
    render_clarification,
    render_probe_response,
    render_chat_message,
)
from styles import PYLON_BLUE, apply_page_style, create_footer


# Page configuration
st.set_page_config(
    page_title="PYLON PROBE | 자연어 질의",
    layout="wide",
    page_icon="🤖"
)

# Apply styling
st.markdown(apply_page_style(), unsafe_allow_html=True)

# Header
st.markdown(f'<h1 style="color: {PYLON_BLUE};">🤖 PYLON PROBE</h1>', unsafe_allow_html=True)
st.markdown("자연어로 질문하시면 분석 결과와 함께 상세 페이지로 이동할 수 있습니다.")

# Initialize session state
if "probe_history" not in st.session_state:
    st.session_state.probe_history = []  # List of {role, content, message_id?, response?}
if "probe_waiting_clarification" not in st.session_state:
    st.session_state.probe_waiting_clarification = None
if "probe_last_plan" not in st.session_state:
    st.session_state.probe_last_plan = None  # Last confirmed plan for context
if "probe_message_counter" not in st.session_state:
    st.session_state.probe_message_counter = 0  # Monotonic counter for message IDs

# Data loading
data_dir = Path("data")
dal = DataAccessLayer(data_dir)


# Helper functions (defined before use)
def _get_next_message_id() -> str:
    """Generate unique message ID using monotonic counter."""
    st.session_state.probe_message_counter += 1
    return f"probe_msg_{st.session_state.probe_message_counter}"


def _get_conversation_context(max_turns: int = 10) -> List[Dict[str, Any]]:
    """Get recent conversation context for LLM."""
    history = st.session_state.get("probe_history", [])
    # Return last N turns
    return history[-max_turns:] if history else []


def _generate_answer(query: str, plan, exec_result) -> str:
    """Generate natural language answer using LLM or rule-based."""
    try:
        from src.copilot.planner import _get_openai_client
        import os
        import json
        
        client = _get_openai_client()
        
        # Get model
        model = "gpt-4o-mini"
        try:
            if hasattr(st, "secrets") and "PYLON_LLM_MODEL" in st.secrets:
                model = st.secrets["PYLON_LLM_MODEL"]
        except Exception:
            pass
        
        if model == "gpt-4o-mini":
            model = os.getenv("PYLON_LLM_MODEL", "gpt-4o-mini")
        
        # Prepare result summary
        result_summary = ""
        if exec_result.result_df is not None and len(exec_result.result_df) > 0:
            top_rows = exec_result.result_df.head(5).to_dict('records')
            result_summary = f"""
실행 결과:
- 총 {len(exec_result.result_df)}건의 데이터
- 요약: {json.dumps(exec_result.summary, ensure_ascii=False)}
- 상위 5건: {json.dumps(top_rows, ensure_ascii=False, default=str)}
"""
        else:
            result_summary = "조건에 해당하는 데이터가 없습니다."
        
        # Build prompt
        answer_prompt = f"""
사용자 질의: {query}

실행된 계획:
- 질의 유형: {plan.query_type}
- 지표: {plan.metric}
- 기간: {plan.time_range.type}
- 필터: {plan.filters.to_dict()}

{result_summary}

위 결과를 바탕으로 사용자에게 자연스러운 한국어로 답변을 작성해주세요.
답변은 5줄 이내로 간결하게 작성하고, 주요 수치와 인사이트를 포함해주세요.
"""
        
        resp = client.chat.completions.create(
            model=model,
            temperature=0.3,
            messages=[
                {
                    "role": "system",
                    "content": "너는 PYLON 에너지 운영 플랫폼의 PROBE이다. 분석 결과를 사용자에게 자연스럽고 전문적으로 설명한다."
                },
                {"role": "user", "content": answer_prompt},
            ],
        )
        
        return (resp.choices[0].message.content or "").strip()
        
    except Exception:
        # Fallback to rule-based answer
        return _generate_rule_based_answer(plan, exec_result)


def _generate_rule_based_answer(plan, exec_result) -> str:
    """Generate rule-based answer."""
    parts = []
    
    if plan.query_type == "top_n":
        parts.append(f"요청하신 조건으로 **상위 {plan.top_n}개** 국소를 분석했습니다.")
    elif plan.query_type == "trend":
        parts.append("요청하신 기간의 **추이 분석** 결과입니다.")
    elif plan.query_type == "comparison":
        parts.append("**비교 분석** 결과입니다.")
    
    if exec_result.summary:
        if "total_value" in exec_result.summary:
            parts.append(f"총합: {exec_result.summary['total_value']:,.0f}")
        if "total_sites" in exec_result.summary:
            parts.append(f"분석 대상: {exec_result.summary['total_sites']}개 국소")
    
    return "\n\n".join(parts) if parts else "분석이 완료되었습니다."


def _build_evidence(plan, exec_result) -> Evidence:
    """Build evidence from plan and execution result."""
    # Build applied filters dict
    applied_filters = {}
    if plan.filters.region:
        applied_filters["지역"] = ", ".join(plan.filters.region)
    if plan.filters.site_type:
        applied_filters["설비유형"] = ", ".join(plan.filters.site_type)
    if plan.filters.contract_type_major:
        applied_filters["계약유형"] = ", ".join(plan.filters.contract_type_major)
    if plan.filters.contract_target:
        applied_filters["계약대상"] = plan.filters.contract_target
    if plan.filters.rapa:
        applied_filters["RAPA"] = plan.filters.rapa
    if plan.filters.network_gen:
        applied_filters["네트워크 세대"] = ", ".join(plan.filters.network_gen)
    
    # Build time range string
    time_range_str = ""
    if plan.time_range.type == "last_n_months":
        time_range_str = f"최근 {plan.time_range.n}개월"
    elif plan.time_range.type == "yymm_range":
        time_range_str = f"{plan.time_range.start_yymm} ~ {plan.time_range.end_yymm}"
    elif plan.time_range.type == "single_yymm":
        time_range_str = str(plan.time_range.yymm)
    
    # Determine data source
    if plan.metric == Metric.USAGE_KWH.value:
        data_source = "실사용량 데이터"
    elif plan.metric == Metric.COST_WON.value:
        data_source = "청구서 데이터"
    else:
        data_source = "통합 데이터"
    
    # Get metric name
    metric_names = {
        Metric.USAGE_KWH.value: "전력 사용량 (kWh)",
        Metric.COST_WON.value: "전기요금 (원)",
        Metric.UNIT_COST.value: "평균 단가 (원/kWh)",
        Metric.BILL_VS_ACTUAL_GAP.value: "청구서 vs 실사용량 차이",
    }
    metric_name = metric_names.get(plan.metric, plan.metric)
    
    return Evidence(
        applied_filters=applied_filters,
        metric=metric_name,
        time_range=time_range_str,
        data_source=data_source,
        num_records=len(exec_result.result_df) if exec_result.result_df is not None else 0,
    )


def _calculate_confidence(plan, exec_result) -> float:
    """Calculate confidence score (0~1)."""
    confidence = 1.0
    
    # Reduce confidence if clarification was needed
    if plan.clarification_needed:
        confidence *= 0.7
    
    # Reduce confidence if no results
    if exec_result.result_df is None or len(exec_result.result_df) == 0:
        confidence *= 0.5
    
    # Reduce confidence if filters are too broad (all defaults)
    if not plan.filters.region and not plan.filters.site_type:
        confidence *= 0.9
    
    return min(1.0, max(0.0, confidence))


def _generate_response(
    plan,
    exec_result,
    original_query: str
) -> CopilotResponse:
    """Generate CopilotResponse from plan execution result."""
    from src.copilot.navigation import create_nav_links_from_plan
    
    # Generate answer using LLM or rule-based
    answer = _generate_answer(original_query, plan, exec_result)
    
    # Build evidence
    evidence = _build_evidence(plan, exec_result)
    
    # Generate nav links
    nav_links = create_nav_links_from_plan(plan)
    
    # Calculate confidence
    confidence = _calculate_confidence(plan, exec_result)
    
    # Check ambiguity
    is_ambiguous = plan.clarification_needed or confidence < 0.7
    
    return CopilotResponse(
        answer=answer,
        evidence=evidence,
        nav_links=nav_links,
        confidence=confidence,
        is_ambiguous=is_ambiguous,
    )


def _process_query(query: str, dal: DataAccessLayer) -> None:
    """Process user query and generate response with context awareness."""
    try:
        # Generate message ID for user message
        user_msg_id = _get_next_message_id()
        
        # Add user message to history
        st.session_state.probe_history.append({
            "role": "user",
            "content": query,
            "message_id": user_msg_id
        })
        st.session_state.probe_last_query = query
        
        # Get conversation context
        conversation_context = _get_conversation_context(max_turns=10)
        
        # Get previous plan for merging
        previous_plan = st.session_state.get("probe_last_plan")
        
        # Generate plan (with context and previous plan)
        with st.spinner("질문을 분석하는 중..."):
            plan, plan_metadata = plan_with_fallback(
                user_query=query,
                conversation_context=conversation_context,
                previous_plan=previous_plan
            )
        
        # Check for clarification
        if plan.clarification_needed:
            st.session_state.probe_waiting_clarification = plan
            st.info("추가 정보가 필요합니다. 아래에서 선택해주세요.")
            st.rerun()
            return
        
        # Load data
        bills_df = dal.load_bills()
        actual_df = dal.load_actual()
        plan_df = dal.load_plan()
        site_master_df = dal.load_site_master()
        
        # Execute plan
        with st.spinner("데이터를 분석하는 중..."):
            exec_result = execute_plan(
                plan,
                bills_df=bills_df,
                actual_df=actual_df,
                plan_df=plan_df,
                site_master_df=site_master_df,
            )
        
        if not exec_result.success:
            error_msg = exec_result.error_message or "알 수 없는 오류"
            
            # Generate assistant message ID
            assistant_msg_id = _get_next_message_id()
            st.session_state.probe_history.append({
                "role": "assistant",
                "content": f"죄송합니다. 실행 중 오류가 발생했습니다: {error_msg}",
                "message_id": assistant_msg_id
            })
            st.rerun()
            return
        
        # Generate response
        response = _generate_response(plan, exec_result, query)
        
        # Generate assistant message ID
        assistant_msg_id = _get_next_message_id()
        
        # Add assistant message to history (with response object)
        st.session_state.probe_history.append({
            "role": "assistant",
            "content": response.answer,
            "message_id": assistant_msg_id,
            "response": response
        })
        
        # Save confirmed plan for next query
        st.session_state.probe_last_plan = plan
        
        st.rerun()
        
    except Exception as e:
        # Error handling: don't crash the app
        error_msg = str(e)
        st.error(f"❌ 오류 발생: {error_msg}")
        
        # Generate assistant message ID
        assistant_msg_id = _get_next_message_id()
        st.session_state.probe_history.append({
            "role": "assistant",
            "content": f"죄송합니다. 오류가 발생했습니다: {error_msg}",
            "message_id": assistant_msg_id
        })
        st.rerun()


# Query input section
st.markdown("---")
st.markdown("### 💬 질문 입력")

col1, col2 = st.columns([4, 1])

with col1:
    query = st.text_input(
        "PROBE에게 질문하세요",
        key="probe_query_input",
        placeholder="예: 동부지역 최근 2개월 전력사용량 상위 20개",
        help="전력량, 전기료, 추이, 비교 등 다양한 질문을 할 수 있습니다. '이어서', '그럼' 등으로 후속 질문도 가능합니다.",
        label_visibility="collapsed"
    )

with col2:
    submit_button = st.button("질문하기", type="primary", use_container_width=True)

# Process query
if submit_button and query:
    _process_query(query, dal)

# Show clarification if needed
if st.session_state.probe_waiting_clarification:
    st.markdown("---")
    plan = st.session_state.probe_waiting_clarification
    clarification_key = f"probe_clarification_{st.session_state.probe_message_counter}"
    try:
        answer = render_clarification(plan, key=clarification_key)
        if answer:
            # Refine query with answer
            refined_query = f"{st.session_state.probe_last_query} ({answer})"
            st.session_state.probe_waiting_clarification = None
            _process_query(refined_query, dal)
            st.rerun()
    except Exception as e:
        st.error(f"추가 질문 처리 오류: {str(e)}")

# Chat history (no duplicate output, newest first)
if st.session_state.probe_history:
    st.markdown("---")
    st.markdown("### 💬 대화 기록")
    
    try:
        # Render in reverse order (newest first)
        # Note: message_id is assigned at creation time, so key uniqueness is preserved
        for item in reversed(st.session_state.probe_history):
            message_id = item.get("message_id", f"probe_msg_{uuid.uuid4().hex[:8]}")
            
            if item["role"] == "user":
                # User message: simple chat bubble
                render_chat_message(
                    role=item["role"],
                    content=item["content"],
                    is_user=True,
                    message_id=message_id
                )
            else:
                # Assistant message: chat bubble + response details (evidence + links)
                response = item.get("response")
                if response:
                    # Render chat message with full response details
                    # Note: render_chat_message renders answer text ONCE,
                    # and render_probe_response (called inside) does NOT render it again
                    render_chat_message(
                        role=item["role"],
                        content=item["content"],
                        is_user=False,
                        message_id=message_id,
                        response=response
                    )
                else:
                    # Simple error message
                    render_chat_message(
                        role=item["role"],
                        content=item["content"],
                        is_user=False,
                        message_id=message_id
                    )
    except Exception as e:
        st.error(f"대화 기록 렌더링 오류: {str(e)}")

# Footer
st.markdown("---")
st.markdown(create_footer(), unsafe_allow_html=True)

