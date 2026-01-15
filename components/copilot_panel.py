"""
Copilot panel component for PYLON platform.

This component provides a persistent Copilot UI that can be used across all pages.
"""

from __future__ import annotations

import streamlit as st
from typing import Optional, Dict, Any, List
import pandas as pd

from src.copilot.planner import plan_with_fallback
from src.copilot.executor import execute_plan
from src.copilot.schemas import (
    Plan,
    CopilotResponse,
    Evidence,
    Deeplink,
    Metric,
)
from src.copilot.navigation import create_nav_links_from_plan
from src.copilot.ui import (
    render_clarification,
    render_copilot_response,
    render_chat_message,
    render_query_input,
)
from src.data_access import DataAccessLayer
from pathlib import Path


def initialize_copilot_session():
    """Initialize Copilot session state."""
    if "copilot_history" not in st.session_state:
        st.session_state.copilot_history = []
    if "copilot_waiting_clarification" not in st.session_state:
        st.session_state.copilot_waiting_clarification = None


def render_copilot_panel(
    data_dir: Optional[Path] = None,
    position: str = "sidebar"
) -> None:
    """
    Render Copilot panel in sidebar or main area.
    
    Args:
        data_dir: Data directory path (optional, will use default if not provided)
        position: "sidebar" or "main"
    """
    initialize_copilot_session()
    
    container = st.sidebar if position == "sidebar" else st.container()
    
    with container:
        st.markdown("---")
        st.markdown("## 🤖 PYLON Copilot")
        st.caption("자연어로 질문하시면 분석 결과를 제공합니다.")
        
        # Query input
        query = render_query_input(key="copilot_query_input")
        
        # Execute button
        if st.button("질문하기", key="copilot_submit", type="primary", use_container_width=True):
            if query:
                _process_query(query, data_dir)
        
        # Show clarification if needed
        if st.session_state.copilot_waiting_clarification:
            plan = st.session_state.copilot_waiting_clarification
            answer = render_clarification(plan)
            if answer:
                # Refine query with answer
                refined_query = f"{st.session_state.copilot_last_query} ({answer})"
                st.session_state.copilot_waiting_clarification = None
                _process_query(refined_query, data_dir)
        
        # Show chat history
        if st.session_state.copilot_history:
            st.markdown("---")
            st.markdown("### 💬 대화 기록")
            for item in st.session_state.copilot_history[-5:]:  # Show last 5
                render_chat_message(
                    role=item["role"],
                    content=item["content"],
                    is_user=(item["role"] == "user")
                )


def _process_query(query: str, data_dir: Optional[Path] = None) -> None:
    """Process user query and generate response."""
    if not data_dir:
        data_dir = Path("data")
    
    # Add to history
    st.session_state.copilot_history.append({
        "role": "user",
        "content": query
    })
    st.session_state.copilot_last_query = query
    
    try:
        # Generate plan
        with st.spinner("질문을 분석하는 중..."):
            plan, plan_metadata = plan_with_fallback(query)
        
        # Check for clarification
        if plan.clarification_needed:
            st.session_state.copilot_waiting_clarification = plan
            st.info("추가 정보가 필요합니다. 아래에서 선택해주세요.")
            st.rerun()
            return
        
        # Load data
        dal = DataAccessLayer(data_dir)
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
            st.error(f"❌ 실행 실패: {error_msg}")
            st.session_state.copilot_history.append({
                "role": "assistant",
                "content": f"죄송합니다. 실행 중 오류가 발생했습니다: {error_msg}"
            })
            return
        
        # Generate response
        response = _generate_response(plan, exec_result, query)
        
        # Add to history
        st.session_state.copilot_history.append({
            "role": "assistant",
            "content": response.answer
        })
        
        # Display response
        render_copilot_response(response)
        
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ 오류 발생: {str(e)}")
        st.session_state.copilot_history.append({
            "role": "assistant",
            "content": f"죄송합니다. 오류가 발생했습니다: {str(e)}"
        })


def _generate_response(
    plan: Plan,
    exec_result: 'ExecutionResult',
    original_query: str
) -> CopilotResponse:
    """
    Generate CopilotResponse from plan execution result.
    
    Args:
        plan: Executed plan
        exec_result: Execution result
        original_query: Original user query
    
    Returns:
        CopilotResponse object
    """
    from src.copilot.executor import ExecutionResult
    
    # Generate answer using LLM or rule-based
    answer = _generate_answer_with_llm(original_query, plan, exec_result)
    
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


def _generate_answer_with_llm(
    query: str,
    plan: Plan,
    exec_result: 'ExecutionResult'
) -> str:
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
                    "content": "너는 PYLON 에너지 운영 플랫폼의 Copilot이다. 분석 결과를 사용자에게 자연스럽고 전문적으로 설명한다."
                },
                {"role": "user", "content": answer_prompt},
            ],
        )
        
        return (resp.choices[0].message.content or "").strip()
        
    except Exception:
        # Fallback to rule-based answer
        return _generate_rule_based_answer(plan, exec_result)


def _generate_rule_based_answer(
    plan: Plan,
    exec_result: 'ExecutionResult'
) -> str:
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


def _build_evidence(
    plan: Plan,
    exec_result: 'ExecutionResult'
) -> Evidence:
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


def _calculate_confidence(
    plan: Plan,
    exec_result: 'ExecutionResult'
) -> float:
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

