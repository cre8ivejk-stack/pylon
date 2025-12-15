"""Sample data generator for PYLON platform."""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple


def generate_sample_data(data_dir: Path) -> None:
    """
    Generate sample datasets for MVP demonstration.
    
    Args:
        data_dir: Directory to save parquet files
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Configuration
    np.random.seed(42)
    months = [f"23{m:02d}" for m in range(7, 13)] + [f"24{m:02d}" for m in range(1, 13)]
    regions = ["수도권", "중부", "동부", "서부"]
    site_types = ["기지국", "통합국", "사옥", "중계국", "기타"]
    contract_types = ["정액", "종량"]
    contract_targets = ["ME", "MC"]  # 한전계약(ME), 건물계약(MC)
    network_gens = ["3G", "LTE", "5G"]
    voltages = ["저압", "고압"]
    data_sources = ["EMS", "PRB", "EST"]
    
    n_sites = 300
    
    # Generate site_master
    sites = []
    for i in range(n_sites):
        site_id = f"SITE{i:04d}"
        site_type = np.random.choice(site_types, p=[0.55, 0.2, 0.05, 0.15, 0.05])
        sites.append({
            'site_id': site_id,
            'site_name': f"{site_type}_{i:04d}",
            'region': np.random.choice(regions),
            'site_type': site_type,
            'voltage': np.random.choice(voltages, p=[0.7, 0.3]),
            'contract_type': np.random.choice(contract_types, p=[0.4, 0.6]),
            'contract_target': np.random.choice(contract_targets, p=[0.7, 0.3]),  # 70% ME, 30% MC
            'network_gen': np.random.choice(network_gens, p=[0.05, 0.35, 0.6]),  # 5% 3G, 35% LTE, 60% 5G
            'is_rapa': np.random.choice([True, False], p=[0.3, 0.7])  # 30% RAPA
        })
    
    site_master = pd.DataFrame(sites)
    site_master.to_parquet(data_dir / "sample_site_master.parquet", index=False)
    
    # Generate bills
    bills = []
    for month in months:
        for _, site_row in site_master.iterrows():
            site_id = site_row['site_id']
            contract_type = site_row['contract_type']
            
            # Base consumption with seasonality
            base_kwh = np.random.uniform(5000, 50000)
            month_num = int(month[2:])
            seasonal = 1.0 + 0.3 * np.sin((month_num - 3) * np.pi / 6)  # Peak in summer
            kwh_bill = base_kwh * seasonal * np.random.uniform(0.9, 1.1)
            
            # Some sites have zero usage occasionally
            if np.random.random() < 0.02:
                kwh_bill = 0
            
            # Contract power
            if contract_type == "정액":
                contract_power_kw = kwh_bill / 720 * 1.2  # Rough conversion
            else:
                contract_power_kw = kwh_bill / 720 * 1.5
            
            # Cost calculation (simplified)
            if contract_type == "정액":
                cost_bill = contract_power_kw * 8000 + kwh_bill * 80  # 기본요금 + 전력량요금
            else:
                cost_bill = kwh_bill * 120
            
            bills.append({
                'yymm': month,
                'site_id': site_id,
                'kwh_bill': kwh_bill,
                'cost_bill': cost_bill,
                'contract_type': contract_type,
                'contract_type_minor': '표준형',  # 향후 확장 예정
                'contract_power_kw': contract_power_kw,
                'region': site_row['region'],
                'contract_target': site_row['contract_target'],
                'network_gen': site_row['network_gen'],
                'is_rapa': site_row['is_rapa']
            })
    
    bills_df = pd.DataFrame(bills)
    bills_df.to_parquet(data_dir / "sample_bills.parquet", index=False)
    
    # Generate actual (with some variance from bills)
    actual = []
    for _, bill_row in bills_df.iterrows():
        # Actual differs from bill by some amount
        variance_factor = np.random.uniform(0.85, 1.15)
        kwh_actual = bill_row['kwh_bill'] * variance_factor
        
        # Some sites missing actual data
        if np.random.random() < 0.05:
            continue
        
        # Data source affects confidence
        ds = np.random.choice(data_sources, p=[0.5, 0.3, 0.2])
        confidence_map = {"EMS": 0.95, "PRB": 0.80, "EST": 0.60}
        confidence = confidence_map[ds] * np.random.uniform(0.95, 1.0)
        
        # Cost estimation
        if bill_row['contract_type'] == "정액":
            cost_actual_est = bill_row['contract_power_kw'] * 8000 + kwh_actual * 80
        else:
            cost_actual_est = kwh_actual * 120
        
        actual.append({
            'yymm': bill_row['yymm'],
            'site_id': bill_row['site_id'],
            'kwh_actual': kwh_actual,
            'cost_actual_est': cost_actual_est,
            'data_source': ds,
            'confidence': confidence,
            'region': bill_row['region'],
            'contract_target': bill_row['contract_target'],
            'network_gen': bill_row['network_gen'],
            'is_rapa': bill_row['is_rapa']
        })
    
    actual_df = pd.DataFrame(actual)
    actual_df.to_parquet(data_dir / "sample_actual.parquet", index=False)
    
    # Generate plan
    plan = []
    for month in months:
        # Aggregate plan by month
        total_kwh_plan = bills_df[bills_df['yymm'] == month]['kwh_bill'].sum() * 1.05  # Plan is 5% higher
        total_cost_plan = bills_df[bills_df['yymm'] == month]['cost_bill'].sum() * 1.05
        
        plan.append({
            'yymm': month,
            'site_id': None,
            'kwh_plan': total_kwh_plan,
            'cost_plan': total_cost_plan
        })
    
    plan_df = pd.DataFrame(plan)
    plan_df.to_parquet(data_dir / "sample_plan.parquet", index=False)
    
    # Generate traffic
    traffic = []
    for month in months:
        for _, site_row in site_master.iterrows():
            site_id = site_row['site_id']
            # Traffic correlates loosely with kwh
            site_bill = bills_df[(bills_df['yymm'] == month) & (bills_df['site_id'] == site_id)]
            if len(site_bill) > 0:
                kwh = site_bill['kwh_bill'].values[0]
                gb_traffic = kwh / 10 * np.random.uniform(0.8, 1.2)  # Rough correlation
            else:
                gb_traffic = np.random.uniform(100, 10000)
            
            traffic.append({
                'yymm': month,
                'site_id': site_id,
                'gb_traffic': gb_traffic,
                'region': site_row['region'],
                'network_gen': site_row['network_gen']
            })
    
    traffic_df = pd.DataFrame(traffic)
    traffic_df.to_parquet(data_dir / "sample_traffic.parquet", index=False)
    
    print(f"✓ Generated sample data in {data_dir}")
    print(f"  - Sites: {len(site_master)}")
    print(f"  - Bills: {len(bills_df)} records")
    print(f"  - Actual: {len(actual_df)} records")
    print(f"  - Plan: {len(plan_df)} records")
    print(f"  - Traffic: {len(traffic_df)} records")


def get_sample_site_master() -> pd.DataFrame:
    """Quick site master for testing."""
    return pd.DataFrame([
        {'site_id': 'SITE0001', 'site_name': '기지국_0001', 'region': '수도권', 
         'site_type': '기지국', 'voltage': '저압', 'contract_type': '종량'},
    ])


