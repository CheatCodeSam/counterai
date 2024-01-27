import contextlib
from typing import Annotated, AsyncIterator

import boto3
from fastapi import Depends, FastAPI
from mypy_boto3_sagemaker_runtime import SageMakerRuntimeClient

client = None


@contextlib.asynccontextmanager
async def sagemaker_lifespan(app: FastAPI) -> AsyncIterator[None]:
    global client
    client = boto3.client("sagemaker-runtime")
    yield
    client.close()


async def get_sagemaker():
    global client
    return client


SageMakerDependency = Annotated[SageMakerRuntimeClient, Depends(get_sagemaker)]
