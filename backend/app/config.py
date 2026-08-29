from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./training.db"
    app_name: str = "Personalized AI Training Platform"
    openai_api_key: str | None = None
    llm_model: str = "gpt-4o-mini"
    llm_max_attempts: int = 3
    prompt_version: str = "workout_plan.v1"


settings = Settings()
