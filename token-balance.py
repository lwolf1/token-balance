#!/usr/bin/env python3
"""
token-balance — Query API credit balances from multiple providers.
Outputs Waybar-compatible JSON for display in any bar.

Supported providers: deepseek, openai, openrouter
Output format: {"text": "¥15.71", "class": "online", "tooltip": "..."}

Usage:
  token-balance --provider deepseek              # single provider
  token-balance --provider all                   # first available
  token-balance --provider deepseek --proxy http://127.0.0.1:7897
"""

import argparse, json, os, re, subprocess, sys

HOME = os.path.expanduser("~")

def get_env_path():
    return os.environ.get("TOKEN_BALANCE_ENV") or f"{HOME}/.hermes/.env"

def read_env_var(filename, name):
    try:
        with open(filename) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k.strip() == name:
                    return v.strip().strip("'\"")
    except FileNotFoundError:
        pass
    return None

def try_curl(url, auth_header, proxy=None):
    cmd = ["curl", "-s", "--max-time", "8"]

    # Try proxies in order: explicit → Clash → v2raya → direct
    proxies_to_try = []
    if proxy:
        proxies_to_try = [proxy]
    else:
        for host, port in [("127.0.0.1", 7897), ("127.0.0.1", 7890),
                           ("127.0.0.1", 20171), ("127.0.0.1", 1080)]:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.3)
            if s.connect_ex((host, port)) == 0:
                proxies_to_try.append(f"http://{host}:{port}")
            s.close()
        proxies_to_try.append(None)  # direct as last resort

    for p in proxies_to_try:
        try:
            c = cmd[:]
            if p:
                c += ["-x", p]
            c += ["-H", auth_header, url]
            r = subprocess.run(c, capture_output=True, text=True, timeout=8)
            out = r.stdout.strip()
            if out:
                data = json.loads(out)
                if isinstance(data, dict) and data.get("is_available") is not None:
                    return data
        except Exception:
            continue

    # Final fallback
    try:
        r = subprocess.run(cmd + ["-H", auth_header, url],
                           capture_output=True, text=True, timeout=8)
        return json.loads(r.stdout) if r.stdout.strip() else {}
    except Exception:
        return {}

# ── Provider handlers ──

def deepseek_balance(api_key, proxy):
    data = try_curl(
        "https://api.deepseek.com/user/balance",
        "Authorization: " + "Bearer" + " " + api_key,
        proxy
    )
    if data.get("is_available") and data.get("balance_infos"):
        info = data["balance_infos"][0]
        amt = float(info["total_balance"])
        sym = "¥" if info.get("currency") == "CNY" else "$"
        return {
            "text": f"{sym}{amt:.2f}",
            "class": "online",
            "alt": f"deepseek-{info['currency']}",
            "tooltip": f"DeepSeek: {sym}{amt:.2f} remaining"
        }
    return None

def openai_balance(api_key, proxy):
    data = try_curl(
        "https://api.openai.com/dashboard/billing/credit_grants",
        "Authorization: " + "Bearer" + " " + api_key,
        proxy
    )
    if data and "total_available" in data:
        total = float(data["total_available"])
        used = float(data.get("total_used", 0))
        return {
            "text": f"${total:.2f}",
            "class": "online",
            "alt": "openai-usd",
            "tooltip": f"OpenAI: ${total:.2f} available (${used:.2f} used)"
        }
    return None

def openrouter_balance(api_key, proxy):
    data = try_curl(
        "https://openrouter.ai/api/v1/auth/key",
        "Authorization: " + "Bearer" + " " + api_key,
        proxy
    )
    if data and "data" in data:
        cred = float(data["data"].get("credits", 0))
        return {
            "text": f"${cred:.2f}",
            "class": "online",
            "alt": "openrouter-usd",
            "tooltip": f"OpenRouter: ${cred:.2f} credits"
        }
    return None

def groq_balance(api_key, proxy):
    """Groq doesn't expose a balance API, but /v1/user/status returns usage."""
    data = try_curl(
        "https://api.groq.com/openai/v1/user/status",
        "Authorization: " + "Bearer" + " " + api_key,
        proxy
    )
    if data and "sessions" in data:
        return {
            "text": "active",
            "class": "online",
            "alt": "groq",
            "tooltip": "Groq: pay-as-you-go (no pre-paid balance)"
        }
    return None

def siliconflow_balance(api_key, proxy):
    data = try_curl(
        "https://api.siliconflow.cn/v1/user/info",
        "Authorization: " + "Bearer" + " " + api_key,
        proxy
    )
    if data and isinstance(data, dict):
        # Try different response shapes
        balance = data.get("balance")
        if balance is not None:
            amt = float(balance)
            return {
                "text": f"¥{amt:.2f}",
                "class": "online",
                "alt": "siliconflow-cny",
                "tooltip": f"SiliconFlow: ¥{amt:.2f} remaining"
            }
        # Fallback: check for totalBalance or similar
        tb = data.get("totalBalance") or data.get("total_balance")
        if tb is not None:
            return {
                "text": f"¥{float(tb):.2f}",
                "class": "online",
                "alt": "siliconflow-cny",
                "tooltip": f"SiliconFlow: ¥{float(tb):.2f} remaining"
            }
        # If we got a valid response but no balance field, show available
        if data.get("is_available") or data.get("id") or data.get("userId"):
            return {
                "text": "ok",
                "class": "online",
                "alt": "siliconflow",
                "tooltip": "SiliconFlow: account active (balance unknown)"
            }
    return None

def together_balance(api_key, proxy):
    """Together AI: /api/v1/user/credits → credits"""
    data = try_curl(
        "https://api.together.xyz/api/v1/user/credits",
        "Authorization: " + "Bearer" + " " + api_key,
        proxy
    )
    if data and isinstance(data, dict):
        c = data.get("credits")
        if c is not None:
            return {
                "text": f"${float(c):.2f}",
                "class": "online",
                "alt": "together-usd",
                "tooltip": f"Together AI: ${float(c):.2f} credits"
            }
    return None

def fireworks_balance(api_key, proxy):
    """Fireworks AI: /v1/user → credits"""
    data = try_curl(
        "https://api.fireworks.ai/v1/user",
        "Authorization: " + "Bearer" + " " + api_key,
        proxy
    )
    if data and isinstance(data, dict):
        c = data.get("credits")
        if c is not None:
            return {
                "text": f"${float(c):.2f}",
                "class": "online",
                "alt": "fireworks-usd",
                "tooltip": f"Fireworks AI: ${float(c):.2f} credits"
            }
    return None

def anthropic_balance(api_key, proxy):
    """Anthropic: /v1/organizations/billing → credits.
       Requires an org-level API key (Console → Settings → API Keys)."""
    data = try_curl(
        "https://api.anthropic.com/v1/organizations/billing",
        "x-api-key: " + api_key,
        proxy
    )
    if data and isinstance(data, dict):
        c = data.get("credits")
        if c is not None:
            sym = "$"
            amt = float(c)
            return {
                "text": f"{sym}{amt:.2f}",
                "class": "online",
                "alt": "anthropic-usd",
                "tooltip": f"Anthropic (Claude): {sym}{amt:.2f} credits"
            }
        # Check for balance in nested structure
        bal = data.get("balance") or data.get("total_balance")
        if bal is not None:
            return {
                "text": f"${float(bal):.2f}",
                "class": "online",
                "alt": "anthropic-usd",
                "tooltip": f"Anthropic (Claude): ${float(bal):.2f} remaining"
            }
        # Valid response but unknown field shape
        if data.get("organization_id") or data.get("id"):
            return {
                "text": "ok",
                "class": "online",
                "alt": "anthropic",
                "tooltip": "Anthropic (Claude): reachable (balance unknown)"
            }
    return None

def gemini_balance(api_key, proxy):
    """Google Gemini: no prepaid balance (quota-based via GCP).
       Check API key validity via model list instead."""
    data = try_curl(
        "https://generativelanguage.googleapis.com/v1beta/models",
        "x-goog-api-key: " + api_key,
        proxy
    )
    if data and isinstance(data, dict):
        if "models" in data or data.get("models"):
            return {
                "text": "quota",
                "class": "online",
                "alt": "gemini",
                "tooltip": "Gemini: pay-per-use (quota-based, no pre-paid balance)"
            }
    return None

PROVIDERS = {
    "openai": openai_balance,
    "anthropic": anthropic_balance,
    "gemini": gemini_balance,
    "deepseek": deepseek_balance,
    "openrouter": openrouter_balance,
    "together": together_balance,
    "fireworks": fireworks_balance,
    "siliconflow": siliconflow_balance,
    "groq": groq_balance,
}

def main():
    parser = argparse.ArgumentParser(description="Query API token balance")
    parser.add_argument("--provider", "-p", default="deepseek",
                        choices=list(PROVIDERS.keys()) + ["all"],
                        help="API provider")
    parser.add_argument("--proxy", help="Proxy URL")
    args = parser.parse_args()

    env_file = get_env_path()
    results = []

    if args.provider == "all":
        for name in PROVIDERS:
            key = read_env_var(env_file, f"{name.upper()}_API_KEY")
            if key and key != "***":
                r = PROVIDERS[name](key, args.proxy)
                if r:
                    results.append(r)
        if results:
            primary = results[0]
            primary["tooltip"] = "\n".join(r["tooltip"] for r in results)
            print(json.dumps(primary))
            return
    else:
        handler = PROVIDERS[args.provider]
        key = read_env_var(env_file, f"{args.provider.upper()}_API_KEY")
        if key and key != "***":
            r = handler(key, args.proxy)
            if r:
                print(json.dumps(r))
                return

    print(json.dumps({
        "text": "?",
        "class": "offline",
        "tooltip": f"{args.provider}: unreachable or no key"
    }))

if __name__ == "__main__":
    main()
