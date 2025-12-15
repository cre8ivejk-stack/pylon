"""Configuration loader for PYLON platform."""

import yaml
from pathlib import Path
from typing import Dict, Any


def load_governance_config(config_path: Path = None) -> Dict[str, Any]:
    """
    Load governance configuration from YAML file.
    
    Args:
        config_path: Path to config file. If None, uses default config/governance.yaml
    
    Returns:
        Dictionary with governance configuration
    """
    if config_path is None:
        config_path = Path("config") / "governance.yaml"
    
    # Default values
    defaults = {
        'official_version': 'v1.0',
        'plan_locked': False,
        'exception_applied': 0
    }
    
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                # Merge with defaults
                return {**defaults, **config}
        else:
            return defaults
    except Exception as e:
        print(f"Warning: Could not load governance config: {e}")
        return defaults




