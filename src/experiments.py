"""Experiment management for IDEA validation."""

import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime
from typing import Optional
from src.models import Experiment


class ExperimentManager:
    """Manage experiments for IDEA validation."""
    
    def __init__(self, data_dir: Path):
        """
        Initialize experiment manager.
        
        Args:
            data_dir: Directory to store experiments.parquet
        """
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.experiments_file = self.data_dir / "experiments.parquet"
    
    def load_experiments(self) -> pd.DataFrame:
        """Load all experiments from storage."""
        if not self.experiments_file.exists():
            return pd.DataFrame(columns=[
                'id', 'hypothesis', 'kpi', 'scope', 'start_date',
                'end_date', 'status', 'results', 'created_at'
            ])
        
        try:
            df = pd.read_parquet(self.experiments_file)
            return df
        except Exception as e:
            st.error(f"실험 데이터 로드 실패: {e}")
            return pd.DataFrame()
    
    def save_experiments(self, df: pd.DataFrame) -> None:
        """Save experiments to storage."""
        try:
            df.to_parquet(self.experiments_file, index=False)
        except Exception as e:
            st.error(f"실험 저장 실패: {e}")
    
    def create_experiment(
        self,
        hypothesis: str,
        kpi: str,
        scope: str,
        start_date: datetime,
        end_date: datetime,
        status: str = "설계"
    ) -> Experiment:
        """
        Create a new experiment.
        
        Args:
            hypothesis: Experiment hypothesis
            kpi: Key performance indicator
            scope: Experiment scope
            start_date: Start date
            end_date: End date
            status: Initial status
        
        Returns:
            Created Experiment object
        """
        experiments_df = self.load_experiments()
        
        # Generate ID
        if len(experiments_df) == 0:
            exp_id = "EXP0001"
        else:
            last_id = experiments_df['id'].max()
            num = int(last_id[3:]) + 1
            exp_id = f"EXP{num:04d}"
        
        experiment = Experiment(
            id=exp_id,
            hypothesis=hypothesis,
            kpi=kpi,
            scope=scope,
            start_date=start_date,
            end_date=end_date,
            status=status
        )
        
        # Append to dataframe
        new_row = pd.DataFrame([experiment.to_dict()])
        experiments_df = pd.concat([experiments_df, new_row], ignore_index=True)
        self.save_experiments(experiments_df)
        
        return experiment
    
    def update_experiment(
        self,
        exp_id: str,
        status: Optional[str] = None,
        results: Optional[str] = None
    ) -> bool:
        """
        Update experiment.
        
        Args:
            exp_id: Experiment ID
            status: New status (optional)
            results: New results (optional)
        
        Returns:
            Success boolean
        """
        experiments_df = self.load_experiments()
        
        if exp_id not in experiments_df['id'].values:
            st.error(f"실험 ID {exp_id}를 찾을 수 없습니다.")
            return False
        
        if status:
            experiments_df.loc[experiments_df['id'] == exp_id, 'status'] = status
        if results:
            experiments_df.loc[experiments_df['id'] == exp_id, 'results'] = results
        
        self.save_experiments(experiments_df)
        return True
    
    def get_active_experiments(self) -> pd.DataFrame:
        """Get active experiments (not 완료 or 중단)."""
        experiments_df = self.load_experiments()
        if len(experiments_df) == 0:
            return experiments_df
        return experiments_df[~experiments_df['status'].isin(['완료', '중단'])]




