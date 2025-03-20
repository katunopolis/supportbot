"""
Admin Panel Module for Support Bot

This module provides a web-based admin panel for managing support requests.
It can be enabled/disabled without affecting the core functionality.
"""

from .handlers import register_admin_panel_handlers
from .config import is_admin_panel_enabled

__all__ = ['register_admin_panel_handlers', 'is_admin_panel_enabled'] 