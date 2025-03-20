"""
Configuration for the Admin Panel module.
"""

import os
from typing import Optional

# Feature flag for the admin panel
ADMIN_PANEL_ENABLED = os.getenv('ADMIN_PANEL_ENABLED', 'true').lower() == 'true'

def is_admin_panel_enabled() -> bool:
    """Check if the admin panel module is enabled."""
    return ADMIN_PANEL_ENABLED

def get_admin_panel_url() -> str:
    """Get the URL for the admin panel WebApp."""
    base_url = os.getenv('BASE_WEBAPP_URL', '')
    return f"{base_url}/admin-panel.html" 