from getstream import Stream
from getstream.models import CallRequest
from getstream.models import CallRequest, MemberRequest
from app.core.config import settings


class StreamService:
    """
    Service wrapper around Stream Video SDK.
    """

    api_key = settings.STREAM_API_KEY #exposing for frontend responses

    client = Stream(
        api_key=settings.STREAM_API_KEY,
        api_secret=settings.STREAM_API_SECRET,
    )

    @staticmethod
    def create_call(call_id: str, customer_id: str, priest_id: str):

        """
        Create a Stream video call.
        """

        call = StreamService.client.video.call(
            "default",
            call_id
        )

        call.create(
            data=CallRequest(
                created_by_id=customer_id,
                members=[
                    MemberRequest(user_id=customer_id),
                    MemberRequest(user_id=priest_id)
                ],
                settings_override={
                    "backstage": {
                        "enabled": False
                    }
                }
            )
        )

        return call

    @staticmethod
    def end_call(call_id: str):
        """
        End an active Stream video call.
        """

        call = StreamService.client.video.call(
            "default",
            call_id
        )

        call.end()

    @staticmethod
    def create_token(user_id: str):
        """
        Generate Stream JWT token for a user.
        """

        return StreamService.client.create_token(user_id)