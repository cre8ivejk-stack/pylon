"""Sample data generator for PYLON platform."""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple


def generate_sample_data(data_dir: Path) -> None:
    """
    Generate rich sample datasets for comprehensive testing.
    
    Includes:
    - 3 full years of data (2024-2026)
    - 500 sites with diverse characteristics
    - Realistic scenarios: normal, high-risk, zero-usage, billing errors
    - Seasonal patterns and trends (3G decline, 5G growth)
    - Contract optimization opportunities
    
    Args:
        data_dir: Directory to save parquet files
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Configuration
    np.random.seed(42)
    # 2024.01 ~ 2026.04 (28 months)
    months = []
    for year in range(2024, 2026):
        for m in range(1, 13):
            months.append(f"{year}{m:02d}")
    # Add 2026.01 ~ 2026.04
    for m in range(1, 5):
        months.append(f"2026{m:02d}")
    regions = ["수도권", "중부", "동부", "서부"]
    site_types = ["기지국", "통합국", "사옥", "중계국", "IDC", "기타"]  # Added IDC
    contract_types = ["정액", "종량"]
    contract_targets = ["ME", "MC"]  # 한전계약(ME), 건물계약(MC)
    network_gens = ["3G", "LTE", "5G"]
    voltages = ["저압", "고압"]
    data_sources = ["EMS", "PRB", "EST"]
    
    n_sites = 500  # Increased from 300
    
    # 지역별 좌표 범위 및 샘플 주소
    region_coords = {
        "수도권": {
            "lat_range": (37.40, 37.70),
            "lon_range": (126.80, 127.20),
            "cities": ["서울시 강남구", "서울시 서초구", "서울시 송파구", "경기도 성남시", "경기도 수원시", "경기도 용인시"]
        },
        "중부": {
            "lat_range": (36.20, 36.50),
            "lon_range": (127.30, 127.50),
            "cities": ["대전시 유성구", "대전시 서구", "충청남도 천안시", "충청북도 청주시", "세종시"]
        },
        "동부": {
            "lat_range": (35.10, 35.20),
            "lon_range": (129.00, 129.10),
            "cities": ["부산시 해운대구", "부산시 수영구", "울산시 남구", "경상남도 창원시", "경상북도 포항시"]
        },
        "서부": {
            "lat_range": (35.10, 35.20),
            "lon_range": (126.80, 127.00),
            "cities": ["광주시 북구", "광주시 서구", "전라남도 목포시", "전라북도 전주시", "전라남도 순천시"]
        }
    }
    
    # Generate site_master with scenario tags
    sites = []
    for i in range(n_sites):
        site_id = f"SITE{i:04d}"
        site_type = np.random.choice(site_types, p=[0.50, 0.18, 0.05, 0.12, 0.10, 0.05])
        network_gen = np.random.choice(network_gens, p=[0.05, 0.35, 0.60])  # 5% 3G, 35% LTE, 60% 5G
        is_rapa = np.random.choice([True, False], p=[0.30, 0.70])
        region = np.random.choice(regions)
        
        # 지역별 좌표 및 주소 생성
        region_info = region_coords[region]
        lat = np.random.uniform(*region_info["lat_range"])
        lon = np.random.uniform(*region_info["lon_range"])
        city = np.random.choice(region_info["cities"])
        street_num = np.random.randint(1, 999)
        building_num = np.random.randint(1, 99)
        address = f"{city} {street_num}길 {building_num}"
        
        # Scenario assignment (for diverse test cases)
        scenario = "normal"
        if i < 50:  # First 50 sites: High Risk scenarios
            scenario = "high_risk"
        elif i < 100:  # Next 50: Contract optimization candidates
            scenario = "overcontracted"
        elif i < 125:  # Next 25: Zero usage (철거 대상)
            scenario = "zero_usage"
        elif i < 175:  # Next 50: Billing errors
            scenario = "billing_error"
        
        sites.append({
            'site_id': site_id,
            'site_name': f"{site_type}_{i:04d}",
            'region': region,
            'site_type': site_type,
            'voltage': np.random.choice(voltages, p=[0.7, 0.3]),
            'contract_type': np.random.choice(contract_types, p=[0.4, 0.6]),
            'contract_target': np.random.choice(contract_targets, p=[0.7, 0.3]),  # 70% ME, 30% MC
            'network_gen': network_gen,
            'generation': network_gen,  # For filter compatibility
            'is_rapa': is_rapa,
            'rapa_type': 'RAPA' if is_rapa else '일반',  # For filter compatibility
            'scenario': scenario,  # Internal tag for data generation
            'address': address,  # 주소
            'latitude': round(lat, 6),  # 위도
            'longitude': round(lon, 6)  # 경도
        })
    
    site_master = pd.DataFrame(sites)
    site_master.to_parquet(data_dir / "sample_site_master.parquet", index=False)
    
    # Generate bills with realistic scenarios
    bills = []
    for month_idx, month in enumerate(months):
        year = int(month[:4])
        month_num = int(month[4:6])
        
        for _, site_row in site_master.iterrows():
            site_id = site_row['site_id']
            contract_type = site_row['contract_type']
            network_gen = site_row['network_gen']
            scenario = site_row['scenario']
            
            # Base consumption varies by site type and generation
            if site_row['site_type'] == 'IDC':
                base_kwh = np.random.uniform(50000, 200000)
            elif site_row['site_type'] == '사옥':
                base_kwh = np.random.uniform(30000, 100000)
            elif site_row['site_type'] == '통합국':
                base_kwh = np.random.uniform(20000, 80000)
            else:
                base_kwh = np.random.uniform(5000, 50000)
            
            # Seasonality: Peak in summer (June-August)
            seasonal = 1.0 + 0.4 * np.sin((month_num - 3) * np.pi / 6)
            
            # Year-over-year trend
            if network_gen == "3G":
                # 3G declining over time (phase-out effect)
                trend = 1.0 - 0.15 * (year - 2024)
            elif network_gen == "5G":
                # 5G growing
                trend = 1.0 + 0.10 * (year - 2024)
            else:
                # LTE stable
                trend = 1.0
            
            # Apply scenario-specific patterns
            if scenario == "high_risk":
                # High variance, occasional spikes
                kwh_bill = base_kwh * seasonal * trend * np.random.uniform(0.5, 2.0)
            elif scenario == "overcontracted":
                # Consistently low usage vs contract
                kwh_bill = base_kwh * seasonal * trend * np.random.uniform(0.4, 0.7)
            elif scenario == "zero_usage":
                # Zero usage for last 3-6 months (phase-out)
                # For 25 months, zero out last 3-4 months
                if month_idx >= len(months) - 4:
                    kwh_bill = 0
                else:
                    kwh_bill = base_kwh * seasonal * trend * np.random.uniform(0.8, 1.0)
            elif scenario == "billing_error":
                # Occasional large discrepancies
                if np.random.random() < 0.2:
                    kwh_bill = base_kwh * seasonal * trend * np.random.uniform(1.5, 3.0)
                else:
                    kwh_bill = base_kwh * seasonal * trend * np.random.uniform(0.9, 1.1)
            else:  # normal
                kwh_bill = base_kwh * seasonal * trend * np.random.uniform(0.9, 1.1)
            
            # Contract power
            if contract_type == "정액":
                if scenario == "overcontracted":
                    # Over-contracted: contract power much higher than actual usage
                    contract_power_kw = (kwh_bill / 720 * 1.2) * 1.5
                else:
                    contract_power_kw = kwh_bill / 720 * 1.2
            else:
                contract_power_kw = kwh_bill / 720 * 1.5
            
            # Cost calculation (more realistic)
            if contract_type == "정액":
                basic_charge = contract_power_kw * 8000  # 기본요금
                energy_charge = kwh_bill * 80  # 전력량요금
                cost_bill = basic_charge + energy_charge
            else:
                cost_bill = kwh_bill * 120
            
            bills.append({
                'yymm': int(month),  # Convert to int for consistency
                'site_id': site_id,
                'kwh_bill': round(kwh_bill, 2),
                'cost_bill': round(cost_bill, 2),
                'contract_type': contract_type,
                'contract_type_minor': '표준형',
                'contract_power_kw': round(contract_power_kw, 2),
                'region': site_row['region'],
                'contract_target': site_row['contract_target'],
                'network_gen': network_gen,
                'generation': network_gen,  # For filter compatibility
                'is_rapa': site_row['is_rapa'],
                'rapa_type': site_row['rapa_type']  # For filter compatibility
            })
    
    bills_df = pd.DataFrame(bills)
    bills_df.to_parquet(data_dir / "sample_bills.parquet", index=False)
    
    # Generate actual (with scenario-based variance from bills)
    actual = []
    # Get scenario mapping from site_master
    scenario_map = dict(zip(site_master['site_id'], site_master['scenario']))
    
    for _, bill_row in bills_df.iterrows():
        site_id = bill_row['site_id']
        scenario = scenario_map.get(site_id, 'normal')
        
        # Determine variance based on scenario
        if scenario == "billing_error":
            # Large discrepancy between bill and actual
            if np.random.random() < 0.3:  # 30% chance of major error
                variance_factor = np.random.choice([0.5, 1.8])  # Under or over billing
            else:
                variance_factor = np.random.uniform(0.90, 1.10)
        elif scenario == "high_risk":
            # Higher variance
            variance_factor = np.random.uniform(0.70, 1.30)
        else:
            # Normal variance
            variance_factor = np.random.uniform(0.95, 1.05)
        
        kwh_actual = bill_row['kwh_bill'] * variance_factor
        
        # Some sites missing actual data (reduced from 5% to 3%)
        if np.random.random() < 0.03:
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
            'site_id': site_id,
            'kwh_actual': round(kwh_actual, 2),
            'cost_actual_est': round(cost_actual_est, 2),
            'data_source': ds,
            'confidence': round(confidence, 4),
            'region': bill_row['region'],
            'contract_target': bill_row['contract_target'],
            'network_gen': bill_row['network_gen'],
            'generation': bill_row['generation'],
            'is_rapa': bill_row['is_rapa'],
            'rapa_type': bill_row['rapa_type']
        })
    
    actual_df = pd.DataFrame(actual)
    actual_df.to_parquet(data_dir / "sample_actual.parquet", index=False)
    
    # Generate plan (strategic targets, slightly optimistic)
    plan = []
    for month in months:
        month_int = int(month)
        # Aggregate plan by month - plan is typically 3-7% higher than actual
        plan_buffer = np.random.uniform(1.03, 1.07)
        total_kwh_plan = bills_df[bills_df['yymm'] == month_int]['kwh_bill'].sum() * plan_buffer
        total_cost_plan = bills_df[bills_df['yymm'] == month_int]['cost_bill'].sum() * plan_buffer
        
        plan.append({
            'yymm': month_int,
            'site_id': None,
            'kwh_plan': round(total_kwh_plan, 2),
            'cost_plan': round(total_cost_plan, 2)
        })
    
    plan_df = pd.DataFrame(plan)
    plan_df.to_parquet(data_dir / "sample_plan.parquet", index=False)
    
    # Generate traffic (network generation specific patterns)
    traffic = []
    for month_idx, month in enumerate(months):
        month_int = int(month)
        year = int(month[:4])
        
        for _, site_row in site_master.iterrows():
            site_id = site_row['site_id']
            network_gen = site_row['network_gen']
            
            # Traffic correlates with kwh but varies by generation
            site_bill = bills_df[(bills_df['yymm'] == month_int) & (bills_df['site_id'] == site_id)]
            
            if len(site_bill) > 0:
                kwh = site_bill['kwh_bill'].values[0]
                
                # Base traffic from energy consumption
                if network_gen == "5G":
                    # 5G: High traffic, growing over time
                    base_traffic = kwh / 8 * (1.0 + 0.15 * (year - 2024))
                elif network_gen == "LTE":
                    # LTE: Moderate traffic, stable
                    base_traffic = kwh / 12
                else:  # 3G
                    # 3G: Low traffic, declining
                    base_traffic = kwh / 20 * (1.0 - 0.20 * (year - 2024))
                
                gb_traffic = base_traffic * np.random.uniform(0.8, 1.2)
            else:
                gb_traffic = np.random.uniform(100, 10000)
            
            traffic.append({
                'yymm': month_int,
                'site_id': site_id,
                'gb_traffic': round(gb_traffic, 2),
                'region': site_row['region'],
                'network_gen': network_gen,
                'generation': network_gen
            })
    
    traffic_df = pd.DataFrame(traffic)
    traffic_df.to_parquet(data_dir / "sample_traffic.parquet", index=False)
    
    print(f"✅ Generated enriched sample data in {data_dir}")
    print(f"  📍 Sites: {len(site_master)}")
    print(f"  📊 Bills: {len(bills_df):,} records ({len(months)} months × {n_sites} sites)")
    print(f"  📈 Actual: {len(actual_df):,} records ({len(actual_df)/len(bills_df)*100:.1f}% coverage)")
    print(f"  📋 Plan: {len(plan_df)} records")
    print(f"  🌐 Traffic: {len(traffic_df):,} records")
    print(f"\n  🎯 Scenarios:")
    print(f"     - Normal: {len([s for s in site_master['scenario'] if s == 'normal'])} sites")
    print(f"     - High Risk: {len([s for s in site_master['scenario'] if s == 'high_risk'])} sites")
    print(f"     - Overcontracted: {len([s for s in site_master['scenario'] if s == 'overcontracted'])} sites")
    print(f"     - Zero Usage: {len([s for s in site_master['scenario'] if s == 'zero_usage'])} sites")
    print(f"     - Billing Error: {len([s for s in site_master['scenario'] if s == 'billing_error'])} sites")
    print(f"\n  📅 Period: 2024.01 ~ 2026.04 (28 months)")
    print(f"  🏢 Regions: {', '.join(regions)}")
    print(f"  📡 Generations: 3G ({len(site_master[site_master['network_gen']=='3G'])}), "
          f"LTE ({len(site_master[site_master['network_gen']=='LTE'])}), "
          f"5G ({len(site_master[site_master['network_gen']=='5G'])})")


def get_sample_site_master() -> pd.DataFrame:
    """Quick site master for testing."""
    return pd.DataFrame([
        {'site_id': 'SITE0001', 'site_name': '기지국_0001', 'region': '수도권', 
         'site_type': '기지국', 'voltage': '저압', 'contract_type': '종량'},
    ])


