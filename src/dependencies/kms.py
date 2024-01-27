import contextlib
from functools import lru_cache
from typing import Annotated, AsyncIterator

import boto3
from fastapi import Depends, FastAPI
from mypy_boto3_kms import KMSClient

from ..config import ConfigDependency

client = None


@contextlib.asynccontextmanager
async def kms_lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    if client:
        client.close()


@lru_cache
def get_kms(config: ConfigDependency):
    global client
    client = boto3.client("kms", region_name=config.aws_region)
    return client


KMSDependency = Annotated[KMSClient, Depends(get_kms)]
