import datetime as dt

from sqlalchemy import Column, DateTime, Integer, String, Text

from ca_server.database import Base


class CaRoot(Base):
    __tablename__ = "ca_root"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    cert_pem = Column(Text, nullable=False)
    key_pem = Column(Text, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)


class IssuedCert(Base):
    __tablename__ = "issued_cert"
    id = Column(Integer, primary_key=True)
    serial = Column(String(64), unique=True, nullable=False)
    subject_cn = Column(String(255))
    profile = Column(String(32))
    requested_by = Column(String(255))
    cert_pem = Column(Text, nullable=False)
    status = Column(String(16), default="good")  # good | revoked
    not_after = Column(DateTime)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)
