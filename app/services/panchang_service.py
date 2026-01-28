import httpx
from datetime import datetime
from app.core.config import settings

TOKEN_URL = "https://api.prokerala.com/token"
PANCHANG_URL = "https://api.prokerala.com/v2/astrology/panchang/advanced"

async def get_access_token():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": settings.PROKERALA_CLIENT_ID,
                "client_secret": settings.PROKERALA_CLIENT_SECRET,
            },
        )
        response.raise_for_status()
        return response.json()["access_token"]


async def get_advanced_panchang(date, coordinates):
    token = await get_access_token()

    datetime_str = f"{date}T00:00:00+05:30"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            PANCHANG_URL,
            params={
                "datetime": datetime_str,
                "coordinates": coordinates,
                "ayanamsa": 1,
                "la": "en",
            },
            headers={
                "Authorization": f"Bearer {token}"
            }
        )
        response.raise_for_status()
        return response.json()["data"]
