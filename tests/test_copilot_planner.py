"""
Test cases for Copilot planner.

Tests plan generation from sample queries.
"""

import pytest
from src.copilot.planner import plan_with_fallback
from src.copilot.schemas import Plan


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


def test_plan_schema_validation():
    """Test that all sample queries generate valid plans."""
    for i, query in enumerate(SAMPLE_QUERIES, 1):
        try:
            plan, metadata = plan_with_fallback(query)
            
            # Validate plan structure
            assert isinstance(plan, Plan), f"Query {i}: Plan is not Plan instance"
            
            # Validate plan
            is_valid, error_msg = plan.validate()
            assert is_valid, f"Query {i} validation failed: {error_msg}"
            
            # Check required fields
            assert plan.query_type, f"Query {i}: query_type is missing"
            assert plan.metric, f"Query {i}: metric is missing"
            assert plan.time_range, f"Query {i}: time_range is missing"
            assert plan.filters is not None, f"Query {i}: filters is missing"
            
            # Check time_range structure
            assert plan.time_range.type in ["last_n_months", "yymm_range", "single_yymm"], \
                f"Query {i}: Invalid time_range.type"
            
            if plan.time_range.type == "last_n_months":
                assert plan.time_range.n is not None and plan.time_range.n > 0, \
                    f"Query {i}: time_range.n must be positive"
            elif plan.time_range.type == "yymm_range":
                assert plan.time_range.start_yymm is not None, \
                    f"Query {i}: time_range.start_yymm required"
                assert plan.time_range.end_yymm is not None, \
                    f"Query {i}: time_range.end_yymm required"
            elif plan.time_range.type == "single_yymm":
                assert plan.time_range.yymm is not None, \
                    f"Query {i}: time_range.yymm required"
            
            # Check top_n for top_n queries
            if plan.query_type == "top_n":
                assert plan.top_n is not None and plan.top_n > 0, \
                    f"Query {i}: top_n required for top_n queries"
            
            # Check clarification
            if plan.clarification_needed:
                assert plan.clarification_question, \
                    f"Query {i}: clarification_question required when clarification_needed=true"
            
            print(f"✅ Query {i}: '{query}' -> Valid plan")
            print(f"   - query_type: {plan.query_type}")
            print(f"   - metric: {plan.metric}")
            print(f"   - time_range: {plan.time_range.type}")
            print(f"   - method: {metadata.get('method', 'unknown')}")
            
        except Exception as e:
            pytest.fail(f"Query {i} ('{query}') failed: {e}")


if __name__ == "__main__":
    # Run tests
    try:
        test_plan_schema_validation()
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

