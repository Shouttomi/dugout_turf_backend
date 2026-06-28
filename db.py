"""Database engine + session for Dugout Turf Arena.

Connects to the Aiven-hosted MySQL using credentials from the environment
(.env). Aiven requires TLS, so a CA cert path is passed through to PyMySQL.
"""
import base64
import os
import tempfile
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DB_NAME = os.getenv("DB_NAME", "turfbooking")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_SSL_CA = os.getenv("DB_SSL_CA", "").strip()
# On Vercel there is no writable filesystem for uploaded files.
# Encode your ca.pem with: base64 -w0 ca.pem
# Then set DB_SSL_CA_CONTENT to that string in your Vercel env vars.
DB_SSL_CA_CONTENT = os.getenv("DB_SSL_CA_CONTENT", "").strip()

# PyMySQL TLS args. Aiven needs SSL. If a CA file is provided we verify it.
connect_args = {}
if DB_SSL_CA_CONTENT:
    ca_bytes = base64.b64decode(DB_SSL_CA_CONTENT)
    tmp = tempfile.NamedTemporaryFile(suffix=".pem", delete=False)
    tmp.write(ca_bytes)
    tmp.close()
    connect_args["ssl"] = {"ca": tmp.name}
elif DB_SSL_CA:
    connect_args["ssl"] = {"ca": DB_SSL_CA}
else:
    # still negotiate TLS, just without local CA verification
    connect_args["ssl"] = {"ssl": True}

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=280,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
