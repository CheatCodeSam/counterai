import contextlib
from typing import Annotated, AsyncIterator

import boto3
from fastapi import Depends, FastAPI
from mypy_boto3_kms import KMSClient

client = None


@contextlib.asynccontextmanager
async def kms_lifespan(app: FastAPI) -> AsyncIterator[None]:
    global client
    client = boto3.client("kms")
    yield
    client.close()


async def get_kms():
    global client
    return client


KMSDependency = Annotated[KMSClient, Depends(get_kms)]
