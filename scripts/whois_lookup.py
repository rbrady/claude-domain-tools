#!/usr/bin/env python3
"""
Whois domain lookup tool for Claude Code.
Checks domain availability via WhoAPI.
"""
import re
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import requests


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


class WhoisAPI:
    """Client for WhoAPI whois lookups."""

    API_BASE_URL = "https://api.whoapi.com/"
    TIMEOUT_SECONDS = 10

    def __init__(self, api_token=None):
        """Initialize API client.

        Args:
            api_token: WhoAPI token. If None, will try WHOAPI_TOKEN env var.
        """
        if api_token is None:
            api_token = os.environ.get("WHOAPI_TOKEN")

        self.api_token = api_token

    def lookup(self, domain):
        """Lookup domain via WhoAPI.

        Args:
            domain: Domain name to lookup

        Returns:
            dict: Result with status (available/taken/error) and details
        """
        if not self.api_token:
            return {
                "status": "error",
                "error_type": "configuration_error",
                "message": "API token not set. Set WHOAPI_TOKEN environment variable.",
                "suggested_action": "Run: export WHOAPI_TOKEN=your_token_here"
            }

        try:
            response = requests.get(
                self.API_BASE_URL,
                params={
                    "domain": domain,
                    "apikey": self.api_token
                },
                timeout=self.TIMEOUT_SECONDS
            )

            if response.status_code == 401:
                return {
                    "status": "error",
                    "error_type": "api_error",
                    "message": "API key invalid or missing.",
                    "suggested_action": "Check your WHOAPI_TOKEN environment variable."
                }

            if response.status_code == 429:
                return {
                    "status": "error",
                    "error_type": "api_error",
                    "message": "API rate limit reached.",
                    "suggested_action": "Try again later. Cached results still work!"
                }

            if response.status_code != 200:
                return {
                    "status": "error",
                    "error_type": "api_error",
                    "message": f"API returned status {response.status_code}",
                    "suggested_action": "Try again later or check WhoAPI status."
                }

            data = response.json()

            # Parse response
            if not data.get("domain_registered", True):
                return {
                    "status": "available",
                    "domain": domain
                }
            else:
                return {
                    "status": "taken",
                    "domain": domain,
                    "registrant": data.get("registrant_name", "Unknown"),
                    "expires": data.get("expiration_date", "Unknown"),
                    "registrar": data.get("registrar_name", "Unknown")
                }

        except requests.Timeout:
            return {
                "status": "error",
                "error_type": "api_error",
                "message": "API request timeout after 10 seconds.",
                "suggested_action": "Check your internet connection and try again."
            }

        except requests.RequestException as e:
            return {
                "status": "error",
                "error_type": "api_error",
                "message": f"Network error: {str(e)}",
                "suggested_action": "Check your internet connection."
            }
