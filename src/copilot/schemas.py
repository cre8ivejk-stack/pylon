"""
Plan schema definitions for Copilot NLQ system.

This module defines the structured plan schema that LLM generates from natural language queries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Literal, Dict, Any
from enum import Enum


class QueryType(str, Enum):
    """Query type enumeration."""
    TOP_N = "top_n"
    TREND = "trend"
    COMPARISON = "comparison"
    ANOMALY = "anomaly"
    RECOMMENDATION = "recommendation"


class Metric(str, Enum):
    """Metric enumeration."""
    USAGE_KWH = "usage_kwh"
    COST_WON = "cost_won"
    UNIT_COST = "unit_cost"
    BILL_VS_ACTUAL_GAP = "bill_vs_actual_gap"


@dataclass
class TimeRange:
    """Time range specification."""
    type: Literal["last_n_months", "yymm_range", "single_yymm"]
    # For last_n_months
    n: Optional[int] = None
    # For yymm_range
    start_yymm: Optional[int] = None
    end_yymm: Optional[int] = None
    # For single_yymm
    yymm: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {"type": self.type}
        if self.n is not None:
            result["n"] = self.n
        if self.start_yymm is not None:
            result["start_yymm"] = self.start_yymm
        if self.end_yymm is not None:
            result["end_yymm"] = self.end_yymm
        if self.yymm is not None:
            result["yymm"] = self.yymm
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TimeRange:
        """Create TimeRange from dictionary."""
        return cls(
            type=data["type"],
            n=data.get("n"),
            start_yymm=data.get("start_yymm"),
            end_yymm=data.get("end_yymm"),
            yymm=data.get("yymm"),
        )


@dataclass
class Filters:
    """Filter specifications."""
    region: Optional[List[str]] = None
    site_type: Optional[List[str]] = None
    contract_type_major: Optional[List[str]] = None
    contract_target: Optional[str] = None
    rapa: Optional[str] = None
    network_gen: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {}
        if self.region:
            result["region"] = self.region
        if self.site_type:
            result["site_type"] = self.site_type
        if self.contract_type_major:
            result["contract_type_major"] = self.contract_type_major
        if self.contract_target:
            result["contract_target"] = self.contract_target
        if self.rapa:
            result["rapa"] = self.rapa
        if self.network_gen:
            result["network_gen"] = self.network_gen
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Filters:
        """Create Filters from dictionary."""
        return cls(
            region=data.get("region"),
            site_type=data.get("site_type"),
            contract_type_major=data.get("contract_type_major"),
            contract_target=data.get("contract_target"),
            rapa=data.get("rapa"),
            network_gen=data.get("network_gen"),
        )


@dataclass
class Plan:
    """
    Structured plan for executing a natural language query.
    
    This is the output of the LLM planner and input to the executor.
    """
    query_type: str  # QueryType enum value
    metric: str  # Metric enum value
    time_range: TimeRange
    filters: Filters
    group_by: Optional[List[str]] = None
    top_n: Optional[int] = None
    clarification_needed: bool = False
    clarification_question: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "query_type": self.query_type,
            "metric": self.metric,
            "time_range": self.time_range.to_dict(),
            "filters": self.filters.to_dict(),
            "clarification_needed": self.clarification_needed,
        }
        if self.group_by:
            result["group_by"] = self.group_by
        if self.top_n is not None:
            result["top_n"] = self.top_n
        if self.clarification_question:
            result["clarification_question"] = self.clarification_question
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Plan:
        """Create Plan from dictionary."""
        return cls(
            query_type=data["query_type"],
            metric=data["metric"],
            time_range=TimeRange.from_dict(data["time_range"]),
            filters=Filters.from_dict(data.get("filters", {})),
            group_by=data.get("group_by"),
            top_n=data.get("top_n"),
            clarification_needed=data.get("clarification_needed", False),
            clarification_question=data.get("clarification_question"),
        )
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate plan structure.
        
        Returns:
            (is_valid, error_message)
        """
        # Validate query_type
        valid_query_types = {qt.value for qt in QueryType}
        if self.query_type not in valid_query_types:
            return False, f"Invalid query_type: {self.query_type}. Must be one of {valid_query_types}"
        
        # Validate metric
        valid_metrics = {m.value for m in Metric}
        if self.metric not in valid_metrics:
            return False, f"Invalid metric: {self.metric}. Must be one of {valid_metrics}"
        
        # Validate time_range
        if self.time_range.type == "last_n_months":
            if self.time_range.n is None or self.time_range.n <= 0:
                return False, "time_range.n must be positive integer for last_n_months"
        elif self.time_range.type == "yymm_range":
            if self.time_range.start_yymm is None or self.time_range.end_yymm is None:
                return False, "time_range.start_yymm and end_yymm required for yymm_range"
        elif self.time_range.type == "single_yymm":
            if self.time_range.yymm is None:
                return False, "time_range.yymm required for single_yymm"
        else:
            return False, f"Invalid time_range.type: {self.time_range.type}"
        
        # Validate top_n for top_n queries
        if self.query_type == "top_n" and (self.top_n is None or self.top_n <= 0):
            return False, "top_n must be positive integer for top_n queries"
        
        # Validate clarification
        if self.clarification_needed and not self.clarification_question:
            return False, "clarification_question required when clarification_needed=true"
        
        return True, None


@dataclass
class Evidence:
    """Evidence information for Copilot response."""
    applied_filters: Dict[str, Any]
    metric: str
    time_range: str
    data_source: str
    num_records: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "applied_filters": self.applied_filters,
            "metric": self.metric,
            "time_range": self.time_range,
            "data_source": self.data_source,
            "num_records": self.num_records,
        }


@dataclass
class Deeplink:
    """Deeplink information (legacy, for backward compatibility)."""
    title: str
    url: str
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "title": self.title,
            "url": self.url,
        }
        if self.description:
            result["description"] = self.description
        return result


@dataclass
class NavLink:
    """
    Navigation link using session_state instead of URL query params.
    
    This is the new standard for Copilot navigation.
    """
    title: str
    target_page: str  # e.g., "pages/1_에너지_인텔리전스.py"
    nav_payload: Dict[str, Any]  # {"filters": {...}, "context": {...}}
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "title": self.title,
            "target_page": self.target_page,
            "nav_payload": self.nav_payload,
        }
        if self.description:
            result["description"] = self.description
        return result


@dataclass
class CopilotResponse:
    """
    Copilot response structure.
    
    Contains answer, evidence, links, and confidence.
    """
    answer: str  # 요약 답변 (5줄 이내)
    evidence: Evidence
    nav_links: List[NavLink]  # 1~3개 (새로운 표준)
    confidence: float  # 0~1
    is_ambiguous: bool = False
    links: Optional[List[Deeplink]] = None  # 레거시 호환용
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "answer": self.answer,
            "evidence": self.evidence.to_dict(),
            "nav_links": [link.to_dict() for link in self.nav_links],
            "confidence": self.confidence,
            "is_ambiguous": self.is_ambiguous,
        }
        if self.links:
            result["links"] = [link.to_dict() for link in self.links]
        return result


# Supported filter values
SUPPORTED_REGIONS = ["수도권", "중부", "동부", "서부"]
SUPPORTED_SITE_TYPES = ["기지국", "통합국", "사옥", "중계국", "IDC", "기타"]
SUPPORTED_CONTRACT_TYPES = ["정액", "종량"]
SUPPORTED_CONTRACT_TARGETS = ["전체", "한전계약(ME)", "건물계약(MC)"]
SUPPORTED_RAPA = ["전체", "RAPA", "비RAPA"]
SUPPORTED_NETWORK_GEN = ["3G", "LTE", "5G"]
SUPPORTED_GROUP_BY = ["yymm", "region", "site_type", "contract_type", "contract_target", "rapa", "network_gen"]

