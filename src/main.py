import base64
import hashlib

from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException, UploadFile
from mangum import Mangum
from pydantic import BaseModel, Field

from .config import ConfigDependency
from .dependencies.kms import KMSDependency, kms_lifespan
from .dependencies.sagemaker_runtime import SageMakerDependency, sagemaker_lifespan
from .util.lifespans import Lifespans

app = FastAPI(lifespan=Lifespans([kms_lifespan, sagemaker_lifespan]))


@app.post("/certify/")
async def certify(
    file: UploadFile,
    sagemaker: SageMakerDependency,
    kms: KMSDependency,
    config: ConfigDependency,
):
    contents = await file.read()
    # client_res = sagemaker.invoke_endpoint(EndpointName=config.sagemaker_endpoint, Body=contents)  # noqa: ERA001
    sagemaker_res = "HUMAN"
    if sagemaker_res == "HUMAN":
        sha256_hash = hashlib.sha256(contents).digest()
        certificate = kms.sign(
            KeyId=config.key_id,
            Message=sha256_hash,
            SigningAlgorithm="RSASSA_PSS_SHA_256",
        )
        base64_encoded_data = base64.b64encode(certificate["Signature"])
        return {"certified": True, "certificate": base64_encoded_data}
    else:
        return {"certified": False, "certificate": None}


class VerifyBody(BaseModel):
    signature: str = Field(description="The digital signature.")
    sha256_hash_hex: str = Field(description="The SHA256 hash of the file content.")


@app.post("/verify/")
async def verify(
    body: VerifyBody,
    kms: KMSDependency,
    config: ConfigDependency,
):
    try:
        signature_bytes = base64.b64decode(body.signature)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid signature format")
    try:
        sha256_hash = bytes.fromhex(body.sha256_hash_hex)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid sha256 hash")
    is_valid_signature = False
    try:
        client_res = kms.verify(
            KeyId=config.key_id,
            Message=sha256_hash,
            Signature=signature_bytes,
            SigningAlgorithm="RSASSA_PSS_SHA_256",
        )
        is_valid_signature = client_res["SignatureValid"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "KMSInvalidSignatureException":
            is_valid_signature = False
        else:
            raise HTTPException(
                status_code=500, detail={"message": "Internal Server Error"}
            )
    return {
        "is_valid": is_valid_signature,
    }


@app.get("/public-key/")
async def public_key(
    kms: KMSDependency,
    config: ConfigDependency,
):
    public_key_res = kms.get_public_key(KeyId=config.key_id)
    public_key = public_key_res["PublicKey"]
    public_key_base64 = base64.b64encode(public_key).decode()
    return {"public_key": public_key_base64}


handler = Mangum(app)
