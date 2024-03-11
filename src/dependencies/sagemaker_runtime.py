import contextlib
from functools import lru_cache
from typing import Annotated, AsyncIterator

import boto3
from fastapi import Depends, FastAPI
from mypy_boto3_sagemaker_runtime import SageMakerRuntimeClient

from ..config import ConfigDependency

client = None


@contextlib.asynccontextmanager
async def sagemaker_lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    if client:
        client.close()


@lru_cache
def get_sagemaker(config: ConfigDependency):
    global client
    client = boto3.client("sagemaker-runtime", region_name=config.aws_region)
    return client


SageMakerDependency = Annotated[SageMakerRuntimeClient, Depends(get_sagemaker)]
