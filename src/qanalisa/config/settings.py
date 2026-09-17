from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed runtime settings for QAnalisa."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    jira_base_url: str
    jira_email: str
    jira_api_token: str

    ai_provider: str = "claude_cli"
    claude_command: str = "claude"
    claude_model: str | None = None
    claude_timeout_seconds: int = 120
