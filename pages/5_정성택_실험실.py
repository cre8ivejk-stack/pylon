"""정성택 실험실: 한전 전기요금 시뮬레이터 화면 임베드 전용 페이지"""

from pathlib import Path
import sys

import streamlit as st
import streamlit.components.v1 as components

# 상위 디렉토리를 PYTHONPATH에 추가 (배포 호환용)
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from styles import PYLON_BLUE, apply_page_style, create_footer

# 페이지 설정
st.set_page_config(
    page_title="한전 전기요금 시뮬레이터 | PYLON",
    layout="wide",
    page_icon="⚡",
)

# PYLON 스타일 적용
st.markdown(apply_page_style(), unsafe_allow_html=True)

# 헤더
st.markdown(
    f'<h1 style="color: {PYLON_BLUE};">⚡ 한전 전기요금 시뮬레이터</h1>',
    unsafe_allow_html=True,
)
st.markdown(
    "오프라인용 HTML 시뮬레이터를 그대로 임베드한 화면입니다."
)

st.divider()

# HTML 파일 경로
html_rel_path = Path("etc/한전_전기요금_시뮬레이터_250401시행_오프라인용_v1_0.html")
html_path = (parent_dir / html_rel_path).resolve()

if not html_path.exists():
    st.error("⚠️ 전기요금 시뮬레이터 HTML 파일을 찾을 수 없습니다.")
    st.info(f"경로를 확인해주세요: `{html_path}`")
else:
    html_content = html_path.read_text(encoding="utf-8")

    # Streamlit 안에 HTML 전체를 임베드
    components.html(
        html_content,
        height=900,          # 필요 시 조정 가능
        scrolling=True,
    )

st.divider()

# Footer
st.markdown(create_footer(), unsafe_allow_html=True)
