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
