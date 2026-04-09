"""
Experiment 9: How do discriminated unions work in pydantic-settings CLI?

Test: Notification = email | sms, discriminated by "type" field.
"""

from typing import Literal
from pydantic import BaseModel
from pydantic_settings import CliApp


# === Discriminated union models ===

class NotificationEmail(BaseModel):
    """Send an email notification."""
    type: Literal["email"] = "email"
    to: str
    subject: str
    body: str | None = None


class NotificationSMS(BaseModel):
    """Send an SMS notification."""
    type: Literal["sms"] = "sms"
    phone: str
    message: str


# === Approach A: JSON-only (simplest) ===

class NotifyJsonCmd(BaseModel):
    """Send notification (JSON input)."""
    notification: str  # Accept as raw JSON string

    def cli_cmd(self):
        import json
        data = json.loads(self.notification)
        print(f"Notification: {json.dumps(data, indent=2)}")


# === Approach B: Type flag selects fields ===
# User picks --type email or --type sms, we show relevant fields

class NotifyFlatCmd(BaseModel):
    """Send notification (flat flags, all fields exposed)."""
    type: str  # "email" or "sms"
    # Email fields
    to: str | None = None
    subject: str | None = None
    body: str | None = None
    # SMS fields
    phone: str | None = None
    message: str | None = None

    def cli_cmd(self):
        if self.type == "email":
            notif = NotificationEmail(to=self.to, subject=self.subject, body=self.body)
        elif self.type == "sms":
            notif = NotificationSMS(phone=self.phone, message=self.message)
        else:
            print(f"Unknown type: {self.type}")
            return
        print(f"Notification: {notif.model_dump_json(indent=2)}")


# ============================
# Test runner
# ============================

if __name__ == "__main__":
    print("=" * 60)
    print("EXPERIMENT 9: Discriminated Unions")
    print("=" * 60)

    tests = [
        # Approach A: JSON
        ("JSON --help", NotifyJsonCmd, ["--help"]),
        ("JSON email", NotifyJsonCmd, [
            "--notification", '{"type":"email","to":"user@x.com","subject":"Hi","body":"Hello"}'
        ]),
        ("JSON sms", NotifyJsonCmd, [
            "--notification", '{"type":"sms","phone":"+1234567890","message":"Hello"}'
        ]),

        # Approach B: Flat flags
        ("Flat --help", NotifyFlatCmd, ["--help"]),
        ("Flat email", NotifyFlatCmd, [
            "--type", "email", "--to", "user@x.com", "--subject", "Hi", "--body", "Hello"
        ]),
        ("Flat sms", NotifyFlatCmd, [
            "--type", "sms", "--phone", "+1234567890", "--message", "Hello"
        ]),
    ]

    for desc, model, args in tests:
        print(f"\n--- {desc} ---")
        print(f"  args: {' '.join(args)}")
        try:
            CliApp.run(model, cli_args=args)
            print("  [OK]")
        except SystemExit as e:
            print(f"  [EXIT {e.code}]")
        except Exception as e:
            print(f"  [ERROR] {type(e).__name__}: {e}")
