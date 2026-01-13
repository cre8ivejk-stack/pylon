"""
PYLON 테스트 앱 - Playground 배포 테스트용
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="PYLON - 에너지 운영 플랫폼",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Header
st.title("⚡ PYLON - 에너지 관리 플랫폼")
st.markdown("**SKT Network센터 에너지 최적화 시스템**")
st.divider()

# System info
st.header("🔧 시스템 정보")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Python 버전", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
with col2:
    st.metric("Streamlit 버전", st.__version__)
with col3:
    st.metric("Pandas 버전", pd.__version__)

st.divider()

# Test data loading
st.header("📂 데이터 로딩 테스트")

data_dir = Path("data")
st.write(f"데이터 디렉토리: `{data_dir.absolute()}`")

if data_dir.exists():
    st.success("✅ 데이터 디렉토리 존재")
    
    # List files
    files = list(data_dir.glob("*.parquet"))
    st.write(f"발견된 Parquet 파일: {len(files)}개")
    
    for file in files:
        file_size_mb = file.stat().st_size / (1024 * 1024)
        st.write(f"- `{file.name}` ({file_size_mb:.2f} MB)")
    
    # Try loading one file
    if files:
        st.subheader("샘플 데이터 로딩 테스트")
        try:
            sample_file = files[0]
            df = pd.read_parquet(sample_file)
            st.success(f"✅ {sample_file.name} 로드 성공!")
            st.write(f"행 수: {len(df):,}, 열 수: {len(df.columns)}")
            st.dataframe(df.head(3), use_container_width=True)
        except Exception as e:
            st.error(f"❌ 파일 로드 실패: {str(e)}")
else:
    st.error("❌ 데이터 디렉토리가 존재하지 않습니다")

st.divider()

# Module import test
st.header("📦 모듈 Import 테스트")

modules_to_test = [
    ("src.data_access", "DataAccessLayer"),
    ("src.actions", "ActionManager"),
    ("src.models", "GovernanceBadge"),
    ("components.global_controls", "render_governance_badges"),
    ("styles", "PYLON_BLUE"),
]

import_results = []
for module_name, item_name in modules_to_test:
    try:
        module = __import__(module_name, fromlist=[item_name])
        getattr(module, item_name)
        import_results.append({"모듈": f"{module_name}.{item_name}", "상태": "✅ 성공"})
    except Exception as e:
        import_results.append({"모듈": f"{module_name}.{item_name}", "상태": f"❌ 실패: {str(e)}"})

import_df = pd.DataFrame(import_results)
st.dataframe(import_df, use_container_width=True)

st.divider()

# Quick navigation
st.header("🚀 페이지 메뉴")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.page_link("pages/1_에너지_인텔리전스.py", label="📊 에너지 인텔리전스", icon="⚡")
with col2:
    st.page_link("pages/2_성과_리스크_관리.py", label="📈 성과 & 리스크", icon="⚠️")
with col3:
    st.page_link("pages/3_최적화_실행.py", label="🎯 최적화 & 실행", icon="🎯")
with col4:
    st.page_link("pages/4_검증_실증.py", label="🔬 검증 & 실증", icon="✅")

st.divider()

# Status
st.success("🎉 **테스트 앱이 정상적으로 실행되고 있습니다!**")
st.info("위 테스트 결과를 확인하고, 문제가 없으면 전체 앱을 활성화하세요.")

# Footer
st.markdown("---")
st.caption("PYLON v0.0.3 - Test Mode | Powered by Streamlit")
