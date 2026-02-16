#!/usr/bin/env python3
"""
Whois domain lookup tool for Claude Code.
Checks domain availability via WhoAPI.
"""
import re
import json
import os
import sys
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
                    "r": "whois",
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

            # Check API status
            if data.get("status") != 0:
                return {
                    "status": "error",
                    "error_type": "api_error",
                    "message": data.get("status_desc", "API error"),
                    "suggested_action": "Check API status or try again later."
                }

            # Parse response
            if not data.get("registered", True):
                return {
                    "status": "available",
                    "domain": domain
                }
            else:
                # Extract registrant organization from contacts
                registrant = "Unknown"
                contacts = data.get("contacts", [])
                for contact in contacts:
                    if contact.get("type") == "registrant":
                        registrant = contact.get("organization", contact.get("name", "Unknown"))
                        break

                # Format expiration date (extract just the date part)
                expires = data.get("date_expires", "Unknown")
                if expires != "Unknown" and " " in expires:
                    expires = expires.split(" ")[0]

                return {
                    "status": "taken",
                    "domain": domain,
                    "registrant": registrant,
                    "expires": expires,
                    "registrar": data.get("registrar", "Unknown")
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


def main():
    """Main CLI entry point."""
    # Check Python version
    if sys.version_info < (3, 6):
        error = {
            "status": "error",
            "error_type": "system_error",
            "message": "Python 3.6 or higher required",
            "suggested_action": "Upgrade Python: python3 --version"
        }
        print(json.dumps(error, indent=2))
        sys.exit(1)

    # Parse arguments
    if len(sys.argv) != 2:
        error = {
            "status": "error",
            "error_type": "validation_error",
            "message": "No domain provided",
            "suggested_action": "Usage: python whois_lookup.py <domain>"
        }
        print(json.dumps(error, indent=2))
        sys.exit(1)

    domain = sys.argv[1]

    # Validate domain
    if not validate_domain(domain):
        error = {
            "status": "error",
            "error_type": "validation_error",
            "message": "Invalid domain format",
            "suggested_action": "Domain must be like: example.com or sub.example.com"
        }
        print(json.dumps(error, indent=2))
        sys.exit(1)

    # Check cache
    cache = Cache()
    cached_result = cache.get(domain)

    if cached_result:
        print(json.dumps(cached_result, indent=2))
        sys.exit(0)

    # Call API
    api = WhoisAPI()
    result = api.lookup(domain)

    # Cache successful results
    if result["status"] in ["available", "taken"]:
        result["checked_at"] = datetime.utcnow().isoformat() + "Z"
        cache.set(domain, result)

    # Output result
    print(json.dumps(result, indent=2))

    # Exit with appropriate code
    if result["status"] == "error":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
