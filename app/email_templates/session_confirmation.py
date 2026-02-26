from datetime import datetime

def build_session_confirmation_email(join_url: str):
    year = datetime.now().year
    subject = "Your session has been confirmed"

    body = f"""
    <html>
      <body>
        <h2>Your one-on-one session is confirmed</h2>
        <p>You can join using the link below:</p>
        <a href="{join_url}">Join Session</a>
        <p>&copy; {year} Maathre</p>
      </body>
    </html>
    """

    return subject, body