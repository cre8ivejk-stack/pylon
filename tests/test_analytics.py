"""Unit tests for analytics module."""

import pytest
import pandas as pd
import numpy as np
from src.analytics import (
    calculate_plan_variance,
    calculate_bill_actual_error,
    calculate_risk_score,
    classify_bill_actual_mismatch,
    detect_zero_usage_sites,
    recommend_contract_power_adjustment,
    decompose_cost_variance,
    calculate_yoy_comparison
)


class TestPlanVariance:
    """Tests for plan variance calculation."""
    
    def test_basic_variance(self):
        """Test basic variance calculation."""
        result = calculate_plan_variance(actual_value=110, plan_value=100)
        
        assert result['variance'] == 10
        assert result['variance_pct'] == 10.0
        assert result['achievement_rate'] == 110.0
    
    def test_negative_variance(self):
        """Test negative variance (under plan)."""
        result = calculate_plan_variance(actual_value=90, plan_value=100)
        
        assert result['variance'] == -10
        assert result['variance_pct'] == -10.0
        assert result['achievement_rate'] == 90.0
    
    def test_zero_plan(self):
        """Test with zero plan value."""
        result = calculate_plan_variance(actual_value=50, plan_value=0)
        
        assert result['variance'] == 50
        assert result['variance_pct'] == 0.0
        assert result['achievement_rate'] == 0.0


class TestBillActualError:
    """Tests for bill vs actual error calculation."""
    
    def test_positive_error(self):
        """Test positive error (actual > bill)."""
        error = calculate_bill_actual_error(actual_kwh=110, bill_kwh=100)
        assert error == 10.0
    
    def test_negative_error(self):
        """Test negative error (actual < bill)."""
        error = calculate_bill_actual_error(actual_kwh=90, bill_kwh=100)
        assert error == -10.0
    
    def test_zero_bill(self):
        """Test with zero bill value."""
        error = calculate_bill_actual_error(actual_kwh=50, bill_kwh=0)
        assert error == 0.0


class TestRiskScore:
    """Tests for risk score calculation."""
    
    def test_high_risk(self):
        """Test high risk scenario."""
        result = calculate_risk_score(
            impact=10_000_000,  # 10M KRW
            likelihood=0.8,
            confidence=0.9
        )
        assert result['raw_score'] == 10_000_000 * 0.8 * 0.9
        assert 50 < result['display_score'] <= 100
    
    def test_low_risk(self):
        """Test low risk scenario."""
        result = calculate_risk_score(
            impact=100_000,  # 100K KRW
            likelihood=0.1,
            confidence=0.5
        )
        assert result['raw_score'] == 100_000 * 0.1 * 0.5
        assert 0.0 <= result['display_score'] < 10
    
    def test_zero_impact(self):
        """Test with zero impact."""
        result = calculate_risk_score(
            impact=0,
            likelihood=1.0,
            confidence=1.0
        )
        assert result['raw_score'] == 0.0
        assert result['display_score'] == 0.0


class TestBillActualClassification:
    """Tests for bill vs actual mismatch classification."""
    
    def test_normal_range(self):
        """Test normal range classification."""
        row = pd.Series({
            'kwh_actual': 105,
            'kwh_bill': 100,
            'contract_type': '종량'
        })
        
        classification = classify_bill_actual_mismatch(row)
        assert classification == "정상 범위"
    
    def test_investigation_needed(self):
        """Test investigation needed classification."""
        row = pd.Series({
            'kwh_actual': 125,
            'kwh_bill': 100,
            'contract_type': '종량'
        })
        
        classification = classify_bill_actual_mismatch(row)
        assert classification == "조사 필요"
    
    def test_urgent_investigation(self):
        """Test urgent investigation classification."""
        row = pd.Series({
            'kwh_actual': 150,
            'kwh_bill': 100,
            'contract_type': '종량'
        })
        
        classification = classify_bill_actual_mismatch(row)
        assert classification == "긴급 조사"
    
    def test_explainable_fixed_rate(self):
        """Test explainable for fixed rate contracts."""
        row = pd.Series({
            'kwh_actual': 108,
            'kwh_bill': 100,
            'contract_type': '정액'
        })
        
        classification = classify_bill_actual_mismatch(row)
        assert classification == "설명 가능 (정액)"
    
    def test_missing_data(self):
        """Test missing actual data."""
        row = pd.Series({
            'kwh_actual': np.nan,
            'kwh_bill': 100,
            'contract_type': '종량'
        })
        
        classification = classify_bill_actual_mismatch(row)
        assert classification == "데이터 누락"


class TestZeroUsageDetection:
    """Tests for zero usage site detection."""
    
    def test_detect_zero_sites(self):
        """Test zero usage site detection."""
        bills_df = pd.DataFrame([
            {'site_id': 'SITE001', 'yymm': '2401', 'kwh_bill': 0},
            {'site_id': 'SITE001', 'yymm': '2402', 'kwh_bill': 0},
            {'site_id': 'SITE001', 'yymm': '2403', 'kwh_bill': 0},
            {'site_id': 'SITE002', 'yymm': '2401', 'kwh_bill': 0},
            {'site_id': 'SITE002', 'yymm': '2402', 'kwh_bill': 100},
            {'site_id': 'SITE003', 'yymm': '2401', 'kwh_bill': 100},
        ])
        
        result = detect_zero_usage_sites(bills_df, months=3)
        
        assert len(result) == 1
        assert result.iloc[0]['site_id'] == 'SITE001'
        assert result.iloc[0]['zero_months'] == 3
    
    def test_no_zero_sites(self):
        """Test with no zero usage sites."""
        bills_df = pd.DataFrame([
            {'site_id': 'SITE001', 'yymm': '2401', 'kwh_bill': 100},
            {'site_id': 'SITE001', 'yymm': '2402', 'kwh_bill': 100},
        ])
        
        result = detect_zero_usage_sites(bills_df, months=3)
        assert len(result) == 0


class TestCostVarianceDecomposition:
    """Tests for cost variance decomposition."""
    
    def test_usage_effect_only(self):
        """Test pure usage effect (same unit price)."""
        result = decompose_cost_variance(
            actual_cost=110,
            plan_cost=100,
            actual_kwh=110,
            plan_kwh=100
        )
        
        # When unit price is the same, all variance is from usage
        assert result['total_variance'] == 10
        assert abs(result['usage_effect'] - 10) < 0.1
        assert abs(result['price_effect']) < 0.1
    
    def test_price_effect_only(self):
        """Test pure price effect (same kWh)."""
        result = decompose_cost_variance(
            actual_cost=110,
            plan_cost=100,
            actual_kwh=100,
            plan_kwh=100
        )
        
        # When kWh is the same, all variance is from price
        assert result['total_variance'] == 10
        assert abs(result['usage_effect']) < 0.1
        assert abs(result['price_effect'] - 10) < 0.1
    
    def test_zero_plan_kwh(self):
        """Test with zero plan kWh."""
        result = decompose_cost_variance(
            actual_cost=100,
            plan_cost=50,
            actual_kwh=100,
            plan_kwh=0
        )
        
        assert result['total_variance'] == 50


class TestYoYComparison:
    """Tests for year-over-year comparison."""
    
    def test_basic_yoy(self):
        """Test basic YoY calculation."""
        df = pd.DataFrame([
            {'yymm': '2301', 'kwh_bill': 100},
            {'yymm': '2401', 'kwh_bill': 110},
        ])
        
        yoy = calculate_yoy_comparison(df, current_month='2401', metric='kwh_bill')
        assert yoy == 10.0
    
    def test_no_previous_year(self):
        """Test with no previous year data."""
        df = pd.DataFrame([
            {'yymm': '2401', 'kwh_bill': 100},
        ])
        
        yoy = calculate_yoy_comparison(df, current_month='2401', metric='kwh_bill')
        assert yoy is None
    
    def test_zero_previous_value(self):
        """Test with zero previous year value."""
        df = pd.DataFrame([
            {'yymm': '2301', 'kwh_bill': 0},
            {'yymm': '2401', 'kwh_bill': 100},
        ])
        
        yoy = calculate_yoy_comparison(df, current_month='2401', metric='kwh_bill')
        assert yoy is None


class TestContractPowerRecommendation:
    """Tests for contract power adjustment recommendation."""
    
    def test_reduction_recommendation(self):
        """Test reduction recommendation."""
        site_df = pd.DataFrame([
            {'yymm': '2401', 'kwh_bill': 50000, 'contract_power_kw': 100},
            {'yymm': '2402', 'kwh_bill': 52000, 'contract_power_kw': 100},
            {'yymm': '2403', 'kwh_bill': 48000, 'contract_power_kw': 100},
        ])
        
        result = recommend_contract_power_adjustment(site_df, safety_margin=1.15)
        
        assert result['current_contract_kw'] == 100
        assert result['savings_est'] > 0  # Should recommend reduction
        assert '감설' in result['recommendation']
    
    def test_no_data(self):
        """Test with no data."""
        site_df = pd.DataFrame()
        
        result = recommend_contract_power_adjustment(site_df)
        
        assert result['recommendation'] == '데이터 부족'
        assert result['savings_est'] == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

