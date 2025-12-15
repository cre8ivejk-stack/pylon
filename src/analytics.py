"""Analytics and calculation functions for PYLON platform."""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional


def calculate_plan_variance(
    actual_value: float,
    plan_value: float
) -> Dict[str, float]:
    """
    Calculate variance between actual and plan.
    
    Args:
        actual_value: Actual value
        plan_value: Plan value
    
    Returns:
        Dictionary with variance, variance_pct, achievement_rate
    """
    if plan_value == 0:
        return {
            'variance': float(round(actual_value, 10)),
            'variance_pct': 0.0,
            'achievement_rate': 0.0
        }
    
    variance = actual_value - plan_value
    variance_pct = (variance / plan_value) * 100
    achievement_rate = (actual_value / plan_value) * 100
    
    return {
        'variance': float(round(variance, 10)),
        'variance_pct': float(round(variance_pct, 10)),
        'achievement_rate': float(round(achievement_rate, 10))
    }


def calculate_bill_actual_error(
    actual_kwh,
    bill_kwh
):
    """
    Calculate error rate between actual and bill.
    
    Args:
        actual_kwh: Actual kWh (scalar or Series)
        bill_kwh: Bill kWh (scalar or Series)
    
    Returns:
        Error rate as percentage (scalar or Series)
    """
    actual = pd.to_numeric(actual_kwh, errors="coerce")
    bill = pd.to_numeric(bill_kwh, errors="coerce")
    
    # Replace 0 with NaN to avoid division by zero
    denom = bill.replace(0, np.nan) if isinstance(bill, pd.Series) else (np.nan if bill == 0 else bill)
    
    # Calculate error
    err = ((actual - bill) / denom) * 100
    
    # Fill NaN with 0.0
    if isinstance(err, pd.Series):
        return err.fillna(0.0)
    else:
        return 0.0 if pd.isna(err) else float(err)


def calculate_risk_score(
    impact: float,
    likelihood: float,
    confidence: float
) -> Dict[str, float]:
    """
    Calculate risk score (raw and display).
    
    Args:
        impact: Financial impact in KRW (absolute cost difference)
        likelihood: Likelihood of risk (0-1)
        confidence: Confidence in data (0-1)
    
    Returns:
        Dictionary with raw_score (KRW-based) and display_score (0-100)
    """
    # Raw score = impact * likelihood * confidence (KRW scale)
    raw_score = impact * likelihood * confidence
    
    # Display score for ranking gauge (0-100 scale)
    # Normalize impact assuming max critical impact of 10M KRW
    impact_normalized = min(impact / 10_000_000, 1.0)
    display_score = impact_normalized * likelihood * confidence * 100
    
    return {
        'raw_score': float(round(raw_score, 2)),
        'display_score': float(round(display_score, 2))
    }


def classify_bill_actual_mismatch(
    row: pd.Series,
    threshold_pct: float = 10.0
) -> str:
    """
    Classify bill vs actual mismatch.
    
    Args:
        row: DataFrame row with bill and actual data
        threshold_pct: Threshold for classification
    
    Returns:
        Classification string
    """
    error_pct = abs(calculate_bill_actual_error(row.get('kwh_actual', 0), row.get('kwh_bill', 0)))
    
    if pd.isna(row.get('kwh_actual')):
        return "데이터 누락"
    
    if row.get('contract_type') == "정액" and error_pct < threshold_pct:
        return "설명 가능 (정액)"
    
    if error_pct < threshold_pct:
        return "정상 범위"
    elif error_pct < 30:
        return "조사 필요"
    else:
        return "긴급 조사"


def detect_zero_usage_sites(bills_df: pd.DataFrame, months: int = 3) -> pd.DataFrame:
    """
    Detect sites with zero usage for consecutive months.
    
    Args:
        bills_df: Bills dataframe
        months: Number of consecutive months to check
    
    Returns:
        DataFrame of sites with zero usage
    """
    if len(bills_df) == 0:
        return pd.DataFrame()
    
    # Sort by site and month
    bills_sorted = bills_df.sort_values(['site_id', 'yymm'])
    
    # Filter zero usage
    zero_usage = bills_sorted[bills_sorted['kwh_bill'] == 0].copy()
    
    # Count consecutive zeros per site
    zero_count = zero_usage.groupby('site_id').size().reset_index(name='zero_months')
    
    # Filter sites with >= months consecutive zeros
    problem_sites = zero_count[zero_count['zero_months'] >= months]
    
    return problem_sites


def recommend_contract_power_adjustment(
    site_df: pd.DataFrame,
    safety_margin: float = 1.15
) -> Dict[str, any]:
    """
    Recommend contract power adjustment based on usage patterns.
    
    Args:
        site_df: DataFrame with site usage history
        safety_margin: Safety margin multiplier
    
    Returns:
        Recommendation dictionary
    """
    if len(site_df) == 0 or 'kwh_bill' not in site_df.columns:
        return {'recommendation': '데이터 부족', 'new_contract_kw': 0, 'savings_est': 0}
    
    # Estimate max demand from kWh (rough approximation)
    # Assuming 720 hours per month
    site_df['demand_est_kw'] = site_df['kwh_bill'] / 720
    
    # Get current contract power
    current_contract_kw = site_df['contract_power_kw'].iloc[-1] if 'contract_power_kw' in site_df.columns else 0
    
    # Calculate recommended power with safety margin
    max_demand_kw = site_df['demand_est_kw'].max()
    recommended_kw = max_demand_kw * safety_margin
    
    # Calculate potential savings (basic rate difference)
    # Assuming 8000 KRW/kW for basic charge
    if current_contract_kw > recommended_kw * 1.1:
        # Recommend reduction
        savings_est = (current_contract_kw - recommended_kw) * 8000
        recommendation = f"계약전력 감설 권고: {current_contract_kw:.1f}kW → {recommended_kw:.1f}kW"
    elif current_contract_kw < recommended_kw * 0.9:
        # Recommend increase to avoid penalties
        penalty_est = (recommended_kw - current_contract_kw) * 12000  # Penalty rate
        recommendation = f"계약전력 증설 필요: {current_contract_kw:.1f}kW → {recommended_kw:.1f}kW (초과요금 위험)"
        savings_est = -penalty_est
    else:
        recommendation = "적정 수준"
        savings_est = 0
    
    return {
        'recommendation': recommendation,
        'current_contract_kw': current_contract_kw,
        'new_contract_kw': recommended_kw,
        'savings_est': savings_est
    }


def calculate_kwh_per_traffic(
    bills_df: pd.DataFrame,
    traffic_df: pd.DataFrame,
    yymm: str
) -> pd.DataFrame:
    """
    Calculate kWh per GB traffic efficiency.
    
    Args:
        bills_df: Bills dataframe
        traffic_df: Traffic dataframe
        yymm: Target month
    
    Returns:
        Merged dataframe with efficiency metric
    """
    bills_month = bills_df[bills_df['yymm'] == yymm].copy()
    traffic_month = traffic_df[traffic_df['yymm'] == yymm].copy()
    
    merged = bills_month.merge(traffic_month, on='site_id', how='inner')
    
    # Calculate efficiency
    merged['kwh_per_gb'] = merged['kwh_bill'] / merged['gb_traffic'].replace(0, np.nan)
    
    return merged


def decompose_cost_variance(
    actual_cost: float,
    plan_cost: float,
    actual_kwh: float,
    plan_kwh: float
) -> Dict[str, float]:
    """
    Decompose cost variance into usage and price effects.
    
    Args:
        actual_cost: Actual cost
        plan_cost: Plan cost
        actual_kwh: Actual kWh
        plan_kwh: Plan kWh
    
    Returns:
        Dictionary with usage_effect, price_effect, total_variance
    """
    if plan_kwh == 0:
        return {'usage_effect': 0, 'price_effect': 0, 'total_variance': actual_cost - plan_cost}
    
    # Calculate unit prices
    actual_unit_price = actual_cost / actual_kwh if actual_kwh > 0 else 0
    plan_unit_price = plan_cost / plan_kwh
    
    # Usage effect: (actual_kwh - plan_kwh) * plan_unit_price
    usage_effect = (actual_kwh - plan_kwh) * plan_unit_price
    
    # Price effect: (actual_unit_price - plan_unit_price) * actual_kwh
    price_effect = (actual_unit_price - plan_unit_price) * actual_kwh
    
    total_variance = actual_cost - plan_cost
    
    return {
        'usage_effect': usage_effect,
        'price_effect': price_effect,
        'total_variance': total_variance
    }


def calculate_yoy_comparison(
    df: pd.DataFrame,
    current_month: str,
    metric: str = 'kwh_bill'
) -> Optional[float]:
    """
    Calculate year-over-year change.
    
    Args:
        df: Dataframe with yymm and metric columns
        current_month: Current month (e.g., "2401")
        metric: Metric to compare
    
    Returns:
        YoY percentage change or None if not available
    """
    # Calculate previous year month
    year = int(current_month[:2])
    month = int(current_month[2:])
    prev_year = year - 1
    prev_month = f"{prev_year:02d}{month:02d}"
    
    current_value = df[df['yymm'] == current_month][metric].sum()
    prev_value = df[df['yymm'] == prev_month][metric].sum()
    
    if prev_value == 0:
        return None
    
    return ((current_value - prev_value) / prev_value) * 100


def calculate_anomaly_score(
    site_df: pd.DataFrame,
    metric: str = 'kwh_bill',
    threshold_std: float = 2.0
) -> pd.DataFrame:
    """
    Calculate anomaly scores for site time series.
    
    Args:
        site_df: Site dataframe with time series
        metric: Metric to analyze
        threshold_std: Standard deviation threshold
    
    Returns:
        DataFrame with anomaly scores
    """
    if len(site_df) < 3 or metric not in site_df.columns:
        return site_df
    
    site_df = site_df.copy()
    
    # Calculate rolling mean and std
    site_df['rolling_mean'] = site_df[metric].rolling(window=3, min_periods=1).mean()
    site_df['rolling_std'] = site_df[metric].rolling(window=3, min_periods=1).std()
    
    # Calculate z-score
    site_df['z_score'] = (site_df[metric] - site_df['rolling_mean']) / site_df['rolling_std'].replace(0, 1)
    
    # Flag anomalies
    site_df['is_anomaly'] = abs(site_df['z_score']) > threshold_std
    
    return site_df

