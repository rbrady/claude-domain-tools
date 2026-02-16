import pytest
import sys
import os

# Add scripts directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from whois_lookup import validate_domain


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
