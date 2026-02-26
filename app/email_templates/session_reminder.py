from datetime import datetime

def build_session_reminder_email(join_url: str):
    year = datetime.now().year
    subject = "Reminder: Your session starts in 5 minutes"

    body = f"""
    <html>
      <body>
        <h2>Session Reminder</h2>
        <p>Your session starts in 5 minutes.</p>
        <a href="{join_url}">Join Session</a>
        <p>&copy; {year} Maathre</p>
      </body>
    </html>
    """

    return subject, body