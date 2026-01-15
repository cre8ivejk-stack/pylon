"""
Complex NLQ execution for comparison and analysis queries.

This module extends the basic TOP N queries to support:
- Bill vs Actual comparison
- Plan vs Actual comparison
- Trend analysis
- Year-over-year comparison
"""

from __future__ import annotations

import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from src.analytics import (
    calculate_bill_actual_error,
    classify_bill_actual_mismatch,
    calculate_plan_variance,
    calculate_yoy_comparison,
    decompose_cost_variance,
)


@dataclass
class ComparisonResult:
    """Result of a comparison analysis."""
    summary: Dict[str, Any]
    detailed_df: pd.DataFrame
    analysis_type: str
    region_agg: Optional[pd.DataFrame] = None
    site_type_agg: Optional[pd.DataFrame] = None


def execute_bill_actual_comparison(
    bills_df: pd.DataFrame,
    actual_df: pd.DataFrame,
    site_master_df: pd.DataFrame,
    *,
    regions: Optional[List[str]] = None,
    site_types: Optional[List[str]] = None,
    year: Optional[int] = None,
    months: Optional[List[int]] = None,
    contract_target: Optional[str] = None,
    contract_type_major: Optional[List[str]] = None,
    network_gen: Optional[List[str]] = None,
    rapa: Optional[str] = None,
) -> ComparisonResult:
    """
    Execute bill vs actual comparison analysis.
    
    Args:
        bills_df: Bills dataframe
        actual_df: Actual usage dataframe
        site_master_df: Site master dataframe
        regions: Filter by regions
        site_types: Filter by site types
        year: Target year (e.g., 2024)
        months: Target months (e.g., [1, 2, 3, ...])
    
    Returns:
        ComparisonResult with summary and detailed data
    """
    # Filter by year if specified
    if year:
        bills_df = bills_df[bills_df['yymm'].astype(str).str.startswith(str(year))].copy()
        actual_df = actual_df[actual_df['yymm'].astype(str).str.startswith(str(year))].copy()
    
    # Filter by months if specified
    if months:
        bills_df = bills_df[bills_df['yymm'].astype(str).str[4:6].astype(int).isin(months)].copy()
        actual_df = actual_df[actual_df['yymm'].astype(str).str[4:6].astype(int).isin(months)].copy()
    
    # Merge bills and actual
    merged = bills_df.merge(
        actual_df,
        on=['yymm', 'site_id'],
        how='left',
        suffixes=('', '_actual')
    )
    
    # Merge with site master for filtering
    if not site_master_df.empty:
        merged = merged.merge(
            site_master_df[['site_id', 'region', 'site_type']],
            on='site_id',
            how='left'
        )
        
        # Apply filters
        if regions:
            merged = merged[merged['region'].isin(regions)]
        if site_types:
            merged = merged[merged['site_type'].isin(site_types)]
        
        # Apply additional filters
        if contract_target and contract_target != "전체":
            target_map = {
                '한전계약(ME)': 'ME',
                '건물계약(MC)': 'MC'
            }
            target_value = target_map.get(contract_target, contract_target)
            for col_name in ['contract_target', 'contract_target_cd', '계약대상']:
                if col_name in merged.columns:
                    merged = merged[merged[col_name] == target_value]
                    break
        
        if contract_type_major:
            if "contract_type" in merged.columns:
                merged = merged[merged["contract_type"].isin(contract_type_major)]
        
        if network_gen:
            for col_name in ['network_gen', 'network_generation', '세대']:
                if col_name in merged.columns:
                    merged = merged[merged[col_name].isin(network_gen)]
                    break
        
        if rapa and rapa != "전체":
            for col_name in ['is_rapa', 'rapa_yn', 'rapa', 'rapa_type']:
                if col_name in merged.columns:
                    if merged[col_name].dtype == bool:
                        if rapa == 'RAPA':
                            merged = merged[merged[col_name] == True]
                        else:  # '비RAPA'
                            merged = merged[merged[col_name] == False]
                    else:
                        if rapa == 'RAPA':
                            merged = merged[merged[col_name].isin(['Y', 'y', 'RAPA'])]
                        else:  # '비RAPA'
                            merged = merged[merged[col_name].isin(['N', 'n', '비RAPA', 'non-RAPA'])]
                    break
    
    # Calculate summary statistics
    total_kwh_bill = merged['kwh_bill'].sum()
    total_kwh_actual = merged['kwh_actual'].sum()
    total_cost_bill = merged['cost_bill'].sum()
    
    # Calculate estimated cost from actual
    avg_unit_cost = total_cost_bill / total_kwh_bill if total_kwh_bill > 0 else 0
    estimated_cost_from_actual = total_kwh_actual * avg_unit_cost
    
    # Calculate differences
    kwh_diff = total_kwh_actual - total_kwh_bill
    kwh_diff_pct = (kwh_diff / total_kwh_bill * 100) if total_kwh_bill > 0 else 0
    cost_diff = estimated_cost_from_actual - total_cost_bill
    cost_diff_pct = (cost_diff / total_cost_bill * 100) if total_cost_bill > 0 else 0
    
    # Calculate error rates per site
    merged['error_pct'] = calculate_bill_actual_error(
        merged['kwh_actual'],
        merged['kwh_bill']
    )
    
    # Classify mismatches
    merged['mismatch_class'] = merged.apply(
        lambda row: classify_bill_actual_mismatch(row, threshold_pct=10.0),
        axis=1
    )
    
    # Aggregate by region for detailed analysis
    if 'region' in merged.columns:
        region_agg = merged.groupby('region').agg({
            'kwh_bill': 'sum',
            'kwh_actual': 'sum',
            'cost_bill': 'sum',
            'site_id': 'count'
        }).reset_index()
        region_agg['cost_actual_est'] = region_agg['kwh_actual'] * avg_unit_cost
        region_agg['kwh_diff'] = region_agg['kwh_actual'] - region_agg['kwh_bill']
        region_agg['kwh_diff_pct'] = (region_agg['kwh_diff'] / region_agg['kwh_bill'] * 100).round(2)
        region_agg['cost_diff'] = region_agg['cost_actual_est'] - region_agg['cost_bill']
        region_agg['cost_diff_pct'] = (region_agg['cost_diff'] / region_agg['cost_bill'] * 100).round(2)
        region_agg.columns = ['지역', '청구서_전력량', '실사용_전력량', '청구서_요금', '국소수', 
                              '실사용_기반_추정요금', '전력량_차이', '전력량_차이율', '요금_차이', '요금_차이율']
    else:
        region_agg = pd.DataFrame()
    
    # Aggregate by site_type
    if 'site_type' in merged.columns:
        site_type_agg = merged.groupby('site_type').agg({
            'kwh_bill': 'sum',
            'kwh_actual': 'sum',
            'cost_bill': 'sum',
            'site_id': 'count'
        }).reset_index()
        site_type_agg['cost_actual_est'] = site_type_agg['kwh_actual'] * avg_unit_cost
        site_type_agg['kwh_diff'] = site_type_agg['kwh_actual'] - site_type_agg['kwh_bill']
        site_type_agg['kwh_diff_pct'] = (site_type_agg['kwh_diff'] / site_type_agg['kwh_bill'] * 100).round(2)
        site_type_agg['cost_diff'] = site_type_agg['cost_actual_est'] - site_type_agg['cost_bill']
        site_type_agg['cost_diff_pct'] = (site_type_agg['cost_diff'] / site_type_agg['cost_bill'] * 100).round(2)
        site_type_agg.columns = ['설비유형', '청구서_전력량', '실사용_전력량', '청구서_요금', '국소수',
                                '실사용_기반_추정요금', '전력량_차이', '전력량_차이율', '요금_차이', '요금_차이율']
    else:
        site_type_agg = pd.DataFrame()
    
    # Mismatch classification summary
    mismatch_summary = merged['mismatch_class'].value_counts().to_dict()
    
    summary = {
        'total_kwh_bill': float(total_kwh_bill),
        'total_kwh_actual': float(total_kwh_actual),
        'total_cost_bill': float(total_cost_bill),
        'estimated_cost_from_actual': float(estimated_cost_from_actual),
        'kwh_diff': float(kwh_diff),
        'kwh_diff_pct': float(kwh_diff_pct),
        'cost_diff': float(cost_diff),
        'cost_diff_pct': float(cost_diff_pct),
        'avg_unit_cost': float(avg_unit_cost),
        'mismatch_summary': mismatch_summary,
        'total_sites': int(len(merged)),
    }
    
    # Detailed dataframe: site-level analysis
    detailed = merged[[
        'site_id', 'yymm', 'region', 'site_type',
        'kwh_bill', 'kwh_actual', 'cost_bill',
        'error_pct', 'mismatch_class'
    ]].copy()
    
    detailed['cost_actual_est'] = detailed['kwh_actual'] * avg_unit_cost
    detailed['kwh_diff'] = detailed['kwh_actual'] - detailed['kwh_bill']
    detailed['cost_diff'] = detailed['cost_actual_est'] - detailed['cost_bill']
    
    result = ComparisonResult(
        summary=summary,
        detailed_df=detailed,
        analysis_type='bill_actual_comparison',
    )
    result.region_agg = region_agg
    result.site_type_agg = site_type_agg
    return result


@dataclass
class TrendResult:
    """Result of a trend analysis."""
    monthly_df: pd.DataFrame  # 월별 집계 데이터
    summary: Dict[str, Any]  # 요약 통계 (총합, 평균, 최고/최저, 증감률 등)
    analysis_type: str


def execute_trend_analysis(
    bills_df: pd.DataFrame,
    actual_df: pd.DataFrame,
    site_master_df: pd.DataFrame,
    *,
    metric: str = "kwh_actual",
    regions: Optional[List[str]] = None,
    site_types: Optional[List[str]] = None,
    year: Optional[int] = None,
    start_month: Optional[int] = None,
    end_month: Optional[int] = None,
    contract_target: Optional[str] = None,
    contract_type_major: Optional[List[str]] = None,
    network_gen: Optional[List[str]] = None,
    rapa: Optional[str] = None,
) -> TrendResult:
    """
    Execute trend analysis (월별 추이 분석).
    
    Args:
        bills_df: Bills dataframe
        actual_df: Actual usage dataframe
        site_master_df: Site master dataframe
        metric: Metric to analyze ("kwh_actual", "kwh_bill", "cost_bill", "cost_actual_est")
        regions: Filter by regions
        site_types: Filter by site types
        year: Target year (e.g., 2025)
        start_month: Start month (1-12)
        end_month: End month (1-12)
        contract_target: Filter by contract target
        contract_type_major: Filter by contract type
        network_gen: Filter by network generation
        rapa: Filter by RAPA
    
    Returns:
        TrendResult with monthly aggregated data and summary statistics
    """
    # Select source dataframe based on metric
    if metric in ("kwh_actual", "cost_actual_est"):
        source_df = actual_df.copy()
        if metric == "kwh_actual":
            metric_col = "kwh_actual"
        else:
            metric_col = "cost_actual_est"
    else:
        source_df = bills_df.copy()
        if metric == "kwh_bill":
            metric_col = "kwh_bill"
        else:
            metric_col = "cost_bill"
    
    # Filter by year if specified
    if year:
        source_df = source_df[source_df['yymm'].astype(str).str.startswith(str(year))].copy()
    
    # Filter by month range if specified
    if start_month and end_month:
        source_df['month'] = source_df['yymm'].astype(str).str[4:6].astype(int)
        source_df = source_df[
            (source_df['month'] >= start_month) & 
            (source_df['month'] <= end_month)
        ].copy()
        source_df = source_df.drop(columns=['month'])
    
    # Merge with site master for filtering
    if not site_master_df.empty:
        source_df = source_df.merge(
            site_master_df[['site_id', 'region', 'site_type']],
            on='site_id',
            how='left'
        )
        
        # Apply filters
        if regions:
            source_df = source_df[source_df['region'].isin(regions)]
        if site_types:
            source_df = source_df[source_df['site_type'].isin(site_types)]
        
        # Apply additional filters
        if contract_target and contract_target != "전체":
            target_map = {
                '한전계약(ME)': 'ME',
                '건물계약(MC)': 'MC'
            }
            target_value = target_map.get(contract_target, contract_target)
            for col_name in ['contract_target', 'contract_target_cd', '계약대상']:
                if col_name in source_df.columns:
                    source_df = source_df[source_df[col_name] == target_value]
                    break
        
        if contract_type_major:
            if "contract_type" in source_df.columns:
                source_df = source_df[source_df["contract_type"].isin(contract_type_major)]
        
        if network_gen:
            for col_name in ['network_gen', 'network_generation', '세대']:
                if col_name in source_df.columns:
                    source_df = source_df[source_df[col_name].isin(network_gen)]
                    break
        
        if rapa and rapa != "전체":
            for col_name in ['is_rapa', 'rapa_yn', 'rapa', 'rapa_type']:
                if col_name in source_df.columns:
                    if source_df[col_name].dtype == bool:
                        if rapa == 'RAPA':
                            source_df = source_df[source_df[col_name] == True]
                        else:  # '비RAPA'
                            source_df = source_df[source_df[col_name] == False]
                    else:
                        if rapa == 'RAPA':
                            source_df = source_df[source_df[col_name].isin(['Y', 'y', 'RAPA'])]
                        else:  # '비RAPA'
                            source_df = source_df[source_df[col_name].isin(['N', 'n', '비RAPA', 'non-RAPA'])]
                    break
    
    # Check if metric column exists
    if metric_col not in source_df.columns:
        return TrendResult(
            monthly_df=pd.DataFrame(columns=['yymm', 'value', 'month_label']),
            summary={'error': f'Metric column {metric_col} not found'},
            analysis_type='trend'
        )
    
    # Aggregate by month
    monthly_agg = source_df.groupby('yymm')[metric_col].agg([
        'sum',  # 총합
        'mean',  # 평균
        'count'  # 국소 수
    ]).reset_index()
    
    monthly_agg.columns = ['yymm', 'total_value', 'avg_value', 'site_count']
    
    # Sort by yymm
    monthly_agg = monthly_agg.sort_values('yymm').reset_index(drop=True)
    
    # Create month label for display
    monthly_agg['month_label'] = monthly_agg['yymm'].astype(str).apply(
        lambda x: f"{x[:4]}.{x[4:6]}" if len(x) >= 6 else x
    )
    
    # Calculate month-over-month changes
    monthly_agg['mom_change'] = monthly_agg['total_value'].diff()
    monthly_agg['mom_change_pct'] = (monthly_agg['mom_change'] / monthly_agg['total_value'].shift(1) * 100).round(2)
    
    # Calculate summary statistics
    total_value = float(monthly_agg['total_value'].sum())
    avg_monthly = float(monthly_agg['total_value'].mean())
    max_month = monthly_agg.loc[monthly_agg['total_value'].idxmax(), 'month_label']
    max_value = float(monthly_agg['total_value'].max())
    min_month = monthly_agg.loc[monthly_agg['total_value'].idxmin(), 'month_label']
    min_value = float(monthly_agg['total_value'].min())
    
    # Calculate overall trend (first month vs last month)
    if len(monthly_agg) >= 2:
        first_value = float(monthly_agg.iloc[0]['total_value'])
        last_value = float(monthly_agg.iloc[-1]['total_value'])
        overall_change = last_value - first_value
        overall_change_pct = (overall_change / first_value * 100) if first_value > 0 else 0
    else:
        overall_change = 0
        overall_change_pct = 0
    
    # Calculate average monthly change
    avg_mom_change = float(monthly_agg['mom_change'].mean()) if len(monthly_agg) > 1 else 0
    avg_mom_change_pct = float(monthly_agg['mom_change_pct'].mean()) if len(monthly_agg) > 1 else 0
    
    summary = {
        'total_value': total_value,
        'avg_monthly': avg_monthly,
        'max_month': max_month,
        'max_value': max_value,
        'min_month': min_month,
        'min_value': min_value,
        'overall_change': overall_change,
        'overall_change_pct': round(overall_change_pct, 2),
        'avg_mom_change': avg_mom_change,
        'avg_mom_change_pct': round(avg_mom_change_pct, 2),
        'num_months': len(monthly_agg),
        'total_sites': int(monthly_agg['site_count'].sum()),
        'avg_sites_per_month': float(monthly_agg['site_count'].mean()),
    }
    
    return TrendResult(
        monthly_df=monthly_agg,
        summary=summary,
        analysis_type='trend'
    )

