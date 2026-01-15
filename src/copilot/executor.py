"""
Plan executor for Copilot NLQ system.

This module executes structured plans on dataframes and generates results.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass

from src.copilot.schemas import Plan, Metric, QueryType, TimeRange, Filters
from src.analytics import (
    calculate_bill_actual_error,
    classify_bill_actual_mismatch,
    calculate_plan_variance,
    calculate_yoy_comparison,
)


@dataclass
class ExecutionResult:
    """Result of plan execution."""
    result_df: pd.DataFrame
    summary: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None


def execute_plan(
    plan: Plan,
    *,
    bills_df: pd.DataFrame,
    actual_df: pd.DataFrame,
    plan_df: pd.DataFrame,
    site_master_df: pd.DataFrame,
) -> ExecutionResult:
    """
    Execute a plan on dataframes.
    
    Args:
        plan: Plan to execute
        bills_df: Bills dataframe
        actual_df: Actual usage dataframe
        plan_df: Plan dataframe
        site_master_df: Site master dataframe
    
    Returns:
        ExecutionResult with result_df and summary
    """
    try:
        if plan.query_type == QueryType.TOP_N.value:
            return _execute_top_n(plan, bills_df, actual_df, site_master_df)
        elif plan.query_type == QueryType.TREND.value:
            return _execute_trend(plan, bills_df, actual_df, site_master_df)
        elif plan.query_type == QueryType.COMPARISON.value:
            return _execute_comparison(plan, bills_df, actual_df, site_master_df)
        elif plan.query_type == QueryType.ANOMALY.value:
            return _execute_anomaly(plan, bills_df, actual_df, site_master_df)
        elif plan.query_type == QueryType.RECOMMENDATION.value:
            return _execute_recommendation(plan, bills_df, actual_df, site_master_df)
        else:
            return ExecutionResult(
                result_df=pd.DataFrame(),
                summary={},
                success=False,
                error_message=f"Unsupported query_type: {plan.query_type}",
            )
    except Exception as e:
        return ExecutionResult(
            result_df=pd.DataFrame(),
            summary={},
            success=False,
            error_message=str(e),
        )


def _get_metric_column(metric: str) -> str:
    """Map metric enum to dataframe column name."""
    mapping = {
        Metric.USAGE_KWH.value: "kwh_actual",
        Metric.COST_WON.value: "cost_bill",
        Metric.UNIT_COST.value: "unit_cost",  # Calculated
        Metric.BILL_VS_ACTUAL_GAP.value: "gap",  # Calculated
    }
    return mapping.get(metric, "kwh_actual")


def _get_dataframe_for_metric(
    metric: str,
    bills_df: pd.DataFrame,
    actual_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, str]:
    """
    Get appropriate dataframe for metric.
    
    Returns:
        (dataframe, column_name)
    """
    if metric == Metric.USAGE_KWH.value:
        if not actual_df.empty:
            return actual_df, "kwh_actual"
        else:
            return bills_df, "kwh_bill"
    elif metric == Metric.COST_WON.value:
        return bills_df, "cost_bill"
    else:
        # For calculated metrics, use bills as base
        return bills_df, "kwh_bill"


def _get_yymm_list(time_range: TimeRange, available_yymm: List[int]) -> List[int]:
    """Get yymm list from time_range."""
    if time_range.type == "last_n_months":
        if time_range.n:
            sorted_yymm = sorted(available_yymm)
            return sorted_yymm[-time_range.n:] if len(sorted_yymm) >= time_range.n else sorted_yymm
    elif time_range.type == "yymm_range":
        if time_range.start_yymm and time_range.end_yymm:
            return [ym for ym in available_yymm if time_range.start_yymm <= ym <= time_range.end_yymm]
    elif time_range.type == "single_yymm":
        if time_range.yymm:
            return [time_range.yymm] if time_range.yymm in available_yymm else []
    return available_yymm


def _apply_filters(df: pd.DataFrame, filters: Filters, site_master_df: pd.DataFrame) -> pd.DataFrame:
    """Apply filters to dataframe."""
    result = df.copy()
    
    # Merge with site master for filtering
    if not site_master_df.empty:
        sm_cols = ["site_id"]
        # Add all columns that might be needed for filtering
        for col in ["region", "site_type", "contract_type", "contract_target", "network_gen", "is_rapa", "rapa_type"]:
            if col in site_master_df.columns:
                sm_cols.append(col)
        
        result = result.merge(
            site_master_df[sm_cols],
            on="site_id",
            how="left",
            suffixes=("", "_sm")
        )
        
        # Normalize columns: prefer site_master values, fallback to source
        for col in ["region", "site_type", "contract_type"]:
            col_sm = f"{col}_sm"
            if col_sm in result.columns:
                result[col] = result[col_sm].fillna(result.get(col, None))
            elif col not in result.columns:
                result[col] = None
    
    # Apply filters
    if filters.region and "region" in result.columns:
        result = result[result["region"].isin(filters.region)]
    
    if filters.site_type and "site_type" in result.columns:
        result = result[result["site_type"].isin(filters.site_type)]
    
    if filters.contract_type_major:
        # Try multiple column names for contract_type
        contract_col = None
        for col_name in ["contract_type", "contract_type_sm"]:
            if col_name in result.columns:
                contract_col = col_name
                break
        if contract_col:
            result = result[result[contract_col].isin(filters.contract_type_major)]
    
    if filters.contract_target and filters.contract_target != "전체":
        target_map = {
            "한전계약(ME)": "ME",
            "건물계약(MC)": "MC"
        }
        target_value = target_map.get(filters.contract_target, filters.contract_target)
        for col_name in ["contract_target", "contract_target_cd", "계약대상"]:
            if col_name in result.columns:
                result = result[result[col_name] == target_value]
                break
    
    if filters.rapa and filters.rapa != "전체":
        # Try multiple column names and formats
        rapa_col = None
        for col_name in ["is_rapa", "is_rapa_sm", "rapa_yn", "rapa", "rapa_type", "rapa_type_sm"]:
            if col_name in result.columns:
                rapa_col = col_name
                break
        if rapa_col:
            if result[rapa_col].dtype == bool:
                if filters.rapa == "RAPA":
                    result = result[result[rapa_col] == True]
                else:
                    result = result[result[rapa_col] == False]
            else:
                if filters.rapa == "RAPA":
                    result = result[result[rapa_col].isin(["Y", "y", "RAPA", "RAPA국소"])]
                else:
                    result = result[result[rapa_col].isin(["N", "n", "비RAPA", "non-RAPA", "비RAPA국소"])]
    
    if filters.network_gen:
        # Try multiple column names
        network_col = None
        for col_name in ["network_gen", "network_gen_sm", "network_generation", "generation", "세대"]:
            if col_name in result.columns:
                network_col = col_name
                break
        if network_col:
            result = result[result[network_col].isin(filters.network_gen)]
    
    return result


def _execute_top_n(
    plan: Plan,
    bills_df: pd.DataFrame,
    actual_df: pd.DataFrame,
    site_master_df: pd.DataFrame,
) -> ExecutionResult:
    """Execute top_n query."""
    # Get appropriate dataframe
    source_df, metric_col = _get_dataframe_for_metric(plan.metric, bills_df, actual_df)
    
    if source_df.empty:
        return ExecutionResult(
            result_df=pd.DataFrame(),
            summary={},
            success=False,
            error_message="데이터가 없습니다.",
        )
    
    # Get yymm list
    available_yymm = sorted(source_df["yymm"].dropna().astype(int).unique().tolist())
    yymm_list = _get_yymm_list(plan.time_range, available_yymm)
    
    # Filter by time range
    if yymm_list:
        source_df = source_df[source_df["yymm"].astype(int).isin(yymm_list)].copy()
    
    # Apply filters
    filtered_df = _apply_filters(source_df, plan.filters, site_master_df)
    
    # Merge with site master for site_name
    if not site_master_df.empty and "site_name" in site_master_df.columns:
        filtered_df = filtered_df.merge(
            site_master_df[["site_id", "site_name"]],
            on="site_id",
            how="left"
        )
    
    # Aggregate by site
    if metric_col not in filtered_df.columns:
        return ExecutionResult(
            result_df=pd.DataFrame(),
            summary={},
            success=False,
            error_message=f"지표 컬럼({metric_col})이 데이터에 없습니다.",
        )
    
    agg_cols = ["site_id"]
    if "site_name" in filtered_df.columns:
        agg_cols.append("site_name")
    if "region" in filtered_df.columns:
        agg_cols.append("region")
    if "site_type" in filtered_df.columns:
        agg_cols.append("site_type")
    
    agg = (
        filtered_df.groupby(agg_cols, dropna=False)[metric_col]
        .sum()
        .reset_index()
        .rename(columns={metric_col: "value"})
        .sort_values("value", ascending=False)
    )
    
    # Apply top_n
    if plan.top_n:
        agg = agg.head(plan.top_n)
    
    # Add rank
    agg.insert(0, "rank", range(1, len(agg) + 1))
    
    # Summary
    summary = {
        "total_sites": len(agg),
        "total_value": float(agg["value"].sum()),
        "avg_value": float(agg["value"].mean()),
        "max_value": float(agg["value"].max()),
        "min_value": float(agg["value"].min()),
        "yymm_list": yymm_list,
    }
    
    return ExecutionResult(
        result_df=agg,
        summary=summary,
        success=True,
    )


def _execute_trend(
    plan: Plan,
    bills_df: pd.DataFrame,
    actual_df: pd.DataFrame,
    site_master_df: pd.DataFrame,
) -> ExecutionResult:
    """Execute trend query."""
    # Get appropriate dataframe
    source_df, metric_col = _get_dataframe_for_metric(plan.metric, bills_df, actual_df)
    
    if source_df.empty:
        return ExecutionResult(
            result_df=pd.DataFrame(),
            summary={},
            success=False,
            error_message="데이터가 없습니다.",
        )
    
    # Get yymm list
    available_yymm = sorted(source_df["yymm"].dropna().astype(int).unique().tolist())
    yymm_list = _get_yymm_list(plan.time_range, available_yymm)
    
    # Filter by time range
    if yymm_list:
        source_df = source_df[source_df["yymm"].astype(int).isin(yymm_list)].copy()
    
    # Apply filters
    filtered_df = _apply_filters(source_df, plan.filters, site_master_df)
    
    # Aggregate by month
    if metric_col not in filtered_df.columns:
        return ExecutionResult(
            result_df=pd.DataFrame(),
            summary={},
            success=False,
            error_message=f"지표 컬럼({metric_col})이 데이터에 없습니다.",
        )
    
    monthly_agg = (
        filtered_df.groupby("yymm")[metric_col]
        .agg(["sum", "mean", "count"])
        .reset_index()
    )
    monthly_agg.columns = ["yymm", "total_value", "avg_value", "site_count"]
    monthly_agg = monthly_agg.sort_values("yymm").reset_index(drop=True)
    
    # Calculate month-over-month changes
    monthly_agg["mom_change"] = monthly_agg["total_value"].diff()
    monthly_agg["mom_change_pct"] = (
        (monthly_agg["mom_change"] / monthly_agg["total_value"].shift(1) * 100)
        .round(2)
    )
    
    # Create month label
    monthly_agg["month_label"] = monthly_agg["yymm"].astype(str).apply(
        lambda x: f"{x[:4]}.{x[4:6]}" if len(x) >= 6 else x
    )
    
    # Summary
    if len(monthly_agg) > 0:
        first_value = float(monthly_agg.iloc[0]["total_value"])
        last_value = float(monthly_agg.iloc[-1]["total_value"])
        overall_change_pct = ((last_value - first_value) / first_value * 100) if first_value > 0 else 0
        
        summary = {
            "num_months": len(monthly_agg),
            "total_value": float(monthly_agg["total_value"].sum()),
            "avg_monthly": float(monthly_agg["total_value"].mean()),
            "max_month": monthly_agg.loc[monthly_agg["total_value"].idxmax(), "month_label"],
            "max_value": float(monthly_agg["total_value"].max()),
            "min_month": monthly_agg.loc[monthly_agg["total_value"].idxmin(), "month_label"],
            "min_value": float(monthly_agg["total_value"].min()),
            "overall_change_pct": round(overall_change_pct, 2),
            "avg_mom_change_pct": float(monthly_agg["mom_change_pct"].mean()),
        }
    else:
        summary = {}
    
    return ExecutionResult(
        result_df=monthly_agg,
        summary=summary,
        success=True,
    )


def _execute_comparison(
    plan: Plan,
    bills_df: pd.DataFrame,
    actual_df: pd.DataFrame,
    site_master_df: pd.DataFrame,
) -> ExecutionResult:
    """Execute comparison query."""
    if plan.metric != Metric.BILL_VS_ACTUAL_GAP.value:
        return ExecutionResult(
            result_df=pd.DataFrame(),
            summary={},
            success=False,
            error_message="비교 질의는 bill_vs_actual_gap 지표만 지원합니다.",
        )
    
    # Get yymm list
    available_yymm = sorted(bills_df["yymm"].dropna().astype(int).unique().tolist())
    yymm_list = _get_yymm_list(plan.time_range, available_yymm)
    
    # Filter by time range
    if yymm_list:
        bills_filtered = bills_df[bills_df["yymm"].astype(int).isin(yymm_list)].copy()
        actual_filtered = actual_df[actual_df["yymm"].astype(int).isin(yymm_list)].copy()
    else:
        bills_filtered = bills_df.copy()
        actual_filtered = actual_df.copy()
    
    # Merge bills and actual
    merged = bills_filtered.merge(
        actual_filtered,
        on=["yymm", "site_id"],
        how="left",
        suffixes=("", "_actual")
    )
    
    # Apply filters
    merged = _apply_filters(merged, plan.filters, site_master_df)
    
    # Calculate gap
    merged["gap_kwh"] = merged["kwh_actual"] - merged["kwh_bill"]
    merged["gap_pct"] = calculate_bill_actual_error(
        merged["kwh_actual"],
        merged["kwh_bill"]
    )
    
    # Calculate estimated cost from actual
    avg_unit_cost = (
        merged["cost_bill"].sum() / merged["kwh_bill"].sum()
        if merged["kwh_bill"].sum() > 0 else 0
    )
    merged["cost_actual_est"] = merged["kwh_actual"] * avg_unit_cost
    merged["gap_cost"] = merged["cost_actual_est"] - merged["cost_bill"]
    
    # Classify mismatches
    merged["mismatch_class"] = merged.apply(
        lambda row: classify_bill_actual_mismatch(row, threshold_pct=10.0),
        axis=1
    )
    
    # Summary
    summary = {
        "total_kwh_bill": float(merged["kwh_bill"].sum()),
        "total_kwh_actual": float(merged["kwh_actual"].sum()),
        "total_cost_bill": float(merged["cost_bill"].sum()),
        "kwh_diff": float(merged["gap_kwh"].sum()),
        "kwh_diff_pct": float((merged["gap_kwh"].sum() / merged["kwh_bill"].sum() * 100) if merged["kwh_bill"].sum() > 0 else 0),
        "cost_diff": float(merged["gap_cost"].sum()),
        "mismatch_summary": merged["mismatch_class"].value_counts().to_dict(),
        "total_sites": len(merged),
    }
    
    # Result dataframe: site-level comparison
    result_df = merged[[
        "site_id", "yymm", "region", "site_type",
        "kwh_bill", "kwh_actual", "gap_kwh", "gap_pct",
        "cost_bill", "cost_actual_est", "gap_cost",
        "mismatch_class"
    ]].copy()
    
    return ExecutionResult(
        result_df=result_df,
        summary=summary,
        success=True,
    )


def _execute_anomaly(
    plan: Plan,
    bills_df: pd.DataFrame,
    actual_df: pd.DataFrame,
    site_master_df: pd.DataFrame,
) -> ExecutionResult:
    """Execute anomaly detection query."""
    # Similar to top_n but with anomaly scoring
    source_df, metric_col = _get_dataframe_for_metric(plan.metric, bills_df, actual_df)
    
    if source_df.empty:
        return ExecutionResult(
            result_df=pd.DataFrame(),
            summary={},
            success=False,
            error_message="데이터가 없습니다.",
        )
    
    # Get yymm list
    available_yymm = sorted(source_df["yymm"].dropna().astype(int).unique().tolist())
    yymm_list = _get_yymm_list(plan.time_range, available_yymm)
    
    if yymm_list:
        source_df = source_df[source_df["yymm"].astype(int).isin(yymm_list)].copy()
    
    # Apply filters
    filtered_df = _apply_filters(source_df, plan.filters, site_master_df)
    
    # Calculate anomaly scores per site
    site_agg = (
        filtered_df.groupby("site_id")[metric_col]
        .agg(["mean", "std", "count"])
        .reset_index()
    )
    site_agg.columns = ["site_id", "mean_value", "std_value", "count"]
    
    # Calculate z-score
    overall_mean = site_agg["mean_value"].mean()
    overall_std = site_agg["mean_value"].std()
    site_agg["z_score"] = (site_agg["mean_value"] - overall_mean) / (overall_std + 1e-10)
    site_agg["is_anomaly"] = abs(site_agg["z_score"]) > 2.0
    
    # Merge with site master
    if not site_master_df.empty:
        site_agg = site_agg.merge(
            site_master_df[["site_id", "site_name", "region", "site_type"]],
            on="site_id",
            how="left"
        )
    
    # Sort by z_score (absolute value)
    site_agg["abs_z_score"] = site_agg["z_score"].abs()
    site_agg = site_agg.sort_values("abs_z_score", ascending=False)
    
    # Filter anomalies only
    anomaly_df = site_agg[site_agg["is_anomaly"]].copy()
    
    if plan.top_n:
        anomaly_df = anomaly_df.head(plan.top_n)
    
    # Summary
    summary = {
        "total_sites": len(site_agg),
        "anomaly_count": len(anomaly_df),
        "anomaly_rate": len(anomaly_df) / len(site_agg) * 100 if len(site_agg) > 0 else 0,
    }
    
    return ExecutionResult(
        result_df=anomaly_df,
        summary=summary,
        success=True,
    )


def _execute_recommendation(
    plan: Plan,
    bills_df: pd.DataFrame,
    actual_df: pd.DataFrame,
    site_master_df: pd.DataFrame,
) -> ExecutionResult:
    """Execute recommendation query."""
    # For now, similar to top_n but with recommendation logic
    # This can be extended with actual recommendation algorithms
    return _execute_top_n(plan, bills_df, actual_df, site_master_df)

