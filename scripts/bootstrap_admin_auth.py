#!/usr/bin/env python3
"""Bootstrapping script for Credence Operator Admin Authentication.

Usage:
    python3 scripts/bootstrap_admin_auth.py [local|dev|prod] [--print-token]
"""

from __future__ import annotations

import argparse
import re
import secrets
from pathlib import Path


def generate_admin_token() -> str:
    """Generate a high-entropy cryptographically secure admin token."""
    return f"cred_adm_{secrets.token_urlsafe(32)}"


def bootstrap_local(env_file_path: Path, print_only: bool = False) -> str:
    """Bootstrap or retrieve local development admin API key in .env."""
    if not env_file_path.exists():
        env_file_path.touch()

    content = env_file_path.read_text(encoding="utf-8")
    match = re.search(r"^CREDENCE_ADMIN_API_KEY=([^\s#]+)", content, re.MULTILINE)

    if match and match.group(1):
        token = match.group(1).strip("\"'")
    else:
        token = generate_admin_token()
        if "CREDENCE_ADMIN_API_KEY=" in content:
            content = re.sub(
                r"^CREDENCE_ADMIN_API_KEY=.*",
                f'CREDENCE_ADMIN_API_KEY="{token}"',
                content,
                flags=re.MULTILINE,
            )
        else:
            content += f'\n# Administrative Security & Operator Token\nCREDENCE_ADMIN_API_KEY="{token}"\n'
        env_file_path.write_text(content, encoding="utf-8")

    if print_only:
        print(token)
    else:
        print("=" * 64)
        print("🛡️  CREDENCE LOCAL OPERATOR AUTHENTICATION BOOTSTRAP")
        print("=" * 64)
        print(f"Environment:         Local (.env: {env_file_path})")
        print(f"Admin API Key:       {token}")
        print(f"Header:              Authorization: Bearer {token}")
        print(f"Alternative Header:  X-Credence-Admin-Key: {token}")
        print("=" * 64)
        print("✅ Ready to authenticate in browser workstation at: https://credence.nexus#admin")
    return token


def bootstrap_gcp(env_name: str, print_only: bool = False) -> None:
    """Validate or guide Secret Manager configuration for GCP environments."""
    project_id = "credence-dev-495173" if env_name == "dev" else "credence-prod-505902"
    secret_name = "credence-admin-api-key"  # noqa: S105

    print("=" * 64)
    print(f"🛡️  CREDENCE {env_name.upper()} OPERATOR AUTHENTICATION CONFIG")
    print("=" * 64)
    print(f"Target Project:      {project_id}")
    print(f"Secret Manager ID:   {secret_name}")
    print("Command to seed:")
    print(f"  gcloud secrets create {secret_name} --data-file=- --project={project_id} << 'EOF'")
    print(f"  {generate_admin_token()}")
    print("  EOF")
    print("=" * 64)


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap Credence Admin Auth Credentials")
    parser.add_argument("env", nargs="?", default="local", choices=["local", "dev", "prod"], help="Target environment")
    parser.add_argument("--print-token", action="store_true", help="Print only the raw token string")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    env_path = repo_root / ".env"

    if args.env == "local":
        bootstrap_local(env_path, print_only=args.print_token)
    else:
        bootstrap_gcp(args.env, print_only=args.print_token)


if __name__ == "__main__":
    main()
