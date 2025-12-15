"""과제 목록 및 메타데이터 정의

전략문서의 과제 체계와 연동되는 과제 카탈로그입니다.
"""

from typing import Dict, List
from dataclasses import dataclass

@dataclass
class Task:
    """과제 정보"""
    task_id: str
    task_name: str
    domain: str  # '억세스분야', '설비분야', 'Core/전송'
    description: str
    status: str = "진행 중"  # 진행 중, 완료, 계획, 중단


# 과제 카탈로그
TASK_CATALOG: List[Task] = [
    # 억세스분야
    Task(
        task_id="ACCESS_001",
        task_name="LTE Mod.",
        domain="억세스분야",
        description="LTE 모듈 최적화를 통한 전력 절감"
    ),
    Task(
        task_id="ACCESS_002",
        task_name="3G Fade-Out",
        domain="억세스분야",
        description="3G 서비스 단계적 종료"
    ),
    Task(
        task_id="ACCESS_003",
        task_name="SA",
        domain="억세스분야",
        description="5G SA(Standalone) 전환"
    ),
    Task(
        task_id="ACCESS_004",
        task_name="Power Saving",
        domain="억세스분야",
        description="기지국 전력 절감 모드 적용"
    ),
    Task(
        task_id="ACCESS_005",
        task_name="E-Project",
        domain="억세스분야",
        description="에너지 효율화 통합 프로젝트"
    ),
    Task(
        task_id="ACCESS_006",
        task_name="3G출력조절",
        domain="억세스분야",
        description="3G 송출 전력 최적화"
    ),
    
    # 설비분야
    Task(
        task_id="FACILITY_001",
        task_name="노후냉방기 대체",
        domain="설비분야",
        description="노후 냉방기 고효율 장비로 교체"
    ),
    Task(
        task_id="FACILITY_002",
        task_name="외기냉방",
        domain="설비분야",
        description="외기 냉방 시스템 도입 (Dual)"
    ),
    Task(
        task_id="FACILITY_003",
        task_name="필름형태양광",
        domain="설비분야",
        description="필름형 태양광 패널 설치"
    ),
    Task(
        task_id="FACILITY_004",
        task_name="온도상향",
        domain="설비분야",
        description="냉방 설정 온도 상향 조정"
    ),
    
    # Core/전송
    Task(
        task_id="CORE_001",
        task_name="F/H Zero Power化",
        domain="Core/전송",
        description="Fronthaul/Backhaul 제로 파워 모드"
    ),
    Task(
        task_id="CORE_002",
        task_name="Server Power Saving",
        domain="Core/전송",
        description="서버 전력 절감 모드 적용"
    ),
]


def get_tasks_by_domain(domain: str) -> List[Task]:
    """도메인별 과제 목록 반환
    
    Args:
        domain: '억세스분야', '설비분야', 'Core/전송', '전체'
    
    Returns:
        해당 도메인의 과제 리스트
    """
    if domain == '전체':
        return TASK_CATALOG
    return [task for task in TASK_CATALOG if task.domain == domain]


def get_task_by_id(task_id: str) -> Task:
    """과제 ID로 과제 정보 반환"""
    for task in TASK_CATALOG:
        if task.task_id == task_id:
            return task
    return None


def get_domains() -> List[str]:
    """전체 도메인 목록 반환"""
    return ['억세스분야', '설비분야', 'Core/전송']

