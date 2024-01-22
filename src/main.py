from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, UploadFile
import hashlib
import boto3
import os

from mypy_boto3_kms import KMSClient

async def get_kms():
    client = boto3.client('kms')
    print("booting")
    try:
        yield client
    finally:
        print("closing")
        client.close()

KMSDependency = Annotated[KMSClient, Depends(get_kms)]

app = FastAPI()

@app.post("/certify/")
async def certify(file: UploadFile):
    contents = await file.read()
    print(contents)
    return {"certified": True}
 

@app.post("/verify/")
async def verify(signature: str, file: UploadFile, kms: KMSDependency):
    contents = await file.read()
    contents.decode()
    sha256_hash = hashlib.sha256(contents).digest()
    key_arn = os.environ.get("AWS_KMS_KEY_ARN")
    if not key_arn:
        raise HTTPException(status_code=500, detail="Key ARN not in Env")
    client_res = kms.verify(
        KeyId=key_arn,
        Message=sha256_hash,
        MessageType="RAW",
        Signature=signature.encode(),
        SigningAlgorithm="ECDSA_SHA_256"
        )
    is_valid_signature = client_res['SignatureValid']
    return {"filename": file.filename, "sha256": sha256_hash, "is_valid": is_valid_signature}
