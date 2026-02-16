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
