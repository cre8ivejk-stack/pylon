"""성택작업 페이지"""

import streamlit as st
from pathlib import Path
import sys

# Add parent directory to path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# 페이지 설정
st.set_page_config(
    page_title="성택작업",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 헤더
st.title("🔧 성택작업")
st.markdown("---")

# 메인 컨텐츠
st.info("📝 작업 영역입니다. 필요한 내용을 추가하세요.")

# 레이아웃 예시
col1, col2 = st.columns(2)

with col1:
    st.subheader("왼쪽 영역")
    st.write("내용을 추가하세요.")

with col2:
    st.subheader("오른쪽 영역")
    st.write("내용을 추가하세요.")

