import os
import sys
import getpass
from dotenv import load_dotenv
from supabase import create_client


def main():
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    anon = os.getenv("SUPABASE_ANON_KEY")

    if not url or not anon:
        print("ERROR: SUPABASE_URL or SUPABASE_ANON_KEY missing in .env", file=sys.stderr)
        sys.exit(1)

    # Read credentials
    email = None
    password = None

    # Support CLI args: --email, --password
    for i, arg in enumerate(sys.argv):
        if arg == "--email" and i + 1 < len(sys.argv):
            email = sys.argv[i + 1]
        if arg == "--password" and i + 1 < len(sys.argv):
            password = sys.argv[i + 1]

    if not email:
        email = input("Email: ").strip()
    if not password:
        password = getpass.getpass("Password: ")

    client = create_client(url, anon)

    try:
        result = client.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })
        session = result.session
        if not session:
            print("ERROR: Invalid credentials or no session returned", file=sys.stderr)
            sys.exit(2)

        print("access_token=", session.access_token)
        print("refresh_token=", session.refresh_token)
        if result.user:
            print("user_id=", result.user.id)
            print("email=", result.user.email)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
