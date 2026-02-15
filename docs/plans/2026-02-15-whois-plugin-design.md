# Whois Lookup Plugin Design

**Date:** 2026-02-15
**Status:** Approved
**Version:** 1.0 (Single domain lookup)

## Overview

A Claude Code skill and Python script that enables Claude to check domain availability via WhoAPI. Solves the problem of Claude suggesting domain names without knowing if they're available, forcing users to manually check each one.

## Problem Statement

When users ask Claude for domain name suggestions, Claude currently cannot verify availability. Users must manually check each suggestion, often finding that most are already taken. This creates friction and wastes time.

## Goals

**v1 (This Design):**
- Enable Claude to check if a single domain is available
- Provide smart summaries (available vs. taken with details)
- Minimize setup friction for users
- Cache results to conserve API quota

**v2 (Future):**
- Batch lookup for multiple domains at once
- More efficient for brainstorming sessions

## Architecture

### Project Structure
```
claude-domain-tools/
├── scripts/
│   └── whois_lookup.py       # Python script for API calls
├── skills/
│   ├── whois-lookup.md       # Skill for single domain lookup
│   └── whois-setup.md        # Instructions for getting API key
├── docs/
│   └── plans/                # Design docs
└── README.md                 # Installation and usage guide
```

### Installation Flow
1. User clones repo or copies files
2. User signs up at WhoAPI (10k free requests)
3. User retrieves API key from WhoAPI dashboard
4. User sets `WHOAPI_TOKEN` environment variable
5. User copies skill files to `~/.claude/skills/`
6. Claude can now perform whois lookups

### Runtime Flow
1. User asks Claude about domain availability
2. Claude reads `whois-lookup.md` skill
3. Claude executes: `python scripts/whois_lookup.py example.com`
4. Script checks cache (`~/.cache/claude-whois/`)
5. If cache miss or expired (>24hrs), script calls WhoAPI
6. Script returns formatted JSON to stdout
7. Claude parses and presents results conversationally

### Key Design Decisions
- **Cache location:** `~/.cache/claude-whois/` (follows XDG standards)
- **Cache duration:** 24 hours per domain (domains rarely change status quickly)
- **Output format:** JSON for reliable parsing by Claude
- **API token:** Environment variable (secure, no credential files)
- **Language:** Python 3.6+ (universal, good JSON support)

## Components

### whois_lookup.py
Main Python script (~150-200 lines).

**Responsibilities:**
- Accept domain name as command line argument
- Check cache for recent results
- Call WhoAPI if cache miss or expired
- Parse API response into smart summary
- Cache results for 24 hours
- Return formatted JSON to stdout

**Output Formats:**
```json
// Available domain
{
  "status": "available",
  "domain": "example.com"
}

// Taken domain
{
  "status": "taken",
  "domain": "example.com",
  "registrant": "Example Corp",
  "expires": "2027-01-15",
  "registrar": "Example Registrar Inc"
}

// Error
{
  "status": "error",
  "error_type": "api_error",
  "message": "API rate limit reached",
  "suggested_action": "Try again in 30 minutes"
}
```

**Dependencies:**
- Python 3.6+
- `requests` library (only external dependency)

### whois-lookup.md
Claude skill file that provides instructions.

**Contents:**
- When to use the tool (domain availability questions)
- Command syntax: `python scripts/whois_lookup.py <domain>`
- How to interpret JSON output
- How to present results conversationally

### whois-setup.md
Setup instructions for users.

**Contents:**
- Link to WhoAPI signup page
- How to retrieve API key from dashboard
- How to set `WHOAPI_TOKEN` for different shells (bash, zsh, fish)
- Troubleshooting common setup issues

## Data Flow

### Successful Lookup Flow
```
1. User → Claude: "Is example.com available?"
2. Claude reads: whois-lookup.md skill
3. Claude executes: python scripts/whois_lookup.py example.com
4. Script checks cache: ~/.cache/claude-whois/example.com.json
   ├─ If exists and <24hrs old → return cached data
   └─ If missing/expired → continue to API call
5. Script → WhoAPI: GET https://api.whoapi.com/?domain=example.com&apikey=TOKEN
6. WhoAPI → Script: JSON response with whois data
7. Script parses:
   ├─ Extract availability status
   └─ If taken: extract registrant, expiration, registrar
8. Script writes cache: ~/.cache/claude-whois/example.com.json
9. Script → stdout: formatted JSON
10. Claude → User: "example.com is available!" or detailed status
```

### Cache File Format
```json
{
  "domain": "example.com",
  "checked_at": "2026-02-15T10:30:00Z",
  "status": "taken",
  "registrant": "Example Corp",
  "expires": "2027-01-15",
  "registrar": "Example Registrar Inc"
}
```

## Error Handling

### API Errors
- **401 Unauthorized:** "API key invalid or missing. Run whois-setup skill for instructions."
- **429 Rate Limited:** "API rate limit reached. Try again in X minutes. (Cached results still work!)"
- **500 Server Error:** "WhoAPI service error. Try again later."
- **Timeout (>10s):** "API request timed out. Check your connection."

### Input Validation
- **Invalid format:** "Invalid domain format. Must be like: example.com or sub.example.com"
- **Empty input:** "No domain provided. Usage: python whois_lookup.py <domain>"
- **Unsupported TLD:** Relay API error message

### File System Errors
- **Cache dir creation fails:** Log warning, degrade gracefully (no caching)
- **Cache file corrupt:** Delete corrupt file, fetch fresh data
- **Permission denied:** Warn user, continue without caching

### Dependency Errors
- **Python < 3.6:** Check at startup, print version requirement
- **requests missing:** Print: `pip install requests`

### Error Output Format
All errors return JSON for consistent parsing:
```json
{
  "status": "error",
  "error_type": "api_error|validation_error|system_error",
  "message": "Human-readable description",
  "suggested_action": "What the user should do"
}
```

### Logging
- Optional `--debug` flag for troubleshooting
- Debug logs: `~/.cache/claude-whois/debug.log`

## Testing

### Manual Testing Checklist

**Basic Functionality:**
- [ ] Lookup available domain
- [ ] Lookup taken domain
- [ ] Test invalid domain format
- [ ] Verify JSON output is valid

**Caching:**
- [ ] First lookup hits API
- [ ] Second lookup uses cache
- [ ] Cache expires after 24 hours
- [ ] Cache file exists and is readable

**Error Scenarios:**
- [ ] Run without `WHOAPI_TOKEN` set
- [ ] Run with invalid API key
- [ ] Test without internet connection
- [ ] Test unsupported TLD

**Skill Integration:**
- [ ] Ask Claude about domain availability
- [ ] Verify Claude invokes script correctly
- [ ] Verify Claude interprets results
- [ ] Test conversational presentation

### Test Domains
- `google.com` - guaranteed taken, stable data
- `thisisaveryunlikelydomainname123456789.com` - likely available
- `invalid domain` - malformed input
- `test.dev` - newer gTLD (.dev)

### Success Criteria
- Script executes in <2s with cache hit
- Script executes in <10s with API call
- All errors return valid JSON
- Claude uses tool without confusion
- Cache reduces API calls to 1/domain/day

## Future Enhancements (v2)

### Batch Lookup
- New script: `whois_batch.py`
- Accept multiple domains (file or args)
- Parallel API calls (with rate limit respect)
- Summary table output
- New skill: `whois-batch.md`

### Other Ideas
- Support additional APIs (fallback if WhoAPI down)
- Domain suggestion based on availability
- Price checking for premium domains
- Historical availability tracking

## Security Considerations

- **API Key Storage:** Environment variable only, never commit to git
- **Cache Permissions:** Ensure cache directory is user-readable only
- **Input Sanitization:** Validate domain format before API calls
- **Rate Limiting:** Respect API limits, implement backoff
- **Error Messages:** Don't expose internal paths or API keys in errors

## Dependencies

**Runtime:**
- Python 3.6+
- `requests` library

**Development:**
- Git (for version control)
- Text editor

**External Services:**
- WhoAPI account (free tier: 10k requests)

## Installation Requirements

**User Setup:**
1. Python 3.6+ installed
2. `pip install requests`
3. WhoAPI account with API key
4. `WHOAPI_TOKEN` environment variable set
5. Skills copied to `~/.claude/skills/`

**Estimated Setup Time:** 5-10 minutes

## Success Metrics

- Users can check domain availability through Claude
- Setup takes <10 minutes for new users
- API quota sufficient for typical use (10k requests = ~400/day for 25 days)
- Cache hit rate >50% during brainstorming sessions
- Zero credential management issues (env var approach)

## Alternatives Considered

**MCP Server:**
- ❌ Requires compilation/installation
- ❌ Background process management
- ❌ More complex user setup
- ✅ More structured tool interface

**System whois Command:**
- ✅ No API key needed
- ✅ Zero external dependencies
- ❌ Doesn't report availability for many TLDs (.dev, .app, etc.)
- ❌ Inconsistent output formats
- ❌ Rate limiting by registries

**Skill + Bash Scripts:**
- ✅ Very portable
- ❌ Harder to parse JSON
- ❌ Harder to manage cache logic
- ❌ Less readable code

## Decision: Skill + Python Script

Chosen for optimal balance of simplicity, portability, and functionality.
