"""
Integration tests for Copilot system.

Tests plan generation, execution, and deeplink creation for sample queries.
"""

import pytest
from pathlib import Path
import pandas as pd

from src.copilot.planner import plan_with_fallback
from src.copilot.executor import execute_plan
from src.copilot.deeplink import create_deeplink_from_plan
from src.copilot.schemas import CopilotResponse
from src.data_access import DataAccessLayer


# Sample queries for testing
SAMPLE_QUERIES = [
    "동부지역 최근 2개월 전력사용량 상위 20개",
    "수도권 2024년 1월부터 12월까지 전기료 추이",
    "중부지역 기지국 최근 3개월 전기료가 가장 높은 국소 top10",
    "서부지역 정액제 한전계약 5G 국소 최근 6개월 전력사용량 상위 30개",
    "수도권의 청구서전력량과 실사용전력량 비교의 2024년에 관해 분석",
    "동부지역 IDC 최근 1개월 단가 추이",
    "전체 지역 최근 12개월 전력사용량이 가장 높은 중계국 top50",
    "수도권 RAPA 국소 최근 3개월 전기료 변화",
    "중부지역 건물계약 종량제 국소 최근 2개월 전력사용량 상위 15개",
    "2024년 1월 수도권 기지국 전기료 분석",
]


def test_plan_generation_and_execution():
    """Test plan generation and execution for sample queries."""
    data_dir = Path("data")
    dal = DataAccessLayer(data_dir)
    
    bills_df = dal.load_bills()
    actual_df = dal.load_actual()
    plan_df = dal.load_plan()
    site_master_df = dal.load_site_master()
    
    if bills_df.empty:
        pytest.skip("No data available for testing")
    
    for i, query in enumerate(SAMPLE_QUERIES, 1):
        try:
            # Generate plan
            plan, plan_metadata = plan_with_fallback(query)
            
            # Validate plan
            is_valid, error_msg = plan.validate()
            assert is_valid, f"Query {i} plan validation failed: {error_msg}"
            
            # Skip if clarification needed
            if plan.clarification_needed:
                print(f"Query {i}: Clarification needed - {plan.clarification_question}")
                continue
            
            # Execute plan
            exec_result = execute_plan(
                plan,
                bills_df=bills_df,
                actual_df=actual_df,
                plan_df=plan_df,
                site_master_df=site_master_df,
            )
            
            assert exec_result.success, f"Query {i} execution failed: {exec_result.error_message}"
            assert exec_result.result_df is not None, f"Query {i}: result_df is None"
            
            # Generate deeplinks
            links = create_deeplink_from_plan(plan)
            assert len(links) > 0, f"Query {i}: No deeplinks generated"
            assert len(links) <= 3, f"Query {i}: Too many deeplinks ({len(links)})"
            
            # Validate deeplinks
            for link in links:
                assert link.title, f"Query {i}: Link title is empty"
                assert link.url, f"Query {i}: Link URL is empty"
            
            print(f"✅ Query {i}: '{query}'")
            print(f"   - Plan: {plan.query_type}, {plan.metric}")
            print(f"   - Result: {len(exec_result.result_df)} rows")
            print(f"   - Links: {len(links)} deeplinks")
            
        except Exception as e:
            pytest.fail(f"Query {i} ('{query}') failed: {e}")


def test_deeplink_generation():
    """Test deeplink generation from plans."""
    for i, query in enumerate(SAMPLE_QUERIES[:5], 1):  # Test first 5
        try:
            plan, _ = plan_with_fallback(query)
            
            if plan.clarification_needed:
                continue
            
            links = create_deeplink_from_plan(plan)
            
            # Check that links are valid
            for link in links:
                assert link.title
                assert link.url
                # URL should start with / or be a valid path
                assert link.url.startswith("/") or "?" in link.url or link.url.startswith("pages/")
            
            print(f"✅ Deeplink test {i}: {len(links)} links generated")
            
        except Exception as e:
            pytest.fail(f"Deeplink test {i} failed: {e}")


if __name__ == "__main__":
    # Run tests
    try:
        test_plan_generation_and_execution()
        test_deeplink_generation()
        print("\n✅ All integration tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()



