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
