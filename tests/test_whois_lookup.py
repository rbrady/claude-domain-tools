import pytest
import sys
import os

# Add scripts directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from whois_lookup import validate_domain, Cache
import json
from datetime import datetime, timedelta
from pathlib import Path


class TestDomainValidation:
    def test_valid_domain(self):
        """Test that valid domain names pass validation."""
        assert validate_domain("example.com") == True
        assert validate_domain("sub.example.com") == True
        assert validate_domain("example.co.uk") == True
        assert validate_domain("test-domain.dev") == True

    def test_invalid_domain_empty(self):
        """Test that empty domain fails validation."""
        assert validate_domain("") == False
        assert validate_domain(None) == False

    def test_invalid_domain_format(self):
        """Test that malformed domains fail validation."""
        assert validate_domain("invalid domain") == False
        assert validate_domain("no-tld") == False
        assert validate_domain(".startswith-dot.com") == False
        assert validate_domain("endswith-dot.com.") == False


class TestCache:
    def test_cache_miss(self, tmp_path):
        """Test cache returns None when no cached data exists."""
        cache = Cache(cache_dir=str(tmp_path))
        result = cache.get("example.com")
        assert result is None

    def test_cache_hit_fresh(self, tmp_path):
        """Test cache returns data when fresh (<24hrs)."""
        cache = Cache(cache_dir=str(tmp_path))

        # Create fresh cache entry
        data = {
            "domain": "example.com",
            "checked_at": datetime.utcnow().isoformat() + "Z",
            "status": "taken"
        }
        cache.set("example.com", data)

        # Retrieve it
        result = cache.get("example.com")
        assert result is not None
        assert result["domain"] == "example.com"
        assert result["status"] == "taken"

    def test_cache_expired(self, tmp_path):
        """Test cache returns None when data is expired (>24hrs)."""
        cache = Cache(cache_dir=str(tmp_path))

        # Create expired cache entry (25 hours ago)
        old_time = datetime.utcnow() - timedelta(hours=25)
        data = {
            "domain": "example.com",
            "checked_at": old_time.isoformat() + "Z",
            "status": "taken"
        }
        cache.set("example.com", data)

        # Should return None because expired
        result = cache.get("example.com")
        assert result is None

    def test_cache_creates_directory(self, tmp_path):
        """Test cache creates directory if it doesn't exist."""
        cache_path = tmp_path / "subdir" / "cache"
        cache = Cache(cache_dir=str(cache_path))

        data = {"domain": "test.com", "checked_at": datetime.utcnow().isoformat() + "Z"}
        cache.set("test.com", data)

        assert cache_path.exists()
