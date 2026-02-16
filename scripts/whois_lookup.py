#!/usr/bin/env python3
"""
Whois domain lookup tool for Claude Code.
Checks domain availability via WhoAPI.
"""
import re
import json
from datetime import datetime, timedelta
from pathlib import Path


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


class Cache:
    """Simple file-based cache for whois lookups."""

    CACHE_TTL_HOURS = 24

    def __init__(self, cache_dir=None):
        """Initialize cache.

        Args:
            cache_dir: Directory to store cache files. Defaults to ~/.cache/claude-whois/
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "claude-whois"
        else:
            cache_dir = Path(cache_dir)

        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, domain):
        """Get cache file path for domain."""
        # Use domain as filename (safe since we validate domain format)
        return self.cache_dir / f"{domain}.json"

    def get(self, domain):
        """Get cached data for domain if not expired.

        Args:
            domain: Domain name to lookup

        Returns:
            dict: Cached data or None if cache miss/expired
        """
        cache_path = self._get_cache_path(domain)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)

            # Check if expired
            checked_at = datetime.fromisoformat(data["checked_at"].replace("Z", "+00:00"))
            age = datetime.utcnow() - checked_at.replace(tzinfo=None)

            if age > timedelta(hours=self.CACHE_TTL_HOURS):
                return None

            return data
        except (json.JSONDecodeError, KeyError, ValueError):
            # Corrupt cache file
            cache_path.unlink(missing_ok=True)
            return None

    def set(self, domain, data):
        """Store data in cache.

        Args:
            domain: Domain name
            data: Dictionary to cache
        """
        cache_path = self._get_cache_path(domain)

        try:
            with open(cache_path, 'w') as f:
                json.dump(data, f, indent=2)
        except (IOError, OSError):
            # Fail gracefully if can't write cache
            pass
