"""
Copilot module for PYLON platform.
Provides deeplink generation, navigation helpers, and NLQ planning.
"""

from src.copilot.deeplink import (
    create_deeplink,
    parse_filters_from_query_params,
    update_query_params_from_filters,
    FilterParams,
)

from src.copilot.schemas import (
    Plan,
    QueryType,
    Metric,
    TimeRange,
    Filters,
)

from src.copilot.planner import (
    plan_with_llm,
    plan_with_fallback,
)

from src.copilot.ui import (
    render_clarification,
    render_plan_summary,
    render_plan_execution_result,
    render_query_input,
    render_copilot_response,
    render_chat_message,
)

from src.copilot.executor import (
    execute_plan,
    ExecutionResult,
)

from src.copilot.schemas import (
    Evidence,
    Deeplink,
    CopilotResponse,
    NavLink,
)

from src.copilot.navigation import (
    create_nav_links_from_plan,
    apply_copilot_nav_to_filters,
)

__all__ = [
    # Deeplink
    "create_deeplink",
    "parse_filters_from_query_params",
    "update_query_params_from_filters",
    "FilterParams",
    # Schemas
    "Plan",
    "QueryType",
    "Metric",
    "TimeRange",
    "Filters",
    # Planner
    "plan_with_llm",
    "plan_with_fallback",
    # UI
    "render_clarification",
    "render_plan_summary",
    "render_plan_execution_result",
    "render_query_input",
    "render_copilot_response",
    "render_chat_message",
    # Executor
    "execute_plan",
    "ExecutionResult",
    # Response schemas
    "Evidence",
    "Deeplink",
    "CopilotResponse",
    "NavLink",
    # Navigation
    "create_nav_links_from_plan",
    "apply_copilot_nav_to_filters",
]

