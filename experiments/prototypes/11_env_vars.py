"""
Experiment 11: Do env vars work with our manual dispatch pattern?

When we call CliApp.run(model, cli_args=[...]), does pydantic-settings
still read environment variables? This is critical for auth (MYCLI_TOKEN).
"""

import os
from pydantic import BaseModel
from pydantic_settings import BaseSettings, CliApp


# === Approach A: BaseModel (what we've been using) ===

class CmdAsModel(BaseModel):
    """Command as plain BaseModel."""
    name: str
    token: str | None = None

    def cli_cmd(self):
        print(f"  name={self.name} token={self.token}")


# === Approach B: BaseSettings (reads env vars natively) ===

class CmdAsSettings(BaseSettings):
    """Command as BaseSettings — should read env vars."""
    name: str
    token: str | None = None

    def cli_cmd(self):
        print(f"  name={self.name} token={self.token}")


# === Approach C: BaseModel but with manual env var reading ===

class CmdWithEnvFallback(BaseModel):
    """Command with manual env var fallback for auth."""
    name: str
    token: str | None = None

    def cli_cmd(self):
        # Manual fallback: if --token not provided, check env
        effective_token = self.token or os.environ.get("MYCLI_TOKEN")
        print(f"  name={self.name} token={effective_token}")


# === Approach D: Auth fields as a separate BaseSettings model ===

class AuthConfig(BaseSettings):
    """Auth config that reads from env vars."""
    model_config = {"env_prefix": "MYCLI_"}
    token: str | None = None


class CmdWithAuthModel(BaseModel):
    """Command that uses separate auth model."""
    name: str

    def cli_cmd(self):
        auth = AuthConfig()
        print(f"  name={self.name} token={auth.token}")


if __name__ == "__main__":
    print("=" * 60)
    print("EXPERIMENT 11: Environment Variable Integration")
    print("=" * 60)

    # Set env var
    os.environ["MYCLI_TOKEN"] = "env-secret-123"
    os.environ["TOKEN"] = "raw-token-456"

    tests = [
        # BaseModel — does NOT read env vars (expected)
        ("BaseModel, no --token", CmdAsModel, ["--name", "test"]),
        ("BaseModel, with --token", CmdAsModel, ["--name", "test", "--token", "cli-token"]),

        # BaseSettings — SHOULD read env vars
        ("BaseSettings, no --token (should read env)", CmdAsSettings, ["--name", "test"]),
        ("BaseSettings, with --token (should override)", CmdAsSettings, ["--name", "test", "--token", "cli-token"]),

        # Manual fallback
        ("Manual fallback, no --token", CmdWithEnvFallback, ["--name", "test"]),
        ("Manual fallback, with --token", CmdWithEnvFallback, ["--name", "test", "--token", "cli-token"]),

        # Separate auth model
        ("Separate auth model", CmdWithAuthModel, ["--name", "test"]),
    ]

    for desc, model, args in tests:
        print(f"\n--- {desc} ---")
        try:
            CliApp.run(model, cli_args=args)
            print("  [OK]")
        except Exception as e:
            print(f"  [ERROR] {type(e).__name__}: {e}")

    # Clean up
    del os.environ["MYCLI_TOKEN"]
    del os.environ["TOKEN"]
