"""PYLON Styles Module"""

from .pylon_theme import (
    # Core Colors
    PYLON_BLUE,
    PYLON_GREEN,
    PYLON_ORANGE,
    PYLON_RED,
    PYLON_BG,
    PYLON_BORDER,
    PYLON_TEXT,
    
    # Semantic Colors
    COLOR_SUCCESS,
    COLOR_WARNING,
    COLOR_DANGER,
    COLOR_PRIMARY,
    
    # Helper Functions
    get_metric_color,
    get_status_color,
    get_risk_color,
    apply_page_style,
    create_colored_header,
    create_strategy_banner,
    create_metric_badge,
    create_footer,
)

__all__ = [
    # Colors
    "PYLON_BLUE",
    "PYLON_GREEN",
    "PYLON_ORANGE",
    "PYLON_RED",
    "PYLON_BG",
    "PYLON_BORDER",
    "PYLON_TEXT",
    "COLOR_SUCCESS",
    "COLOR_WARNING",
    "COLOR_DANGER",
    "COLOR_PRIMARY",
    # Functions
    "get_metric_color",
    "get_status_color",
    "get_risk_color",
    "apply_page_style",
    "create_colored_header",
    "create_strategy_banner",
    "create_metric_badge",
    "create_footer",
]


