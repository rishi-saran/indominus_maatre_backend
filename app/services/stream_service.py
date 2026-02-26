
class StreamService:
    @staticmethod
    def enable_backstage(stream_id: str):
        print(f"[STREAM] Backstage enabled for {stream_id}")

    @staticmethod
    def start_call(stream_id: str):
        print(f"[STREAM] Call started for {stream_id}")

    @staticmethod
    def end_call(stream_id: str):
        print(f"[STREAM] Call ended for {stream_id}")