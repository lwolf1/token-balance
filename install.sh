#!/usr/bin/env bash
set -euo pipefail

# token-balance — one-liner install
# Usage: bash <(curl -s https://raw.githubusercontent.com/oscar/token-balance/main/install.sh)

REPO="https://raw.githubusercontent.com/oscar/token-balance/main"
BIN="$HOME/.local/bin"
ENV_FILE="${TOKEN_BALANCE_ENV:-$HOME/.config/token-balance.env}"
WAYBAR_CONFIG="$HOME/.config/waybar/config.jsonc"
WAYBAR_STYLE="$HOME/.config/waybar/style.css"

echo ":: Installing token-balance..."

# 1. Install script
mkdir -p "$BIN"
curl -sSL "$REPO/token-balance.py" -o "$BIN/token-balance"
chmod +x "$BIN/token-balance"
echo "   ✓ Script installed to $BIN/token-balance"

# 2. Create env file if missing
if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" << 'ENVEOF'
# token-balance API keys
# Uncomment and fill in the providers you use:
# DEEPSEEK_API_KEY=sk-your-key-here
# OPENAI_API_KEY=sk-your-key-here
# OPENROUTER_API_KEY=sk-or-your-key-here
ENVEOF
    echo "   ✓ Config created at $ENV_FILE"
    echo "   ⚠  Edit it to add your API keys!"
else
    echo "   ✓ Config already exists at $ENV_FILE"
fi

# 3. Waybar config (append custom module if Waybar exists)
if command -v waybar &>/dev/null; then
    mkdir -p "$(dirname "$WAYBAR_CONFIG")"
    echo "   ℹ  Waybar detected. Add this module to $WAYBAR_CONFIG:"
    echo ""
    echo '    "custom/token-balance": {'
    echo '        "exec": "'"$BIN/token-balance"' --provider deepseek",'
    echo '        "interval": 120,'
    echo '        "return-type": "json",'
    echo '        "format": "{}"'
    echo '    },'
    echo ""
    echo "    And this to $WAYBAR_STYLE:"
    echo ""
    echo '    #custom-token-balance { padding: 0 8px; font-weight: 600; }'
    echo '    #custom-token-balance.offline { color: #f87171; }'
    echo '    #custom-token-balance.online { color: #e0e8f0; }'
    echo ""
fi

# 4. Verify
echo ":: Testing..."
if "$BIN/token-balance" --help &>/dev/null; then
    echo "   ✓ Installation OK"
    echo ""
    echo "   Next steps:"
    echo "   1. Edit $ENV_FILE with your API keys"
    echo "   2. Run: token-balance --provider deepseek"
    echo "   3. Add the Waybar module and restart waybar"
else
    echo "   ✗ Something went wrong"
    exit 1
fi
