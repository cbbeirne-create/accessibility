"""Compatibility entrypoint.

The application was previously implemented as a monolithic server.py.  Keep this
module only so older process definitions importing ``backend.server:app`` do not
silently boot the obsolete insecure implementation.
"""
from backend.main import app

__all__ = ['app']
