from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", frozen=True
    )

    key_id: str = Field(validation_alias="AWS_KMS_KEY_ID")
    sagemaker_endpoint: str = Field(validation_alias="AWS_SAGEMAKER_ENDPOINT")
    aws_region: str = Field(validation_alias="AWS_REGION")


@lru_cache
def get_config():
    return Config()


ConfigDependency = Annotated[Config, Depends(get_config)]
