"""3대 전략방향 섹션 컴포넌트

전략문서의 3대 핵심 방향성을 시각화합니다.
"""

import streamlit as st
from styles import PYLON_BLUE, PYLON_GREEN, PYLON_BORDER


def render_strategy_overview():
    """3대 전략방향 카드 렌더링
    
    전략문서의:
    - #1 가시성 & 성과관리
    - #2 에너지 소모 절감
    - #3 비용 최적화
    """
    
    st.markdown("## 🎯 센터 에너지 관리체계 강화방안 (2026~2028)")
    
    # PYLON banner with PROMINENT brand color
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {PYLON_BLUE} 0%, #2d5986 100%); 
                padding: 1.5rem 2rem; 
                border-radius: 12px; 
                color: white; 
                margin-bottom: 2rem;
                box-shadow: 0 6px 20px rgba(31, 58, 95, 0.4);
                border: 3px solid {PYLON_BLUE};">
        <p style="margin: 0; font-size: 1.1rem; font-weight: 600; line-height: 1.6;">
        ⚡ <strong style="font-size: 1.3rem;">PYLON</strong>은 전략 실행의 운영 백본으로, 
        모니터링(내부/외부 비교) → 성과 & 리스크 관리를 담당합니다.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Active strategy: PYLON handles this direction - VERY PROMINENT
        st.markdown(f"""
        <div style="border: 5px solid {PYLON_BLUE}; 
                    border-radius: 15px; 
                    padding: 1.5rem; 
                    background: linear-gradient(to bottom, #ffffff 0%, {PYLON_BLUE}08 100%);
                    height: 280px; 
                    box-shadow: 0 8px 24px rgba(31, 58, 95, 0.35);
                    position: relative;">
            <div style="position: absolute; top: -15px; right: 20px; 
                        background: {PYLON_BLUE}; color: white; 
                        padding: 5px 15px; border-radius: 20px; 
                        font-size: 0.8rem; font-weight: bold; 
                        box-shadow: 0 2px 8px rgba(31, 58, 95, 0.4);">
                ⚡ ACTIVE
            </div>
            <h3 style="color: {PYLON_BLUE}; margin-top: 0; font-size: 1.3rem; font-weight: 800;">
                📊 #1 가시성 & 성과관리
            </h3>
            <p style="color: #333; font-size: 0.9rem; line-height: 1.6; font-weight: 500;">
                <strong style="color: {PYLON_BLUE};">AT/DT 기반 운영 최적화 체계 구축</strong><br>
                <span style="background: {PYLON_BLUE}; color: white; padding: 4px 10px; border-radius: 5px; 
                      font-size: 0.75rem; font-weight: bold; display: inline-block; margin: 8px 0;">
                    ⚡ PYLON 담당
                </span>
                <br><br>
                • 전사 에너지 가시성 확보<br>
                • 계획 대비 실적 추적<br>
                • 청구서 vs 실사용량 비교<br>
                • 과제 성과 추적 및 검증<br>
                • 월 1회 전기료 WG 운영
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Inactive strategy: informational only
        st.markdown(f"""
        <div style="border: 2px solid {PYLON_BORDER}; border-radius: 10px; padding: 1rem; 
                    background: white; height: 280px;">
            <h3 style="color: #666; margin-top: 0;">⚡ #2 에너지 소모 절감</h3>
            <p style="color: #555; font-size: 0.9rem; line-height: 1.6;">
                <strong>Access·설비·Core/전송 과제 추진</strong><br><br>
                <span style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px; 
                      font-size: 0.75rem; margin-right: 4px;">억세스</span>
                LTE Mod., 3G Fade-Out, SA<br>
                <span style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px; 
                      font-size: 0.75rem; margin-right: 4px;">설비</span>
                외기냉방, 필름형태양광, 온도상향<br>
                <span style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px; 
                      font-size: 0.75rem; margin-right: 4px;">Core/전송</span>
                Zero Power化, Server PS
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # Inactive strategy: informational only
        st.markdown(f"""
        <div style="border: 2px solid {PYLON_BORDER}; border-radius: 10px; padding: 1rem; 
                    background: white; height: 280px;">
            <h3 style="color: #666; margin-top: 0;">💰 #3 비용 최적화</h3>
            <p style="color: #555; font-size: 0.9rem; line-height: 1.6;">
                <strong>정액·종량 관점 + RAPA/도전</strong><br><br>
                • 계약전력 최적화 (정액)<br>
                • 요금제 변경 추천 (종량)<br>
                • RAPA 적용 확대<br>
                • Power Theft 방지 (도전)<br>
                • Billing Consistency 리스크 관리
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")

