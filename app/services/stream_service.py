from getstream import Stream
from getstream.models import UserRequest
from app.core.config import settings


class StreamService:

    api_key = settings.STREAM_API_KEY

    client = Stream(
        api_key=settings.STREAM_API_KEY,
        api_secret=settings.STREAM_API_SECRET,
    )

    @staticmethod
    def create_token(user_id: str) -> str:
        """Generate a token for a user to join a Stream call."""
        return StreamService.client.create_token(str(user_id))

    @staticmethod
    def create_call(call_id: str, customer_id: str, priest_id: str):
        """Create a call and assign members."""
        call = StreamService.client.video.call("default", call_id)
        
        # Ensure the users exist in Stream before creating the call with them as members
        # Upserting them here helps prevent duplicate "ghost" users across sessions
        # if they join from multiple tabs, by anchoring their identity in Stream.
        StreamService.client.upsert_users(
            UserRequest(id=str(customer_id), role="user"),
            UserRequest(id=str(priest_id), role="user")
        )

        # Create the call with specific members and SETTINGS_OVERRIDE inside data.
        # This is critical because passing settings_override as a kwarg fails.
        # By including it in the data dictionary, we ensure the call is created 
        # with backstage ALREADY disabled, preventing JoinBackstage errors.
        # We assign the 'admin' role to both for guaranteed join permissions 
        # in the 'video:default' scope, as 'host' was missing JoinBackstage.
        call.create(
            data={
                "created_by_id": str(customer_id),
                "members": [
                    {"user_id": str(customer_id), "role": "admin"}, #should change the role, only for testing purposes
                    {"user_id": str(priest_id), "role": "admin"}#should change the role, only for testing purposes
                ],
                "settings_override": {
                    "backstage": {
                        "enabled": False
                    }
                }
            }
        )
        print(f"Stream call {call_id} created with backstage disabled (admin role).")

    @staticmethod
    def enable_backstage(call_id: str):
        """Enable backstage mode so the priest can warm up 5 min before the session.
        Currently forced to False to avoid JoinBackstage errors.
        """
        call = StreamService.client.video.call("default", call_id)

        # Use the explicit settings_override kwarg for update() as found in tests
        response = call.update(
            settings_override={
                "backstage": {
                    "enabled": False
                }
            }
        )
        print(f"Stream call {call_id} enable_backstage (no-op): {response}")

    @staticmethod
    def start_call(call_id: str):
        """Disable backstage so all members can join when the session goes live."""
        call = StreamService.client.video.call("default", call_id)

        # Use the explicit settings_override kwarg for update() as found in tests
        response = call.update(
            settings_override={
                "backstage": {
                    "enabled": False
                }
            }
        )
        print(f"Stream call {call_id} start_call (backstage off): {response}")

    @staticmethod
    def end_call(call_id: str):
        call = StreamService.client.video.call("default", call_id)

        call.end()