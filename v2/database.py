import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import declarative_base
from common.dbutil import init_db, make_session_factory, SessionProxy
from common import settings

DB_NAME = settings.get("CA_DB_NAME", "ca_server", "db_name", "ca_db")
Base = declarative_base()
engine = None
SessionLocal = SessionProxy()


def init():
    global engine
    import ca_server.models  # noqa: F401  ensure models are registered
    engine = init_db(DB_NAME, Base)
    SessionLocal.configure(make_session_factory(engine))
