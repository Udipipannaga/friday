from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_prefix='FRIDAY_', extra='ignore')
    database_url: str = 'sqlite:///./friday.db'
    redis_url: str = 'redis://localhost:6379/0'
    origin: str = 'http://localhost:5173'
    secure_cookie: bool = False
    registration_open: bool = False
    owner_email: str = 'udipi.adithya@gmail.com'
    provider: str = 'openai'
    model: str = ''
    api_key: str = ''
    ollama_url: str = 'http://ollama:11434'
    search_key: str = ''
    daily_jobs: int = 30
    max_active_jobs: int = 3
    max_output_tokens: int = 3000
    lease_seconds: int = 180
    task_seconds: int = 900
    study_queue_path: str = '/app/private-evaluation/human-review-queue.jsonl'
    study_manifest_path: str = '/app/private-evaluation/run-manifest.json'


settings = Settings()
