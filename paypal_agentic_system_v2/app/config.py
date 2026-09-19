from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = 'PayPal Agentic AI System'
    environment: str = 'development'
    paypal_mock_mode: bool = True
    paypal_base_url: str = 'https://api-m.sandbox.paypal.com'
    paypal_client_id: str = ''
    paypal_client_secret: str = ''
    tool_registry_path: str = 'data/tool_registry.json'
    database_url: str = 'sqlite:///./data/app.db'
    rag_knowledge_dir: str = 'data/knowledge'
    retrieval_top_k: int = 8
    openai_api_key: str = ''
    openai_model: str = 'gpt-4.1-mini'
    openai_base_url: str = 'https://api.openai.com/v1'
    llm_temperature: float = 0.0
    require_confirmation: bool = True
    max_retries: int = 2
    request_timeout_seconds: float = 30.0
    log_level: str = 'INFO'
    otel_enabled: bool = False
    model_config = SettingsConfigDict(env_file='.env', extra='ignore', case_sensitive=False)

settings = Settings()
