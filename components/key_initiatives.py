"""4대 중점 추진 과제 위젯

전략문서에 명시된 4대 중점 과제 로드맵을 표시합니다.
"""

import streamlit as st
from styles import PYLON_BLUE, PYLON_GREEN, PYLON_BORDER


def render_key_initiatives():
    """4대 중점 추진 과제 타임라인 렌더링
    
    - PYLON (대시보드 & 에너지 에이전트)
    - 시험성적서 Modernization
    - 외기 냉방 도입 (Dual)
    - 필름형 태양광
    """
    
    st.markdown("## 🚀 4대 중점 추진 과제 & Timeline")
    
    st.info("💡 2026~2028 기간 동안 집중 추진되는 핵심 과제입니다.")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # PYLON: Active strategy with VERY PROMINENT brand color
        st.markdown(f"""
        <div style="border: 5px solid {PYLON_BLUE}; 
                    border-radius: 12px; 
                    padding: 1.25rem; 
                    background: linear-gradient(to bottom, #ffffff 0%, {PYLON_BLUE}10 100%);
                    min-height: 220px; 
                    box-shadow: 0 8px 20px rgba(31, 58, 95, 0.35);
                    position: relative;
                    transform: scale(1.02);">
            <div style="position: absolute; top: -12px; right: 15px; 
                        background: {PYLON_BLUE}; color: white; 
                        padding: 4px 12px; border-radius: 15px; 
                        font-size: 0.7rem; font-weight: bold; 
                        box-shadow: 0 2px 6px rgba(31, 58, 95, 0.4);">
                ACTIVE
            </div>
            <h4 style="color: {PYLON_BLUE}; margin-top: 0; font-size: 1.2rem; font-weight: 800;">
                ⚡ PYLON
            </h4>
            <p style="font-size: 0.85rem; color: #333; line-height: 1.5; font-weight: 500;">
                <strong style="color: {PYLON_BLUE};">대시보드 & 에너지 에이전트</strong><br><br>
                📍 단계: <span style="background: {PYLON_BLUE}; color: white; padding: 4px 10px; 
                               border-radius: 5px; font-weight: bold;">확산</span><br>
                📅 기간: 2026.01~2028.12<br><br>
                • 가시성 확보<br>
                • 성과 추적<br>
                • 리스크 모니터링<br>
                • AI 기반 최적화
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Energy savings project: PROMINENT GREEN for success/savings
        st.markdown(f"""
        <div style="border: 3px solid {PYLON_GREEN}; 
                    border-radius: 10px; 
                    padding: 1rem; 
                    background: linear-gradient(to bottom, #ffffff 0%, {PYLON_GREEN}08 100%);
                    min-height: 220px;
                    box-shadow: 0 4px 12px rgba(76, 127, 109, 0.25);">
            <h4 style="color: {PYLON_GREEN}; margin-top: 0; font-weight: 700;">
                📋 시험성적서 Modernization
            </h4>
            <p style="font-size: 0.85rem; color: #555; line-height: 1.5;">
                <br>
                📍 단계: <span style="background: {PYLON_GREEN}; color: white; padding: 3px 10px; 
                               border-radius: 5px; font-weight: bold;">PoC</span><br>
                📅 기간: 2026.07~2027.06<br><br>
                • 디지털 전환<br>
                • 자동화 검증<br>
                • 데이터 정합성
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # Energy savings project: PROMINENT GREEN
        st.markdown(f"""
        <div style="border: 3px solid {PYLON_GREEN}; 
                    border-radius: 10px; 
                    padding: 1rem; 
                    background: linear-gradient(to bottom, #ffffff 0%, {PYLON_GREEN}08 100%);
                    min-height: 220px;
                    box-shadow: 0 4px 12px rgba(76, 127, 109, 0.25);">
            <h4 style="color: {PYLON_GREEN}; margin-top: 0; font-weight: 700;">
                ❄️ 외기 냉방 도입
            </h4>
            <p style="font-size: 0.85rem; color: #555; line-height: 1.5;">
                <strong>(Dual System)</strong><br><br>
                📍 단계: <span style="background: {PYLON_GREEN}; color: white; padding: 3px 10px; 
                               border-radius: 5px; font-weight: bold;">확산</span><br>
                📅 기간: 2026.01~2028.12<br><br>
                • 외기 활용 냉방<br>
                • 에너지 절감<br>
                • 단계적 확대
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        # Energy savings project: PROMINENT GREEN
        st.markdown(f"""
        <div style="border: 3px solid {PYLON_GREEN}; 
                    border-radius: 10px; 
                    padding: 1rem; 
                    background: linear-gradient(to bottom, #ffffff 0%, {PYLON_GREEN}08 100%);
                    min-height: 220px;
                    box-shadow: 0 4px 12px rgba(76, 127, 109, 0.25);">
            <h4 style="color: {PYLON_GREEN}; margin-top: 0; font-weight: 700;">
                ☀️ 필름형 태양광
            </h4>
            <p style="font-size: 0.85rem; color: #555; line-height: 1.5;">
                <br>
                📍 단계: <span style="background: {PYLON_GREEN}; color: white; padding: 3px 10px; 
                               border-radius: 5px; font-weight: bold;">검토</span><br>
                📅 기간: 2026.01~2027.06<br><br>
                • 신재생 에너지<br>
                • 필름형 패널<br>
                • 설치 용이성<br>
                • 비용 절감
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")

