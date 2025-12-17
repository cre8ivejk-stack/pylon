"""
PYLON Brand Color System
========================

Single source of truth for PYLON app color palette.
Apply colors semantically, not randomly.

Color Meanings:
- BLUE: Network backbone, stability, core platform
- GREEN: Energy savings, performance, success
- ORANGE: Risk, attention needed, warnings
- RED: Critical issues, exceptions, urgent
"""

# Core Brand Colors
PYLON_BLUE = "#1F3A5F"      # Core / Backbone / Platform identity
PYLON_GREEN = "#4C7F6D"     # Energy / Savings / Performance
PYLON_ORANGE = "#C97C2D"    # Risk / Attention / Warnings
PYLON_RED = "#8B2C2C"       # Critical / Exception / Urgent

# UI Foundation
PYLON_BG = "#F5F7FA"        # Background
PYLON_BORDER = "#D0D7E2"    # Borders and dividers
PYLON_TEXT = "#2B2E34"      # Primary text color

# Semantic Mappings
COLOR_SUCCESS = PYLON_GREEN
COLOR_WARNING = PYLON_ORANGE
COLOR_DANGER = PYLON_RED
COLOR_PRIMARY = PYLON_BLUE

# Helper Functions
def get_metric_color(value: float, threshold_warning: float, threshold_danger: float, 
                     inverse: bool = False) -> str:
    """
    Get color based on metric value and thresholds.
    
    Args:
        value: Metric value
        threshold_warning: Warning threshold
        threshold_danger: Danger threshold
        inverse: If True, higher is worse (e.g., cost, risk)
                 If False, higher is better (e.g., savings, efficiency)
    
    Returns:
        Color hex code
    """
    if inverse:
        # Higher is worse
        if value >= threshold_danger:
            return COLOR_DANGER
        elif value >= threshold_warning:
            return COLOR_WARNING
        else:
            return COLOR_SUCCESS
    else:
        # Higher is better
        if value >= threshold_danger:
            return COLOR_SUCCESS
        elif value >= threshold_warning:
            return COLOR_WARNING
        else:
            return COLOR_DANGER


def get_status_color(status: str) -> str:
    """
    Get color for action/project status.
    
    Args:
        status: Status string (TODO/DOING/DONE or similar)
    
    Returns:
        Color hex code
    """
    status_upper = status.upper()
    
    if status_upper in ["DONE", "완료", "VERIFIED", "검증완료", "SUCCESS"]:
        return COLOR_SUCCESS
    elif status_upper in ["DOING", "진행 중", "IN_FLIGHT", "진행중", "IN_PROGRESS"]:
        return COLOR_WARNING
    elif status_upper in ["TODO", "해야 할 일", "PENDING", "대기"]:
        return COLOR_PRIMARY
    elif status_upper in ["BLOCKED", "보류", "CANCELLED", "중단", "CRITICAL"]:
        return COLOR_DANGER
    else:
        return PYLON_TEXT


def get_risk_color(risk_score: float) -> str:
    """
    Get color for risk score.
    
    Args:
        risk_score: Risk score (0-1 scale)
    
    Returns:
        Color hex code
    """
    if risk_score >= 0.7:
        return COLOR_DANGER      # High risk
    elif risk_score >= 0.4:
        return COLOR_WARNING     # Medium risk
    else:
        return COLOR_SUCCESS     # Low risk


def apply_page_style() -> str:
    """
    Get CSS for consistent page styling.
    
    Returns:
        CSS string to inject via st.markdown
    """
    return f"""
    <style>
        /* PYLON Brand Colors */
        :root {{
            --pylon-blue: {PYLON_BLUE};
            --pylon-green: {PYLON_GREEN};
            --pylon-orange: {PYLON_ORANGE};
            --pylon-red: {PYLON_RED};
            --pylon-bg: {PYLON_BG};
            --pylon-border: {PYLON_BORDER};
            --pylon-text: {PYLON_TEXT};
        }}
        
        /* Page Background */
        .main {{
            background-color: {PYLON_BG};
        }}
        
        /* Headers */
        h1, h2, h3 {{
            color: {PYLON_TEXT};
        }}
        
        /* Footer styling */
        footer {{
            border-top: 2px solid {PYLON_BORDER};
            color: {PYLON_TEXT};
        }}
        
        /* Strategy banner */
        .strategy-banner {{
            border-left: 4px solid {PYLON_BLUE};
            padding: 1rem;
            margin: 1rem 0;
            background: white;
        }}
        
        .strategy-banner.inactive {{
            border-left-color: {PYLON_BORDER};
        }}
        
        /* Performance metrics */
        .metric-success {{
            color: {PYLON_GREEN};
        }}
        
        .metric-warning {{
            color: {PYLON_ORANGE};
        }}
        
        .metric-danger {{
            color: {PYLON_RED};
        }}
    </style>
    """


def create_colored_header(text: str, color: str = PYLON_BLUE, size: int = 2) -> str:
    """
    Create a colored header.
    
    Args:
        text: Header text
        color: Color hex code
        size: Header size (1-6)
    
    Returns:
        HTML string for st.markdown
    """
    return f'<h{size} style="color: {color};">{text}</h{size}>'


def create_strategy_banner(title: str, description: str, active: bool = True) -> str:
    """
    Create a strategy banner with semantic coloring.
    
    Args:
        title: Banner title
        description: Banner description
        active: Whether strategy is active (blue) or inactive (gray)
    
    Returns:
        HTML string for st.markdown
    """
    border_color = PYLON_BLUE if active else PYLON_BORDER
    
    return f"""
    <div style="
        border-left: 4px solid {border_color};
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        background: white;
        border-radius: 4px;
    ">
        <h3 style="margin: 0; color: {PYLON_TEXT};">{title}</h3>
        <p style="margin: 0.5rem 0 0 0; color: #666;">{description}</p>
    </div>
    """


def create_metric_badge(label: str, value: str, color: str = PYLON_GREEN) -> str:
    """
    Create a colored metric badge.
    
    Args:
        label: Metric label
        value: Metric value
        color: Badge color
    
    Returns:
        HTML string for st.markdown
    """
    return f"""
    <div style="
        display: inline-block;
        padding: 0.5rem 1rem;
        margin: 0.25rem;
        background: {color}15;
        border: 2px solid {color};
        border-radius: 8px;
        color: {color};
        font-weight: bold;
    ">
        <div style="font-size: 0.8rem; opacity: 0.8;">{label}</div>
        <div style="font-size: 1.5rem;">{value}</div>
    </div>
    """


def create_footer() -> str:
    """
    Create consistent footer with PYLON branding.
    
    Returns:
        HTML string for st.markdown
    """
    return f"""
    <div style="
        margin-top: 3rem;
        padding-top: 2rem;
        border-top: 2px solid {PYLON_BORDER};
        text-align: center;
        color: {PYLON_TEXT};
    ">
        <p><strong>PYLON v0.0.3 (Dev) | SKT Network ESG추진팀</strong></p>
    </div>
    """


