"""CA business logic: root-CA bootstrap, CSR signing, revocation, status."""
import datetime as dt
import secrets

from common import crypto
from ca_server import models
from ca_server.database import SessionLocal


def get_or_create_root():
    db = SessionLocal()
    try:
        root = db.query(models.CaRoot).first()
        if root:
            return root
        key = crypto.generate_rsa_key()
        cert = crypto.create_self_signed_ca(key, "GovStack IM Root CA")
        root = models.CaRoot(
            name="GovStack IM Root CA",
            cert_pem=crypto.cert_to_pem(cert),
            key_pem=crypto.key_to_pem(key),
        )
        db.add(root)
        db.commit()
        db.refresh(root)
        return root
    finally:
        db.close()


def root_cert_pem() -> str:
    return get_or_create_root().cert_pem


def sign_csr(csr_pem: str, profile: str, requested_by: str = "") -> dict:
    root = get_or_create_root()
    ca_cert = crypto.load_cert(root.cert_pem)
    ca_key = crypto.load_key(root.key_pem)
    csr = crypto.load_csr(csr_pem)
    if not csr.is_signature_valid:
        raise ValueError("CSR signature invalid")

    serial = secrets.randbits(64) | 1
    cert = crypto.sign_csr(csr, ca_cert, ca_key, serial, profile=profile)
    cert_pem = crypto.cert_to_pem(cert)

    db = SessionLocal()
    try:
        rec = models.IssuedCert(
            serial=crypto.cert_serial(cert),
            subject_cn=crypto.cert_common_name(cert),
            profile=profile,
            requested_by=requested_by,
            cert_pem=cert_pem,
            status="good",
            not_after=cert.not_valid_after,
        )
        db.add(rec)
        db.commit()
        return {"serial": rec.serial, "cert_pem": cert_pem,
                "ca_cert_pem": root.cert_pem}
    finally:
        db.close()


def revoke(serial: str) -> bool:
    db = SessionLocal()
    try:
        rec = db.query(models.IssuedCert).filter_by(serial=serial).first()
        if not rec:
            return False
        rec.status = "revoked"
        rec.revoked_at = dt.datetime.utcnow()
        db.commit()
        return True
    finally:
        db.close()


def ocsp_status(serial: str) -> dict:
    """OCSP-style status check used by security servers before trusting a cert."""
    db = SessionLocal()
    try:
        rec = db.query(models.IssuedCert).filter_by(serial=serial).first()
        if not rec:
            return {"serial": serial, "status": "unknown"}
        status = rec.status
        if status == "good" and rec.not_after and rec.not_after < dt.datetime.utcnow():
            status = "expired"
        return {"serial": serial, "status": status,
                "subject_cn": rec.subject_cn, "profile": rec.profile}
    finally:
        db.close()


def delete_cert(serial: str) -> bool:
    db = SessionLocal()
    try:
        rec = db.query(models.IssuedCert).filter_by(serial=serial).first()
        if not rec:
            return False
        db.delete(rec)
        db.commit()
        return True
    finally:
        db.close()


def list_certs() -> list:
    db = SessionLocal()
    try:
        rows = db.query(models.IssuedCert).order_by(models.IssuedCert.id.desc()).all()
        return [{"serial": r.serial, "subject_cn": r.subject_cn, "profile": r.profile,
                 "status": r.status, "requested_by": r.requested_by,
                 "not_after": r.not_after.isoformat() if r.not_after else None,
                 "created_at": r.created_at.isoformat() if r.created_at else None}
                for r in rows]
    finally:
        db.close()
