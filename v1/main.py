"""CA Server — issues and manages X.509 certificates for the whole federation.

Independent server. Port 9001. DB: ca_db.
Roles (mirrors X-Road approved CA + OCSP responder):
  * Self-signed Root CA
  * Signs CSRs into auth / sign / tsa / ocsp certificates
  * Revocation + OCSP-style status endpoint
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ca_server import ca_core, database

app = FastAPI(title="IM CA Server", version="1.0")


class SignReq(BaseModel):
    csr_pem: str
    profile: str = "generic"
    requested_by: str = ""


class RevokeReq(BaseModel):
    serial: str


@app.on_event("startup")
def _startup():
    database.init()
    ca_core.get_or_create_root()


@app.get("/api/ca-cert", response_class=PlainTextResponse)
def ca_cert():
    return ca_core.root_cert_pem()


@app.post("/api/sign")
def sign(req: SignReq):
    try:
        return ca_core.sign_csr(req.csr_pem, req.profile, req.requested_by)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/revoke")
def revoke(req: RevokeReq):
    ok = ca_core.revoke(req.serial)
    if not ok:
        raise HTTPException(404, "serial not found")
    return {"revoked": req.serial}


@app.get("/api/ocsp/{serial}")
def ocsp(serial: str):
    return ca_core.ocsp_status(serial)


@app.get("/api/certs")
def certs():
    return ca_core.list_certs()


@app.delete("/api/certs/{serial}")
def delete_cert(serial: str):
    if not ca_core.delete_cert(serial):
        raise HTTPException(404, "serial not found")
    return {"deleted": serial}


app.mount("/", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static"),
                           html=True), name="static")
