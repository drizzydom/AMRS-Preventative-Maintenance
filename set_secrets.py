"""
set_secrets.py: Script to securely store sensitive secrets in the system keyring.
Works on macOS, Windows, and Linux. Run this script once per machine to set up secrets.
"""
import keyring
import getpass

SERVICE = "amrs"
SECRETS = [
    "USER_FIELD_ENCRYPTION_KEY",
    "RENDER_EXTERNAL_URL",
    "SYNC_URL",
    "SYNC_USERNAME",
    "AMRS_ONLINE_URL",
    "AMRS_ADMIN_USERNAME",
    "AMRS_ADMIN_PASSWORD",
    "MAIL_SERVER",
    "MAIL_PORT",
    "MAIL_USE_TLS",
    "MAIL_USERNAME",
    "MAIL_PASSWORD",
    "MAIL_DEFAULT_SENDER",
    "SECRET_KEY",
    "BOOTSTRAP_SECRET_TOKEN",
]

def main():
    print("\nAMRS Secure Secret Setup (keyring)")
    print("----------------------------------")
    for key in SECRETS:
        existing = keyring.get_password(SERVICE, key)
        if existing:
            print(f"[SKIP] {key} already set.")
            continue
        value = getpass.getpass(f"Enter value for {key}: ")
        if value:
            keyring.set_password(SERVICE, key, value)
            print(f"[OK] {key} stored.")
        else:
            print(f"[WARN] {key} skipped (empty value).")
    print("\nAll done! Secrets are now stored securely in your system keyring.")

if __name__ == "__main__":
    main()
