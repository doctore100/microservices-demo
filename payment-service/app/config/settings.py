from pathlib import Path

from pydantic import Field, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    REDIS_PASSWORD: SecretStr = Field(default=..., description="Redis password", )
    REDIS_HOST: SecretStr = Field(default=..., description="Redis host", )


    @computed_field(return_type=Path)
    @property
    def proj_root(self) -> Path:
        """
        Returns the project root directory computed by resolving two
        levels up from the current settings module location.

        :return: Absolute path to the project root.
        """
        return Path(__file__).resolve().parents[2]
