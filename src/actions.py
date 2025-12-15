"""Action management system for PYLON platform."""

import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional
from src.models import Action, ActionStatus, ActionCategory


class ActionManager:
    """Manage action lifecycle and persistence."""
    
    def __init__(self, data_dir: Path):
        """
        Initialize action manager.
        
        Args:
            data_dir: Directory to store actions.parquet
        """
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.actions_file = self.data_dir / "actions.parquet"
    
    def load_actions(self) -> pd.DataFrame:
        """Load all actions from storage."""
        if not self.actions_file.exists():
            return pd.DataFrame(columns=[
                'id', 'created_at', 'due_date', 'owner', 'status',
                'category', 'site_id', 'description', 'evidence_links'
            ])
        
        try:
            df = pd.read_parquet(self.actions_file)
            return df
        except Exception as e:
            st.error(f"조치 데이터 로드 실패: {e}")
            return pd.DataFrame()
    
    def save_actions(self, df: pd.DataFrame) -> None:
        """Save actions to storage."""
        try:
            df.to_parquet(self.actions_file, index=False)
        except Exception as e:
            st.error(f"조치 저장 실패: {e}")
    
    def create_action(
        self,
        owner: str,
        category: ActionCategory,
        description: str,
        site_id: Optional[str] = None,
        evidence_links: Optional[List[str]] = None,
        due_days: int = 7
    ) -> Action:
        """
        Create a new action.
        
        Args:
            owner: Action owner
            category: Action category
            description: Action description
            site_id: Related site ID (optional)
            evidence_links: Links to evidence (optional)
            due_days: Days until due date
        
        Returns:
            Created Action object
        """
        now = datetime.now()
        actions_df = self.load_actions()
        
        # Generate ID
        if len(actions_df) == 0:
            action_id = "ACT0001"
        else:
            last_id = actions_df['id'].max()
            num = int(last_id[3:]) + 1
            action_id = f"ACT{num:04d}"
        
        action = Action(
            id=action_id,
            created_at=now,
            due_date=now + timedelta(days=due_days),
            owner=owner,
            status=ActionStatus.TODO,
            category=category,
            site_id=site_id,
            description=description,
            evidence_links=evidence_links or []
        )
        
        # Append to dataframe
        new_row = pd.DataFrame([action.to_dict()])
        actions_df = pd.concat([actions_df, new_row], ignore_index=True)
        self.save_actions(actions_df)
        
        return action
    
    def update_action_status(self, action_id: str, new_status: ActionStatus) -> bool:
        """
        Update action status.
        
        Args:
            action_id: Action ID to update
            new_status: New status
        
        Returns:
            Success boolean
        """
        actions_df = self.load_actions()
        
        if action_id not in actions_df['id'].values:
            st.error(f"조치 ID {action_id}를 찾을 수 없습니다.")
            return False
        
        actions_df.loc[actions_df['id'] == action_id, 'status'] = new_status.value
        self.save_actions(actions_df)
        return True
    
    def get_actions_by_owner(self, owner: str) -> pd.DataFrame:
        """Get all actions for a specific owner."""
        actions_df = self.load_actions()
        if len(actions_df) == 0:
            return actions_df
        return actions_df[actions_df['owner'] == owner]
    
    def get_pending_actions(self, owner: str) -> pd.DataFrame:
        """Get pending (TODO/DOING) actions for owner."""
        actions_df = self.get_actions_by_owner(owner)
        if len(actions_df) == 0:
            return actions_df
        return actions_df[actions_df['status'].isin([ActionStatus.TODO.value, ActionStatus.DOING.value])]
    
    def get_action_stats(self, owner: str) -> dict:
        """Get action statistics for owner."""
        actions_df = self.get_actions_by_owner(owner)
        
        if len(actions_df) == 0:
            return {'total': 0, 'todo': 0, 'doing': 0, 'done': 0, 'overdue': 0}
        
        now = datetime.now()
        actions_df['due_date_dt'] = pd.to_datetime(actions_df['due_date'])
        
        return {
            'total': len(actions_df),
            'todo': len(actions_df[actions_df['status'] == ActionStatus.TODO.value]),
            'doing': len(actions_df[actions_df['status'] == ActionStatus.DOING.value]),
            'done': len(actions_df[actions_df['status'] == ActionStatus.DONE.value]),
            'overdue': len(actions_df[
                (actions_df['status'] != ActionStatus.DONE.value) & 
                (actions_df['due_date_dt'] < now)
            ])
        }




