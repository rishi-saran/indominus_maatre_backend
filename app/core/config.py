from pydantic import BaseModel

# this is just for development testing, need to change this in prod

class Settings(BaseModel):
    # JWT
    JWT_SECRET_KEY: str = "super-secret-change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


settings = Settings()
