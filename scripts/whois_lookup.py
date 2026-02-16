#!/usr/bin/env python3
"""
Whois domain lookup tool for Claude Code.
Checks domain availability via WhoAPI.
"""
import re


def validate_domain(domain):
    """Validate domain name format.

    Args:
        domain: Domain name string to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not domain or domain is None:
        return False

    # Basic domain regex: alphanumeric, hyphens, dots, must have TLD
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain))
