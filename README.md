# token-balance

#this project was built using AI

Display your LLM API credit balance in any Wayland bar or terminal.

## Supported Providers

| Provider | Env Variable | Balance Endpoint | Display |
|----------|-------------|-----------------|---------|
| **OpenAI** | `OPENAI_API_KEY` | `/dashboard/billing/credit_grants` | Available $ |
| **Anthropic (Claude)** | `ANTHROPIC_API_KEY` | `/v1/organizations/billing` | Credits $ |
| **Google Gemini** | `GEMINI_API_KEY` | `/v1beta/models` (validates key) | "quota" |
| **DeepSeek** | `DEEPSEEK_API_KEY` | `/user/balance` | ¥ or $ |
| **OpenRouter** | `OPENROUTER_API_KEY` | `/api/v1/auth/key` | Credits $ |
| **Together AI** | `TOGETHER_API_KEY` | `/api/v1/user/credits` | Credits $ |
| **Fireworks AI** | `FIREWORKS_API_KEY` | `/v1/user` | Credits $ |
| **SiliconFlow (硅基流动)** | `SILICONFLOW_API_KEY` | `/v1/user/info` | ¥ or "ok" |
| **Groq** | `GROQ_API_KEY` | `/v1/user/status` | "active" |

Use `--provider all` to try each in order and show the first that responds.

## Quick Start

```bash
# Install
pip install -r requirements.txt
cp token-balance.py ~/.local/bin/token-balance
chmod +x ~/.local/bin/token-balance

# Test a single provider
token-balance --provider deepseek
# → {"text": "¥15.71", "class": "online", "tooltip": "DeepSeek: ¥15.71 remaining"}

# Try all configured providers (shows first available)
token-balance --provider all
```

## Waybar Config

Add to `~/.config/waybar/config.jsonc`:

```jsonc
"custom/token-balance": {
    "exec": "token-balance --provider all",
    "interval": 120,
    "return-type": "json",
    "format": "{}",
    "tooltip": true
}
```

With proxy (China users):

```jsonc
"custom/token-balance": {
    "exec": "token-balance --provider deepseek --proxy http://127.0.0.1:7897",
    "interval": 120,
    "return-type": "json",
    "format": "{}"
}
```

## API Keys

Keys are read from `~/.hermes/.env` by default. Set a custom env file:

```bash
TOKEN_BALANCE_ENV=*** token-balance --provider deepseek
```

The env file should contain lines like:
```
DEEPSEEK_API_KEY=sk-...
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

## Adding a New Provider

1. Write a `XXX_balance(api_key, proxy)` function that returns a dict or None
2. Add it to the `PROVIDERS` dict
3. The env variable is auto-derived from the name: `xxx` → `XXX_API_KEY`
4. Update this README

## Proxy

Auto-discovers proxies in order: explicit → Clash (7897) → Clash (7890) → v2raya (20171) → direct.
Or set explicitly:

```bash
token-balance --provider deepseek --proxy http://127.0.0.1:7897
```
