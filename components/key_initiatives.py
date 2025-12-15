"""4대 중점 추진 과제 위젯

전략문서에 명시된 4대 중점 과제 로드맵을 표시합니다.
"""

import streamlit as st


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
        st.markdown("""
        <div style="border: 2px solid #667eea; border-radius: 8px; padding: 1rem; 
                    background: white; min-height: 220px;">
            <h4 style="color: #667eea; margin-top: 0;">
                ⚡ PYLON
            </h4>
            <p style="font-size: 0.85rem; color: #555; line-height: 1.5;">
                <strong>대시보드 & 에너지 에이전트</strong><br><br>
                📍 단계: <span style="background: #E8EAF6; padding: 2px 8px; 
                               border-radius: 4px; font-weight: bold;">확산</span><br>
                📅 기간: 2026.01~2028.12<br><br>
                • 가시성 확보<br>
                • 성과 추적<br>
                • 리스크 모니터링<br>
                • AI 기반 최적화
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="border: 2px solid #26A69A; border-radius: 8px; padding: 1rem; 
                    background: white; min-height: 220px;">
            <h4 style="color: #26A69A; margin-top: 0;">
                📋 시험성적서 Modernization
            </h4>
            <p style="font-size: 0.85rem; color: #555; line-height: 1.5;">
                <br>
                📍 단계: <span style="background: #E0F2F1; padding: 2px 8px; 
                               border-radius: 4px; font-weight: bold;">PoC</span><br>
                📅 기간: 2026.07~2027.06<br><br>
                • 디지털 전환<br>
                • 자동화 검증<br>
                • 데이터 정합성
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="border: 2px solid #FFA726; border-radius: 8px; padding: 1rem; 
                    background: white; min-height: 220px;">
            <h4 style="color: #FFA726; margin-top: 0;">
                ❄️ 외기 냉방 도입
            </h4>
            <p style="font-size: 0.85rem; color: #555; line-height: 1.5;">
                <strong>(Dual System)</strong><br><br>
                📍 단계: <span style="background: #FFF3E0; padding: 2px 8px; 
                               border-radius: 4px; font-weight: bold;">확산</span><br>
                📅 기간: 2026.01~2028.12<br><br>
                • 외기 활용 냉방<br>
                • 에너지 절감<br>
                • 단계적 확대
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div style="border: 2px solid #66BB6A; border-radius: 8px; padding: 1rem; 
                    background: white; min-height: 220px;">
            <h4 style="color: #66BB6A; margin-top: 0;">
                ☀️ 필름형 태양광
            </h4>
            <p style="font-size: 0.85rem; color: #555; line-height: 1.5;">
                <br>
                📍 단계: <span style="background: #E8F5E9; padding: 2px 8px; 
                               border-radius: 4px; font-weight: bold;">검토</span><br>
                📅 기간: 2026.01~2027.06<br><br>
                • 신재생 에너지<br>
                • 필름형 패널<br>
                • 설치 용이성<br>
                • 비용 절감
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")

