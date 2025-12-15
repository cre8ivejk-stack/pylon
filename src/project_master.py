"""과제 마스터 관리"""

import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime


class ProjectMasterManager:
    """과제 마스터 데이터 관리"""
    
    def __init__(self, data_dir: Path):
        """
        초기화
        
        Args:
            data_dir: 데이터 디렉토리
        """
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.file_path = self.data_dir / "project_master.parquet"
        
        # 초기 데이터가 없으면 생성
        if not self.file_path.exists():
            self._create_initial_projects()
    
    def _create_initial_projects(self):
        """표준 과제 목록 초기화"""
        initial_projects = [
            # 억세스분야
            {
                'project_id': 'PRJ_ACCESS_001',
                'project_name': 'LTE Mod.',
                'domain': '억세스분야',
                'status': '진행 중',
                'target_savings_krw': 150_000_000,
                'actual_savings_krw': 120_000_000,
                'verified_savings_krw': 0,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            },
            {
                'project_id': 'PRJ_ACCESS_002',
                'project_name': '3G Fade-Out',
                'domain': '억세스분야',
                'status': '완료',
                'target_savings_krw': 200_000_000,
                'actual_savings_krw': 210_000_000,
                'verified_savings_krw': 0,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            },
            {
                'project_id': 'PRJ_ACCESS_003',
                'project_name': 'SA',
                'domain': '억세스분야',
                'status': '진행 중',
                'target_savings_krw': 180_000_000,
                'actual_savings_krw': 150_000_000,
                'verified_savings_krw': 0,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            },
            {
                'project_id': 'PRJ_ACCESS_004',
                'project_name': 'Power Saving',
                'domain': '억세스분야',
                'status': '진행 중',
                'target_savings_krw': 120_000_000,
                'actual_savings_krw': 100_000_000,
                'verified_savings_krw': 0,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            },
            {
                'project_id': 'PRJ_ACCESS_005',
                'project_name': 'E-Project',
                'domain': '억세스분야',
                'status': '해야 할 일',
                'target_savings_krw': 100_000_000,
                'actual_savings_krw': 0,
                'verified_savings_krw': 0,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            },
            {
                'project_id': 'PRJ_ACCESS_006',
                'project_name': '3G출력조절',
                'domain': '억세스분야',
                'status': '진행 중',
                'target_savings_krw': 90_000_000,
                'actual_savings_krw': 85_000_000,
                'verified_savings_krw': 0,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            },
            # 설비분야
            {
                'project_id': 'PRJ_FACILITY_001',
                'project_name': '노후냉방기 교체',
                'domain': '설비분야',
                'status': '진행 중',
                'target_savings_krw': 250_000_000,
                'actual_savings_krw': 230_000_000,
                'verified_savings_krw': 0,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            },
            {
                'project_id': 'PRJ_FACILITY_002',
                'project_name': '외기냉방',
                'domain': '설비분야',
                'status': '진행 중',
                'target_savings_krw': 180_000_000,
                'actual_savings_krw': 170_000_000,
                'verified_savings_krw': 0,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            },
            {
                'project_id': 'PRJ_FACILITY_003',
                'project_name': '필름형태양광',
                'domain': '설비분야',
                'status': '해야 할 일',
                'target_savings_krw': 80_000_000,
                'actual_savings_krw': 0,
                'verified_savings_krw': 0,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            },
            {
                'project_id': 'PRJ_FACILITY_004',
                'project_name': '온도상향',
                'domain': '설비분야',
                'status': '진행 중',
                'target_savings_krw': 130_000_000,
                'actual_savings_krw': 120_000_000,
                'verified_savings_krw': 0,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            },
            # Core/전송
            {
                'project_id': 'PRJ_CORE_001',
                'project_name': 'F/H Zero Power화',
                'domain': 'Core/전송',
                'status': '진행 중',
                'target_savings_krw': 160_000_000,
                'actual_savings_krw': 140_000_000,
                'verified_savings_krw': 0,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            },
            {
                'project_id': 'PRJ_CORE_002',
                'project_name': 'Server Power Saving',
                'domain': 'Core/전송',
                'status': '진행 중',
                'target_savings_krw': 110_000_000,
                'actual_savings_krw': 105_000_000,
                'verified_savings_krw': 0,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        ]
        
        df = pd.DataFrame(initial_projects)
        df.to_parquet(self.file_path, index=False)
    
    def load_projects(self) -> pd.DataFrame:
        """과제 목록 로드"""
        if not self.file_path.exists():
            self._create_initial_projects()
        
        return pd.read_parquet(self.file_path)
    
    def add_project(
        self,
        project_name: str,
        domain: str,
        target_savings_krw: float = 0,
        status: str = '해야 할 일'
    ) -> str:
        """
        과제 추가
        
        Args:
            project_name: 과제명
            domain: 대분류 (억세스분야/설비분야/Core/전송)
            target_savings_krw: 목표 절감액
            status: 진행 상태
        
        Returns:
            생성된 project_id
        """
        df = self.load_projects()
        
        # Generate new project_id
        domain_prefix_map = {
            '억세스분야': 'ACCESS',
            '설비분야': 'FACILITY',
            'Core/전송': 'CORE'
        }
        prefix = domain_prefix_map.get(domain, 'OTHER')
        existing_ids = df[df['domain'] == domain]['project_id'].tolist()
        
        # Find next available number
        max_num = 0
        for pid in existing_ids:
            try:
                num = int(pid.split('_')[-1])
                max_num = max(max_num, num)
            except:
                pass
        
        new_id = f"PRJ_{prefix}_{max_num + 1:03d}"
        
        # Create new project
        new_project = {
            'project_id': new_id,
            'project_name': project_name,
            'domain': domain,
            'status': status,
            'target_savings_krw': target_savings_krw,
            'actual_savings_krw': 0,
            'verified_savings_krw': 0,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Append and save
        df = pd.concat([df, pd.DataFrame([new_project])], ignore_index=True)
        df.to_parquet(self.file_path, index=False)
        
        return new_id
    
    def update_project(
        self,
        project_id: str,
        actual_savings_krw: Optional[float] = None,
        verified_savings_krw: Optional[float] = None,
        status: Optional[str] = None
    ) -> bool:
        """
        과제 정보 업데이트
        
        Args:
            project_id: 과제 ID
            actual_savings_krw: 실적 절감액
            verified_savings_krw: 확정 절감액
            status: 진행 상태
        
        Returns:
            성공 여부
        """
        df = self.load_projects()
        
        if project_id not in df['project_id'].values:
            return False
        
        mask = df['project_id'] == project_id
        
        if actual_savings_krw is not None:
            df.loc[mask, 'actual_savings_krw'] = actual_savings_krw
        
        if verified_savings_krw is not None:
            df.loc[mask, 'verified_savings_krw'] = verified_savings_krw
        
        if status is not None:
            df.loc[mask, 'status'] = status
        
        df.loc[mask, 'updated_at'] = datetime.now().isoformat()
        
        df.to_parquet(self.file_path, index=False)
        return True
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """특정 과제 조회"""
        df = self.load_projects()
        
        project_rows = df[df['project_id'] == project_id]
        
        if len(project_rows) == 0:
            return None
        
        return project_rows.iloc[0].to_dict()


