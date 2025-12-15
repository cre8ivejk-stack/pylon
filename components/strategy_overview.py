"""3대 전략방향 섹션 컴포넌트

전략문서의 3대 핵심 방향성을 시각화합니다.
"""

import streamlit as st


def render_strategy_overview():
    """3대 전략방향 카드 렌더링
    
    전략문서의:
    - #1 가시성 & 성과관리
    - #2 에너지 소모 절감
    - #3 비용 최적화
    """
    
    st.markdown("## 🎯 센터 에너지 관리체계 강화방안 (2026~2028)")
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 1rem; border-radius: 0.5rem; color: white; margin-bottom: 1rem;">
        <p style="margin: 0; font-size: 0.9rem;">
        ⚡ <strong>PYLON</strong>은 전략 실행의 운영 백본으로, 
        모니터링(내부/외부 비교) → 성과 & 리스크 관리를 담당합니다.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="border: 2px solid #4CAF50; border-radius: 10px; padding: 1rem; 
                    background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%); height: 280px;">
            <h3 style="color: #2E7D32; margin-top: 0;">📊 #1 가시성 & 성과관리</h3>
            <p style="color: #1B5E20; font-size: 0.9rem; line-height: 1.6;">
                <strong>AT/DT 기반 운영 최적화 체계 구축</strong><br><br>
                • 전사 에너지 가시성 확보<br>
                • 계획 대비 실적 추적<br>
                • 청구서 vs 실사용량 비교<br>
                • 과제 성과 추적 및 검증<br>
                • 월 1회 전기료 WG 운영
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="border: 2px solid #FF9800; border-radius: 10px; padding: 1rem; 
                    background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%); height: 280px;">
            <h3 style="color: #E65100; margin-top: 0;">⚡ #2 에너지 소모 절감</h3>
            <p style="color: #BF360C; font-size: 0.9rem; line-height: 1.6;">
                <strong>Access·설비·Core/전송 과제 추진</strong><br><br>
                <span style="background: #FFF8E1; padding: 2px 6px; border-radius: 3px; 
                      font-size: 0.75rem; margin-right: 4px;">억세스</span>
                LTE Mod., 3G Fade-Out, SA<br>
                <span style="background: #FFF8E1; padding: 2px 6px; border-radius: 3px; 
                      font-size: 0.75rem; margin-right: 4px;">설비</span>
                외기냉방, 필름형태양광, 온도상향<br>
                <span style="background: #FFF8E1; padding: 2px 6px; border-radius: 3px; 
                      font-size: 0.75rem; margin-right: 4px;">Core/전송</span>
                Zero Power化, Server PS
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="border: 2px solid #2196F3; border-radius: 10px; padding: 1rem; 
                    background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%); height: 280px;">
            <h3 style="color: #0D47A1; margin-top: 0;">💰 #3 비용 최적화</h3>
            <p style="color: #01579B; font-size: 0.9rem; line-height: 1.6;">
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

