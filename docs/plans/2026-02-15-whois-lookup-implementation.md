# Whois Lookup Plugin Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python script and Claude skill that enables domain availability checking via WhoAPI.

**Architecture:** Single Python script handles API calls, caching, and error handling. Two skill files guide Claude on using the tool and help users set up API access. Cache stored in `~/.cache/claude-whois/` with 24-hour TTL.

**Tech Stack:** Python 3.6+, requests library, WhoAPI REST API, JSON for data exchange.

---

## Task 1: Create Project Structure

**Files:**
- Create: `scripts/` directory
- Create: `skills/` directory
- Create: `tests/` directory

**Step 1: Create directory structure**

```bash
mkdir -p scripts skills tests
```

**Step 2: Verify structure**

Run: `ls -la`
Expected: See `scripts/`, `skills/`, `tests/` directories

**Step 3: Commit**

```bash
git add scripts/ skills/ tests/
git commit -s -m "feat: add project directory structure"
```

---

## Task 2: Setup Python Testing Infrastructure

**Files:**
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `tests/__init__.py`

**Step 1: Create requirements.txt**

```txt
requests>=2.25.0
```

**Step 2: Create requirements-dev.txt**

```txt
-r requirements.txt
pytest>=7.0.0
pytest-mock>=3.6.0
```

**Step 3: Create empty test init file**

```bash
touch tests/__init__.py
```

**Step 4: Install dependencies**

Run: `pip install -r requirements-dev.txt`
Expected: All packages install successfully

**Step 5: Verify pytest works**

Run: `pytest --version`
Expected: `pytest 7.x.x` or higher

**Step 6: Commit**

```bash
git add requirements.txt requirements-dev.txt tests/__init__.py
git commit -s -m "feat: add Python dependencies and test infrastructure"
```

---

## Task 3: Write Domain Validation Tests

**Files:**
- Create: `tests/test_whois_lookup.py`

**Step 1: Write domain validation tests**

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_whois_lookup.py::TestDomainValidation -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'whois_lookup'"

**Step 3: Create minimal whois_lookup.py**

Create: `scripts/whois_lookup.py`

```python
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
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_whois_lookup.py::TestDomainValidation -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add tests/test_whois_lookup.py scripts/whois_lookup.py
git commit -s -m "feat: add domain validation with tests"
```

---

## Task 4: Write Cache Logic Tests

**Files:**
- Modify: `tests/test_whois_lookup.py`

**Step 1: Add cache tests**

Add to `tests/test_whois_lookup.py`:

```python
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from whois_lookup import Cache


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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_whois_lookup.py::TestCache -v`
Expected: FAIL with "ImportError: cannot import name 'Cache'"

**Step 3: Implement Cache class**

Add to `scripts/whois_lookup.py`:

```python
import json
from datetime import datetime, timedelta
from pathlib import Path


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
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_whois_lookup.py::TestCache -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add tests/test_whois_lookup.py scripts/whois_lookup.py
git commit -s -m "feat: add cache logic with 24hr TTL"
```

---

## Task 5: Write API Client Tests

**Files:**
- Modify: `tests/test_whois_lookup.py`

**Step 1: Add API client tests**

Add to `tests/test_whois_lookup.py`:

```python
from whois_lookup import WhoisAPI


class TestWhoisAPI:
    def test_api_requires_token(self):
        """Test that API requires token to be set."""
        api = WhoisAPI(api_token=None)
        result = api.lookup("example.com")

        assert result["status"] == "error"
        assert result["error_type"] == "configuration_error"
        assert "API token" in result["message"]

    def test_api_lookup_success_available(self, mocker):
        """Test successful API lookup for available domain."""
        # Mock the requests.get call
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": 0,  # WhoAPI returns 0 for success
            "domain_registered": False
        }
        mocker.patch("requests.get", return_value=mock_response)

        api = WhoisAPI(api_token="test_token")
        result = api.lookup("example.com")

        assert result["status"] == "available"
        assert result["domain"] == "example.com"

    def test_api_lookup_success_taken(self, mocker):
        """Test successful API lookup for taken domain."""
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": 0,
            "domain_registered": True,
            "registrant_name": "Example Corp",
            "expiration_date": "2027-01-15",
            "registrar_name": "Example Registrar Inc"
        }
        mocker.patch("requests.get", return_value=mock_response)

        api = WhoisAPI(api_token="test_token")
        result = api.lookup("example.com")

        assert result["status"] == "taken"
        assert result["domain"] == "example.com"
        assert result["registrant"] == "Example Corp"
        assert result["expires"] == "2027-01-15"
        assert result["registrar"] == "Example Registrar Inc"

    def test_api_lookup_rate_limit(self, mocker):
        """Test handling of rate limit errors."""
        mock_response = mocker.Mock()
        mock_response.status_code = 429
        mocker.patch("requests.get", return_value=mock_response)

        api = WhoisAPI(api_token="test_token")
        result = api.lookup("example.com")

        assert result["status"] == "error"
        assert result["error_type"] == "api_error"
        assert "rate limit" in result["message"].lower()

    def test_api_lookup_unauthorized(self, mocker):
        """Test handling of unauthorized errors (bad API key)."""
        mock_response = mocker.Mock()
        mock_response.status_code = 401
        mocker.patch("requests.get", return_value=mock_response)

        api = WhoisAPI(api_token="bad_token")
        result = api.lookup("example.com")

        assert result["status"] == "error"
        assert result["error_type"] == "api_error"
        assert "API key invalid" in result["message"]

    def test_api_lookup_timeout(self, mocker):
        """Test handling of timeout errors."""
        import requests
        mocker.patch("requests.get", side_effect=requests.Timeout())

        api = WhoisAPI(api_token="test_token")
        result = api.lookup("example.com")

        assert result["status"] == "error"
        assert result["error_type"] == "api_error"
        assert "timeout" in result["message"].lower()
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_whois_lookup.py::TestWhoisAPI -v`
Expected: FAIL with "ImportError: cannot import name 'WhoisAPI'"

**Step 3: Implement WhoisAPI class**

Add to `scripts/whois_lookup.py`:

```python
import requests


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
                "message": "API request timed out after 10 seconds.",
                "suggested_action": "Check your internet connection and try again."
            }

        except requests.RequestException as e:
            return {
                "status": "error",
                "error_type": "api_error",
                "message": f"Network error: {str(e)}",
                "suggested_action": "Check your internet connection."
            }
```

Also add at top of file:

```python
import os
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_whois_lookup.py::TestWhoisAPI -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add tests/test_whois_lookup.py scripts/whois_lookup.py
git commit -s -m "feat: add WhoAPI client with error handling"
```

---

## Task 6: Write Main CLI Logic

**Files:**
- Modify: `scripts/whois_lookup.py`

**Step 1: Add main function and CLI handling**

Add to end of `scripts/whois_lookup.py`:

```python
import sys


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
```

**Step 2: Make script executable**

Run: `chmod +x scripts/whois_lookup.py`

**Step 3: Test with missing domain**

Run: `python scripts/whois_lookup.py`
Expected: JSON error about missing domain

**Step 4: Test with invalid domain**

Run: `python scripts/whois_lookup.py "invalid domain"`
Expected: JSON error about invalid format

**Step 5: Test with valid domain (will fail without API key)**

Run: `python scripts/whois_lookup.py example.com`
Expected: JSON error about missing API token

**Step 6: Commit**

```bash
git add scripts/whois_lookup.py
git commit -s -m "feat: add main CLI logic and argument handling"
```

---

## Task 7: Write whois-lookup Skill File

**Files:**
- Create: `skills/whois-lookup.md`

**Step 1: Create whois-lookup skill**

```markdown
---
name: whois-lookup
description: Check if a domain name is available or taken using WhoAPI
---

# Whois Domain Lookup

Use this skill when the user asks about domain availability or you're suggesting domain names and want to check if they're available.

## When to Use

- User asks: "Is example.com available?"
- User asks: "Check if these domains are taken"
- You're suggesting domain names and want to verify availability
- User mentions they need a domain name for a project

## How to Use

**Command:**
```bash
python scripts/whois_lookup.py <domain>
```

**Example:**
```bash
python scripts/whois_lookup.py example.com
```

## Output Format

The script returns JSON with one of three statuses:

**Available Domain:**
```json
{
  "status": "available",
  "domain": "example.com"
}
```

**Taken Domain:**
```json
{
  "status": "taken",
  "domain": "example.com",
  "registrant": "Example Corp",
  "expires": "2027-01-15",
  "registrar": "Example Registrar Inc"
}
```

**Error:**
```json
{
  "status": "error",
  "error_type": "api_error",
  "message": "API rate limit reached",
  "suggested_action": "Try again in 30 minutes"
}
```

## How to Present Results

**For available domains:**
- "Great news! example.com is available and ready to register."
- Link to registrar if helpful

**For taken domains:**
- "example.com is already registered to [registrant], registered through [registrar], and expires on [date]."
- If expiring soon, mention potential availability
- Suggest alternatives if appropriate

**For errors:**
- Present the error message and suggested action clearly
- If API token missing, direct user to whois-setup skill

## Important Notes

- Results are cached for 24 hours to conserve API quota
- The script requires WHOAPI_TOKEN environment variable to be set
- If user hasn't set up API access, guide them to use: `whois-setup` skill
- Free tier provides 10,000 requests (sufficient for most use cases)

## Troubleshooting

**"API token not set" error:**
- User needs to set up WhoAPI access
- Direct them to the whois-setup skill

**"Rate limit reached" error:**
- Cached lookups still work
- Wait 30-60 minutes before new lookups
- Consider suggesting user upgrade WhoAPI plan if frequent

**Network errors:**
- Check internet connection
- Try again in a few moments
- Verify WhoAPI service status
```

**Step 2: Verify file format**

Run: `cat skills/whois-lookup.md | head -20`
Expected: See proper YAML frontmatter and content

**Step 3: Commit**

```bash
git add skills/whois-lookup.md
git commit -s -m "feat: add whois-lookup skill for Claude"
```

---

## Task 8: Write whois-setup Skill File

**Files:**
- Create: `skills/whois-setup.md`

**Step 1: Create whois-setup skill**

```markdown
---
name: whois-setup
description: Instructions for setting up WhoAPI access for domain lookups
---

# Whois Setup Guide

This skill helps users set up WhoAPI access for domain availability checking.

## Step 1: Sign Up for WhoAPI

1. Visit: https://whoapi.com/
2. Click "Sign Up" or "Get Started"
3. Create a free account
4. **Free tier includes 10,000 API requests** (plenty for personal use!)

## Step 2: Get Your API Key

1. Log in to your WhoAPI account
2. Go to your dashboard
3. Find the "API Key" section
4. Copy your API key (keep it secure!)

## Step 3: Set Environment Variable

The whois lookup tool reads your API key from the `WHOAPI_TOKEN` environment variable.

**For Bash (Linux/Mac with bash):**
```bash
# Add to ~/.bashrc or ~/.bash_profile
export WHOAPI_TOKEN="your_api_key_here"

# Then reload:
source ~/.bashrc
```

**For Zsh (Mac default):**
```bash
# Add to ~/.zshrc
export WHOAPI_TOKEN="your_api_key_here"

# Then reload:
source ~/.zshrc
```

**For Fish:**
```bash
# Add to ~/.config/fish/config.fish
set -gx WHOAPI_TOKEN "your_api_key_here"

# Then reload:
source ~/.config/fish/config.fish
```

**Verify it's set:**
```bash
echo $WHOAPI_TOKEN
```

Should display your API key (not empty).

## Step 4: Test the Setup

Try a lookup to verify everything works:

```bash
python scripts/whois_lookup.py google.com
```

**Expected output:**
```json
{
  "status": "taken",
  "domain": "google.com",
  "registrant": "Google LLC",
  ...
}
```

If you see the JSON response, you're all set! 🎉

## Troubleshooting

**"API token not set" error:**
- Make sure you exported the variable correctly
- Restart your terminal or reload your shell config
- Check spelling: `WHOAPI_TOKEN` (all caps)

**"API key invalid" error:**
- Double-check you copied the key correctly (no extra spaces)
- Verify the key is active in your WhoAPI dashboard
- Try generating a new API key

**"requests module not found" error:**
```bash
pip install -r requirements.txt
```

**Still having issues?**
- Check WhoAPI documentation: https://whoapi.com/documentation
- Verify account status and quota at: https://whoapi.com/dashboard
- Check that Python 3.6+ is installed: `python3 --version`

## API Quota Management

**Free tier limits:**
- 10,000 requests included
- Results are cached for 24 hours (reduces API usage)
- Plan accordingly: ~400 lookups/day for 25 days

**Check your usage:**
- Log in to WhoAPI dashboard
- View remaining quota
- Upgrade if needed for higher volumes

## Security Notes

- Never commit your API key to git
- Keep `WHOAPI_TOKEN` in environment variables only
- Don't share your API key publicly
- Regenerate key if accidentally exposed
```

**Step 2: Verify file format**

Run: `cat skills/whois-setup.md | head -20`
Expected: See proper YAML frontmatter and content

**Step 3: Commit**

```bash
git add skills/whois-setup.md
git commit -s -m "feat: add whois-setup skill with API key instructions"
```

---

## Task 9: Update README with Documentation

**Files:**
- Modify: `README.md`

**Step 1: Update README**

Replace contents of `README.md`:

```markdown
# Claude Domain Tools

Domain availability checking tools for Claude Code agents.

## Overview

Enables Claude to check domain availability via WhoAPI, eliminating the need to manually verify domain suggestions. Features smart caching (24hr TTL) to conserve API quota.

## Features

- ✅ Single domain availability checking
- ✅ Smart summaries (available vs. taken with details)
- ✅ 24-hour caching to minimize API calls
- ✅ Comprehensive error handling
- ✅ Simple setup (copy files + env var)
- 🔜 Batch domain lookup (v2)

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Requires:
- Python 3.6+
- `requests` library

### 2. Get WhoAPI Access

1. Sign up at [WhoAPI](https://whoapi.com/) (free tier: 10k requests)
2. Get your API key from the dashboard
3. Set environment variable:

```bash
# Add to ~/.bashrc or ~/.zshrc
export WHOAPI_TOKEN="your_api_key_here"
```

### 3. Copy Skills to Claude

```bash
# Copy skill files to Claude's skill directory
cp skills/*.md ~/.claude/skills/
```

Or if you prefer manual installation:
- Copy `skills/whois-lookup.md` to `~/.claude/skills/`
- Copy `skills/whois-setup.md` to `~/.claude/skills/`

## Usage

### Via Claude

Just ask Claude about domains:

```
User: "Is example.com available?"
Claude: *uses whois-lookup skill* "example.com is already taken..."

User: "Suggest 5 domain names for my startup"
Claude: *suggests domains and checks availability automatically*
```

### Direct CLI Usage

```bash
# Check single domain
python scripts/whois_lookup.py example.com

# Output (JSON):
{
  "status": "taken",
  "domain": "example.com",
  "registrant": "Example Corp",
  "expires": "2027-01-15",
  "registrar": "Example Registrar Inc"
}
```

## How It Works

1. **Cache Check**: Looks for cached result in `~/.cache/claude-whois/`
2. **API Call**: If cache miss/expired, calls WhoAPI
3. **Parse & Cache**: Extracts key info, caches for 24 hours
4. **Return JSON**: Outputs structured data Claude can parse

**Cache Duration:** 24 hours per domain (domains rarely change status quickly)

## Project Structure

```
claude-domain-tools/
├── scripts/
│   └── whois_lookup.py       # Main Python script
├── skills/
│   ├── whois-lookup.md       # Claude skill for lookups
│   └── whois-setup.md        # Setup instructions
├── tests/
│   └── test_whois_lookup.py  # Unit tests
├── docs/
│   └── plans/                # Design & implementation docs
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Testing

Run the test suite:

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=scripts tests/

# Run specific test class
pytest tests/test_whois_lookup.py::TestDomainValidation -v
```

## Troubleshooting

**"API token not set" error:**
- Verify `WHOAPI_TOKEN` is exported: `echo $WHOAPI_TOKEN`
- Restart terminal after setting environment variable
- Check `.bashrc` or `.zshrc` for correct syntax

**"Rate limit reached" error:**
- Free tier: 10k requests total
- Cached lookups still work
- Wait or upgrade WhoAPI plan

**"requests module not found":**
```bash
pip install requests
```

**Skill not found by Claude:**
- Verify skills copied to `~/.claude/skills/`
- Check file permissions: `ls -la ~/.claude/skills/`
- Restart Claude Code

## API Quota Management

**Free Tier:**
- 10,000 requests included
- ~400 lookups/day for 25 days
- Caching reduces actual API calls significantly

**Check Usage:**
- Log in to [WhoAPI Dashboard](https://whoapi.com/dashboard)
- View remaining quota
- Upgrade if needed

## Roadmap

**v1.0 (Current):**
- ✅ Single domain lookup
- ✅ Cache with 24hr TTL
- ✅ Smart error handling
- ✅ Claude skill integration

**v2.0 (Planned):**
- Batch domain lookup
- Parallel API calls with rate limiting
- Summary table output
- Enhanced caching strategies

## Security

- API key stored in environment variable only
- Never commit `WHOAPI_TOKEN` to git
- Cache files contain no sensitive data
- Regenerate API key if exposed

## License

See LICENSE file for details.

## Contributing

Contributions welcome! Please:
1. Follow existing code style
2. Add tests for new features
3. Update documentation
4. Run test suite before submitting

## Support

- **WhoAPI Docs:** https://whoapi.com/documentation
- **Issues:** File issues in this repository
- **Setup Help:** Use `whois-setup` skill in Claude
```

**Step 2: Verify README renders correctly**

Run: `cat README.md | head -50`
Expected: See proper markdown formatting

**Step 3: Commit**

```bash
git add README.md
git commit -s -m "docs: update README with comprehensive documentation"
```

---

## Task 10: Manual Integration Test

**Files:**
- None (testing only)

**Step 1: Test without API token**

```bash
unset WHOAPI_TOKEN
python scripts/whois_lookup.py example.com
```

Expected output:
```json
{
  "status": "error",
  "error_type": "configuration_error",
  "message": "API token not set. Set WHOAPI_TOKEN environment variable.",
  "suggested_action": "Run: export WHOAPI_TOKEN=your_token_here"
}
```

**Step 2: Set test API token (if you have one)**

```bash
export WHOAPI_TOKEN="your_actual_token"
python scripts/whois_lookup.py google.com
```

Expected: JSON response with "taken" status

**Step 3: Test cache by running twice**

```bash
# First run (hits API)
time python scripts/whois_lookup.py google.com

# Second run (uses cache, should be faster)
time python scripts/whois_lookup.py google.com
```

Expected: Second run significantly faster (<0.1s)

**Step 4: Verify cache file created**

```bash
ls -la ~/.cache/claude-whois/
cat ~/.cache/claude-whois/google.com.json
```

Expected: See `google.com.json` with proper data

**Step 5: Test with Claude (if skills copied)**

In Claude Code:
```
User: Is google.com available?
```

Expected: Claude uses whois-lookup skill and presents results

**Step 6: Document test results**

Create quick test summary in terminal or notes.

---

## Task 11: Final Verification and Tag Release

**Files:**
- None (verification only)

**Step 1: Run full test suite**

```bash
pytest tests/ -v --cov=scripts
```

Expected: All tests pass, good coverage

**Step 2: Test CLI help scenario**

```bash
python scripts/whois_lookup.py
python scripts/whois_lookup.py "invalid domain"
python scripts/whois_lookup.py example.com
```

Expected: All produce proper JSON output

**Step 3: Verify project structure**

```bash
tree -L 2 -I '__pycache__|*.pyc'
```

Expected structure:
```
.
├── README.md
├── docs
│   └── plans
├── requirements-dev.txt
├── requirements.txt
├── scripts
│   └── whois_lookup.py
├── skills
│   ├── whois-lookup.md
│   └── whois-setup.md
└── tests
    ├── __init__.py
    └── test_whois_lookup.py
```

**Step 4: Tag v1.0 release**

```bash
git tag -a v1.0 -m "Release v1.0: Single domain whois lookup with caching"
```

**Step 5: View final commit log**

```bash
git log --oneline --graph
```

Expected: Clean commit history with logical progression

---

## Success Criteria

✅ All unit tests pass
✅ Script validates domain formats correctly
✅ Cache works with 24-hour TTL
✅ API client handles errors gracefully
✅ CLI returns proper JSON in all cases
✅ Skills integrate smoothly with Claude
✅ README provides clear setup instructions
✅ Code follows Python best practices (PEP 8)

## Future Enhancements (v2)

Once v1 is complete and tested, we can add:
- Batch domain lookup (`whois_batch.py`)
- Parallel API calls with rate limiting
- `whois-batch.md` skill
- Enhanced error recovery
- Optional output formats (table view)
