from pathlib import Path

from pydantic import Field, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    :ivar REDIS_PASSWORD: Password for Redis authentication.
    :ivar REDIS_HOST: Hostname of the Redis server.
    :ivar REDIS_PORT: Port number of the Redis server.
    :ivar proj_root: Absolute path to the project root directory.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    REDIS_PASSWORD: SecretStr = Field(
        default=...,
        description="Redis password",
    )
    REDIS_HOST: SecretStr = Field(
        default=...,
        description="Redis host",
    )
    REDIS_PORT: int = Field(
        default=10073,
        description="Redis port",
    )

    @computed_field(return_type=Path)
    @property
    def proj_root(self) -> Path:
        """
        Return the project root directory.

        :return: Absolute path to the project root.
        :rtype: Path
        """
        return Path(__file__).resolve().parents[2]
