"""Data Access Layer for PYLON platform."""

import pandas as pd
import streamlit as st
from pathlib import Path
from typing import Optional, Dict, Any
from src.sample_data import generate_sample_data


class DataAccessLayer:
    """
    Data Access Layer providing unified interface to data sources.
    Supports both sample data and uploaded data.
    """
    
    def __init__(self, data_dir: Path):
        """
        Initialize data access layer.
        
        Args:
            data_dir: Directory containing data files
        """
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure sample data exists
        if not self._sample_data_exists():
            generate_sample_data(self.data_dir)
    
    def _sample_data_exists(self) -> bool:
        """Check if sample data files exist."""
        required_files = [
            "sample_bills.parquet",
            "sample_actual.parquet",
            "sample_plan.parquet",
            "sample_traffic.parquet",
            "sample_site_master.parquet"
        ]
        return all((self.data_dir / f).exists() for f in required_files)
    
    @st.cache_data(ttl=3600)
    def load_bills(_self) -> pd.DataFrame:
        """Load bills data with caching."""
        try:
            df = pd.read_parquet(_self.data_dir / "sample_bills.parquet")
            return _self._validate_bills(df)
        except Exception as e:
            st.error(f"청구서 데이터 로드 실패: {e}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=3600)
    def load_actual(_self) -> pd.DataFrame:
        """Load actual usage data with caching."""
        try:
            df = pd.read_parquet(_self.data_dir / "sample_actual.parquet")
            return _self._validate_actual(df)
        except Exception as e:
            st.error(f"실사용량 데이터 로드 실패: {e}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=3600)
    def load_plan(_self) -> pd.DataFrame:
        """Load plan data with caching."""
        try:
            df = pd.read_parquet(_self.data_dir / "sample_plan.parquet")
            return _self._validate_plan(df)
        except Exception as e:
            st.error(f"계획 데이터 로드 실패: {e}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=3600)
    def load_traffic(_self) -> pd.DataFrame:
        """Load traffic data with caching."""
        try:
            df = pd.read_parquet(_self.data_dir / "sample_traffic.parquet")
            return _self._validate_traffic(df)
        except Exception as e:
            st.error(f"트래픽 데이터 로드 실패: {e}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=3600)
    def load_site_master(_self) -> pd.DataFrame:
        """Load site master data with caching."""
        try:
            df = pd.read_parquet(_self.data_dir / "sample_site_master.parquet")
            return _self._validate_site_master(df)
        except Exception as e:
            st.error(f"국소 마스터 데이터 로드 실패: {e}")
            return pd.DataFrame()
    
    def _validate_bills(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate bills schema."""
        required_cols = ['yymm', 'site_id', 'kwh_bill', 'cost_bill', 
                        'contract_type', 'contract_power_kw', 'region']
        missing = set(required_cols) - set(df.columns)
        if missing:
            raise ValueError(f"청구서 데이터 필수 컬럼 누락: {missing}")
        return df
    
    def _validate_actual(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate actual schema."""
        required_cols = ['yymm', 'site_id', 'kwh_actual', 'cost_actual_est', 
                        'data_source', 'confidence']
        missing = set(required_cols) - set(df.columns)
        if missing:
            raise ValueError(f"실사용량 데이터 필수 컬럼 누락: {missing}")
        return df
    
    def _validate_plan(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate plan schema."""
        required_cols = ['yymm', 'kwh_plan', 'cost_plan']
        missing = set(required_cols) - set(df.columns)
        if missing:
            raise ValueError(f"계획 데이터 필수 컬럼 누락: {missing}")
        return df
    
    def _validate_traffic(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate traffic schema."""
        required_cols = ['yymm', 'site_id', 'gb_traffic']
        missing = set(required_cols) - set(df.columns)
        if missing:
            raise ValueError(f"트래픽 데이터 필수 컬럼 누락: {missing}")
        return df
    
    def _validate_site_master(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate site master schema."""
        required_cols = ['site_id', 'site_name', 'region', 'site_type', 
                        'voltage', 'contract_type']
        missing = set(required_cols) - set(df.columns)
        if missing:
            raise ValueError(f"국소 마스터 필수 컬럼 누락: {missing}")
        return df
    
    def upload_data(self, uploaded_file, data_type: str) -> bool:
        """
        Upload and validate user data.
        
        Args:
            uploaded_file: Streamlit uploaded file object
            data_type: Type of data ('bills', 'actual', 'plan', 'traffic', 'site_master')
        
        Returns:
            Success boolean
        """
        try:
            # Read file
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith('.parquet'):
                df = pd.read_parquet(uploaded_file)
            else:
                st.error("지원하지 않는 파일 형식입니다. CSV 또는 Parquet 파일을 업로드하세요.")
                return False
            
            # Validate
            validator = getattr(self, f'_validate_{data_type}')
            df = validator(df)
            
            # Save
            output_path = self.data_dir / f"sample_{data_type}.parquet"
            df.to_parquet(output_path, index=False)
            
            st.success(f"{data_type} 데이터 업로드 완료: {len(df)} rows")
            return True
            
        except Exception as e:
            st.error(f"데이터 업로드 실패: {e}")
            return False






