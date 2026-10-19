import os
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

DB_PATH = os.getenv("DB_PATH", "data/anomaly_guard.db")
if os.getenv("TESTING") == "true":
    DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
else:
    os.makedirs(os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else ".", exist_ok=True)
    DATABASE_URL = f"sqlite:///{DB_PATH}"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=15000")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class Transaction(Base):
    __tablename__ = "parsed_transactions"
    tx_id = Column(String, primary_key=True)
    origin_account_id = Column(String, index=True)
    vendor_hash = Column(String)
    amount_kes = Column(Float)
    timestamp = Column(DateTime, index=True)
    tx_count_15min = Column(Integer)
    tx_count_24h = Column(Integer)
    time_since_last_tx = Column(Float)
    verdict = Column(Integer)
    score = Column(Float)

def init_db():
    Base.metadata.create_all(bind=engine)
