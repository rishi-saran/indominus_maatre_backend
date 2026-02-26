from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_ANON_KEY: str
    SUPABASE_JWT_SECRET: str
    
    # Razorpay Configuration
    RAZORPAY_KEY_ID: str
    RAZORPAY_KEY_SECRET: str
    RAZORPAY_WEBHOOK_SECRET: str
    
    # Prokerala panchang config
    PROKERALA_CLIENT_ID: str
    PROKERALA_CLIENT_SECRET: str

    # redis(mq)
    REDIS_URL: str

    # aws ses smtp
    SES_SMTP_HOST: str
    SES_SMTP_PORT: int
    SES_SMTP_USERNAME: str
    SES_SMTP_PASSWORD: str
    SES_FROM_EMAIL: str

    class Config:
        env_file = ".env"


settings = Settings()