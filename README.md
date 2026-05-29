# token-balance

Display your LLM API credit balance in any Wayland bar.

Supports **DeepSeek**, **OpenAI**, **OpenRouter** — outputs Waybar-compatible JSON.

## Quick Start

```bash
# Install
pip install -r requirements.txt
cp token-balance.py ~/.local/bin/token-balance
chmod +x ~/.local/bin/token-balance

# Test
token-balance --provider deepseek
# → {"text": "¥15.71", "class": "online", "tooltip": "DeepSeek: ¥15.71 remaining"}
```

## Waybar Config

Add a custom module to `~/.config/waybar/config.jsonc`:

```jsonc
"custom/token-balance": {
    "exec": "token-balance --provider deepseek",
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

Multiple providers (shows first available):

```jsonc
"custom/token-balance": {
    "exec": "token-balance --provider all",
    "interval": 120,
    "return-type": "json"
}
```

## API Keys

The script reads keys from `~/.hermes/.env` by default:

```
DEEPSEEK_API_KEY=sk-...
OPENAI_API_KEY=sk-...
OPENROUTER_API_KEY=sk-...
```

Override with `TOKEN_BALANCE_ENV` environment variable:

```bash
export TOKEN_BALANCE_ENV=~/.config/my-keys.env
```

## Supported Providers

| Provider | Key Env Var | Balance Endpoint |
|----------|-------------|-----------------|
| DeepSeek | `DEEPSEEK_API_KEY` | `/user/balance` |
| OpenAI | `OPENAI_API_KEY` | `/dashboard/billing/credit_grants` |
| OpenRouter | `OPENROUTER_API_KEY` | `/api/v1/auth/key` |

Add more by writing a handler function and adding it to the `PROVIDERS` dict.

## Output Format

```json
{
    "text": "¥15.71",
    "class": "online",
    "alt": "deepseek-CNY",
    "tooltip": "DeepSeek: ¥15.71 remaining"
}
```

- `online` / `offline` CSS class for styling
- Tooltip shows details on hover

## Waybar Styling

Add to `~/.config/waybar/style.css`:

```css
#custom-token-balance {
    padding: 0 8px;
    font-weight: 600;
}
#custom-token-balance.offline {
    color: #f87171;
}
#custom-token-balance.online {
    color: #e0e8f0;
}
```

## Other Bars

- **EWW / AGS**: parse the JSON output and render in a window
- **niri**: works via Waybar or any bar with custom command support
- **Sway / Hyprland / river**: same — any bar that supports `exec` + JSON parsing

## License

MIT
