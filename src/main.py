import base64
import hashlib

from fastapi import FastAPI, HTTPException, UploadFile

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
    client_res = sagemaker.invoke_endpoint(
        EndpointName=config.sagemaker_endpoint, Body=contents
    )
    sagemaker_res = client_res["Body"].read().decode()
    if sagemaker_res == "HUMAN":
        sha256_hash = hashlib.sha256(contents).digest()
        certificate = kms.sign(
            KeyId=config.key_arn,
            Message=sha256_hash,
            SigningAlgorithm="RSASSA_PSS_SHA_256",
        )
        return {"certified": True, "certificate": certificate}
    else:
        return {"certified": False}


@app.post("/verify/")
async def verify(
    signature: str, file: UploadFile, kms: KMSDependency, config: ConfigDependency
):
    contents = await file.read()
    sha256_hash = hashlib.sha256(contents).digest()
    try:
        signature_bytes = base64.b64decode(signature)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid signature format")
    client_res = kms.verify(
        KeyId=config.key_arn,
        Message=sha256_hash,
        MessageType="DIGEST",
        Signature=signature_bytes,
        SigningAlgorithm="RSASSA_PSS_SHA_256",
    )
    is_valid_signature = client_res["SignatureValid"]
    return {
        "filename": file.filename,
        "sha256": sha256_hash.hex(),
        "is_valid": is_valid_signature,
    }


@app.get("/public-key/")
async def public_key(
    kms: KMSDependency,
    config: ConfigDependency,
):
    public_key_res = kms.get_public_key(KeyId=config.key_arn)
    public_key = public_key_res["PublicKey"]
    return {"public_key": public_key}
