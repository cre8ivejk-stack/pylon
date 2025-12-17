"""Verified savings management for PYLON platform."""

import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime
from typing import Optional


class VerifiedSavingsManager:
    """Manage verified savings records."""
    
    def __init__(self, data_dir: Path):
        """
        Initialize verified savings manager.
        
        Args:
            data_dir: Directory to store verified_savings.parquet
        """
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.savings_file = self.data_dir / "verified_savings.parquet"
    
    def load_savings(self) -> pd.DataFrame:
        """Load all verified savings from storage."""
        if not self.savings_file.exists():
            return pd.DataFrame(columns=[
                'id', 'yymm', 'site_id', 'category', 'verified_savings_krw', 'notes', 'created_at'
            ])
        
        try:
            df = pd.read_parquet(self.savings_file)
            return df
        except Exception as e:
            st.error(f"검증 절감 데이터 로드 실패: {e}")
            return pd.DataFrame()
    
    def save_savings(self, df: pd.DataFrame) -> None:
        """Save verified savings to storage."""
        try:
            df.to_parquet(self.savings_file, index=False)
        except Exception as e:
            st.error(f"검증 절감 저장 실패: {e}")
    
    def create_verified_saving(
        self,
        yymm: str,
        site_id: Optional[str],
        category: str,
        verified_savings_krw: float,
        notes: str = ""
    ) -> str:
        """
        Create a new verified saving record.
        
        Args:
            yymm: Year-month
            site_id: Site ID (optional, can be aggregate)
            category: Category (e.g., "3G Phase-Out", "계약전력 최적화")
            verified_savings_krw: Verified savings amount in KRW
            notes: Additional notes
        
        Returns:
            Created record ID
        """
        savings_df = self.load_savings()
        
        # Generate ID
        if len(savings_df) == 0:
            saving_id = "SAV0001"
        else:
            last_id = savings_df['id'].max()
            num = int(last_id[3:]) + 1
            saving_id = f"SAV{num:04d}"
        
        # Create new record
        new_record = pd.DataFrame([{
            'id': saving_id,
            'yymm': yymm,
            'site_id': site_id if site_id else "전체",
            'category': category,
            'verified_savings_krw': verified_savings_krw,
            'notes': notes,
            'created_at': datetime.now().isoformat()
        }])
        
        # Append
        savings_df = pd.concat([savings_df, new_record], ignore_index=True)
        self.save_savings(savings_df)
        
        return saving_id
    
    def get_total_verified_savings(self) -> float:
        """Get total verified savings."""
        savings_df = self.load_savings()
        if len(savings_df) == 0:
            return 0.0
        return savings_df['verified_savings_krw'].sum()
    
    def get_savings_by_category(self, category: str) -> pd.DataFrame:
        """Get savings filtered by category."""
        savings_df = self.load_savings()
        if len(savings_df) == 0:
            return savings_df
        return savings_df[savings_df['category'] == category]






