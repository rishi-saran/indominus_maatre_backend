from stream_video import StreamVideo
from app.core.config import settings

class StreamService:
    client = StreamVideo(
        api_key=settings.STREAM_API_KEY,
        api_secret=settings.STREAM_API_SECRET,
    )

    @staticmethod
    def create_call(call_id: str):
        """
        Create a 1-on-1 private video call
        """
        call = StreamService.client.call(
            type="default",  
            id=call_id,
        )

        call.create()
        return call

    @staticmethod
    def enable_backstage(call_id: str):
        print(f"[STREAM] Backstage enabled for {call_id}")

    @staticmethod
    def start_call(call_id: str):
        print(f"[STREAM] Call started for {call_id}")

    @staticmethod
    def end_call(call_id: str):
        call = StreamService.client.call("default", call_id)
        call.end()