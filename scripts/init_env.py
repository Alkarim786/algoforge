"""Create a .env with freshly generated secrets. Never overwrites an existing one.

    python scripts/init_env.py                          # local development
    python scripts/init_env.py --domain algoforge.dev   # production: also sets the site's domain

With --domain and an existing .env that has no DOMAIN yet, the domain is added and nothing else changes.
"""
import argparse
import re
import secrets
from pathlib import Path

env_path = Path(__file__).resolve().parents[1] / ".env"

parser = argparse.ArgumentParser(description="Create .env with generated secrets.")
parser.add_argument("--domain", help="public domain for production, e.g. algoforge.example.com")
args = parser.parse_args()

domain = args.domain
if domain and not re.fullmatch(r"(https?://)?[A-Za-z0-9.-]+(:\d+)?", domain):
    raise SystemExit(f"'{domain}' doesn't look like a domain name.")

if env_path.exists():
    existing = env_path.read_text()
    if domain and not re.search(r"^DOMAIN=", existing, re.MULTILINE):
        env_path.write_text(existing.rstrip("\n") + f"\nDOMAIN={domain}\n")
        raise SystemExit(f"Added DOMAIN={domain} to {env_path}.")
    raise SystemExit(f"{env_path} already exists; leaving it alone.")

env_path.write_text(
    "POSTGRES_USER=algoforge\n"
    f"POSTGRES_PASSWORD={secrets.token_hex(24)}\n"
    "POSTGRES_DB=algoforge\n"
    f"JWT_SECRET={secrets.token_hex(32)}\n"
    f"ADMIN_API_KEY={secrets.token_hex(24)}\n"
    + (f"DOMAIN={domain}\n" if domain else "")
)
env_path.chmod(0o600)
print(f"Wrote {env_path}")
