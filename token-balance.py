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
    if proxy:
        cmd += ["-x", proxy]
    cmd += ["-H", auth_header, url]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
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

PROVIDERS = {
    "deepseek": deepseek_balance,
    "openai": openai_balance,
    "openrouter": openrouter_balance,
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
