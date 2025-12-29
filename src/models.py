"""Data models for PYLON platform."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum


class ActionStatus(Enum):
    """Action status enumeration."""
    TODO = "TODO"
    DOING = "DOING"
    DONE = "DONE"
    
    def to_korean(self) -> str:
        """Convert status to Korean display label."""
        mapping = {
            "TODO": "해야 할 일",
            "DOING": "진행 중",
            "DONE": "완료"
        }
        return mapping.get(self.value, self.value)


class ActionCategory(Enum):
    """Action category enumeration."""
    CONTRACT_OPTIMIZATION = "계약전력 최적화"
    TARIFF_CHANGE = "요금제 변경"
    ANOMALY_INVESTIGATION = "이상 조사"
    ZERO_USAGE = "사용량 0 조사"
    BILL_ACTUAL_MISMATCH = "청구서 불일치"
    VERIFICATION = "효과 검증"
    OTHER = "기타"


class DataSource(Enum):
    """Data source enumeration."""
    EMS = "EMS"
    PRB = "PRB"
    EST = "EST"


class ValidationState(Enum):
    """Validation state for widgets."""
    HYPOTHESIS = "Hypothesis"
    IN_FLIGHT = "In-flight"
    VERIFIED = "Verified"
    
    def to_korean(self) -> str:
        """Convert validation state to Korean display label."""
        mapping = {
            "Hypothesis": "가설",
            "In-flight": "진행중",
            "Verified": "검증완료"
        }
        return mapping.get(self.value, self.value)


@dataclass
class Action:
    """Action/Ticket record."""
    id: str
    created_at: datetime
    due_date: datetime
    owner: str
    status: ActionStatus
    category: ActionCategory
    site_id: Optional[str]
    description: str
    evidence_links: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'due_date': self.due_date.isoformat(),
            'owner': self.owner,
            'status': self.status.value,
            'category': self.category.value,
            'site_id': self.site_id,
            'description': self.description,
            'evidence_links': ','.join(self.evidence_links)
        }
    
    @classmethod
    def from_dict(cls, d: dict) -> 'Action':
        """Create from dictionary."""
        return cls(
            id=d['id'],
            created_at=datetime.fromisoformat(d['created_at']),
            due_date=datetime.fromisoformat(d['due_date']),
            owner=d['owner'],
            status=ActionStatus(d['status']),
            category=ActionCategory(d['category']),
            site_id=d.get('site_id'),
            description=d['description'],
            evidence_links=d['evidence_links'].split(',') if d.get('evidence_links') else []
        )


@dataclass
class Experiment:
    """Experiment record for IDEA validation."""
    id: str
    hypothesis: str
    kpi: str
    scope: str
    start_date: datetime
    end_date: datetime
    status: str  # "설계" / "진행중" / "완료" / "중단"
    results: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            'id': self.id,
            'hypothesis': self.hypothesis,
            'kpi': self.kpi,
            'scope': self.scope,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'status': self.status,
            'results': self.results or '',
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, d: dict) -> 'Experiment':
        """Create from dictionary."""
        return cls(
            id=d['id'],
            hypothesis=d['hypothesis'],
            kpi=d['kpi'],
            scope=d['scope'],
            start_date=datetime.fromisoformat(d['start_date']),
            end_date=datetime.fromisoformat(d['end_date']),
            status=d['status'],
            results=d.get('results') if d.get('results') else None,
            created_at=datetime.fromisoformat(d.get('created_at', datetime.now().isoformat()))
        )


@dataclass
class GovernanceBadge:
    """Governance badge information."""
    official_version: str = "v2.3"
    plan_locked: bool = True
    data_freshness: str = "2024-01"  # Will be computed from data
    exceptions_applied: int = 0
    
    @staticmethod
    def create_from_config_and_data(config: dict, latest_yymm = None) -> 'GovernanceBadge':
        """
        Create badge from config and computed data.
        
        Args:
            config: Configuration dictionary
            latest_yymm: Latest month from data (YYMM or YYYYMM format, int or str)
        
        Returns:
            GovernanceBadge instance
        """
        # Format data freshness
        data_freshness = "N/A"
        
        if latest_yymm is not None:
            # Convert to string
            yymm_str = str(latest_yymm)
            
            # Handle both YYYYMM (6 digits) and YYMM (4 digits) formats
            if len(yymm_str) == 6:  # New format: 202401
                year = yymm_str[:4]
                month = yymm_str[4:6]
                data_freshness = f"{year}-{month}"
            elif len(yymm_str) == 4:  # Old format: 2401
                year = f"20{yymm_str[:2]}"
                month = yymm_str[2:4]
                data_freshness = f"{year}-{month}"
        
        return GovernanceBadge(
            official_version=config.get('official_version', 'v1.0'),
            plan_locked=config.get('plan_locked', False),
            data_freshness=data_freshness,
            exceptions_applied=config.get('exception_applied', 0)
        )

